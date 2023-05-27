from peewee import *

from .basemodel import BaseModel
from .user import User


class Team(BaseModel):
    name = CharField(max_length=16, unique=True)
    description = CharField()
    creator = ForeignKeyField(User, related_name="teams")
    created_at = DateTimeField()
    updated_at = DateTimeField()

    def __unicode__(self):
        return unicode(self.name)
