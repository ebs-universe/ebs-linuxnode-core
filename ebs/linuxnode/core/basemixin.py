

import os
import atexit
import shutil
import tempfile
from appdirs import user_cache_dir
from twisted.internet import reactor


class BaseMixin(object):
    _appname = 'iotnode'
    _app_root = os.path.abspath(os.path.dirname(__file__))
    _app_resources = os.path.join(_app_root, 'resources')

    def __init__(self, *args, **kwargs):
        self._reactor = kwargs.pop('reactor', reactor)
        self._cache_dir = None
        self._db_dir = None
        self._temp_dir = None
        super(BaseMixin, self).__init__(*args, **kwargs)

    @property
    def app_resources(self):
        return self._app_resources

    def install(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def _deferred_error_passthrough(self, failure):
        return failure

    def _deferred_error_swallow(self, failure):
        return

    @property
    def reactor(self):
        return self._reactor

    @property
    def appname(self):
        return self._appname

    @property
    def cache_dir(self):
        if not self._cache_dir:
            self._cache_dir = user_cache_dir(self.appname)
            os.makedirs(self._cache_dir, exist_ok=True)
        return self._cache_dir

    @property
    def db_dir(self):
        if not self._db_dir:
            self._db_dir = os.path.join(self.cache_dir, 'db')
            os.makedirs(self._db_dir, exist_ok=True)
        return self._db_dir

    @property
    def temp_dir(self):
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp()
            atexit.register(shutil.rmtree, self._temp_dir)
        return self._temp_dir
