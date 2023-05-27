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
import sys
import time
import utils.subprocess_output
from checks import AgentCheck

pythonVersion = platform.python_version_tuple()
python24 = platform.python_version().startswith('2.4')

class ServerDensityChecks(AgentCheck):
    """ Collects metrics about the machine's disks. """

    DF_COMMAND = ['df', '-k']

    def check(self, instance):
        #self.log.debug('hello')
        ##self.gauge('serverdensity.disk.free', 1)
        #self.gauge('serverdensity.disk.free', 1, device_name="/")
        #self.gauge('serverdensity.disk.free', 2, device_name="/var")
        #self.gauge('serverdensity.disk.free', 3, device_name="/home")
        #self.log.debug('hello2')

        self.log.debug('getDiskUsage: start')

        # Get output from df
        try:
            self.log.debug('getDiskUsage: attempting Popen')
            df = utils.subprocess_output.get_subprocess_output(
                self.DF_COMMAND, self.log
            )

        except Exception:
            self.log.error('getDiskUsage: df -k exception = %s', traceback.format_exc())
            return False

        self.log.debug('getDiskUsage: Popen success, start parsing')

        # Split out each volume
        volumes = df.split('\n')

        self.log.debug('getDiskUsage: parsing, split')

        # Remove first (headings) and last (blank)
        volumes.pop(0)
        volumes.pop()

        self.log.debug('getDiskUsage: parsing, pop')

        usageData = []

        regexp = re.compile(r'([0-9]+)')

        # Set some defaults
        previousVolume = None
        volumeCount = 0

        self.log.debug('getDiskUsage: parsing, start loop')

        for volume in volumes:
            self.log.debug('getDiskUsage: parsing volume: %s', volume)

            # Split out the string
            volume = volume.split(None, 10)

            # Handle df output wrapping onto multiple lines (case 27078 and case 30997)
            # Thanks to http://github.com/sneeu
            if len(volume) == 1:  # If the length is 1 then this just has the mount name
                previousVolume = volume[0]  # We store it, then continue the for
                continue

            if previousVolume is not None:  # If the previousVolume was set (above) during the last loop
                volume.insert(0, previousVolume)  # then we need to insert it into the volume
                previousVolume = None  # then reset so we don't use it again

            volumeCount += 1

            # Sometimes the first column will have a space, which is usually a system line that isn't relevant
            # e.g. map -hosts              0         0          0   100%    /net
            # so we just get rid of it
            # Also ignores lines with no values (AGENT-189)
            if re.match(regexp, volume[1]) is None or re.match(regexp, volume[2]) is None or re.match(regexp, volume[3]) is None:
                pass

            else:
                try:
                    volume[2] = int(volume[2]) / 1024 / 1024  # Used
                    volume[3] = int(volume[3]) / 1024 / 1024  # Available
                except Exception, e:
                    self.log.error('getDiskUsage: parsing, loop %s - Used or Available not present' % (repr(e),))
                usageData.append(volume)
                #self.gauge('serverdensity.disk.size', volume[1], device_name=volume[5])
                #self.gauge('serverdensity.disk.used', volume[2], device_name=volume[5])
                #self.gauge('serverdensity.disk.avail', volume[3], device_name=volume[5])
                self.gauge('serverdensity.disk.use', int(volume[4][:-1]), device_name=volume[5])# remove %
        self.log.debug('getDiskUsage: completed, returning')
        return usageData


if __name__ == '__main__':

    check, _instances = ServerDensityChecks.from_yaml('conf.d/sd.yaml')

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    root.addHandler(ch)

    check.log = root
    try:
        for i in xrange(200):
            results = check.check({})

            for file_system in results:
                print file_system
            time.sleep(30)
    except Exception as e:
        print "Something broke {0}".format(traceback.format_exc())
    finally:
        check.stop()
