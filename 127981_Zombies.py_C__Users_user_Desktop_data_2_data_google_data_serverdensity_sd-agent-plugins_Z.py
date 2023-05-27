"""
  Server Density Plugin
  Zombies measurements

  https://www.serverdensity.com/plugins/zombies/
  https://github.com/serverdensity/sd-agent-plugins/


  Version: 1.0.0
"""

import json
import logging
import platform
import sys
import subprocess
import time


class Zombies(object):

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.version = platform.python_version_tuple()

    def run(self):

        brains = {}

        if platform.system() == 'Linux':

            try:
                proc = subprocess.Popen(
                    ['top', '-b', '-n', '1'],
                    stdout=subprocess.PIPE,
                    close_fds=True)

                top_output = proc.communicate()[0]

                for line in top_output.split('\n'):
                    if not line:
                        continue

                    if line.startswith('Tasks') and line.endswith('zombie'):
                        try:
                            zombies_raw = line.split(',')[-1]
                            if 'zombie' in zombies_raw:
                                brains['zombies'] = zombies_raw.split()[0]
                        except Exception as exception:
                            self.checks_logger.error(
                                'Failed fetching zombie stat from "top" output'
                                .format(exception.message))

            except Exception as exception:
                self.checks_logger.error(
                    'Failed to generate list of containers. Error: {0}'.format(
                        exception.message))
        else:
            self.checks_logger.error(
                'Plugin currently only available on Linux.')

        return brains


if __name__ == '__main__':
    """Standalone test
    """

    raw_agent_config = {
        'Zombies': {
        }
    }

    main_checks_logger = logging.getLogger('Zombies')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    zombies_check = Zombies({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(zombies_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
