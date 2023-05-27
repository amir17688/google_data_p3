from peewee import *

from flask_peewee.auth import BaseUser
from flask_peewee.admin import ModelAdmin

from .basemodel import BaseModel

class User(BaseModel, BaseUser):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(index=True)
    admin = BooleanField(default=True)
    active = BooleanField(default=True)

    @classmethod
    def authenticate(cls, username, password):
        try:
            user = cls.select().where(cls.username==username).get()
            if user.check_password(password):
                return user
        except cls.DoesNotExist:
            return None

    def __unicode__(self):
        return unicode(self.username)


class UserAdmin(ModelAdmin):
    columns = ('username', 'email', 'admin', 'active',)

    def save_model(self, instance, form, adding=False):
        orig_password = instance.password
        user = super(UserAdmin, self).save_model(instance, form, adding)
        if orig_password != form.password.data:
            user.set_password(form.password.data)
            user.save()
        return user
