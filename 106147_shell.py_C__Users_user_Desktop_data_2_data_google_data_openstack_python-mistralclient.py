# Copyright 2015 - StackStorm, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
Command-line interface to the Mistral APIs
"""

import logging
import sys

from mistralclient.api import client
import mistralclient.commands.v2.action_executions
import mistralclient.commands.v2.actions
import mistralclient.commands.v2.cron_triggers
import mistralclient.commands.v2.environments
import mistralclient.commands.v2.executions
import mistralclient.commands.v2.members
import mistralclient.commands.v2.services
import mistralclient.commands.v2.tasks
import mistralclient.commands.v2.workbooks
import mistralclient.commands.v2.workflows
from mistralclient.openstack.common import cliutils as c

from cliff import app
from cliff import command
from cliff import commandmanager

import argparse

LOG = logging.getLogger(__name__)


class OpenStackHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog, indent_increment=2, max_help_position=32,
                 width=None):
        super(OpenStackHelpFormatter, self).__init__(
            prog,
            indent_increment,
            max_help_position,
            width
        )

    def start_section(self, heading):
        # Title-case the headings.
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


class HelpAction(argparse.Action):
    """Custom help action.

    Provide a custom action so the -h and --help options
    to the main app will print a list of the commands.

    The commands are determined by checking the CommandManager
    instance, passed in as the "default" value for the action.

    """
    def __call__(self, parser, namespace, values, option_string=None):
        outputs = []
        max_len = 0
        app = self.default
        parser.print_help(app.stdout)
        app.stdout.write('\nCommands for API v2 :\n')

        for name, ep in sorted(app.command_manager):
            factory = ep.load()
            cmd = factory(self, None)
            one_liner = cmd.get_description().split('\n')[0]
            outputs.append((name, one_liner))
            max_len = max(len(name), max_len)

        for (name, one_liner) in outputs:
            app.stdout.write('  %s  %s\n' % (name.ljust(max_len), one_liner))

        sys.exit(0)


class BashCompletionCommand(command.Command):
    """Prints all of the commands and options for bash-completion."""

    def take_action(self, parsed_args):
        commands = set()
        options = set()

        for option, _action in self.app.parser._option_string_actions.items():
            options.add(option)

        for command_name, _cmd in self.app.command_manager:
            commands.add(command_name)

        print(' '.join(commands | options))


class MistralShell(app.App):

    def __init__(self):
        super(MistralShell, self).__init__(
            description=__doc__.strip(),
            version=mistralclient.__version__,
            command_manager=commandmanager.CommandManager('mistral.cli'),
        )

        # Set v2 commands by default
        self._set_shell_commands(self._get_commands_v2())

    def configure_logging(self):
        log_lvl = logging.DEBUG if self.options.debug else logging.WARNING
        logging.basicConfig(
            format="%(levelname)s (%(module)s) %(message)s",
            level=log_lvl
        )
        logging.getLogger('iso8601').setLevel(logging.WARNING)

        if self.options.verbose_level <= 1:
            logging.getLogger('requests').setLevel(logging.WARNING)

    def build_option_parser(self, description, version,
                            argparse_kwargs=None):
        """Return an argparse option parser for this application.

        Subclasses may override this method to extend
        the parser with more global options.

        :param description: full description of the application
        :paramtype description: str
        :param version: version number for the application
        :paramtype version: str
        :param argparse_kwargs: extra keyword argument passed to the
                                ArgumentParser constructor
        :paramtype extra_kwargs: dict
        """
        argparse_kwargs = argparse_kwargs or {}
        parser = argparse.ArgumentParser(
            description=description,
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
            **argparse_kwargs
        )
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s {0}'.format(version),
            help='Show program\'s version number and exit.'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='count',
            dest='verbose_level',
            default=self.DEFAULT_VERBOSE_LEVEL,
            help='Increase verbosity of output. Can be repeated.',
        )
        parser.add_argument(
            '--log-file',
            action='store',
            default=None,
            help='Specify a file to log output. Disabled by default.',
        )
        parser.add_argument(
            '-q', '--quiet',
            action='store_const',
            dest='verbose_level',
            const=0,
            help='Suppress output except warnings and errors.',
        )
        parser.add_argument(
            '-h', '--help',
            action=HelpAction,
            nargs=0,
            default=self,  # tricky
            help="Show this help message and exit.",
        )
        parser.add_argument(
            '--debug',
            default=False,
            action='store_true',
            help='Show tracebacks on errors.',
        )
        parser.add_argument(
            '--os-mistral-url',
            action='store',
            dest='mistral_url',
            default=c.env('OS_MISTRAL_URL'),
            help='Mistral API host (Env: OS_MISTRAL_URL)'
        )
        parser.add_argument(
            '--os-mistral-version',
            action='store',
            dest='mistral_version',
            default=c.env('OS_MISTRAL_VERSION', default='v2'),
            help='Mistral API version (default = v2) (Env: '
                 'OS_MISTRAL_VERSION)'
        )
        parser.add_argument(
            '--os-mistral-service-type',
            action='store',
            dest='service_type',
            default=c.env('OS_MISTRAL_SERVICE_TYPE', default='workflowv2'),
            help='Mistral service-type (should be the same name as in '
                 'keystone-endpoint) (default = workflowv2) (Env: '
                 'OS_MISTRAL_SERVICE_TYPE)'
        )
        parser.add_argument(
            '--os-mistral-endpoint-type',
            action='store',
            dest='endpoint_type',
            default=c.env('OS_MISTRAL_ENDPOINT_TYPE', default='publicURL'),
            help='Mistral endpoint-type (should be the same name as in '
                 'keystone-endpoint) (default = publicURL) (Env: '
                 'OS_MISTRAL_ENDPOINT_TYPE)'
        )
        parser.add_argument(
            '--os-username',
            action='store',
            dest='username',
            default=c.env('OS_USERNAME', default='admin'),
            help='Authentication username (Env: OS_USERNAME)'
        )
        parser.add_argument(
            '--os-password',
            action='store',
            dest='password',
            default=c.env('OS_PASSWORD'),
            help='Authentication password (Env: OS_PASSWORD)'
        )
        parser.add_argument(
            '--os-tenant-id',
            action='store',
            dest='tenant_id',
            default=c.env('OS_TENANT_ID'),
            help='Authentication tenant identifier (Env: OS_TENANT_ID)'
        )
        parser.add_argument(
            '--os-tenant-name',
            action='store',
            dest='tenant_name',
            default=c.env('OS_TENANT_NAME', 'Default'),
            help='Authentication tenant name (Env: OS_TENANT_NAME)'
        )
        parser.add_argument(
            '--os-auth-token',
            action='store',
            dest='token',
            default=c.env('OS_AUTH_TOKEN'),
            help='Authentication token (Env: OS_AUTH_TOKEN)'
        )
        parser.add_argument(
            '--os-auth-url',
            action='store',
            dest='auth_url',
            default=c.env('OS_AUTH_URL'),
            help='Authentication URL (Env: OS_AUTH_URL)'
        )
        parser.add_argument(
            '--os-cacert',
            action='store',
            dest='cacert',
            default=c.env('OS_CACERT'),
            help='Authentication CA Certificate (Env: OS_CACERT)'
        )
        parser.add_argument(
            '--insecure',
            action='store_true',
            dest='insecure',
            default=c.env('MISTRALCLIENT_INSECURE', default=False),
            help='Disables SSL/TLS certificate verification '
                 '(Env: MISTRALCLIENT_INSECURE)'
        )
        return parser

    def initialize_app(self, argv):
        self._clear_shell_commands()

        ver = client.determine_client_version(self.options.mistral_version)

        self._set_shell_commands(self._get_commands(ver))

        do_help = ('help' in argv) or ('-h' in argv) or not argv

        # Set default for auth_url if not supplied. The default is not
        # set at the parser to support use cases where auth is not enabled.
        # An example use case would be a developer's environment.
        if not self.options.auth_url:
            if self.options.password or self.options.token:
                self.options.auth_url = 'http://localhost:35357/v3'

        # bash-completion should not require authentification.
        if do_help or ('bash-completion' in argv):
            self.options.auth_url = None

        self.client = client.client(
            mistral_url=self.options.mistral_url,
            username=self.options.username,
            api_key=self.options.password,
            project_name=self.options.tenant_name,
            auth_url=self.options.auth_url,
            project_id=self.options.tenant_id,
            endpoint_type=self.options.endpoint_type,
            service_type=self.options.service_type,
            auth_token=self.options.token,
            cacert=self.options.cacert,
            insecure=self.options.insecure
        )

        # Adding client_manager variable to make mistral client work with
        # unified openstack client.
        ClientManager = type(
            'ClientManager',
            (object,),
            dict(workflow_engine=self.client)
        )

        self.client_manager = ClientManager()

    def _set_shell_commands(self, cmds_dict):
        for k, v in cmds_dict.items():
            self.command_manager.add_command(k, v)

    def _clear_shell_commands(self):
        exclude_cmds = ['help', 'complete']

        cmds = self.command_manager.commands.copy()
        for k, v in cmds.items():
            if k not in exclude_cmds:
                self.command_manager.commands.pop(k)

    def _get_commands(self, version):
        if version == 2:
            return self._get_commands_v2()

        return {}

    @staticmethod
    def _get_commands_v2():
        return {
            'bash-completion': BashCompletionCommand,
            'workbook-list': mistralclient.commands.v2.workbooks.List,
            'workbook-get': mistralclient.commands.v2.workbooks.Get,
            'workbook-create': mistralclient.commands.v2.workbooks.Create,
            'workbook-delete': mistralclient.commands.v2.workbooks.Delete,
            'workbook-update': mistralclient.commands.v2.workbooks.Update,
            'workbook-get-definition':
            mistralclient.commands.v2.workbooks.GetDefinition,
            'workbook-validate': mistralclient.commands.v2.workbooks.Validate,
            'workflow-list': mistralclient.commands.v2.workflows.List,
            'workflow-get': mistralclient.commands.v2.workflows.Get,
            'workflow-create': mistralclient.commands.v2.workflows.Create,
            'workflow-delete': mistralclient.commands.v2.workflows.Delete,
            'workflow-update': mistralclient.commands.v2.workflows.Update,
            'workflow-get-definition':
            mistralclient.commands.v2.workflows.GetDefinition,
            'workflow-validate': mistralclient.commands.v2.workflows.Validate,
            'environment-create':
            mistralclient.commands.v2.environments.Create,
            'environment-delete':
            mistralclient.commands.v2.environments.Delete,
            'environment-update':
            mistralclient.commands.v2.environments.Update,
            'environment-list': mistralclient.commands.v2.environments.List,
            'environment-get': mistralclient.commands.v2.environments.Get,
            'run-action': mistralclient.commands.v2.action_executions.Create,
            'action-execution-list':
            mistralclient.commands.v2.action_executions.List,
            'action-execution-get':
            mistralclient.commands.v2.action_executions.Get,
            'action-execution-get-input':
            mistralclient.commands.v2.action_executions.GetInput,
            'action-execution-get-output':
            mistralclient.commands.v2.action_executions.GetOutput,
            'action-execution-update':
            mistralclient.commands.v2.action_executions.Update,
            'action-execution-delete':
            mistralclient.commands.v2.action_executions.Delete,
            'execution-create': mistralclient.commands.v2.executions.Create,
            'execution-delete': mistralclient.commands.v2.executions.Delete,
            'execution-update': mistralclient.commands.v2.executions.Update,
            'execution-list': mistralclient.commands.v2.executions.List,
            'execution-get': mistralclient.commands.v2.executions.Get,
            'execution-get-input':
            mistralclient.commands.v2.executions.GetInput,
            'execution-get-output':
            mistralclient.commands.v2.executions.GetOutput,
            'task-list': mistralclient.commands.v2.tasks.List,
            'task-get': mistralclient.commands.v2.tasks.Get,
            'task-get-published': mistralclient.commands.v2.tasks.GetPublished,
            'task-get-result': mistralclient.commands.v2.tasks.GetResult,
            'task-rerun': mistralclient.commands.v2.tasks.Rerun,
            'action-list': mistralclient.commands.v2.actions.List,
            'action-get': mistralclient.commands.v2.actions.Get,
            'action-create': mistralclient.commands.v2.actions.Create,
            'action-delete': mistralclient.commands.v2.actions.Delete,
            'action-update': mistralclient.commands.v2.actions.Update,
            'action-get-definition':
            mistralclient.commands.v2.actions.GetDefinition,
            'cron-trigger-list': mistralclient.commands.v2.cron_triggers.List,
            'cron-trigger-get': mistralclient.commands.v2.cron_triggers.Get,
            'cron-trigger-create':
            mistralclient.commands.v2.cron_triggers.Create,
            'cron-trigger-delete':
            mistralclient.commands.v2.cron_triggers.Delete,
            'service-list': mistralclient.commands.v2.services.List,
            'member-create': mistralclient.commands.v2.members.Create,
            'member-delete': mistralclient.commands.v2.members.Delete,
            'member-update': mistralclient.commands.v2.members.Update,
            'member-list': mistralclient.commands.v2.members.List,
            'member-get': mistralclient.commands.v2.members.Get,
        }


def main(argv=sys.argv[1:]):
    return MistralShell().run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
