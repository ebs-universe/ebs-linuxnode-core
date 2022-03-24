

from .basemixin import BaseMixin
from .log import NodeLoggingMixin


class NodeBusyMixin(NodeLoggingMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super(NodeBusyMixin, self).__init__(*args, **kwargs)
        self._busy = False

    @property
    def busy(self):
        if self._busy > 0:
            return True
        else:
            return False

    def busy_set(self):
        self._busy += 1

    def busy_clear(self):
        self._busy -= 1
        if self._busy < 0:
            self.log.warn("Busy cleared too many times!")
            self._busy = 0

    def _busy_setter(self, value):
        self.log.debug("Setting node busy status to {0}".format(value))
        self._busy = value
