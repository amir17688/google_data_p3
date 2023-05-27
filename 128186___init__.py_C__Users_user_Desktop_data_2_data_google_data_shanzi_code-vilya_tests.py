import os, shutil

from unittest import TestCase

from tests import settings
from vilya import gitmodels

import yoyo
from yoyo.connections import connect


class VilyaTestCase(TestCase):

    def _init_git_env(self):
        if not os.path.isdir(settings.GIT_REPO_ROOT):
            os.mkdir(settings.GIT_REPO_ROOT)
        if not os.path.isdir(settings.GIT_TEMP_REPO_ROOT):
            os.mkdir(settings.GIT_TEMP_REPO_ROOT)

    def _clear_git_env(self):
        if os.path.isdir(settings.GIT_REPO_ROOT):
            shutil.rmtree(settings.GIT_REPO_ROOT)
        if os.path.isdir(settings.GIT_TEMP_REPO_ROOT):
            shutil.rmtree(settings.GIT_TEMP_REPO_ROOT)

    def setUp(self):
        super(VilyaTestCase, self).setUp()
        self._settings = settings
        self._init_git_env()

    def tearDown(self):
        self._clear_git_env()
        super(VilyaTestCase, self).tearDown()


class VilyaAppTestCase(VilyaTestCase):

    def _create_app(self, settings):
        raise NotImplementedError

    def _migrate_database(self):
        db_config = {
                'host':'localhost',
                'user':'root',
                'passwd':'',
                'name':'vilya-test'}
        db_config.update(self.app.config['DATABASE'])
        migrations_dir = self.app.config['MIGRATIONS_DIR']
        if db_config['passwd']:
            db_config['user'] += ':' + db_config['passwd'] 
        if db_config.get('port'):
            db_config['host'] += ':' + db_config['port'] 
        db_connection_url = "mysql://{user}@{host}/{name}".format(**db_config)
        connection, paramstyle = connect(db_connection_url)
        migrations = yoyo.read_migrations(connection, paramstyle, migrations_dir)
        migrations.to_apply().apply()
        connection.commit()
        self.migrate_info = (connection, paramstyle, migrations_dir)

    def _rollback_database(self):
        connection, paramstyle, migrations_dir = self.migrate_info
        migrations = yoyo.read_migrations(connection, paramstyle, migrations_dir)
        migrations.to_rollback().rollback()
        connection.commit()

    def _create_fixtures(self):
        pass

    def setUp(self):
        super(VilyaAppTestCase, self).setUp()
        self.app = self._create_app(settings)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self._migrate_database()
        self._create_fixtures()

    def tearDown(self):
        self._rollback_database()
        self.app_context.pop()
        super(VilyaAppTestCase, self).tearDown()

