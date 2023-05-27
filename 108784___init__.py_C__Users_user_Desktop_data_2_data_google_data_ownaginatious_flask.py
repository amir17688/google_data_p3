from __future__ import absolute_import, division, \
                       print_function, unicode_literals
from collections import defaultdict
from functools import wraps
from io import open
from flask import request
from flask import Response
import six
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


class BasicRoleAuthError(Exception):
    pass


class UnknownVerbError(Exception):
    pass


class UserAlreadyDefinedError(BasicRoleAuthError):
    pass


class UserNotDefined(BasicRoleAuthError):
    pass


class BadRoleError(BasicRoleAuthError):
    pass


class BasicRoleAuth(object):

    __VERBS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')

    def __init__(self, user_file=None):

        self.users = {}
        self.roles = defaultdict(set)

        if user_file:
            self.load_from_file(user_file)

    def load_from_file(self, user_file):
        """
        Loads users/roles from a file.

        user_file -- file to load the user/roles from
        """

        with open(user_file, 'r+t', encoding='utf8') as f:
            for l in f.readlines():
                user, password, roles = l.strip().split(':', 2)
                roles = roles.split(',')
                self.add_user(user, password)
                self.add_roles(user, roles)

    def save_to_file(self, user_file):
        """
        Saves the current set of users/roles to a file.

        user_file -- file to save the user/roles to
        """

        with open(user_file, 'w+t', encoding='utf8') as f:
            for user, password in sorted(self.users.items()):
                roles = sorted(list(self.roles[user]))
                f.write("%s:%s:%s\n" % (user, password, ','.join(roles)))

    def add_user(self, user, password, roles=None):
        """
        Adds a user to authenticate as.

        user     -- name of the user
        password -- password of the user
        roles    -- an optional list of roles to add
                    to the user
        """

        if user in self.users:
            raise UserAlreadyDefinedError(user)
        self.users[user] = password
        if roles:
            self.add_roles(user, roles)

    def delete_user(self, user):
        """
        Deletes a user.

        user -- name of the user
        """

        if user in self.users:
            del self.users[user]
        if user in self.roles:
            del self.roles[user]

    def add_roles(self, user, roles):
        """
        Adds one or more roles to a user. Adding the
        same role more than once has no effect.

        user  -- name of the user
        roles -- one or more roles to add
        """

        if user not in self.users:
            raise UserNotDefined(user)
        roles = (roles,) if isinstance(roles, six.string_types) else roles
        for role in roles:
            if ',' in role:
                raise BadRoleError('\',\' not allowed in role name (%s) '
                                   'for user %s' % (role, user))
            self.roles[user].add(role)

    def delete_roles(self, user, roles):
        """
        Deletes one or more roles from a user. Removing the
        same role more than once has no effect.

        user  -- name of the user
        roles -- one or more roles to remove
        """

        if user not in self.users:
            raise UserNotDefined(user)
        roles = (roles,) if isinstance(roles, six.string_types) else roles
        for role in roles:
            self.roles[user].remove(role)

    def no_authentication(self):
        """
        Sends a 401 response that enables basic auth.
        """

        return Response(
                'User identity could not be verified.\n'
                'Please login with proper credentials', 401,
                {
                    'WWW-Authenticate': 'Basic realm="Login Required"'
                })

    def no_authorization(self):
        """
        Sends a 401 response indicating authorization failure.
        """

        return Response(
                'The authenticated user is not authorized for the '
                'attempted operation.', 401)

    def _process_targets(self, target):
        """
        Processes a rules/user listing from
        the following forms:

            1. 'role/user'
            2. ('role/user_1', 'role/user_2', ..., 'role/user_n')
            3. {
                    'verb_1,verb_2,...,verb_n': 'role/user',
                    'verb_1,verb_2,...,verb_n':
                        ('role/user_1', ..., 'role/user_n')
                    ...
                }

        Into:

            {
                'GET': set(['role/user_1', ..., 'role/user_n']),
                'POST': set(['role/user_1', ..., 'role/user_n']),
                'PUT': set(['role/user_1', ..., 'role/user_n']),
                'PATCH': set(['role/user_1', ..., 'role/user_n']),
                'DELETE': set(['role/user_1', ..., 'role/user_n'])
            }

        target -- rules to process
        """

        new_target = defaultdict(set)

        if not isinstance(target, dict):
            if isinstance(target, six.string_types):
                target = (target,)
            target = set(target)
            for v in self.__VERBS:
                new_target[v].update(target)
            return new_target
        for k, v in target.items():
            if isinstance(v, six.string_types):
                v = (v,)
            v = set(v)
            for m in (m.upper() for m in k.split(',')):
                if m not in self.__VERBS:
                    raise UnknownVerbError(m)
                new_target[m].update(v)
        return new_target

    def require(self, users=(), roles=(), test_auth=None, test_method=None):
        """
        Authenticates/authorizes a request based on the content of the
        request.authorization parameter.

        users       -- users permitted to call this method
        roles       -- roles permitted to call this method
        test_auth   -- credentials only for testing
        test_method -- method only for testing
        """

        users = self._process_targets(users)
        roles = self._process_targets(roles)

        def loaded_decorated(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                auth = test_auth or request.authorization
                method = test_method.upper() if test_method else request.method
                authenticated = auth and (auth.username in self.users) and \
                    self.users[auth.username] == auth.password
                if not authenticated:
                    return self.no_authentication()
                allowed_users = users[method] if users else None
                allowed_roles = roles[method] if roles else None
                if allowed_users or allowed_roles:
                    auth_as_user = auth.username in allowed_users
                    auth_as_role = allowed_roles & self.roles[auth.username]
                    if not auth_as_user and not auth_as_role:
                        return self.no_authorization()
                return f(*args, **kwargs)
            return decorated
        return loaded_decorated
