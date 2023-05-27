from peewee import *

from .basemodel import BaseModel

class Counter(BaseModel):
    count = IntegerField(default=0)
