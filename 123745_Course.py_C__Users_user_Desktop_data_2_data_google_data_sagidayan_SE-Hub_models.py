import json

__author__ = 'Aran'
from google.appengine.ext import db

class Course(db.Model):
    courseName = db.StringProperty(required=True)
    campusId = db.IntegerProperty(required=True)
    master_id = db.IntegerProperty(required=True)
    # projects = db.StringListProperty(required=True,default=[])
    startDate = db.DateProperty(required=True)
    endDate = db.DateProperty(required=True)
    membersId = db.StringListProperty(required=True)

    def to_JSON(self):
        data = {'courseName' : self.courseName,
                'campusId' : self.campusId,
                'master_id' : self.master_id,
                # 'projects' : self.projects,
                'startDate' : {
                    'year': self.startDate.year,
                    'month': self.startDate.month,
                    'day': self.startDate.day,
                },
                'endDate' : {
                    'year': self.endDate.year,
                    'month': self.endDate.month,
                    'day': self.endDate.day,
                },
                'membersId' : self.membersId,
                'id' : self.key().id()
        }
        return json.dumps(data)
