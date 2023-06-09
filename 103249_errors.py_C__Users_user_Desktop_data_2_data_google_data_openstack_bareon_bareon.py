# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class BaseError(Exception):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super(BaseError, self).__init__(message, *args, **kwargs)


class WrongInputDataError(BaseError):
    pass


class WrongPartitionSchemeError(BaseError):
    pass


class WrongPartitionPolicyError(BaseError):
    pass


class PartitionSchemeMismatchError(BaseError):
    pass


class HardwarePartitionSchemeCannotBeReadError(BaseError):
    pass


class WrongPartitionLabelError(BaseError):
    pass


class PartitionNotFoundError(BaseError):
    pass


class DiskNotFoundError(BaseError):
    pass


class NotEnoughSpaceError(BaseError):
    pass


class PVAlreadyExistsError(BaseError):
    pass


class PVNotFoundError(BaseError):
    pass


class PVBelongsToVGError(BaseError):
    pass


class VGAlreadyExistsError(BaseError):
    pass


class VGNotFoundError(BaseError):
    pass


class LVAlreadyExistsError(BaseError):
    pass


class LVNotFoundError(BaseError):
    pass


class MDAlreadyExistsError(BaseError):
    pass


class MDNotFoundError(BaseError):
    pass


class MDDeviceDuplicationError(BaseError):
    pass


class MDWrongSpecError(BaseError):
    pass


class MDRemovingError(BaseError):
    pass


class WrongConfigDriveDataError(BaseError):
    pass


class WrongImageDataError(BaseError):
    pass


class TemplateWriteError(BaseError):
    pass


class ProcessExecutionError(BaseError):
    def __init__(self, stdout=None, stderr=None, exit_code=None, cmd=None,
                 description=None):
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        self.cmd = cmd
        self.description = description

        if description is None:
            description = ("Unexpected error while running command.")
        if exit_code is None:
            exit_code = '-'
        message = ('%(description)s\n'
                   'Command: %(cmd)s\n'
                   'Exit code: %(exit_code)s\n'
                   'Stdout: %(stdout)r\n'
                   'Stderr: %(stderr)r') % {'description': description,
                                            'cmd': cmd,
                                            'exit_code': exit_code,
                                            'stdout': stdout,
                                            'stderr': stderr}
        super(ProcessExecutionError, self).__init__(message)


class GrubUtilsError(BaseError):
    pass


class FsUtilsError(BaseError):
    pass


class HttpUrlConnectionError(BaseError):
    pass


class HttpUrlInvalidContentLength(BaseError):
    pass


class ImageChecksumMismatchError(BaseError):
    pass


class NoFreeLoopDevices(BaseError):
    pass


class WrongRepositoryError(BaseError):
    pass


class WrongDeviceError(BaseError):
    pass


class UnexpectedProcessError(BaseError):
    pass


class IncorrectChroot(BaseError):
    pass


class TooManyKernels(BaseError):
    pass
