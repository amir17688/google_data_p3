from peewee import *

from .basemodel import BaseModel
from .user import User
from .counter import Counter

class Project(BaseModel):
    creator = ForeignKeyField(User)
    ancestor = ForeignKeyField('self', null=True)
    owner_name = CharField()
    name = CharField(max_length=200)
    description = CharField(max_length=1024, null=True)
    upstream = IntegerField(null=True)
    counter = ForeignKeyField(Counter, null=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    def init_repo(self):
        pass

    def init_cardlists(self):
        pass

    def post_save(self):
        self.init_repo()
        self.init_cardlists()

    @property
    def repo(self):
        pass

    @property
    def fullname(self):
        return u'%s/%s' % (owner_name, name)

    @property
    def path_info(self):
        return '%s.git' % self.id

    def __unicode__(self):
        return unicode(self.fullname)

