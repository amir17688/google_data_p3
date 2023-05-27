from flask.ext.script import Command
import re
import getpass

class CreateSuperUser(Command):
    def run(self):
        while True:
            username = raw_input('username(%s): ' % getpass.getuser())
            if username == '': 
                username = getpass.getuser()
            if not re.match(r'[A-Za-z\.0-9]+', username):
                print 'Invalid Username'
            else: break
        while True:
            email = raw_input('email: ')
            if not re.match(r'[A-Za-z\.0-9\+]+@\w+(\.\w+)*', email):
                print 'Invalid email'
            else: break
        while True:
            passwd = getpass.getpass('password: ')
            rpasswd = getpass.getpass('repeat: ')
            if passwd != rpasswd:
                print 'Password not matching!'
            else: break

        from vilya.models.user import User
        user = User()
        user.username = username
        user.email = email
        user.admin = True
        user.active = True
        user.set_password(passwd)
        user.save()
        print 'Super user created!'

