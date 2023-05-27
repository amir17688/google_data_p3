"""
  Server Density Plugin
  BackupNinja status

  https://github.com/serverdensity/sd-agent-plugins/


  Version: 1.0.0
"""

import json
import logging
import os.path
import re
import sys
import time
from datetime import datetime
from gzip import GzipFile


class BackupNinja(object):
    """SD Plugin for checking backupninja status.

    Parses the backupninja log at /var/log/backupninja.log
    """

    def __init__(self, agent_config, checks_logger, raw_config):
        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.log_parser = re.compile(
            "(\w{3} \d{2} \d{2}:\d{2}:\d{2}) Info: FINISHED: (\d)+ actions "
            "run. (\d)+ fatal. (\d)+ error. (\d)+ warning.")
        self.config = self.raw_config.get('BackupNinja', {})
        self.main_log = self.config.get(
            'main_log', '/var/log/backupninja.log')
        self.rotated_log_type = self.config.get(
            'rotated_log_type', 'sequence')

    def get_default_data(self):
        return {
            'actions': 0,
            'fatal': 0,
            'error': 0,
            'warning': 0,
            'age': -1
        }

    def get_latest_status(self, now, log_file):
        data = self.get_default_data()
        for line in log_file.readlines():
            match = self.log_parser.match(line)
            if match:
                entry_datestr = match.group(1)
                entry_datetime = datetime.strptime(
                    '{0} {1}'.format(now.year, entry_datestr),
                    '%Y %b %d %H:%M:%S')
                diff_date = now - entry_datetime
                total_seconds = (
                    diff_date.seconds + diff_date.days * 24 * 3600)
                data['age'] = int(round(total_seconds / 60))
                data['actions'] = match.group(2)
                data['fatal'] = match.group(3)
                data['error'] = match.group(4)
                data['warning'] = match.group(5)

        return data

    def run(self):

        now = datetime.now()
        if not os.path.exists(self.main_log):
            return self.get_default_data()

        log_file = open(self.main_log)

        data = self.get_latest_status(now, log_file)

        if data['age'] == -1:
            if self.rotated_log_type == 'date':
                log_file_path = '{0}-{1}.gz'.format(
                    self.main_log, now.strftime('%Y%m%d'))
            else:
                # Sequence type.
                log_file_path = '{0}.1.gz'.format(self.main_log)
            if not os.path.exists(log_file_path):
                return data

            log_file = GzipFile(log_file_path)
            return self.get_latest_status(now, log_file)

        return data


if __name__ == '__main__':
    """Standalone test."""

    main_checks_logger = logging.getLogger('BackupNinja')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    backupninja_check = BackupNinja({}, main_checks_logger, {})

    while True:
        try:
            print json.dumps(
                backupninja_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception("Unhandled exception")
        finally:
            time.sleep(60)
