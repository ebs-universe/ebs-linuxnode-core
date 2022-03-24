

from .nodeid import NodeIDMixin
from .log import NodeLoggingMixin
from .busy import NodeBusyMixin
from .shell import BaseShellMixin
from .http import HttpClientMixin
from .resources import ResourceManagerMixin


class BaseIoTNode(ResourceManagerMixin,
                  HttpClientMixin,
                  BaseShellMixin,
                  NodeBusyMixin,
                  NodeLoggingMixin,
                  NodeIDMixin):
    _has_gui = False

    def __init__(self, *args, **kwargs):
        super(BaseIoTNode, self).__init__(*args, **kwargs)

    def install(self):
        super(BaseIoTNode, self).install()
        self._log.info("Installing Node with ID {log_source.id}")

    def start(self):
        super(BaseIoTNode, self).start()
        self._log.info("Starting Node with ID {log_source.id}")

    def stop(self):
        super(BaseIoTNode, self).stop()
        self._log.info("Stopping Node with ID {log_source.id}")
