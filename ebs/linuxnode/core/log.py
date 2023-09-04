

import os
import io
import sys
import time
from twisted import logger
from twisted.logger import LogLevel
from twisted.logger import LogLevelFilterPredicate
from twisted.logger import FilteringLogObserver
from twisted.logger import textFileLogObserver

from appdirs import user_log_dir
from datetime import datetime

from .config import ElementSpec, ItemSpec
from .config import ConfigMixin
from .basemixin import BaseMixin

import logging
logging.basicConfig(level=logging.INFO)


class NodeLoggingMixin(ConfigMixin, BaseMixin):
    _log = None

    def __init__(self, *args, **kwargs):
        super(NodeLoggingMixin, self).__init__(*args, **kwargs)
        self._log_file = None
        self.log_prune()
        self._log = logger.Logger(namespace=self.appname,
                                  source=self)
        self.reactor.callWhenRunning(self._start_logging)

    def install(self):
        super(NodeLoggingMixin, self).install()
        _elements = {
            'debug': ElementSpec('debug', 'debug', ItemSpec(bool, fallback=False, read_only=False)),
        }

        for element, element_spec in _elements.items():
            self.config.register_element(element, element_spec)

    def _observers(self):
        if self.config.debug:
            level = LogLevel.debug
        else:
            level = LogLevel.info

        return [
            # STDLibLogObserver(),
            FilteringLogObserver(
                textFileLogObserver(sys.stdout),
                predicates=[LogLevelFilterPredicate(LogLevel.warn)]
            ),
            FilteringLogObserver(
                textFileLogObserver(io.open(self.log_file, 'a')),
                predicates=[LogLevelFilterPredicate(level)]
            ),
        ]

    def _start_logging(self):
        # TODO Mention that docs don't say reactor should be running
        # TODO Mention that docs are confusing about how extract works
        # TODO Find out about a functional print to console observer
        # TODO Mention problem with IOBase vs TextIOWrapper
        # TODO log_source is not set when logger instantiated in __init__
        logger.globalLogBeginner.beginLoggingTo(self._observers())
        self.log.info("Logging to {logfile}", logfile=self.log_file)

    @property
    def log(self):
        return self._log

    @property
    def log_file(self):
        if not self._log_file:
            self._log_file = os.path.join(
                self.log_dir,
                'runlog_{0}'.format(datetime.today().strftime('%d%m%y'))
            )
        return self._log_file

    def log_prune(self):
        for fname in self.log_files:
            fpath = os.path.join(self.log_dir, fname)
            mtime = os.path.getmtime(fpath)
            if time.time() - mtime > (7 * 24 * 60 * 60):
                os.remove(fpath)

    @property
    def log_files(self):
        return self._log_files()

    def _log_files(self):
        for filename in os.listdir(self.log_dir):
            if os.path.isfile(os.path.join(self.log_dir, filename)):
                yield filename

    @property
    def log_dir(self):
        os.makedirs(user_log_dir(self.appname), exist_ok=True)
        return user_log_dir(self.appname)

    def exim_install(self):
        super(NodeLoggingMixin, self).exim_install()
        self.exim.register_export('logs', self.log_dir)
