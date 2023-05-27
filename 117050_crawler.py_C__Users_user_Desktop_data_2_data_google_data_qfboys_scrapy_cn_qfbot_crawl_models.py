#!/usr/bin/env python
# coding=utf-8
# vim: set et sw=4 ts=4 sts=4
# Author: YuanLin
# Created: 2015-07-25 11:16 CST

from datetime import datetime

from ..ext import db


class Spider(db.Document):
    id = db.SequenceField(primary_key=True)
    created = db.DateTimeField(default=datetime.utcnow, required=True)
    updated = db.DateTimeField(default=datetime.utcnow, required=True)
    name = db.StringField(max_length=50, required=True, unique=True)

    is_active = db.StringField(max_length=50, unique=True)
    description = db.StringField(max_length=120, required=True)
    priority = db.IntField(default=0)
    posts = db.ListField(db.ReferenceField('Post'))

    def __unicode__(self):
        return self.name

    meta = {
        "indexes": ['-priority', 'updated', 'name', 'id'],
        "ordering": ['-priority']
    }
