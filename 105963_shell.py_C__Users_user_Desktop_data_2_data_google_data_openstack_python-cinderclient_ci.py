
# Copyright 2011-2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Command-line interface to the OpenStack Cinder API.
"""

from __future__ import print_function

import argparse
import getpass
import logging
import sys

import requests

from cinderclient import api_versions
from cinderclient import client
from cinderclient import exceptions as exc
from cinderclient import utils
import cinderclient.auth_plugin
from cinderclient._i18n import _

from keystoneclient import discover
from keystoneclient import session
from keystoneclient.auth.identity import v2 as v2_auth
from keystoneclient.auth.identity import v3 as v3_auth
from keystoneclient.exceptions import DiscoveryFailure
import six.moves.urllib.parse as urlparse
from oslo_utils import encodeutils
from oslo_utils import importutils
from oslo_utils import strutils

osprofiler_profiler = importutils.try_import("osprofiler.profiler")

from cinderclient import _i18n
# Enable i18n lazy translation
_i18n.enable_lazy()

DEFAULT_MAJOR_OS_VOLUME_API_VERSION = "2"
DEFAULT_CINDER_ENDPOINT_TYPE = 'publicURL'
V1_SHELL = 'cinderclient.v1.shell'
V2_SHELL = 'cinderclient.v2.shell'
V3_SHELL = 'cinderclient.v3.shell'

logging.basicConfig()
logger = logging.getLogger(__name__)


class CinderClientArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(CinderClientArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        # FIXME(lzyeval): if changes occur in argparse.ArgParser._check_value
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, "error: %(errmsg)s\nTry '%(mainp)s help %(subp)s'"
                     " for more information.\n" %
                     {'errmsg': message.split(choose_from)[0],
                      'mainp': progparts[0],
                      'subp': progparts[2]})

    def _get_option_tuples(self, option_string):
        """Avoid ambiguity in argument abbreviation.

        The idea of this method is to override the default behaviour to
        avoid ambiguity in the abbreviation feature of argparse.
        In the case that the ambiguity is generated by 2 or more parameters
        and only one is visible in the help and the others are with
        help=argparse.SUPPRESS, the ambiguity is solved by taking the visible
        one.
        The use case is for parameters that are left hidden for backward
        compatibility.
        """

        result = super(CinderClientArgumentParser, self)._get_option_tuples(
            option_string)

        if len(result) > 1:
            aux = [x for x in result if x[0].help != argparse.SUPPRESS]
            if len(aux) == 1:
                result = aux

        return result


class OpenStackCinderShell(object):

    def get_base_parser(self):
        parser = CinderClientArgumentParser(
            prog='cinder',
            description=__doc__.strip(),
            epilog='Run "cinder help SUBCOMMAND" for help on a subcommand.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--version',
                            action='version',
                            version=cinderclient.__version__)

        parser.add_argument('-d', '--debug',
                            action='store_true',
                            default=utils.env('CINDERCLIENT_DEBUG',
                                              default=False),
                            help="Shows debugging output.")

        parser.add_argument('--os-auth-system',
                            metavar='<auth-system>',
                            default=utils.env('OS_AUTH_SYSTEM'),
                            help='Defaults to env[OS_AUTH_SYSTEM].')
        parser.add_argument('--os_auth_system',
                            help=argparse.SUPPRESS)

        parser.add_argument('--service-type',
                            metavar='<service-type>',
                            help='Service type. '
                            'For most actions, default is volume.')
        parser.add_argument('--service_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--service-name',
                            metavar='<service-name>',
                            default=utils.env('CINDER_SERVICE_NAME'),
                            help='Service name. '
                            'Default=env[CINDER_SERVICE_NAME].')
        parser.add_argument('--service_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--volume-service-name',
                            metavar='<volume-service-name>',
                            default=utils.env('CINDER_VOLUME_SERVICE_NAME'),
                            help='Volume service name. '
                            'Default=env[CINDER_VOLUME_SERVICE_NAME].')
        parser.add_argument('--volume_service_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-endpoint-type',
                            metavar='<os-endpoint-type>',
                            default=utils.env('CINDER_ENDPOINT_TYPE',
                            default=utils.env('OS_ENDPOINT_TYPE',
                            default=DEFAULT_CINDER_ENDPOINT_TYPE)),
                            help='Endpoint type, which is publicURL or '
                            'internalURL. '
                            'Default=env[OS_ENDPOINT_TYPE] or '
                            'nova env[CINDER_ENDPOINT_TYPE] or '
                            + DEFAULT_CINDER_ENDPOINT_TYPE + '.')
        parser.add_argument('--os_endpoint_type',
                            help=argparse.SUPPRESS)
        parser.add_argument('--endpoint-type',
                            metavar='<endpoint-type>',
                            dest='endpoint_type',
                            help='DEPRECATED! Use --os-endpoint-type.')
        parser.add_argument('--endpoint_type',
                            dest='endpoint_type',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-volume-api-version',
                            metavar='<volume-api-ver>',
                            default=utils.env('OS_VOLUME_API_VERSION',
                                              default=None),
                            help='Block Storage API version. '
                            'Accepts X, X.Y (where X is major and Y is minor '
                            'part).'
                            'Default=env[OS_VOLUME_API_VERSION].')
        parser.add_argument('--os_volume_api_version',
                            help=argparse.SUPPRESS)

        parser.add_argument('--bypass-url',
                            metavar='<bypass-url>',
                            dest='bypass_url',
                            default=utils.env('CINDERCLIENT_BYPASS_URL'),
                            help="Use this API endpoint instead of the "
                            "Service Catalog. Defaults to "
                            "env[CINDERCLIENT_BYPASS_URL].")
        parser.add_argument('--bypass_url',
                            help=argparse.SUPPRESS)

        parser.add_argument('--retries',
                            metavar='<retries>',
                            type=int,
                            default=0,
                            help='Number of retries.')

        if osprofiler_profiler:
            parser.add_argument('--profile',
                                metavar='HMAC_KEY',
                                help='HMAC key to use for encrypting context '
                                'data for performance profiling of operation. '
                                'This key needs to match the one configured '
                                'on the cinder api server. '
                                'Without key the profiling will not be '
                                'triggered even if osprofiler is enabled '
                                'on server side.')

        self._append_global_identity_args(parser)

        # The auth-system-plugins might require some extra options
        cinderclient.auth_plugin.discover_auth_systems()
        cinderclient.auth_plugin.load_auth_system_opts(parser)

        return parser

    def _append_global_identity_args(self, parser):
        # FIXME(bklei): these are global identity (Keystone) arguments which
        # should be consistent and shared by all service clients. Therefore,
        # they should be provided by python-keystoneclient. We will need to
        # refactor this code once this functionality is available in
        # python-keystoneclient.

        parser.add_argument(
            '--os-auth-strategy', metavar='<auth-strategy>',
            default=utils.env('OS_AUTH_STRATEGY', default='keystone'),
            help=_('Authentication strategy (Env: OS_AUTH_STRATEGY'
                   ', default keystone). For now, any other value will'
                   ' disable the authentication.'))
        parser.add_argument(
            '--os_auth_strategy',
            help=argparse.SUPPRESS)

        parser.add_argument('--os-username',
                            metavar='<auth-user-name>',
                            default=utils.env('OS_USERNAME',
                                              'CINDER_USERNAME'),
                            help='OpenStack user name. '
                            'Default=env[OS_USERNAME].')
        parser.add_argument('--os_username',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-password',
                            metavar='<auth-password>',
                            default=utils.env('OS_PASSWORD',
                                              'CINDER_PASSWORD'),
                            help='Password for OpenStack user. '
                            'Default=env[OS_PASSWORD].')
        parser.add_argument('--os_password',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-name',
                            metavar='<auth-tenant-name>',
                            default=utils.env('OS_TENANT_NAME',
                                              'CINDER_PROJECT_ID'),
                            help='Tenant name. '
                            'Default=env[OS_TENANT_NAME].')
        parser.add_argument('--os_tenant_name',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-tenant-id',
                            metavar='<auth-tenant-id>',
                            default=utils.env('OS_TENANT_ID',
                                              'CINDER_TENANT_ID'),
                            help='ID for the tenant. '
                            'Default=env[OS_TENANT_ID].')
        parser.add_argument('--os_tenant_id',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os-auth-url',
                            metavar='<auth-url>',
                            default=utils.env('OS_AUTH_URL',
                                              'CINDER_URL'),
                            help='URL for the authentication service. '
                            'Default=env[OS_AUTH_URL].')
        parser.add_argument('--os_auth_url',
                            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-id', metavar='<auth-user-id>',
            default=utils.env('OS_USER_ID'),
            help=_('Authentication user ID (Env: OS_USER_ID).'))

        parser.add_argument(
            '--os_user_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-domain-id',
            metavar='<auth-user-domain-id>',
            default=utils.env('OS_USER_DOMAIN_ID'),
            help='OpenStack user domain ID. '
            'Defaults to env[OS_USER_DOMAIN_ID].')

        parser.add_argument(
            '--os_user_domain_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-user-domain-name',
            metavar='<auth-user-domain-name>',
            default=utils.env('OS_USER_DOMAIN_NAME'),
            help='OpenStack user domain name. '
                 'Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument(
            '--os_user_domain_name',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-project-id',
            metavar='<auth-project-id>',
            default=utils.env('OS_PROJECT_ID'),
            help='Another way to specify tenant ID. '
            'This option is mutually exclusive with '
            ' --os-tenant-id. '
            'Defaults to env[OS_PROJECT_ID].')

        parser.add_argument(
            '--os_project_id',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-project-name',
            metavar='<auth-project-name>',
            default=utils.env('OS_PROJECT_NAME'),
            help='Another way to specify tenant name. '
                 'This option is mutually exclusive with '
                 ' --os-tenant-name. '
                 'Defaults to env[OS_PROJECT_NAME].')

        parser.add_argument(
            '--os_project_name',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-project-domain-id',
            metavar='<auth-project-domain-id>',
            default=utils.env('OS_PROJECT_DOMAIN_ID'),
            help='Defaults to env[OS_PROJECT_DOMAIN_ID].')

        parser.add_argument(
            '--os-project-domain-name',
            metavar='<auth-project-domain-name>',
            default=utils.env('OS_PROJECT_DOMAIN_NAME'),
            help='Defaults to env[OS_PROJECT_DOMAIN_NAME].')

        parser.add_argument('--os-region-name',
                            metavar='<region-name>',
                            default=utils.env('OS_REGION_NAME',
                                              'CINDER_REGION_NAME'),
                            help='Region name. '
                            'Default=env[OS_REGION_NAME].')
        parser.add_argument('--os_region_name',
                            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-token', metavar='<token>',
            default=utils.env('OS_TOKEN'),
            help=_('Defaults to env[OS_TOKEN].'))
        parser.add_argument(
            '--os_token',
            help=argparse.SUPPRESS)

        parser.add_argument(
            '--os-url', metavar='<url>',
            default=utils.env('OS_URL'),
            help=_('Defaults to env[OS_URL].'))
        parser.add_argument(
            '--os_url',
            help=argparse.SUPPRESS)

        # Register the CLI arguments that have moved to the session object.
        session.Session.register_cli_options(parser)
        parser.set_defaults(insecure=utils.env('CINDERCLIENT_INSECURE',
                                               default=False))

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        if version == '2':
            actions_module = importutils.import_module(V2_SHELL)
        elif version == '3':
            actions_module = importutils.import_module(V3_SHELL)
        else:
            actions_module = importutils.import_module(V1_SHELL)

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        for extension in self.extensions:
            self._find_actions(subparsers, extension.module)

        self._add_bash_completion_subparser(subparsers)

        return parser

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=OpenStackHelpFormatter)

        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hyphen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)

            subparser.add_argument('-h', '--help',
                                   action='help',
                                   help=argparse.SUPPRESS,)

            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def setup_debugging(self, debug):
        if not debug:
            return

        streamhandler = logging.StreamHandler()
        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        streamhandler.setFormatter(logging.Formatter(streamformat))
        logger.setLevel(logging.WARNING)
        logger.addHandler(streamhandler)

        client_logger = logging.getLogger(client.__name__)
        ch = logging.StreamHandler()
        client_logger.setLevel(logging.DEBUG)
        client_logger.addHandler(ch)
        if hasattr(requests, 'logging'):
            requests.logging.getLogger(requests.__name__).addHandler(ch)
        # required for logging when using a keystone session
        ks_logger = logging.getLogger("keystoneclient")
        ks_logger.setLevel(logging.DEBUG)

    def _delimit_metadata_args(self, argv):
        """This function adds -- separator at the appropriate spot
        """
        word = '--metadata'
        tmp = []
        # flag is true in between metadata option and next option
        metadata_options = False
        if word in argv:
            for arg in argv:
                if arg == word:
                    metadata_options = True
                elif metadata_options:
                    if arg.startswith('--'):
                        metadata_options = False
                    elif '=' not in arg:
                        tmp.append(u'--')
                        metadata_options = False
                tmp.append(arg)
            return tmp
        else:
            return argv

    def main(self, argv):
        # Parse args once to find version and debug settings
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self.setup_debugging(options.debug)
        api_version_input = True
        self.options = options

        if not options.os_volume_api_version:
            api_version = api_versions.get_api_version(
                DEFAULT_MAJOR_OS_VOLUME_API_VERSION)
        else:
            api_version = api_versions.get_api_version(
                options.os_volume_api_version)

        # build available subcommands based on version
        major_version_string = "%s" % api_version.ver_major
        self.extensions = client.discover_extensions(major_version_string)
        self._run_extension_hooks('__pre_parse_args__')

        subcommand_parser = self.get_subcommand_parser(major_version_string)
        self.parser = subcommand_parser

        if options.help or not argv:
            subcommand_parser.print_help()
            return 0

        argv = self._delimit_metadata_args(argv)
        args = subcommand_parser.parse_args(argv)
        self._run_extension_hooks('__post_parse_args__', args)

        # Short-circuit and deal with help right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        elif args.func == self.do_bash_completion:
            self.do_bash_completion(args)
            return 0

        (os_username, os_password, os_tenant_name, os_auth_url,
         os_region_name, os_tenant_id, endpoint_type,
         service_type, service_name, volume_service_name, bypass_url,
         cacert, os_auth_system) = (
             args.os_username, args.os_password,
             args.os_tenant_name, args.os_auth_url,
             args.os_region_name, args.os_tenant_id,
             args.os_endpoint_type,
             args.service_type, args.service_name,
             args.volume_service_name,
             args.bypass_url, args.os_cacert,
             args.os_auth_system)
        if os_auth_system and os_auth_system != "keystone":
            auth_plugin = cinderclient.auth_plugin.load_plugin(os_auth_system)
        else:
            auth_plugin = None

        if not service_type:
            service_type = client.SERVICE_TYPES[major_version_string]

        # FIXME(usrleon): Here should be restrict for project id same as
        # for os_username or os_password but for compatibility it is not.

        # V3 stuff
        project_info_provided = ((self.options.os_tenant_name or
                                  self.options.os_tenant_id) or
                                 (self.options.os_project_name and
                                  (self.options.os_project_domain_name or
                                   self.options.os_project_domain_id)) or
                                 self.options.os_project_id)

        if not utils.isunauthenticated(args.func):
            if auth_plugin:
                auth_plugin.parse_opts(args)

            if not auth_plugin or not auth_plugin.opts:
                if not os_username:
                    raise exc.CommandError("You must provide a user name "
                                           "through --os-username or "
                                           "env[OS_USERNAME].")

            if not os_password:
                # No password, If we've got a tty, try prompting for it
                if hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                    # Check for Ctl-D
                    try:
                        os_password = getpass.getpass('OS Password: ')
                    except EOFError:
                        pass
                # No password because we didn't have a tty or the
                # user Ctl-D when prompted.
                if not os_password:
                    raise exc.CommandError("You must provide a password "
                                           "through --os-password, "
                                           "env[OS_PASSWORD] "
                                           "or, prompted response.")

            if not project_info_provided:
                raise exc.CommandError(_(
                    "You must provide a tenant_name, tenant_id, "
                    "project_id or project_name (with "
                    "project_domain_name or project_domain_id) via "
                    "  --os-tenant-name (env[OS_TENANT_NAME]),"
                    "  --os-tenant-id (env[OS_TENANT_ID]),"
                    "  --os-project-id (env[OS_PROJECT_ID])"
                    "  --os-project-name (env[OS_PROJECT_NAME]),"
                    "  --os-project-domain-id "
                    "(env[OS_PROJECT_DOMAIN_ID])"
                    "  --os-project-domain-name "
                    "(env[OS_PROJECT_DOMAIN_NAME])"
                ))

            if not os_auth_url:
                if os_auth_system and os_auth_system != 'keystone':
                    os_auth_url = auth_plugin.get_auth_url()

            if not os_auth_url:
                raise exc.CommandError(
                    "You must provide an authentication URL "
                    "through --os-auth-url or env[OS_AUTH_URL].")

        if not project_info_provided:
            raise exc.CommandError(_(
                "You must provide a tenant_name, tenant_id, "
                "project_id or project_name (with "
                "project_domain_name or project_domain_id) via "
                "  --os-tenant-name (env[OS_TENANT_NAME]),"
                "  --os-tenant-id (env[OS_TENANT_ID]),"
                "  --os-project-id (env[OS_PROJECT_ID])"
                "  --os-project-name (env[OS_PROJECT_NAME]),"
                "  --os-project-domain-id "
                "(env[OS_PROJECT_DOMAIN_ID])"
                "  --os-project-domain-name "
                "(env[OS_PROJECT_DOMAIN_NAME])"
            ))

        if not os_auth_url:
            raise exc.CommandError(
                "You must provide an authentication URL "
                "through --os-auth-url or env[OS_AUTH_URL].")

        auth_session = None
        if not auth_plugin:
            auth_session = self._get_keystone_session()

        insecure = self.options.insecure

        self.cs = client.Client(api_version, os_username,
                                os_password, os_tenant_name, os_auth_url,
                                region_name=os_region_name,
                                tenant_id=os_tenant_id,
                                endpoint_type=endpoint_type,
                                extensions=self.extensions,
                                service_type=service_type,
                                service_name=service_name,
                                volume_service_name=volume_service_name,
                                bypass_url=bypass_url,
                                retries=options.retries,
                                http_log_debug=args.debug,
                                insecure=insecure,
                                cacert=cacert, auth_system=os_auth_system,
                                auth_plugin=auth_plugin,
                                session=auth_session)

        try:
            if not utils.isunauthenticated(args.func):
                self.cs.authenticate()
        except exc.Unauthorized:
            raise exc.CommandError("OpenStack credentials are not valid.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user.")

        endpoint_api_version = None
        # Try to get the API version from the endpoint URL.  If that fails fall
        # back to trying to use what the user specified via
        # --os-volume-api-version or with the OS_VOLUME_API_VERSION environment
        # variable.  Fail safe is to use the default API setting.
        try:
            endpoint_api_version = \
                self.cs.get_volume_api_version_from_endpoint()
        except exc.UnsupportedVersion:
            endpoint_api_version = options.os_volume_api_version
            if api_version_input:
                logger.warning("Cannot determine the API version from "
                               "the endpoint URL. Falling back to the "
                               "user-specified version: %s" %
                               endpoint_api_version)
            else:
                logger.warning("Cannot determine the API version from the "
                               "endpoint URL or user input. Falling back "
                               "to the default API version: %s" %
                               endpoint_api_version)

        profile = osprofiler_profiler and options.profile
        if profile:
            osprofiler_profiler.init(options.profile)

        args.func(self.cs, args)

        if profile:
            trace_id = osprofiler_profiler.get().get_base_id()
            print("Trace ID: %s" % trace_id)
            print("To display trace use next command:\n"
                  "osprofiler trace show --html %s " % trace_id)

    def _run_extension_hooks(self, hook_type, *args, **kwargs):
        """Runs hooks for all registered extensions."""
        for extension in self.extensions:
            extension.run_hooks(hook_type, *args, **kwargs)

    def do_bash_completion(self, args):
        """Prints arguments for bash_completion.

        Prints all commands and options to stdout so that the
        cinder.bash_completion script does not have to hard code them.
        """
        commands = set()
        options = set()
        for sc_str, sc in list(self.subcommands.items()):
            commands.add(sc_str)
            for option in sc._optionals._option_string_actions:
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @utils.arg('command', metavar='<subcommand>', nargs='?',
               help='Shows help for <subcommand>.')
    def do_help(self, args):
        """
        Shows help about this program or one of its subcommands.
        """
        if args.command:
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()

    def get_v2_auth(self, v2_auth_url):

        username = self.options.os_username
        password = self.options.os_password
        tenant_id = self.options.os_tenant_id
        tenant_name = self.options.os_tenant_name

        return v2_auth.Password(
            v2_auth_url,
            username=username,
            password=password,
            tenant_id=tenant_id,
            tenant_name=tenant_name)

    def get_v3_auth(self, v3_auth_url):

        username = self.options.os_username
        user_id = self.options.os_user_id
        user_domain_name = self.options.os_user_domain_name
        user_domain_id = self.options.os_user_domain_id
        password = self.options.os_password
        project_id = self.options.os_project_id or self.options.os_tenant_id
        project_name = (self.options.os_project_name
                        or self.options.os_tenant_name)
        project_domain_name = self.options.os_project_domain_name
        project_domain_id = self.options.os_project_domain_id

        return v3_auth.Password(
            v3_auth_url,
            username=username,
            password=password,
            user_id=user_id,
            user_domain_name=user_domain_name,
            user_domain_id=user_domain_id,
            project_id=project_id,
            project_name=project_name,
            project_domain_name=project_domain_name,
            project_domain_id=project_domain_id,
        )

    def _discover_auth_versions(self, session, auth_url):
        # discover the API versions the server is supporting based on the
        # given URL
        v2_auth_url = None
        v3_auth_url = None
        try:
            ks_discover = discover.Discover(session=session, auth_url=auth_url)
            v2_auth_url = ks_discover.url_for('2.0')
            v3_auth_url = ks_discover.url_for('3.0')
        except DiscoveryFailure:
            # Discovery response mismatch. Raise the error
            raise
        except Exception:
            # Some public clouds throw some other exception or doesn't support
            # discovery. In that case try to determine version from auth_url
            # API version from the original URL
            url_parts = urlparse.urlparse(auth_url)
            (scheme, netloc, path, params, query, fragment) = url_parts
            path = path.lower()
            if path.startswith('/v3'):
                v3_auth_url = auth_url
            elif path.startswith('/v2'):
                v2_auth_url = auth_url
            else:
                raise exc.CommandError('Unable to determine the Keystone'
                                       ' version to authenticate with '
                                       'using the given auth_url.')

        return (v2_auth_url, v3_auth_url)

    def _get_keystone_session(self, **kwargs):
        # first create a Keystone session
        cacert = self.options.os_cacert or None
        cert = self.options.os_cert or None
        insecure = self.options.insecure or False

        if insecure:
            verify = False
        else:
            verify = cacert or True

        ks_session = session.Session(verify=verify, cert=cert)
        # discover the supported keystone versions using the given url
        (v2_auth_url, v3_auth_url) = self._discover_auth_versions(
            session=ks_session,
            auth_url=self.options.os_auth_url)

        username = self.options.os_username or None
        user_domain_name = self.options.os_user_domain_name or None
        user_domain_id = self.options.os_user_domain_id or None

        auth = None
        if v3_auth_url and v2_auth_url:
            # support both v2 and v3 auth. Use v3 if possible.
            if username:
                if user_domain_name or user_domain_id:
                    # use v3 auth
                    auth = self.get_v3_auth(v3_auth_url)
                else:
                    # use v2 auth
                    auth = self.get_v2_auth(v2_auth_url)

        elif v3_auth_url:
            # support only v3
            auth = self.get_v3_auth(v3_auth_url)
        elif v2_auth_url:
            # support only v2
            auth = self.get_v2_auth(v2_auth_url)
        else:
            raise exc.CommandError('Unable to determine the Keystone version '
                                   'to authenticate with using the given '
                                   'auth_url.')

        ks_session.auth = auth
        return ks_session

# I'm picky about my shell help.


class OpenStackHelpFormatter(argparse.HelpFormatter):

    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        if sys.version_info >= (3, 0):
            OpenStackCinderShell().main(sys.argv[1:])
        else:
            OpenStackCinderShell().main(map(encodeutils.safe_decode,
                                            sys.argv[1:]))
    except KeyboardInterrupt:
        print("... terminating cinder client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        logger.debug(e, exc_info=1)
        print("ERROR: %s" % strutils.six.text_type(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":

    main()
