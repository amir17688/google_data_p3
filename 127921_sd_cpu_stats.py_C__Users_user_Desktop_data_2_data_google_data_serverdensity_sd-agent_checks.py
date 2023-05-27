import re
import traceback

# 3p
try:
    import psutil
except ImportError:
    psutil = None

# project
import logging
import platform
import string
import subprocess
import sys
import time
from checks import AgentCheck

pythonVersion = platform.python_version_tuple()
python24 = platform.python_version().startswith('2.4')


class ServerDensityCPUChecks(AgentCheck):
    """ Collects metrics about the machine's disks. """


    def check(self, instance):
        #self.log.debug('hello')
        ##self.gauge('serverdensity.disk.free', 1)
        #self.gauge('serverdensity.disk.free', 1, device_name="/")
        #self.gauge('serverdensity.disk.free', 2, device_name="/var")
        #self.gauge('serverdensity.disk.free', 3, device_name="/home")
        #self.log.debug('hello2')

        self.log.debug('getCPUStats: start')

        cpu_stats = {}

        if sys.platform == 'linux2':
            self.log.debug('getCPUStats: linux2')

            headerRegexp = re.compile(r'.*?([%][a-zA-Z0-9]+)[\s+]?')
            itemRegexp = re.compile(r'.*?\s+(\d+)[\s+]?')
            valueRegexp = re.compile(r'\d+\.\d+')
            proc = None
            try:
                proc = subprocess.Popen(['mpstat', '-P', 'ALL', '1', '1'], stdout=subprocess.PIPE, close_fds=True)
                stats = proc.communicate()[0]

                if int(pythonVersion[1]) >= 6:
                    try:
                        proc.kill()
                    except Exception:
                        self.log.debug('Process already terminated')

                stats = stats.split('\n')
                header = stats[2]
                headerNames = re.findall(headerRegexp, header)
                device = None

                for statsIndex in range(3, len(stats)):
                    row = stats[statsIndex]

                    if not row:  # skip the averages
                        break

                    deviceMatch = re.match(itemRegexp, row)

                    if string.find(row, 'all') is not -1:
                        device = 'ALL'
                    elif deviceMatch is not None:
                        device = 'CPU%s' % deviceMatch.groups()[0]

                    values = re.findall(valueRegexp, row.replace(',', '.'))

                    cpu_stats[device] = {}
                    for headerIndex in range(0, len(headerNames)):
                        headerName = headerNames[headerIndex]
                        cpu_stats[device][headerName] = values[headerIndex]
                        key = headerName.replace('%', '')
                        self.gauge('serverdensity.cpu.{0}'.format(key), float(values[headerIndex]), device_name=device)

            except OSError:
                # we dont have it installed return nothing
                return False

            except Exception:
                import traceback
                self.log.error("getCPUStats: exception = %s", traceback.format_exc())

                if int(pythonVersion[1]) >= 6:
                    try:
                        if proc is not None:
                            proc.kill()
                    except UnboundLocalError:
                        self.log.debug('Process already terminated')
                    except Exception:
                        self.log.debug('Process already terminated')

                return False

        elif sys.platform == 'darwin':
            self.log.debug('getCPUStats: darwin')

            try:
                proc = subprocess.Popen(['sar', '-u', '1', '2'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
                stats = proc.communicate()[0]

                itemRegexp = re.compile(r'\s+(\d+)[\s+]?')
                titleRegexp = re.compile(r'.*?([%][a-zA-Z0-9]+)[\s+]?')
                titles = []
                values = []
                for line in stats.split('\n'):
                    # top line with the titles in
                    if '%' in line:
                        titles = re.findall(titleRegexp, line)
                    if line and line.startswith('Average:'):
                        values = re.findall(itemRegexp, line)

                if values and titles:
                    cpu_stats['CPUs'] = dict(zip(titles, values))

            except Exception:
                import traceback
                self.log.error('getCPUStats: exception = %s', traceback.format_exc())
                return False

        else:
            self.log.debug('getCPUStats: unsupported platform')
            return False

        self.log.debug('getCPUStats: completed, returning')
        return {'cpuStats': cpu_stats}


if __name__ == '__main__':

    check, _instances = ServerDensityCPUChecks.from_yaml('conf.d/sd_cpu_stats.yaml')

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    root.addHandler(ch)

    check.log = root
    try:
        for i in xrange(200):
            print check.check({})
            time.sleep(30)
    except Exception as e:
        print "Something broke {0}".format(traceback.format_exc())
    finally:
        check.stop()
