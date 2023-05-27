from peewee import *
from .basemodel import BaseModel
from .user import User

NO_PERM = 0
READ_PERM = 1
WRITE_PERM = 2
ADMIN_PERM = 3

PERM_CHOICES = (
        (1, 'project'),
        (2, 'team'),
        )

PERM_MAP = {name:num for num, name in PERM_CHOICES}

class Permission(BaseModel):
    user = ForeignKeyField(User, related_name="permissions")
    perm_name = IntegerField(choices=PERM_CHOICES)
    target_id = IntegerField()
    level = IntegerField(
            choices = (
                (NO_PERM, 'no_permission'),
                (READ_PERM, 'read'),
                (WRITE_PERM, 'write'),
                (ADMIN_PERM, 'admin'),
                ))
    @classmethod
    def check_permission(cls, target, user, level):
        if not user:
            return target.anonymous_perm >= level
        try:
            return cls.select().where(
                    cls.user==user,
                    cls.perm_name==target.perm_name,
                    cls.target_id==target.id,
                    cls.level>=level).get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def add_permission(self, target, user, level):
        return cls.create(
                user=user,
                perm_name=target.perm_name,
                target_id=target.id,
                level=level,
                )
