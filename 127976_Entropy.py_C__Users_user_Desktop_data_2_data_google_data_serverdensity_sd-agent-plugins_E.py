"""
  Server Density Plugin
  Available Entropy on system
  http://plugins.serverdensity.com/entropy/
  https://github.com/serverdensity/sd-agent-plugins/
  Autor: @bitbeans
  Version: 1.0.1
"""
import json
import sys
import subprocess
import platform
import logging
import time
from decimal import *


class Entropy(object):

    def __init__(self, agentConfig, checksLogger, rawConfig):
        self.agentConfig = agentConfig
        self.checksLogger = checksLogger
        self.rawConfig = rawConfig
        self.version = platform.python_version_tuple()

    def run(self):
        data = {}
        if platform.system() == 'Linux':
            e = subprocess.check_output(
                "cat /proc/sys/kernel/random/entropy_avail", shell=True)
            data = {'available': float(e)}
        else:
            self.checksLogger.error(
                'Plugin currently only available on Linux.')
        return data

if __name__ == '__main__':
    """Standalone test"""
    raw_agent_config = {
        'Entropy': {
        }
    }

    main_checks_logger = logging.getLogger('Entropy')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    entropy_check = Entropy({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(entropy_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
