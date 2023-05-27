import tornado.web
from views import handlers as handlers_


class Application(tornado.web.Application):
    def __init__(self):
        handlers = handlers_
        settings = dict(debug=True, cookie_secret='&D(1Ihjc23hC)vjdskjf23090c=_09i34ngk')
        tornado.web.Application.__init__(self, handlers=handlers, **settings)
