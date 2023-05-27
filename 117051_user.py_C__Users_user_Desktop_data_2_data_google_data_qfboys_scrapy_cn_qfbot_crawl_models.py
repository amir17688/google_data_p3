#!/usr/bin/env python
# coding=utf-8
# vim: set et sw=4 ts=4 sts=4
# Author: YuanLin
# Created: 2015-07-25 11:16 CST

import hashlib
from datetime import datetime

from flask import url_for, current_app
from werkzeug import security
from flask_mail import Message
from flask_security import UserMixin

from ..ext import db, mail, redis_store


class User(db.Document, UserMixin):
    id = db.SequenceField(primary_key=True)

    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    current_sign_in_at = db.DateTimeField(default=datetime.utcnow,
                                          required=True)
    last_sign_in_at = db.DateTimeField(default=datetime.utcnow)

    is_active = db.BooleanField(default=True)
    created = db.DateTimeField(default=datetime.utcnow())
    updated = db.DateTimeField(default=datetime.utcnow())
    roles = db.IntField(default=0)
    group = db.IntField(default=0)

    def __str__(self):
        return self.cn

    def url(self):
        return url_for('user.detail', id=str(self.id))

    @property
    def email_md5(self):
        email = self.email.strip()
        if isinstance(email, unicode):
            email = email.encode('utf-8')
        return hashlib.md5(email).hexdigest()

    def avatar(self, size=48):
        return "{0}{1}.jpg?size={2}".format(
            current_app.config['GRAVATAR_BASE_URL'], self.email_md5, size
        )

    @staticmethod
    def generate_password(password):
        return security.generate_password_hash(
            current_app.config['SECRET_KEY'] + password
        )

    @staticmethod
    def create_token(length=16):
        return security.gen_salt(length)

    @classmethod
    def create_user(cls, username, email, password, **kwargs):
        password = cls.generate_password(password)
        return cls.objects.create(
            username=username, email=email, password=password, **kwargs
        )

    def set_password(self, password):
        self.password = self.generate_password(password)

    def check_password(self, password):
        return security.check_password_hash(
            self.password,
            current_app.config['SECRET_KEY'] + password
        )

    def reset_password(self):
        redis_store.set(self.username + 'token', self.create_token())
        redis_store.expire(self.username + 'token', 3600)
        msg = Message("Reset your password",
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[self.email])
        msg.body = "link to check token callback"
        mail.send(msg)

    def verify_reset_password_token(self, token):
        if token != redis_store.get(self.username + 'token'):
            return False, 'token expired or wrong'
        else:
            return True, 'success'

    def change_password(self, password, token):
        result = self.verify_reset_password_token(token)
        if result[0]:
            if self.password == User.generate_password(password):
                return False, 'duplicate password'
            else:
                self.password = User.generate_password(password)
                self.save()
                redis_store.remove(self.username + 'token')
                return True, 'success'
        else:
            return result

    def __unicode__(self):
        return self.username

    @property
    def id(self):
        return self.pk

    @classmethod
    def by_email(cls, email):
        return cls.objects(email=email).first()

    meta = {
        'indexes': ['id'],
        'ordering': ['id']
    }
