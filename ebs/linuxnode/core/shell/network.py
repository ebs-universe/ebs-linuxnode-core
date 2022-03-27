

import ifcfg
from twisted.internet.defer import succeed
from ..config import ElementSpec, ItemSpec
from . import BaseShellMixin


class WifiNetworkInfoMixin(BaseShellMixin):
    @property
    def wifi_ssid(self):
        def _handle_result(result):
            return result.strip()
        d = self._shell_execute(['iwgetid', '-s'], _handle_result)
        return d


class NetworkInfoMixin(WifiNetworkInfoMixin):
    def install(self):
        super(NetworkInfoMixin, self).install()
        _elements = {
            'network_interface_wifi': ElementSpec('network', 'wifi', ItemSpec(fallback='wlan0')),
            'network_interface_ethernet': ElementSpec('network', 'ethernet', ItemSpec(fallback='eth0')),
            'network_interfaces': ElementSpec('_derived', self._network_interfaces)
        }
        for name, spec in _elements.items():
            self.config.register_element(name, spec)

    @staticmethod
    def _network_check_interface(interface):
        if_spec = ifcfg.interfaces().get(interface, None)
        if not if_spec:
            return
        if_flags = if_spec['flags'].split('<')[1].split('>')[0].split(',')
        if "UP" in if_flags and "RUNNING" in if_flags:
            return True
        else:
            return False

    @staticmethod
    def _network_get_ipaddress(interface):
        if_spec = ifcfg.interfaces().get(interface, None)
        if not if_spec:
            return
        return if_spec['inet']

    def _network_interfaces(self, config):
        return [config.network_interface_wifi, config.network_interface_ethernet]

    @property
    def network_interfaces(self):
        return self.config.network_interfaces

    @property
    def network_interfaces_wifi(self):
        return [self.config.network_interface_wifi]

    @property
    def network_interfaces_ethernet(self):
        return [self.config.network_interface_ethernet]

    @property
    def network_info(self):
        for interface in self.network_interfaces:
            if self._network_check_interface(interface):
                if interface in self.network_interfaces_wifi:
                    return self.wifi_ssid
                else:
                    return succeed(self._network_get_ipaddress(interface))
        return succeed(None)
