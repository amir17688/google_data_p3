# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
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


import datetime
import unittest

from freezer.openstack import openstack
from freezer.tests.commons import *
from freezer.utils import utils


class TestUtils(unittest.TestCase):

    def test_create_dir(self):

        dir1 = '/tmp'
        dir2 = '/tmp/testnoexistent1234'
        dir3 = '~'
        assert utils.create_dir(dir1) is None
        assert utils.create_dir(dir2) is None
        os.rmdir(dir2)
        assert utils.create_dir(dir3) is None

    # def test_get_vol_fs_type(self):
    #     self.assertRaises(Exception, utils.get_vol_fs_type, "test")
    #
    #     fakeos = Os()
    #     os.path.exists = fakeos.exists
    #     self.assertRaises(Exception, utils.get_vol_fs_type, "test")
    #
    #     fakere = FakeRe()
    #     re.search = fakere.search
    #     assert type(utils.get_vol_fs_type("test")) is str

    def test_get_mount_from_path(self):
        dir1 = '/tmp'
        dir2 = '/tmp/nonexistentpathasdf'
        assert type(utils.get_mount_from_path(dir1)[0]) is str
        assert type(utils.get_mount_from_path(dir1)[1]) is str
        self.assertRaises(Exception, utils.get_mount_from_path, dir2)

        # pytest.raises(Exception, utils.get_mount_from_path, dir2)

    def test_human2bytes(self):
        assert utils.human2bytes('0 B') == 0
        assert utils.human2bytes('1 K') == 1024
        assert utils.human2bytes('1 Gi') == 1073741824
        assert utils.human2bytes('1 tera') == 1099511627776
        assert utils.human2bytes('0.5kilo') == 512
        assert utils.human2bytes('0.1  byte') == 0
        assert utils.human2bytes('1 k') == 1024
        assert utils.human2bytes("1000") == 1000
        self.assertRaises(ValueError, utils.human2bytes, '12 foo')

    def test_OpenstackOptions_creation_success(self):
        env_dict = dict(OS_USERNAME='testusername',
                        OS_TENANT_NAME='testtenantename',
                        OS_AUTH_URL='testauthurl',
                        OS_PASSWORD='testpassword',
                        OS_REGION_NAME='testregion',
                        OS_TENANT_ID='0123456789')
        options = openstack.OpenstackOptions.create_from_dict(env_dict)
        assert options.user_name == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']
        assert options.region_name == env_dict['OS_REGION_NAME']
        assert options.tenant_id == env_dict['OS_TENANT_ID']

        env_dict = dict(OS_USERNAME='testusername',
                        OS_TENANT_NAME='testtenantename',
                        OS_AUTH_URL='testauthurl',
                        OS_PASSWORD='testpassword')
        options = openstack.OpenstackOptions.create_from_dict(env_dict)
        assert options.user_name == env_dict['OS_USERNAME']
        assert options.tenant_name == env_dict['OS_TENANT_NAME']
        assert options.auth_url == env_dict['OS_AUTH_URL']
        assert options.password == env_dict['OS_PASSWORD']
        assert options.region_name is None
        assert options.tenant_id is None

    def test_date_to_timestamp(self):
        # ensure that timestamp is check with appropriate timezone offset
        assert (1417649003+time.timezone) == \
               utils.date_to_timestamp("2014-12-03T23:23:23")

    def prepare_env(self):
        os.environ["HTTP_PROXY"] = 'http://proxy.original.domain:8080'
        os.environ.pop("HTTPS_PROXY", None)

    def test_alter_proxy(self):
        """
        Testing freezer.arguments.alter_proxy function does it set
        HTTP_PROXY and HTTPS_PROXY when 'proxy' key in its dictionary
        """
        # Test wrong proxy value
        self.assertRaises(Exception, utils.alter_proxy, 'boohoo')

        # Test when there is proxy value passed
        self.prepare_env()
        test_proxy = 'http://proxy.alternative.domain:8888'
        utils.alter_proxy(test_proxy)
        assert os.environ["HTTP_PROXY"] == test_proxy
        assert os.environ["HTTPS_PROXY"] == test_proxy


class TestDateTime:
    def setup(self):
        d = datetime.datetime(2015, 3, 7, 17, 47, 44, 716799)
        self.datetime = utils.DateTime(d)

    def test_factory(self):
        new_time = utils.DateTime.now()
        assert isinstance(new_time, utils.DateTime)

    def test_timestamp(self):
        #ensure that timestamp is check with appropriate timezone offset
        assert (1425750464+time.timezone) == self.datetime.timestamp

    def test_repr(self):
        assert '2015-03-07 17:47:44' == '{}'.format(self.datetime)

    def test_initialize_int(self):
        d = utils.DateTime(1425750464)
        assert 1425750464 == d.timestamp
        #ensure that time is check with appropriate timezone offset
        t = time.strftime("%Y-%m-%d %H:%M:%S", 
              time.localtime((time.mktime(time.strptime("2015-03-07 17:47:44", 
                                                    "%Y-%m-%d %H:%M:%S")))-time.timezone))
        assert t == '{}'.format(d)

    def test_initialize_string(self):
        d = utils.DateTime('2015-03-07T17:47:44')
        # ensure that timestamp is check with appropriate timezone offset
        assert (1425750464+time.timezone) == d.timestamp
        assert '2015-03-07 17:47:44' == '{}'.format(d)

    def test_sub(self):
        d2 = datetime.datetime(2015, 3, 7, 18, 18, 38, 508411)
        ts2 = utils.DateTime(d2)
        assert '0:30:53.791612' == '{}'.format(ts2 - self.datetime)

