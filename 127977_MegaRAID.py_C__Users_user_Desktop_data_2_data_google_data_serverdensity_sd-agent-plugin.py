"""
  Server Density Plugin
  MegaRAID monitor


  Version: 1.0.0
"""

import json
import logging
import platform
import sys
import subprocess
import time


class MegaRAID(object):
    """ Check the "State" of the controller using output from
        /opt/MegaRAID/MegaCli/MegaCli64 -LDInfo -Lall -aALL

    """

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.version = platform.python_version_tuple()

    def run(self):

        data = {'state': 'unknown'}

        try:
            proc = subprocess.Popen(
                ['sudo', '/opt/MegaRAID/MegaCli/MegaCli64', '-LDInfo',
                 '-Lall', '-aALL'],
                stdout=subprocess.PIPE,
                close_fds=True)
            output = proc.communicate()[0]
        except OSError as exception:
            self.checks_logger.error(
                'Unable to find /opt/MegaRAID/MegaCli/MegaCli64.'
                ' Error: {0}'.format(exception.message))
            return data

        for line in output.split("\n"):
            print line
            if line.startswith('State'):
                data['state'] = line.split(':')[1].replace(' ', '')

        return data


if __name__ == '__main__':
    """Standalone test
    """

    raw_agent_config = {
    }

    main_checks_logger = logging.getLogger('MegaRAID')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    megaraid_check = MegaRAID({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(megaraid_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
