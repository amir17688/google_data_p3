from __future__ import print_function
from __future__ import unicode_literals

import io
import logging
import os
import random
import subprocess
import re
import tempfile
import threading
import sys
import shutil
import warnings

import time
from collections import defaultdict

from imagemounter import _util, FILE_SYSTEM_TYPES, VOLUME_SYSTEM_TYPES
from imagemounter.volume_system import VolumeSystem

logger = logging.getLogger(__name__)


FILE_SYSTEM_GUIDS = {
    '2AE031AA-0F40-DB11-9590-000C2911D1B8': 'vmfs',
    '8053279D-AD40-DB11-BF97-000C2911D1B8': 'vmkcore-diagnostics',
    '6A898CC3-1DD2-11B2-99A6-080020736631': 'zfs-member',
    'C38C896A-D21D-B211-99A6-080020736631': 'zfs-member',
    '0FC63DAF-8483-4772-8E79-3D69D8477DE4': 'linux',
    'E6D6D379-F507-44C2-A23C-238F2A3DF928': 'lvm',
    '79D3D6E6-07F5-C244-A23C-238F2A3DF928': 'lvm',
    'CA7D7CCB-63ED-4C53-861C-1742536059CC': 'luks'
}


class Volume(object):
    """Information about a volume. Note that every detected volume gets their own Volume object, though it may or may
    not be mounted. This can be seen through the :attr:`mountpoint` attribute -- if it is not set, perhaps the
    :attr:`exception` attribute is set with an exception.
    """

    def __init__(self, disk=None, parent=None, stats=True, fstypes=None, keys=None,
                 pretty=False, mountdir=None, **args):
        """Creates a Volume object that is not mounted yet.

        Only use arguments stats and further as keyword arguments.

        :param disk: the parent disk
        :type disk: :class:`Disk`
        :param bool stats: indicates whether :func:`init` should try to fill statistics
        :param dict fstypes: dict mapping volume indices to file system types to use; use * and ? as volume indexes for
                             additional control. Only when ?=none, unknown will not be used as fallback.
        :param dict keys: dict mapping volume indices to key material
        :param bool pretty: indicates whether pretty names should be used for the mountpoints
        :param str mountdir: location where mountpoints are created, defaulting to a temporary location
        :param args: additional arguments
        """

        self.parent = parent
        self.disk = disk
        self.stats = stats
        self.fstypes = fstypes or {'?': 'unknown'}
        if '?' in self.fstypes and (not self.fstypes['?'] or self.fstypes['?'] == 'none'):
            self.fstypes['?'] = None
        self.keys = keys or {}
        self.pretty = pretty
        self.mountdir = mountdir
        if self.disk.parser.casename:
            self.mountdir = os.path.join(mountdir or tempfile.gettempdir(), self.disk.parser.casename)

        # Should be filled somewhere
        self.size = 0
        self.offset = 0
        self.index = 0
        self.slot = 0
        self.size = 0
        self.flag = 'alloc'
        self.guid = ""
        self.fsdescription = ""
        self.fstype = ""

        # Should be filled by fill_stats
        self.lastmountpoint = ""
        self.label = ""
        self.version = ""
        self.statfstype = ""

        # Should be filled by mount
        self.mountpoint = ""
        self.bindmountpoint = ""
        self.loopback = ""
        self.exception = None
        self.was_mounted = False

        # Used by carving
        self.carvepoint = ""

        # Used by functions that create subvolumes
        self.volumes = VolumeSystem(parent=self, stats=self.stats, fstypes=self.fstypes, keys=self.keys,
                                    pretty=self.pretty, mountdir=self.mountdir, **args)

        # Used by lvm specific functions
        self.volume_group = ""
        self.lv_path = ""

        # Used by LUKS/BDE
        self.luks_path = ""
        self.bde_path = ""

        self.block_size = self.disk.block_size

        self.args = args

    def __unicode__(self):
        return '{0}:{1}'.format(self.index, self.fsdescription or '-')

    def __str__(self):
        return str(self.__unicode__())

    def __getitem__(self, item):
        return self.volumes[item]

    def get_description(self, with_size=True):
        """Obtains a generic description of the volume, containing the file system type, index, label and NTFS version.
        If *with_size* is provided, the volume size is also included.
        """

        desc = ''

        if with_size and self.size:
            desc += '{0} '.format(self.get_size_gib())

        desc += '{1}:{0}'.format(self.statfstype or self.fsdescription or '-', self.index)

        if self.label:
            desc += ' {0}'.format(self.label)

        if self.version:  # NTFS
            desc += ' [{0}]'.format(self.version)

        return desc

    def get_size_gib(self):
        """Obtains the size of the volume in a human-readable format (i.e. in TiBs, GiBs or MiBs)."""

        # Python 3 compatibility
        if sys.version_info[0] == 2:
            integer_types = (int, long)
        else:
            integer_types = int

        # noinspection PyUnresolvedReferences
        if self.size and (isinstance(self.size, integer_types) or self.size.isdigit()):
            if self.size < 1024:
                return "{0} B".format(self.size)
            elif self.size < 1024 ** 2:
                return "{0} KiB".format(round(self.size / 1024, 2))
            elif self.size < 1024**3:
                return "{0} MiB".format(round(self.size / 1024.0 ** 2, 2))
            elif self.size < 1024**4:
                return "{0} GiB".format(round(self.size / 1024.0 ** 3, 2))
            else:
                return "{0} TiB".format(round(self.size / 1024.0 ** 4, 2))
        else:
            return self.size

    def get_magic_type(self):
        """Checks the volume for its magic bytes and returns the magic."""

        with io.open(self.disk.get_fs_path(), "rb") as file:
            file.seek(self.offset)
            fheader = file.read(min(self.size, 4096) if self.size else 4096)

        # TODO fallback to img-cat image -s blocknum | file -
        # if we were able to load the module magic
        try:
            # noinspection PyUnresolvedReferences
            import magic

            if hasattr(magic, 'from_buffer'):
                # using https://github.com/ahupp/python-magic
                logger.debug("Using python-magic Python package for file type magic")
                result = magic.from_buffer(fheader).decode()
                return result

            elif hasattr(magic, 'open'):
                # using Magic file extensions by Rueben Thomas (Ubuntu python-magic module)
                logger.debug("Using python-magic system package for file type magic")
                ms = magic.open(magic.NONE)
                ms.load()
                result = ms.buffer(fheader)
                ms.close()
                return result

            else:
                logger.warning("The python-magic module is not available, but another module named magic was found.")

        except ImportError:
            logger.warning("The python-magic module is not available.")
        except AttributeError:
            logger.warning("The python-magic module is not available, but another module named magic was found.")
        return None

    def get_raw_path(self):
        """Retrieves the base mount path of the volume. Typically equals to :func:`Disk.get_fs_path` but may also be the
        path to a logical volume. This is used to determine the source path for a mount call.
        """

        if self.lv_path:
            return self.lv_path
        elif self.parent and self.parent != self.disk and self.parent.lv_path:
            return self.parent.lv_path
        elif self.parent and self.parent != self.disk and self.parent.bde_path:
            return self.parent.bde_path + '/bde1'
        elif self.luks_path:
            return '/dev/mapper/' + self.luks_path
        elif self.parent and self.parent != self.disk and self.parent.luks_path:
            return '/dev/mapper/' + self.parent.luks_path
        else:
            return self.disk.get_fs_path()

    def get_safe_label(self):
        """Returns a label that is safe to add to a path in the mountpoint for this volume."""

        if self.label == '/':
            return 'root'

        suffix = re.sub(r"[/ \(\)]+", "_", self.label) if self.label else ""
        if suffix and suffix[0] == '_':
            suffix = suffix[1:]
        if len(suffix) > 2 and suffix[-1] == '_':
            suffix = suffix[:-1]
        return suffix

    def carve(self, freespace=True):
        """Call this method to carve the free space of the volume for (deleted) files. Note that photorec has its
        own interface that temporarily takes over the shell.

        :param freespace: indicates whether the entire volume should be carved (False) or only the free space (True)
        :type freespace: bool
        :return: boolean indicating whether the command succeeded
        """

        if not _util.command_exists('photorec'):
            logger.warning("photorec is not installed, could not carve volume")
            return False

        if not self._make_mountpoint(var_name='carvepoint', suffix="carve"):
            return False

        # if no slot, we need to make a loopback that we can use to carve the volume
        loopback_was_created_for_carving = False
        if not self.slot:
            if not self.loopback:
                if not self._find_loopback():
                    logger.error("Can't carve if volume has no slot number and can't be mounted on loopback.")
                    return False
                loopback_was_created_for_carving = True

            # noinspection PyBroadException
            try:
                _util.check_call_(["photorec", "/d", self.carvepoint + os.sep, "/cmd", self.loopback,
                                  ("freespace," if freespace else "") + "search"])

                # clean out the loop device if we created it specifically for carving
                if loopback_was_created_for_carving:
                    # noinspection PyBroadException
                    try:
                        _util.check_call_(['losetup', '-d', self.loopback])
                    except Exception:
                        pass
                    else:
                        self.loopback = ""

                return True
            except Exception:
                logger.exception("Failed carving the volume.")
                return False
        else:
            # noinspection PyBroadException
            try:
                _util.check_call_(["photorec", "/d", self.carvepoint + os.sep, "/cmd", self.get_raw_path(),
                                  str(self.slot) + (",freespace" if freespace else "") + ",search"])
                return True

            except Exception:
                logger.exception("Failed carving the volume.")
                return False

    def _should_mount(self, only_mount=None):
        """Indicates whether this volume should be mounted. Internal method, used by imount.py"""

        return only_mount is None or \
            self.index in only_mount or str(self.index) in only_mount or \
            self.lastmountpoint in only_mount or \
            self.label in only_mount

    def init(self, no_stats=False, only_mount=None):
        """Generator that mounts this volume and either yields itself or recursively generates its subvolumes.

        More specifically, this function will call :func:`fill_stats` (iff *no_stats* is False), followed by
        :func:`mount`, followed by a call to :func:`detect_mountpoint`, after which ``self`` is yielded, or the result
        of the :func:`init` call on each subvolume is yielded

        If only_mount is specified, only volume indexes in this list are mounted. Note that volume indexes are strings.
        """

        logger.debug("Initializing volume {0}".format(self))
        if self.stats and not no_stats:
            self.fill_stats()

        if not self._should_mount(only_mount):
            yield self
            return

        if self.flag != 'alloc':
            return

        logger.info("Mounting volume {0}".format(self))
        self.mount()

        if self.stats and not no_stats:
            self.detect_mountpoint()

        if not self.volumes:
            yield self
        else:
            for v in self.volumes:
                for s in v.init():
                    yield s

    def _make_mountpoint(self, casename=None, var_name='mountpoint', suffix=''):
        """Creates a directory that can be used as a mountpoint. The directory is stored in :attr:`mountpoint`,
        or the varname as specified by the argument.

        :return: boolean indicating whether the mountpoint was successfully created.
        """

        if self.mountdir and not os.path.exists(self.mountdir):
            os.makedirs(self.mountdir)

        if self.pretty:
            md = self.mountdir or tempfile.gettempdir()
            case_name = casename or self.disk.parser.casename or \
                        ".".join(os.path.basename(self.disk.paths[0]).split('.')[0:-1]) or \
                        os.path.basename(self.disk.paths[0])
            if self.disk.parser.casename == case_name:  # the casename is already in the path in this case
                pretty_label = "{0}-{1}".format(str(self.index), self.get_safe_label() or self.fstype or 'volume')
            else:
                pretty_label = "{0}-{1}-{2}".format(case_name, str(self.index),
                                                    self.get_safe_label() or self.fstype or 'volume')
            if suffix:
                pretty_label += "-" + suffix
            path = os.path.join(md, pretty_label)

            # check if path already exists, otherwise try to find another nice path
            if os.path.exists(path):
                for i in range(2, 100):
                    path = os.path.join(md, pretty_label + "-" + str(i))
                    if not os.path.exists(path):
                        break
                else:
                    logger.error("Could not find free mountdir.")
                    return False

            # noinspection PyBroadException
            try:
                os.mkdir(path, 777)
                setattr(self, var_name, path)
                return True
            except Exception:
                logger.exception("Could not create mountdir.")
                return False
        else:
            setattr(self, var_name, tempfile.mkdtemp(prefix='im_' + str(self.index) + '_',
                                                     suffix='_' + self.get_safe_label() +
                                                            ("_" + suffix if suffix else ""),
                                                     dir=self.mountdir))
            return True

    def _find_loopback(self, use_loopback=True, var_name='loopback'):
        """Finds a free loopback device that can be used. The loopback is stored in :attr:`loopback`. If *use_loopback*
        is True, the loopback will also be used directly.

        :return: boolean indicating whether a loopback device was found
        """

        # noinspection PyBroadException
        try:
            loopback = _util.check_output_(['losetup', '-f']).strip()
            setattr(self, var_name, loopback)
        except Exception:
            logger.warning("No free loopback device found.", exc_info=True)
            return False

        # noinspection PyBroadException
        if use_loopback:
            try:
                cmd = ['losetup', '-o', str(self.offset), '--sizelimit', str(self.size),
                       loopback, self.get_raw_path()]
                if not self.disk.read_write:
                    cmd.insert(1, '-r')
                _util.check_call_(cmd, stdout=subprocess.PIPE)
            except Exception as e:
                logger.exception("Loopback device could not be mounted.")
                return False
        return True

    def determine_fs_type(self):
        """Determines the FS type for this partition. This function is used internally to determine which mount system
        to use, based on the file system description. Return values include *ext*, *ufs*, *ntfs*, *lvm* and *luks*.

        Note: does not do anything if fstype is already set to something sensible.
        """

        # Determine fs type. If forced, always use provided type.
        if str(self.index) in self.fstypes:
            self.fstype = self.fstypes[str(self.index)]
        elif '*' in self.fstypes:
            self.fstype = self.fstypes['*']
        elif self.fstype in FILE_SYSTEM_TYPES:
            pass  # already correctly set
        else:
            last_resort = None  # use this if we can't determine the FS type more reliably
            # we have two possible sources for determining the FS type: the description given to us by the detection
            # method, and the type given to us by the stat function
            for fsdesc in (self.fsdescription, self.statfstype, self.guid, self.get_magic_type):
                # For efficiency reasons, not all functions are called instantly.
                if callable(fsdesc):
                    fsdesc = fsdesc()
                logger.debug("Trying to determine fs type from '{}'".format(fsdesc))
                if not fsdesc:
                    continue
                fsdesc = fsdesc.lower()

                # for the purposes of this function, logical volume is nothing, and 'primary' is rather useless info
                if fsdesc in ('logical volume', 'luks volume', 'bde volume', 'primary', 'basic data partition'):
                    continue

                if fsdesc == 'directory':
                    self.fstype = 'dir'  # dummy fs type
                elif re.search(r'\bext[0-9]*\b', fsdesc):
                    self.fstype = 'ext'
                elif 'bsd' in fsdesc:
                    self.fstype = 'ufs'
                elif '0x07' in fsdesc or 'ntfs' in fsdesc:
                    self.fstype = 'ntfs'
                elif '0x8e' in fsdesc or 'lvm' in fsdesc:
                    self.fstype = 'lvm'
                elif 'hfs+' in fsdesc:
                    self.fstype = 'hfs+'
                elif 'hfs' in fsdesc:
                    self.fstype = 'hfs'
                elif 'luks' in fsdesc:
                    self.fstype = 'luks'
                elif 'fat' in fsdesc or 'efi system partition' in fsdesc:
                    # based on http://en.wikipedia.org/wiki/EFI_System_partition, efi is always fat.
                    self.fstype = 'fat'
                elif 'iso 9660' in fsdesc:
                    self.fstype = 'iso'
                elif 'linux compressed rom file system' in fsdesc or 'cramfs' in fsdesc:
                    self.fstype = 'cramfs'
                elif fsdesc.startswith("sgi xfs") or re.search(r'\bxfs\b', fsdesc):
                    self.fstype = "xfs"
                elif 'swap file' in fsdesc or 'linux swap' in fsdesc or 'linux-swap' in fsdesc:
                    self.fstype = 'swap'
                elif 'squashfs' in fsdesc:
                    self.fstype = 'squashfs'
                elif "jffs2" in fsdesc:
                    self.fstype = 'jffs2'
                elif "minix filesystem" in fsdesc:
                    self.fstype = 'minix'
                elif "dos/mbr boot sector" in fsdesc:
                    self.fstype = 'detect'  # vsdetect, choosing between dos and gpt is hard
                elif fsdesc.upper() in FILE_SYSTEM_GUIDS:
                    # this is a bit of a workaround for the fill_guid method
                    self.fstype = FILE_SYSTEM_GUIDS[fsdesc.upper()]
                elif '0x83' in fsdesc:
                    # this is a linux mount, but we can't figure out which one.
                    # we hand it off to the OS, maybe it can try something.
                    # if we use last_resort for more enhanced stuff, we may need to check if we are not setting
                    # it to something less specific here
                    last_resort = 'unknown'
                    continue
                else:
                    continue  # this loop failed

                logger.info("Detected {0} as {1}".format(fsdesc, self.fstype))
                break  # we found something
            else:  # we found nothing
                # if last_resort is something more sensible than unknown, we use that
                # if we have specified a fsfallback which is not set to None, we use that
                # if last_resort is unknown or the fallback is not None, we use unknown
                if last_resort and last_resort != 'unknown':
                    self.fstype = last_resort
                elif '?' in self.fstypes and self.fstypes['?'] is not None:
                    self.fstype = self.fstypes['?']
                elif last_resort == 'unknown' or '?' not in self.fstypes:
                    self.fstype = 'unknown'

        return self.fstype

    def mount(self):
        """Based on the file system type as determined by :func:`determine_fs_type`, the proper mount command is executed
        for this volume. The volume is mounted in a temporary path (or a pretty path if :attr:`pretty` is enabled) in
        the mountpoint as specified by :attr:`mountpoint`.

        If the file system type is a LUKS container or LVM, additional methods may be called, adding subvolumes to
        :attr:`volumes`

        :return: boolean indicating whether the mount succeeded
        """

        raw_path = self.get_raw_path()
        self.determine_fs_type()

        # we need a mountpoint if it is not a lvm or luks volume
        if self.fstype not in ('luks', 'lvm', 'bde') and self.fstype not in VOLUME_SYSTEM_TYPES and \
                self.fstype in FILE_SYSTEM_TYPES and not self._make_mountpoint():
            return False

        # Prepare mount command
        try:
            def call_mount(type, opts):
                cmd = ['mount', raw_path, self.mountpoint, '-t', type, '-o', opts]
                if not self.disk.read_write:
                    cmd[-1] += ',ro'

                _util.check_call_(cmd, stdout=subprocess.PIPE)

            if self.fstype == 'ext':
                call_mount('ext4', 'noexec,noload,loop,offset=' + str(self.offset))

            elif self.fstype == 'ufs':
                call_mount('ufs', 'ufstype=ufs2,loop,offset=' + str(self.offset))

            elif self.fstype == 'ntfs':
                call_mount('ntfs', 'show_sys_files,noexec,force,loop,offset=' + str(self.offset))

            elif self.fstype == 'xfs':
                call_mount('xfs', 'norecovery,loop,offset=' + str(self.offset))

            elif self.fstype == 'hfs+':
                call_mount('hfsplus', 'force,loop,offset=' + str(self.offset) + ',sizelimit=' + str(self.size))

            elif self.fstype in ('iso', 'udf', 'squashfs', 'cramfs', 'minix', 'fat', 'hfs'):
                mnt_type = {'iso': 'iso9660', 'fat': 'vfat'}.get(self.fstype, self.fstype)
                call_mount(mnt_type, 'loop,offset=' + str(self.offset))

            elif self.fstype == 'vmfs':
                if not self._find_loopback():
                    return False

                _util.check_call_(['vmfs-fuse', self.loopback, self.mountpoint], stdout=subprocess.PIPE)

            elif self.fstype == 'unknown':  # mounts without specifying the filesystem type
                cmd = ['mount', raw_path, self.mountpoint, '-o', 'loop,offset=' + str(self.offset)]
                if not self.disk.read_write:
                    cmd[-1] += ',ro'

                _util.check_call_(cmd, stdout=subprocess.PIPE)

            elif self.fstype == 'jffs2':
                self._open_jffs2()

            elif self.fstype == 'luks':
                self._open_luks_container()

            elif self.fstype == 'bde':
                self._open_bde_container()

            elif self.fstype == 'lvm':
                self._open_lvm()

                for _ in self.volumes.detect_volumes('lvm'):
                    pass

            elif self.fstype == 'dir':
                os.rmdir(self.mountpoint)
                os.symlink(raw_path, self.mountpoint)

            elif self.fstype in VOLUME_SYSTEM_TYPES:
                for _ in self.volumes.detect_volumes(self.fstype):
                    pass

            else:
                try:
                    size = self.size / self.disk.block_size
                except TypeError:
                    size = self.size

                logger.warning("Unsupported filesystem {0} (type: {1}, block offset: {2}, length: {3})"
                               .format(self, self.fstype, self.offset / self.disk.block_size, size))
                return False

            self.was_mounted = True

            return True
        except Exception as e:
            logger.exception("Execution failed due to {}".format(e), exc_info=True)
            self.exception = e

            try:
                if self.mountpoint:
                    os.rmdir(self.mountpoint)
                    self.mountpoint = ""
                if self.loopback:
                    self.loopback = ""
            except Exception as e2:
                logger.exception("Clean-up failed", exc_info=True)

            return False

    def bindmount(self, mountpoint):
        """Bind mounts the volume to another mountpoint. Only works if the volume is already mounted. Note that only the
        last bindmountpoint is remembered and cleaned.

        :return: bool indicating whether the bindmount succeeded
        """

        if not self.mountpoint:
            return False
        try:
            self.bindmountpoint = mountpoint
            _util.check_call_(['mount', '--bind', self.mountpoint, self.bindmountpoint], stdout=subprocess.PIPE)
            return True
        except Exception as e:
            self.bindmountpoint = ""
            logger.exception("Error bind mounting {0}.".format(self))
            return False

    def _open_luks_container(self):
        """Command that is an alternative to the :func:`mount` command that opens a LUKS container. The opened volume is
        added to the subvolume set of this volume. Requires the user to enter the key manually.

        TODO: add support for :attr:`keys`

        :return: the Volume contained in the LUKS container, or None on failure.
        """

        # Open a loopback device
        if not self._find_loopback():
            return None

        # Check if this is a LUKS device
        # noinspection PyBroadException
        try:
            _util.check_call_(["cryptsetup", "isLuks", self.loopback], stderr=subprocess.STDOUT)
            # ret = 0 if isLuks
        except Exception:
            logger.warning("Not a LUKS volume")
            # clean the loopback device, we want this method to be clean as possible
            # noinspection PyBroadException
            try:
                _util.check_call_(['losetup', '-d', self.loopback])
                self.loopback = ""
            except Exception:
                pass

            return None

        # Open the LUKS container
        self.luks_path = 'image_mounter_' + str(random.randint(10000, 99999))

        # noinspection PyBroadException
        try:
            cmd = ["cryptsetup", "luksOpen", self.loopback, self.luks_path]
            if not self.disk.read_write:
                cmd.insert(1, '-r')
            _util.check_call_(cmd)
        except Exception:
            self.luks_path = ""
            return None

        size = None
        # noinspection PyBroadException
        try:
            result = _util.check_output_(["cryptsetup", "status", self.luks_path])
            for l in result.splitlines():
                if "size:" in l and "key" not in l:
                    size = int(l.replace("size:", "").replace("sectors", "").strip()) * self.disk.block_size
        except Exception:
            pass

        container = self.volumes._make_subvolume()
        container.index = "{0}.0".format(self.index)
        container.fsdescription = 'LUKS Volume'
        container.flag = 'alloc'
        container.offset = 0
        container.size = size

        return container

    def _open_bde_container(self):
        """Mounts a BDE container. Uses key material provided by the :attr:`keys` attribute. The key material should be
        provided in the same format as to :cmd:`bdemount`, used as follows:

        k:full volume encryption and tweak key
        p:passphrase
        r:recovery password
        s:file to startup key (.bek)

        :return: the Volume contained in the BDE container, or None on failure.
        """

        self.bde_path = tempfile.mkdtemp(prefix='image_mounter_bde_')

        try:
            if str(self.index) in self.keys:
                t, v = self.keys[str(self.index)].split(':', 1)
                key = ['-' + t, v]
            else:
                logger.warning("No key material provided for %s", self)
                key = []
        except ValueError:
            logger.exception("Invalid key material provided (%s) for %s. Expecting [arg]:[value]",
                             self.keys.get(str(self.index)), self)
            return None

        # noinspection PyBroadException
        try:
            cmd = ["bdemount", self.get_raw_path(), self.bde_path, '-o', str(self.offset)]
            cmd.extend(key)
            _util.check_call_(cmd)
        except Exception:
            self.bde_path = ""
            logger.exception("Failed mounting BDE volume %s.", self)
            return None

        container = self.volumes._make_subvolume()
        container.index = "{0}.0".format(self.index)
        container.fsdescription = 'BDE Volume'
        container.flag = 'alloc'
        container.offset = 0
        container.size = self.size

        return container

    def _open_jffs2(self):
        """Perform specific operations to mount a JFFS2 image. This kind of image is sometimes used for things like
        bios images. so external tools are required but given this method you don't have to memorize anything and it
        works fast and easy.

        Note that this module might not yet work while mounting multiple images at the same time.
        """
        # we have to make a ram-device to store the image, we keep 20% overhead
        size_in_kb = int((self.size / 1024) * 1.2)
        _util.check_call_(['modprobe', '-v', 'mtd'])
        _util.check_call_(['modprobe', '-v', 'jffs2'])
        _util.check_call_(['modprobe', '-v', 'mtdram', 'total_size={}'.format(size_in_kb), 'erase_size=256'])
        _util.check_call_(['modprobe', '-v', 'mtdblock'])
        _util.check_call_(['dd', 'if=' + self.get_raw_path(), 'of=/dev/mtd0'])
        _util.check_call_(['mount', '-t', 'jffs2', '/dev/mtdblock0', self.mountpoint])

        return True

    def _open_lvm(self):
        """Performs mount actions on a LVM. Scans for active volume groups from the loopback device, activates it
        and fills :attr:`volumes` with the logical volumes.
        """
        os.environ['LVM_SUPPRESS_FD_WARNINGS'] = '1'

        # find free loopback device
        if not self._find_loopback():
            return False

        time.sleep(0.2)

        # Scan for new lvm volumes
        result = _util.check_output_(["lvm", "pvscan"])
        for l in result.splitlines():
            if self.loopback in l or (self.offset == 0 and self.get_raw_path() in l):
                for vg in re.findall(r'VG (\S+)', l):
                    self.volume_group = vg

        if not self.volume_group:
            logger.warning("Volume is not a volume group. (Searching for %s)", self.loopback)
            return False

        # Enable lvm volumes
        _util.check_call_(["lvm", "vgchange", "-a", "y", self.volume_group], stdout=subprocess.PIPE)

        return True

    def get_volumes(self):
        """Recursively gets a list of all subvolumes and the current volume."""

        if self.volumes:
            volumes = []
            for v in self.volumes:
                volumes.extend(v.get_volumes())
            volumes.append(self)
            return volumes
        else:
            return [self]

    def fill_stats(self):
        """Using :command:`fsstat`, adds some additional information of the volume to the Volume."""

        process = None

        def stats_thread():
            try:
                cmd = ['fsstat', self.get_raw_path(), '-o', str(self.offset // self.disk.block_size)]
                logger.debug('$ {0}'.format(' '.join(cmd)))
                # noinspection PyShadowingNames
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                for line in iter(process.stdout.readline, b''):
                    line = line.decode()
                    if line.startswith("File System Type:"):
                        self.statfstype = line[line.index(':') + 2:].strip()
                    elif line.startswith("Last Mount Point:") or line.startswith("Last mounted on:"):
                        self.lastmountpoint = line[line.index(':') + 2:].strip().replace("//", "/")
                    elif line.startswith("Volume Name:") and not self.label:
                        self.label = line[line.index(':') + 2:].strip()
                    elif line.startswith("Version:"):
                        self.version = line[line.index(':') + 2:].strip()
                    elif line.startswith("Source OS:"):
                        self.version = line[line.index(':') + 2:].strip()
                    elif 'CYLINDER GROUP INFORMATION' in line:
                        # noinspection PyBroadException
                        try:
                            process.terminate()  # some attempt
                        except Exception:
                            pass
                        break

                if self.lastmountpoint and self.label:
                    self.label = "{0} ({1})".format(self.lastmountpoint, self.label)
                elif self.lastmountpoint and not self.label:
                    self.label = self.lastmountpoint
                elif not self.lastmountpoint and self.label and self.label.startswith("/"):  # e.g. /boot1
                    if self.label.endswith("1"):
                        self.lastmountpoint = self.label[:-1]
                    else:
                        self.lastmountpoint = self.label

            except Exception as e:  # ignore any exceptions here.
                logger.exception("Error while obtaining stats.")
                pass

        thread = threading.Thread(target=stats_thread)
        thread.start()

        duration = 5  # longest possible duration for fsstat.
        thread.join(duration)
        if thread.is_alive():
            # noinspection PyBroadException
            try:
                process.terminate()
            except Exception:
                pass
            thread.join()
            logger.debug("Killed fsstat after {0}s".format(duration))

    def detect_mountpoint(self):
        """Attempts to detect the previous mountpoint if this was not done through :func:`fill_stats`. This detection
        does some heuristic method on the mounted volume.
        """

        if self.lastmountpoint:
            return self.lastmountpoint
        if not self.mountpoint:
            return None

        result = None
        paths = os.listdir(self.mountpoint)
        if 'grub' in paths:
            result = '/boot'
        elif 'usr' in paths and 'var' in paths and 'root' in paths:
            result = '/'
        elif 'bin' in paths and 'lib' in paths and 'local' in paths and 'src' in paths and not 'usr' in paths:
            result = '/usr'
        elif 'bin' in paths and 'lib' in paths and 'local' not in paths and 'src' in paths and not 'usr' in paths:
            result = '/usr/local'
        elif 'lib' in paths and 'local' in paths and 'tmp' in paths and not 'var' in paths:
            result = '/var'
        # elif sum(['bin' in paths, 'boot' in paths, 'cdrom' in paths, 'dev' in paths, 'etc' in paths, 'home' in paths,
        #          'lib' in paths, 'lib64' in paths, 'media' in paths, 'mnt' in paths, 'opt' in paths,
        #          'proc' in paths, 'root' in paths, 'sbin' in paths, 'srv' in paths, 'sys' in paths, 'tmp' in paths,
        #          'usr' in paths, 'var' in paths]) > 11:
        #    result = '/'

        if result:
            self.lastmountpoint = result
            if not self.label:
                self.label = self.lastmountpoint
            logger.info("Detected mountpoint as {0} based on files in volume".format(self.lastmountpoint))

        return result

    # noinspection PyBroadException
    def unmount(self):
        """Unounts the volume from the filesystem."""

        for volume in self.volumes:
            volume.unmount()

        if self.loopback and self.volume_group:
            try:
                _util.check_call_(["lvm", 'vgchange', '-a', 'n', self.volume_group], stdout=subprocess.PIPE)
            except Exception:
                return False

            self.volume_group = ""

        if self.loopback and self.luks_path:
            try:
                _util.check_call_(['cryptsetup', 'luksClose', self.luks_path], stdout=subprocess.PIPE)
            except Exception:
                return False

            self.luks_path = ""

        if self.bde_path:
            if not _util.clean_unmount(['fusermount', '-u'], self.bde_path):
                return False

            self.bde_path = ""

        if self.loopback:
            try:
                _util.check_call_(['losetup', '-d', self.loopback])
            except Exception:
                return False

            self.loopback = ""

        if self.bindmountpoint:
            if not _util.clean_unmount(['umount'], self.bindmountpoint, rmdir=False):
                return False

            self.bindmountpoint = ""

        if self.mountpoint:
            if not _util.clean_unmount(['umount'], self.mountpoint):
                return False

            self.mountpoint = ""

        if self.carvepoint:
            try:
                shutil.rmtree(self.carvepoint)
            except OSError:
                return False
            else:
                self.carvepoint = ""

        return True
