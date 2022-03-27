
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


ItemSpec = namedtuple('ItemSpec', ["item_type", "fallback", "read_only"], defaults=[str, '_required', True])
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
        item_type, fallback, read_only = item_spec
        kwargs = {}
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

    def __setattr__(self, element, value):
        if element == '_elements' or element not in self._elements.keys():
            return super(IoTNodeConfig, self).__setattr__(element, value)
        section, item, item_spec = self._elements[element]
        item_type, fallback, read_only = item_spec

        if read_only:
            raise AttributeError("{} element '{}' is read_only. Cannot write."
                                 "".format(self.__class__.__name__, element))
        if item_type == bool:
            value = "yes" if value else "no"

        self._check_section(section)
        self._config.set(section, item, value)
        self._write_config()

    def _config_init(self):
        _elements = {
            'platform': ElementSpec('platform', 'platform', ItemSpec(fallback='native')),
            'debug': ElementSpec('debug', 'debug', ItemSpec(bool, fallback=False)),
        }

        for element, element_spec in _elements.items():
            self.register_element(element, element_spec)
        self._apply_display_layer()

    def print(self):
        print("Node Configuration ({})".format(self.__class__.__name__))
        for element in self._elements.keys():
            print("    {:>30}: {}".format(element, getattr(self, element)))
    # Legacy Config, to be migrated.

    # Video
    @property
    def video_external_player(self):
        if self.platform == 'rpi':
            return self._config.getboolean('video-rpi', 'external_player', fallback=False)

    @property
    def video_dispmanx_layer(self):
        if self.platform == 'rpi':
            return self._config.getint('video-rpi', 'dispmanx_video_layer', fallback=4)

    @property
    def video_show_backdrop(self):
        if self.platform == 'rpi':
            return self._config.getboolean('video-rpi', 'show_backdrop', fallback=False)

    @property
    def video_backdrop_dispmanx_layer(self):
        if self.platform == 'rpi':
            return self._config.getint('video-rpi', 'dispmanx_video_layer', fallback=1)

    # Display
    @property
    def fullscreen(self):
        return self._config.getboolean('display', 'fullscreen', fallback=True)

    @property
    def portrait(self):
        return self._config.getboolean('display', 'portrait', fallback=False)

    @portrait.setter
    def portrait(self, value):
        self._check_section('display')
        self._config.set('display', 'portrait', "yes" if value else "no")
        self._write_config()

    @property
    def flip(self):
        return self._config.getboolean('display', 'flip', fallback=False)

    @flip.setter
    def flip(self, value):
        self._check_section('display')
        self._config.set('display', 'flip', "yes" if value else "no")
        self._write_config()

    @property
    def orientation(self):
        rv = 0
        if self.portrait is True:
            rv += 90
        if self.flip:
            rv += 180
        return rv

    @property
    def os_rotation(self):
        return self._config.getboolean('display', 'os_rotation', fallback=False)

    def orientation_update(self):
        from kivy.config import Config
        Config.set('graphics', 'rotation', self.orientation)

    @property
    def overlay_mode(self):
        return self._config.getboolean('display', 'overlay_mode', fallback=False)

    @property
    def sidebar_width(self):
        return self._config.getfloat('display', 'sidebar_width', fallback=0.3)

    @property
    def sidebar_height(self):
        rv = self._config.getfloat('display', 'sidebar_height', fallback=0.0)
        if not rv:
            rv = self.sidebar_width
        return rv

    @property
    def show_foundation(self):
        return self._config.getboolean('display-rpi', 'show_foundation', fallback=True)

    @property
    def dispmanx_foundation_layer(self):
        return self._config.getint('display-rpi', 'dispmanx_foundation_layer', fallback=1)

    @property
    def foundation_image(self):
        return self._config.get('display-rpi', 'foundation_image', fallback=None)

    @property
    def image_bgcolor(self):
        return self._parse_color(self._config.get('display', 'image_bgcolor', fallback='auto'))

    @property
    def background(self):
        return self._config.get('display', 'background', fallback='images/background.png')

    @background.setter
    def background(self, value):
        self._check_section('display')
        self._config.set('display', 'background', value)
        self._write_config()

    @property
    def background_external_player(self):
        if self.platform == 'rpi':
            return self._config.getboolean('display-rpi', 'background_external_player', fallback=False)

    @property
    def background_dispmanx_layer(self):
        return self._config.getint('display-rpi', 'background_dispmanx_layer', fallback=2)

    @property
    def app_dispmanx_layer(self):
        if self.platform != 'rpi':
            raise AttributeError("dispmanx layer is an RPI thing")
        return self._config.getint('display-rpi', 'dispmanx_app_layer', fallback=5)

    def _apply_display_layer(self):
        if self.platform == 'rpi':
            os.environ.setdefault('KIVY_BCM_DISPMANX_LAYER', str(self.app_dispmanx_layer))


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
