import json

__author__ = 'Aran'
from google.appengine.ext import db
from models.User import User

class Project(db.Model):
    projectName = db.StringProperty(required=True)
    courseId = db.IntegerProperty(required=True)
    master_id = db.IntegerProperty(required=True)
    grade = db.IntegerProperty(required=True, default=0)
    logo_url = db.StringProperty(required=False, default=None)
    gitRepository = db.StringProperty(required=True)
    membersId = db.StringListProperty(required=True)
    info = db.TextProperty(required=False, default="{}")

    def to_JSON(self):
        members = []
        for id in self.membersId:
            members.append(dict(json.loads(User.get_by_id(int(id)).to_JSON())))
        data = {'projectName' : self.projectName,
                'courseId' : self.courseId,
                'master_id' : self.master_id,
                'grade' : self.grade,
                'logo_url' : self.logo_url,
                'gitRepository' : self.gitRepository,
                'members': members,
                'info': json.loads(self.info),
                'id': self.key().id()
                }
        return json.dumps(data)
