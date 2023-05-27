import unittest
import datetime
import StringIO
import tempfile
import configparser

import flask
from flask_ini import FlaskIni

class BasicTestCase(unittest.TestCase):

    def setUp(self):
        test_config_file = StringIO.StringIO('''
[flask]
; should be a string
secret_key                 : 12345678
debug                      : true
permanent_session_lifetime : 100
server_name                = testserv
send_file_max_age_default  : 3600
some_other_flask_var       : something with multiple words

[wibble]
wobble : woo
warble = 123

[foo bar]
bar : http://baz/qux
interp : %(bar)s/hi
''')
        app = flask.Flask(__name__)
        with app.app_context():
            app.iniconfig = FlaskIni()
            # Tests the readfp() primarily - separate test case for read()
            app.iniconfig.readfp(test_config_file)

        @app.route('/hello')
        def hello_world():
            return 'Hello world!'

        self.app = app

    def test_string_var(self):
        self.assertEqual(self.app.config['SECRET_KEY'], '12345678')

    def test_secret_key_is_str(self):
        self.assertIsInstance(self.app.config['SECRET_KEY'], str)

    def test_bool_var(self):
        self.assertEqual(self.app.config['DEBUG'], True)

    def test_int_var(self):
        self.assertEqual(self.app.config['SEND_FILE_MAX_AGE_DEFAULT'], 3600)

    def test_timedelta_var(self):
        self.assertEqual(self.app.config['PERMANENT_SESSION_LIFETIME'],
                         datetime.timedelta(100))

    def test_var_declared_with_equals(self):
        self.assertEqual(self.app.config['SERVER_NAME'], 'testserv')

    def test_non_default_flask_var(self):
        self.assertEqual(self.app.config['SOME_OTHER_FLASK_VAR'],
                         'something with multiple words')

    def test_vars_are_used_by_flask(self):
        self.assertEqual(self.app.debug, True)
        self.assertEqual(self.app.secret_key, '12345678')
        with self.app.app_context():
            self.assertEqual(flask.url_for('hello_world'),
                             'http://testserv/hello')

    def test_non_flask_vars(self):
        self.assertEqual(self.app.iniconfig.get('wibble', 'wobble'), 'woo')
        self.assertEqual(self.app.iniconfig.getint('wibble', 'warble'), 123)
        self.assertEqual(self.app.iniconfig.get('foo bar', 'bar'),
                                                'http://baz/qux')

    def test_interp_var(self):
        self.assertEqual(self.app.iniconfig.get('foo bar', 'interp'),
                                               'http://baz/qux/hi')

    def test_supports_fallback(self):
        with self.assertRaises(configparser.NoOptionError):
            self.app.iniconfig.get('flask', 'non-existent option')

        self.assertEqual(self.app.iniconfig.get('flask', 'non-existent option', fallback='value'), 'value')

# Also test we can read OK from a file using the read() method
class ReadFromFileTestCase(unittest.TestCase):

    def setUp(self):
        app = flask.Flask(__name__)
        app.iniconfig = FlaskIni()
        self.app = app
        self.filename = 'test_config.ini'

    def test_read(self):
        with self.app.app_context():
            names = self.app.iniconfig.read(self.filename)
            self.assertEqual(names, [self.filename])
        self.assertEqual(self.app.config['SECRET'], 'abcxyz')
        self.assertEqual(self.app.debug, True)

