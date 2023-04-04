
# foundation    ()
# backdrop      1
# background    2
# backdrop      3
# video         4
# app           5


import os
import pkg_resources
from six.moves.configparser import ConfigParser
from collections import namedtuple
from appdirs import user_config_dir
from configparser import NoSectionError


ItemSpec = namedtuple('ItemSpec', ["item_type", "fallback", "read_only", "masked"],
                      defaults=[str, '_required', True, False])
ElementSpec = namedtuple('ElementSpec', ['section', 'item', 'item_spec'], defaults=[ItemSpec()])


class IoTNodeConfig(object):
    def __init__(self, appname=None, packagename=None):
        self._elements = {}
        self._packagename = packagename
        self._appname = appname or 'iotnode'
        _root = os.path.abspath(os.path.dirname(__file__))
        self._roots = [_root]
        self._config = ConfigParser()
        print("Reading Config File {}".format(self._config_file))
        self._config.read(self._config_file)
        print("EBS IOT Linux Node Core, version {0}".format(self.linuxnode_core_version))
        self._config_init()

    @property
    def appname(self):
        return self._appname

    @property
    def _config_file(self):
        return os.path.join(user_config_dir(self.appname), 'config.ini')

    @property
    def linuxnode_core_version(self):
        return pkg_resources.get_distribution('ebs-linuxnode-core').version

    @property
    def app_version(self):
        if not self._packagename:
            return
        return pkg_resources.get_distribution(self._packagename).version

    def _write_config(self):
        with open(self._config_file, 'w') as configfile:
            self._config.write(configfile)

    def _check_section(self, section):
        if not self._config.has_section(section):
            self._config.add_section(section)
            self._write_config()

    def _parse_color(self, value, on_error='auto'):
        color = value.split(':')
        if len(color) not in (3, 4):
            return on_error
        try:
            color = (float(x) for x in color)
        except ValueError:
            return on_error
        return tuple(color)

    # Paths
    @property
    def roots(self):
        return list(reversed(self._roots))

    def get_path(self, filepath):
        if not filepath:
            return filepath
        for root in self.roots:
            if os.path.exists(os.path.join(root, filepath)):
                return os.path.join(root, filepath)
        return filepath

    def register_application_root(self, root):
        self._roots.append(root)

    # Modular Config Infrastructure
    def register_element(self, name, element_spec):
        self._elements[name] = element_spec

    def __getattr__(self, element):
        if element not in self._elements.keys():
            raise AttributeError(element)
        section, item, item_spec = self._elements[element]
        item_type, fallback, read_only, masked = item_spec
        kwargs = {}
        if callable(fallback):
            fallback = fallback(self)
        if not fallback == "_required":
            kwargs['fallback'] = fallback
        if section == '_derived':
            return item(self)
        if item_type == str:
            return self._config.get(section, item, **kwargs)
        elif item_type == bool:
            return self._config.getboolean(section, item, **kwargs)
        elif item_type == int:
            return self._config.getint(section, item, **kwargs)
        elif item_type == float:
            return self._config.getfloat(section, item, **kwargs)
        elif item_type == 'kivy_color':
            return self._parse_color(self._config.get(section, item, **kwargs))
        elif item_type == 'path':
            return self.get_path(self._config.get(section, item, **kwargs))

    def __setattr__(self, element, value):
        if element == '_elements' or element not in self._elements.keys():
            return super(IoTNodeConfig, self).__setattr__(element, value)
        section, item, item_spec = self._elements[element]
        item_type, fallback, read_only, masked = item_spec

        if read_only:
            raise AttributeError("{} element '{}' is read_only. Cannot write."
                                 "".format(self.__class__.__name__, element))
        if item_type == bool:
            value = "yes" if value else "no"

        if not value:
            value = ''

        self._check_section(section)
        self._config.set(section, item, value)
        self._write_config()

    def remove(self, element):
        section, item, item_spec = self._elements[element]
        if item_spec.read_only:
            return False
        try:
            return self._config.remove_option(section, item)
        except NoSectionError:
            pass

    def _config_init(self):
        _elements = {
            'platform': ElementSpec('platform', 'platform', ItemSpec(fallback='native')),
        }

        for element, element_spec in _elements.items():
            self.register_element(element, element_spec)

    @staticmethod
    def mask_value(pv):
        v_len = len(pv)
        m_len = int(min(v_len / 8, 8))
        return f"{pv[:m_len]}...{pv[-m_len:]}"

    def scrubbed_value(self, key):
        pv = getattr(self, key)
        if self._elements[key].item_spec.masked and isinstance(pv, str):
            pv = self.mask_value(pv)
        return pv

    def print(self):
        print("Node Configuration ({})".format(self.__class__.__name__))
        for element in self._elements.keys():
            print("    {:>30}: {}".format(element, self.scrubbed_value(element)))


class ConfigMixin(object):
    def __init__(self, *args, **kwargs):
        global current_config
        self._config: IoTNodeConfig = current_config
        super(ConfigMixin, self).__init__(*args, **kwargs)

    @property
    def config(self):
        return self._config

    def config_register_element(self, name, element_spec):
        self.config.register_element(name, element_spec)
