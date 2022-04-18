

import os
import appdirs

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
        self.log.info("Installing Node with ID {id}", id=self.id)
        os.makedirs(appdirs.user_config_dir(self.config.appname), exist_ok=True)

    def start(self):
        super(BaseIoTNode, self).start()
        self.log.info("Starting Node with ID {id}", id=self.id)

    def stop(self):
        super(BaseIoTNode, self).stop()
        self.log.info("Stopping Node with ID {id}", id=self.id)
