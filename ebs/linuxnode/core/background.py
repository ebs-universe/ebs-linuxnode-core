

import os
import time
from collections import namedtuple
from six.moves.urllib.parse import urlparse

from ebs.linuxnode.core.basemixin import BaseMixin
from ebs.linuxnode.core.log import NodeLoggingMixin
from ebs.linuxnode.core.resources import ResourceManagerMixin
from ebs.linuxnode.core.config import ElementSpec, ItemSpec


# TODO This is here, but not particularly tested. Expect it to only work for video.
# In general, background sequencing should be handled outside the Background code or
# by dedicated infrastructure with effectively allows gui_bg to accept a list of this class.
BackgroundSpec = namedtuple('BackgroundSpec', ["target", "bgcolor", "callback", "duration"],
                            defaults=[None, None, None])


class BackgroundProviderBase(object):
    is_visual = True

    def __init__(self, actual):
        self._actual = actual
        self._widget = None
        self._end_call = None
        self._paused = False
        self._eresidual = None
        self._callback = None

    @property
    def actual(self):
        if hasattr(self._actual, 'actual'):
            return self._actual.actual
        else:
            return self._actual

    def check_support(self, target):
        # Check if the provider supports the target and
        # if the target exists.
        raise NotImplementedError

    def play(self, target, duration=None, callback=None, **kwargs):
        # Create a Widgetized Background and return it.
        # It will be attached later.
        if duration and callback:
            self._callback = callback
            self._end_call = self.actual.reactor.callLater(duration, callback)

    def stop(self):
        # Stop and unload the Widgetized Background.
        # The widget has already been detached.
        if self._end_call and self._end_call.active():
            self._end_call.cancel()
        self._widget = None

    def pause(self):
        # Pause the Widgetized Background.
        # It has already been detached.
        if self._paused:
            return
        if self._end_call and self._end_call.active():
            ietime = self._end_call.getTime()
            ptime = time.time()
            self._eresidual = ietime - ptime
            self._end_call.cancel()
        self._paused = True

    def resume(self):
        # Resume the Widgetized Background.
        # It will be attached later.
        if not self._paused:
            return
        self._paused = False
        if self._eresidual:
            self._end_call = self.actual.reactor.callLater(self._eresidual, self._callback)
            self._eresidual = None


class BackgroundCoreMixin(ResourceManagerMixin, NodeLoggingMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super(BackgroundCoreMixin, self).__init__(*args, **kwargs)
        self._bg_providers = []
        self._bg = None
        self._bg_current = None
        self._bg_current_provider = None

    def _background_fallback(self):
        return None

    def install(self):
        super(BackgroundCoreMixin, self).install()
        _elements = {
            'background': ElementSpec('display', 'background',
                                      ItemSpec(str, read_only=False, fallback=self._background_fallback())),
        }
        for name, spec in _elements.items():
            self.config.register_element(name, spec)

    def install_background_provider(self, provider):
        self.log.info("Installing BG Provider {}".format(provider))
        self._bg_providers.insert(0, provider)

    def _get_provider(self, target):
        provider: BackgroundProviderBase
        provider = None
        for lprovider in self._bg_providers:
            if lprovider.check_support(target):
                provider = lprovider
                break
        return provider

    def render_bg_providers(self):
        return [str(x.__class__.__name__) for x in self._bg_providers]

    def background_set(self, target):
        if not target:
            target = None

        provider = self._get_provider(target)
        if not provider:
            self.log.warn("Provider not found for background {}. Not Setting.".format(target))
            target = None

        if target and self.config.background != target:
            old_bg = urlparse(self.config.background)
            if not old_bg.scheme:
                old_fname = os.path.basename(old_bg.path)
                if self.resource_manager.has(old_fname):
                    self.resource_manager.remove(old_fname)
            self.config.background = target

        self.bg_update()

    def bg_clear(self):
        self._bg = None
        if self._bg_current_provider:
            self._bg_current_provider.stop()

    @property
    def bg(self):
        return self._bg_current

    @bg.setter
    def bg(self, value):
        self.log.debug(f"Setting background to {value}", value=value)
        bgcolor, callback, duration = None, None, None
        if isinstance(value, BackgroundSpec):
            value, bgcolor, callback, duration = value

        if self._bg_current == value and not callback and not duration:
            return False

        if not bgcolor:
            try:
                bgcolor = self.config.image_bgcolor
            except:
                bgcolor = 'auto'

        provider = self._get_provider(value)

        if not provider:
            self.log.warn("Provider not found for background {}".format(value))
            value = self.config.background
            self._bg_signal_fallback(with_reset=False)
            provider = self._get_provider(value)
            self.log.warn("Trying to use {} instead.".format(value))

        if not provider:
            self.log.warn("Unable to display config background. Clearing from config.")
            self.config.remove('background')
            self._bg_signal_fallback(with_reset=True)
            value = self.config.background
            provider = self._get_provider(value)

        self.log.debug("Using {} to show background {}".format(provider, value))
        self.bg_clear()

        self._bg_current = value
        self._bg_current_provider = provider
        self._bg = self._bg_current_provider.play(
            value, bgcolor=bgcolor, callback=callback, duration=duration
        )

        return True

    def _bg_signal_fallback(self, with_reset=False):
        pass

    def bg_pause(self):
        self.log.debug("Pausing Background")
        if self._bg_current_provider:
            self._bg_current_provider.pause()

    def bg_resume(self):
        self.log.debug("Resuming Background")
        if self._bg_current_provider:
            self._bg_current_provider.resume()

    def bg_update(self):
        self.bg = self.config.background

    def start(self):
        super(BackgroundCoreMixin, self).start()
        # TODO This will break unless the GUI components are in place. If it needs
        #  to be used separately, an alternate approach needs to be implemented.
        # self.reactor.callLater(3, self.bg_update)

    def stop(self):
        if self._bg_current_provider:
            self._bg_current_provider.stop()
        super(BackgroundCoreMixin, self).stop()
