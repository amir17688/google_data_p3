#-*- coding: utf-8 -*-
import md5
import pickle
from choco.contrib.cache import ChocoCache

class KakaoSession(object):
    def __init__(self, room, id, nick=''):
        self.room = room
        self.id = str(id)
        self.nick = nick

    @staticmethod
    def generate_key(room, user):
        key = '%s:%s' % (str(room), str(user))
        return md5.md5(key).hexdigest()

    @staticmethod
    def get_or_create(room, user, nick=''):
        room = str(room)
        user = str(user)
        key = KakaoSession.generate_key(room, user)
        # if session is already exists
        if ChocoCache.adapter.hexists('choco:sessions', key):
            session = ChocoCache.adapter.hget('choco:sessions', key)
            return pickle.loads(session)
        else:
            # room session list
            room_key = 'choco:room:%s:sessions' % room
            session = KakaoSession(room, user, nick)
            session = pickle.dumps(session)
            multi = ChocoCache.adapter.pipeline()
            multi.hset('choco:sessions', key, session)
            multi.sadd(room_key, key)
            multi.execute()
            session = pickle.loads(session)
            return session

    def update(self, message):
        if (self.nick == '' or self.nick != message.user_nick) \
        and len(message.user_nick) > 0:
            self.nick = message.user_nick
            self.save()

    def save(self):
        key = KakaoSession.generate_key(self.room, self.id)
        updated = pickle.dumps(self)
        ChocoCache.adapter.hset('choco:sessions', key, updated)

    def delete(self):
        key = KakaoSession.generate_key(self.room, self.id)
        multi = ChocoCache.adapter.pipeline()
        multi.hdel('choco:sessions', key)
        multi.execute()

    @property
    def is_admin(self):
        pass
        # admin_id = Cache.get(self.room, 'admin')
        # return admin_id == self.user
