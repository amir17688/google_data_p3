# Copyright 2016 iNuron NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Contains various decorator
"""

import math
import re
import json
import inspect
import time
from ovs.dal.lists.userlist import UserList
from ovs.dal.lists.storagerouterlist import StorageRouterList
from ovs.dal.helpers import Toolbox as DalToolbox
from rest_framework.response import Response
from toolbox import Toolbox
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, NotAcceptable, Throttled
from rest_framework import status
from rest_framework.request import Request
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404
from django.conf import settings
from ovs.dal.exceptions import ObjectNotFoundException
from backend.serializers.serializers import FullSerializer
from ovs.log.logHandler import LogHandler
from ovs.extensions.storage.volatilefactory import VolatileFactory
from ovs.extensions.generic.volatilemutex import VolatileMutex


logger = LogHandler.get('api')
regex = re.compile('^(.*; )?version=(?P<version>([0-9]+|\*)?)(;.*)?$')


def _find_request(args):
    """
    Finds the "request" object in args
    """
    for item in args:
        if isinstance(item, Request) or isinstance(item, WSGIRequest):
            return item


def required_roles(roles):
    """
    Role validation decorator
    """
    def wrap(f):
        """
        Wrapper function
        """
        def new_function(*args, **kw):
            """
            Wrapped function
            """
            request = _find_request(args)
            if not hasattr(request, 'user') or not hasattr(request, 'client'):
                raise NotAuthenticated()
            user = UserList.get_user_by_username(request.user.username)
            if user is None:
                raise NotAuthenticated()
            if not Toolbox.is_token_in_roles(request.token, roles):
                raise PermissionDenied('This call requires roles: %s' % (', '.join(roles)))
            return f(*args, **kw)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def load(object_type=None, min_version=settings.VERSION[0], max_version=settings.VERSION[-1]):
    """
    Parameter discovery decorator
    """
    def wrap(f):
        """
        Wrapper function
        """
        def _try_parse(value):
            """
            Tries to parse a value to a pythonic value
            """
            if value == 'true' or value == 'True':
                return True
            if value == 'false' or value == 'False':
                return False
            return value

        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            request = _find_request(args)
            new_kwargs = {}
            # Find out the arguments of the decorated function
            function_info = inspect.getargspec(f)
            if function_info.defaults is None:
                mandatory_vars = function_info.args[1:]
                optional_vars = []
            else:
                mandatory_vars = function_info.args[1:-len(function_info.defaults)]
                optional_vars = function_info.args[len(mandatory_vars) + 1:]
            # Check versioning
            version = regex.match(request.META['HTTP_ACCEPT']).groupdict()['version']
            versions = (max(min_version, settings.VERSION[0]), min(max_version, settings.VERSION[-1]))
            if version == '*':  # If accepting all versions, it defaults to the highest one
                version = versions[1]
            version = int(version)
            if version < versions[0] or version > versions[1]:
                raise NotAcceptable('API version requirements: {0} <= <version> <= {1}. Got {2}'.format(versions[0], versions[1], version))
            if 'version' in mandatory_vars:
                new_kwargs['version'] = version
                mandatory_vars.remove('version')
            # Fill request parameter, if available
            if 'request' in mandatory_vars:
                new_kwargs['request'] = request
                mandatory_vars.remove('request')
            # Fill main object, if required
            if 'pk' in kwargs and object_type is not None:
                typename = object_type.__name__.lower()
                try:
                    instance = object_type(kwargs['pk'])
                    if typename in mandatory_vars:
                        new_kwargs[typename] = instance
                        mandatory_vars.remove(typename)
                except ObjectNotFoundException:
                    raise Http404()
            # Fill local storagerouter, if requested
            if 'local_storagerouter' in mandatory_vars:
                storagerouter = StorageRouterList.get_by_machine_id(settings.UNIQUE_ID)
                new_kwargs['local_storagerouter'] = storagerouter
                mandatory_vars.remove('local_storagerouter')
            # Fill mandatory parameters
            post_data = request.DATA if hasattr(request, 'DATA') else request.POST
            get_data = request.QUERY_PARAMS if hasattr(request, 'QUERY_PARAMS') else request.GET
            for name in mandatory_vars:
                if name in kwargs:
                    new_kwargs[name] = kwargs[name]
                else:
                    if name not in post_data:
                        if name not in get_data:
                            raise NotAcceptable('Invalid data passed: {0} is missing'.format(name))
                        new_kwargs[name] = _try_parse(get_data[name])
                    else:
                        new_kwargs[name] = _try_parse(post_data[name])
            # Try to fill optional parameters
            for name in optional_vars:
                if name in kwargs:
                    new_kwargs[name] = kwargs[name]
                else:
                    if name in post_data:
                        new_kwargs[name] = _try_parse(post_data[name])
                    elif name in get_data:
                        new_kwargs[name] = _try_parse(get_data[name])
            # Call the function
            return f(args[0], **new_kwargs)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def return_list(object_type, default_sort=None):
    """
    List decorator
    """
    def wrap(f):
        """
        Wrapper function
        """
        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            request = _find_request(args)

            # 1. Pre-loading request data
            sort = request.QUERY_PARAMS.get('sort')
            if sort is None and default_sort is not None:
                sort = default_sort
            sort = None if sort is None else [s for s in reversed(sort.split(','))]
            page = request.QUERY_PARAMS.get('page')
            page = int(page) if page is not None and page.isdigit() else None
            page_size = request.QUERY_PARAMS.get('page_size')
            page_size = int(page_size) if page_size is not None and page_size.isdigit() else None
            page_size = page_size if page_size in [10, 25, 50, 100] else 10
            contents = request.QUERY_PARAMS.get('contents')
            contents = None if contents is None else contents.split(',')

            # 2. Construct hints for decorated function (so it can provide full objects if required)
            if 'hints' not in kwargs:
                kwargs['hints'] = {}
            kwargs['hints']['full'] = sort is not None or contents is not None

            # 3. Fetch data
            data_list = f(*args, **kwargs)
            guid_list = isinstance(data_list, list) and len(data_list) > 0 and isinstance(data_list[0], basestring)

            # 4. Sorting
            if sort is not None:
                if guid_list is True:
                    data_list = [object_type(guid) for guid in data_list]
                    guid_list = False  # The list is converted to objects
                for sort_item in sort:
                    desc = sort_item[0] == '-'
                    field = sort_item[1 if desc else 0:]
                    data_list.sort(key=lambda e: DalToolbox.extract_key(e, field), reverse=desc)

            # 5. Paging
            total_items = len(data_list)
            page_metadata = {'total_items': total_items,
                             'current_page': 1,
                             'max_page': 1,
                             'page_size': page_size,
                             'start_number': min(1, total_items),
                             'end_number': total_items}
            if page is not None:
                max_page = int(math.ceil(total_items / (page_size * 1.0)))
                if page > max_page:
                    page = max_page
                if page == 0:
                    start_number = -1
                    end_number = 0
                else:
                    start_number = (page - 1) * page_size  # Index - e.g. 0 for page 1, 10 for page 2
                    end_number = start_number + page_size  # Index - e.g. 10 for page 1, 20 for page 2
                data_list = data_list[start_number: end_number]
                page_metadata = dict(page_metadata.items() + {'current_page': max(1, page),
                                                              'max_page': max(1, max_page),
                                                              'start_number': start_number + 1,
                                                              'end_number': min(total_items, end_number)}.items())

            # 6. Serializing
            if contents is not None:
                if guid_list is True:
                    data_list = [object_type(guid) for guid in data_list]
                data = FullSerializer(object_type, contents=contents, instance=data_list, many=True).data
            else:
                if guid_list is False:
                    data_list = [item.guid for item in data_list]
                data = data_list

            result = {'data': data,
                      '_paging': page_metadata,
                      '_contents': contents,
                      '_sorting': [s for s in reversed(sort)] if sort else sort}

            # 7. Building response
            return Response(result, status=status.HTTP_200_OK)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def return_object(object_type):
    """
    Object decorator
    """
    def wrap(f):
        """
        Wrapper function
        """
        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            request = _find_request(args)

            # 1. Pre-loading request data
            contents = request.QUERY_PARAMS.get('contents')
            contents = None if contents is None else contents.split(',')

            # 5. Serializing
            obj = f(*args, **kwargs)
            return Response(FullSerializer(object_type, contents=contents, instance=obj).data, status=status.HTTP_200_OK)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def return_task():
    """
    Object decorator
    """
    def wrap(f):
        """
        Wrapper function
        """
        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            task = f(*args, **kwargs)
            return Response(task.id, status=status.HTTP_200_OK)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def return_plain():
    """
    Decorator to return plain data
    """

    def wrap(f):
        """
        Wrapper function
        """

        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            result = f(*args, **kwargs)
            return Response(result, status=status.HTTP_200_OK)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function

    return wrap


def limit(amount, per, timeout):
    """
    Rate-limits the decorated call
    """
    def wrap(f):
        """
        Wrapper function
        """
        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            request = _find_request(args)

            now = time.time()
            key = 'ovs_api_limit_{0}.{1}_{2}'.format(
                f.__module__, f.__name__,
                request.META['HTTP_X_REAL_IP']
            )
            client = VolatileFactory.get_client()
            with VolatileMutex(key):
                rate_info = client.get(key, {'calls': [],
                                             'timeout': None})
                active_timeout = rate_info['timeout']
                if active_timeout is not None:
                    if active_timeout > now:
                        logger.warning('Call {0} is being throttled with a wait of {1}'.format(key, active_timeout - now))
                        raise Throttled(wait=active_timeout - now)
                    else:
                        rate_info['timeout'] = None
                rate_info['calls'] = [call for call in rate_info['calls'] if call > (now - per)] + [now]
                calls = len(rate_info['calls'])
                if calls > amount:
                    rate_info['timeout'] = now + timeout
                    client.set(key, rate_info)
                    logger.warning('Call {0} is being throttled with a wait of {1}'.format(key, timeout))
                    raise Throttled(wait=timeout)
                client.set(key, rate_info)
            return f(*args, **kwargs)

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function
    return wrap


def log(log_slow=True):
    """
    Task logger
    :param log_slow: Indicates whether a slow call should be logged
    """

    def wrap(f):
        """
        Wrapper function
        """

        def new_function(*args, **kwargs):
            """
            Wrapped function
            """
            request = _find_request(args)
            method_args = list(args)[:]
            method_args = method_args[method_args.index(request) + 1:]

            # Log the call
            metadata = {'meta': dict((str(key), str(value)) for key, value in request.META.iteritems()),
                        'request': dict((str(key), str(value)) for key, value in request.REQUEST.iteritems()),
                        'cookies': dict((str(key), str(value)) for key, value in request.COOKIES.iteritems())}
            _logger = LogHandler.get('log', name='api')
            _logger.info('[{0}.{1}] - {2} - {3} - {4} - {5}'.format(
                f.__module__,
                f.__name__,
                getattr(request, 'client').user_guid if hasattr(request, 'client') else None,
                json.dumps(method_args),
                json.dumps(kwargs),
                json.dumps(metadata)
            ))

            # Call the function
            start = time.time()
            return_value = f(*args, **kwargs)
            duration = time.time() - start
            if duration > 5 and log_slow is True:
                logger.warning('API call {0}.{1} took {2}s'.format(f.__module__, f.__name__, round(duration, 2)))
            return return_value

        new_function.__name__ = f.__name__
        new_function.__module__ = f.__module__
        return new_function

    return wrap
