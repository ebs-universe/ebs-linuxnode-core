

import uuid
import netifaces

from .basemixin import BaseMixin
from .config import ConfigMixin
from .config import ElementSpec, ItemSpec


class NodeIDMixin(ConfigMixin, BaseMixin):
    _node_id_netifaces_fallback_interfaces = ['wlp1s0', 'wlan0', 'wlo1', 'eth0']

    def __init__(self, *args, **kwargs):
        super(NodeIDMixin, self).__init__(*args, **kwargs)
        self._id = None

    def install(self):
        super(NodeIDMixin, self).install()
        _elements = {
            'node_id_getter': ElementSpec('id', 'getter', ItemSpec(fallback='netifaces')),
            'node_id_interface': ElementSpec('id', 'interface', ItemSpec(fallback=None)),
            'node_id_override': ElementSpec('id', 'override', ItemSpec(fallback=None)),
        }
        for name, spec in _elements.items():
            self.config.register_element(name, spec)

    @property
    def id(self):
        if self._id is None:
            self._id = self._get_id()
        return self._id

    def _get_id(self):
        if self.config.node_id_override is not None:
            return self.config.node_id_override
        getter = "_get_node_id_{0}".format(self.config.node_id_getter)
        params = {'interface': self.config.node_id_interface}
        return getattr(self, getter)(**params).upper()

    def _get_node_id_uuid(self, **_):
        node_id = uuid.getnode()
        if (node_id >> 40) % 2:
            raise OSError("The system does not seem to have a valid MAC")
        return hex(node_id)[2:]

    def _get_node_id_netifaces_guess(self):
        fallback_interfaces = self._node_id_netifaces_fallback_interfaces
        available_interfaces = netifaces.interfaces()
        default_gateway = netifaces.gateways()['default']
        if default_gateway:
            return default_gateway[netifaces.AF_INET][1]
        for iface in fallback_interfaces:
            if iface in available_interfaces:
                return iface

    def _get_node_id_netifaces(self, **kwargs):
        interface = kwargs.get('interface', None)
        if interface is None:
            interface = self._get_node_id_netifaces_guess()
        mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        return mac.replace(':', '')
