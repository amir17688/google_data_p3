from views import MainHandler, SQLMapHandler


handlers = [
    ('/', MainHandler),
    ('/sqlmap', SQLMapHandler),
]
