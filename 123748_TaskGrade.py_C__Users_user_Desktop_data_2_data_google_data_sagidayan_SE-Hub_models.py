__author__ = 'Aran'


import json
from google.appengine.ext import db


class TaskGrade(db.Model):
    taskId = db.IntegerProperty(required=True)
    userId = db.IntegerProperty(required=True)
    grade = db.IntegerProperty(required=False,default=0)


    def to_JSON(self):
        data = {'taskId' : self.taskId,
                'userId' : self.userId,
                'grade' : self.grade,
                'id' : self.key().id()
                }
        return json.dumps(data)
