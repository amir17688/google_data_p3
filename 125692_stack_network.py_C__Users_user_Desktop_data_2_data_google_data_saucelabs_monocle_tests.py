from o_test import test, tests
from contextlib import contextmanager

from monocle import _o
from monocle.callback import Callback
from monocle.stack import eventloop, network
from monocle.util import sleep

EOL = '\r\n'


class StackConnection(object):

    def __init__(self):
        self.buffer = ""
        self.is_closed = False
        self.is_reading = False
        self.read_cb = Callback()
        self.connect_cb = Callback()
        self.out = []
        self.disconnect_called = 0
        self.resume_called = 0

    def disconnect(self):
        self.disconnect_called += 1

    def closed(self):
        return self.is_closed

    def reading(self):
        return self.is_reading

    def resume(self):
        self.resume_called += 1

    def write(self, data):
        self.out.append(data)


@tests
class ConnectionTestCase(object):

    def __init__(self):
        self.stack_conn = StackConnection()
        self.conn = network.Connection(stack_conn=self.stack_conn)

    @property
    def buffer(self):
        return self.stack_conn.buffer

    @buffer.setter
    def buffer(self, value):
        self.stack_conn.buffer = value

    @_o
    def test(self):
        data = 'ok'
        self.buffer = data
        r = yield self.conn.read(2)
        assert r == data
        assert self.buffer == ''
        assert self.stack_conn.resume_called == 0

    @_o
    def test_read_delay(self):
        data = 'ok'
        self.buffer = 'o'
        self.conn.timeout = 0.2

        def populate():
            self.buffer += 'k'
            self.stack_conn.read_cb(None)

        eventloop.queue_task(0.1, populate)
        r = yield self.conn.read(2)
        assert r == data
        assert self.stack_conn.resume_called == 1
        yield sleep(0.2)  # ensure timeout has expired

    @_o
    def test_read_timeout(self):
        self.conn.timeout = 0.1
        try:
            yield self.conn.read(10)
        except network.ConnectionLost:
            pass
        else:
            raise Exception('ConnectionLost should be raised')
        assert self.stack_conn.resume_called == 1

    @_o
    def test_read_some(self):
        data = 'ok'
        self.buffer = data
        r = yield self.conn.read_some()
        assert r == data
        assert self.buffer == ''
        assert self.stack_conn.resume_called == 0

    @_o
    def test_read_some_delay(self):
        data = 'ok'
        self.conn.timeout = 0.2

        def populate():
            self.buffer = data
            self.stack_conn.read_cb(None)

        eventloop.queue_task(0.1, populate)
        r = yield self.conn.read_some()
        assert r == data
        assert self.stack_conn.resume_called == 1
        yield sleep(0.2)  # ensure timeout has expired

    @_o
    def test_read_some_timeout(self):
        self.conn.timeout = 0.1
        try:
            yield self.conn.read_some()
        except network.ConnectionLost:
            pass
        else:
            raise Exception('ConnectionLost should be raised')
        assert self.stack_conn.resume_called == 1

    @_o
    def test_read_util(self):
        data = 'hello.'
        self.buffer = 'hello.world'
        r = yield self.conn.read_until('.')
        assert r == data
        assert self.buffer == 'world'
        assert self.stack_conn.resume_called == 0

    @_o
    def test_readline(self):
        data = 'hello\n'
        self.buffer = 'hello\nworld'
        r = yield self.conn.readline()
        assert r == data
        assert self.buffer == 'world'
        assert self.stack_conn.resume_called == 0


@contextmanager
def network_server_running(addr, port):
    @_o
    def handler(conn):
        while True:
            try:
                msg = yield conn.read_until(EOL)
            except network.ConnectionLost:
                break
            yield conn.write('you said: ' + msg.strip() + EOL)
    service = network.Service(handler, bindaddr=addr, port=port)
    network.add_service(service)
    try:
        yield
    finally:
        service.stop()


@contextmanager
def network_client():
    client = network.Client()
    try:
        yield client
    finally:
        client.close()


@test
@_o
def test_client():
    addr = '127.0.0.1'
    port = 5555
    with network_server_running(addr, port):
        with network_client() as client:
            msg = 'ok'
            yield client.connect(addr, port)
            yield client.write(msg + EOL)
            result = yield client.read_until(EOL)
            assert result == 'you said: ' + msg + EOL
