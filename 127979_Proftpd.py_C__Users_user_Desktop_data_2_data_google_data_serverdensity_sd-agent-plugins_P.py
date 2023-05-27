"""
  Server Density Plugin
  Proftpd connection details

  https://github.com/serverdensity/sd-agent-plugins/
  Autor: @bitbeans
  Version: 1.0.0
"""
import json
import sys
import subprocess
import platform
import logging
import time
from decimal import *

try:
    """ Q&D check if there is a proftpd binary, so count creater: 1 """
    c = subprocess.check_output(
        "whereis proftpd | awk '{print NF}'", shell=True).strip()
    if float(c) < 2:
        raise Exception("Missing proftpd")
except Exception:
    sys.exit(0)


class Proftpd(object):

    def __init__(self, agentConfig, checksLogger, rawConfig):
        self.agentConfig = agentConfig
        self.checksLogger = checksLogger
        self.rawConfig = rawConfig
        self.version = platform.python_version_tuple()

    def run(self):
        data = {}
        if platform.system() == 'Linux':
            users = []
            connections = []
            try:
                e = subprocess.check_output(
                    "ftpwho -o oneline | grep '^[ 0-9]'", shell=True).strip()
                connections = e.split('\n')
                for connection in connections:
                    tmpuser = connection.split(' ')
                    if users.count(tmpuser[1]) == 0:
                        users.append(tmpuser[1])
            except subprocess.CalledProcessError:
                pass
            data = {'connections': len(connections),
                    'users': len(users)}
        else:
            self.checks_logger.error(
                'Plugin currently only available on Linux.')
        return data

if __name__ == '__main__':
    """Standalone test"""
    raw_agent_config = {
        'Proftpd': {
        }
    }

    main_checks_logger = logging.getLogger('Proftpd')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    proftpd_check = Proftpd({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(proftpd_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
