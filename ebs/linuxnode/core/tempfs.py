

import shutil
import tempfile
from memory_tempfile import MemoryTempfile

from .basemixin import BaseMixin
from .log import NodeLoggingMixin
from .config import ElementSpec
from .config import ItemSpec


class TempFSMixin(NodeLoggingMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        super(TempFSMixin, self).__init__(*args, **kwargs)
        self._tempfile = None
        self._tempdir = None

    def install(self):
        super(TempFSMixin, self).install()
        _elements = {
            'tmpfs_prefer_memory': ElementSpec('tmpfs', 'memory_prefer', ItemSpec(bool, fallback=True)),
            'tmpfs_force_memory': ElementSpec('tmpfs', 'memory_force', ItemSpec(bool, fallback=False)),
            'tmpfs_clean_on_exit': ElementSpec('tmpfs', 'clean_on_exit', ItemSpec(bool, fallback=True)),
        }
        for name, spec in _elements.items():
            self.config.register_element(name, spec)

    def _tempfile_init(self):
        if self.config.tmpfs_force_memory:
            # TODO This should use MemoryTempfile to find a tmpfs or ramfs path,
            #  and fail (throw exception) if a suitable path does not exist.
            #  - The assumption is going to be that it will be upto the deployment
            #    to ensure a suitable path exists.
            #  - Mounting here is not viable due to permission issues
            #  - Using pyfilesystem2 is not viable since all users will also need
            #    to treat it as a pyfilesystem2 object, and external processes
            #    cannot be handed this path.
            raise NotImplementedError
        elif self.config.tmpfs_prefer_memory:
            self._tempfile = MemoryTempfile()
        else:
            self._tempfile = tempfile

    @property
    def tempfile(self):
        if not self._tempfile:
            self._tempfile_init()
        return self._tempfile

    @property
    def tempdir(self):
        if not self._tempdir:
            self._tempdir = self.tempfile.mkdtemp()
        return self._tempdir

    def start(self):
        super().start()
        self.log.debug(f"Using tempfs: {self.tempfile.gettempdir()}")
        self.log.info(f"Using tempdir: {self.tempdir}")

    def stop(self):
        if self.tempdir:
            if self.config.tmpfs_clean_on_exit:
                self.log.info(f"Cleaning up tempdir: {self.tempdir}")
                shutil.rmtree(self.tempdir)
            else:
                self.log.info(f"Not cleaning up tempdir: {self.tempdir}")
        super().stop()
