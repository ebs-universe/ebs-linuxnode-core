

from os import environ
from twisted.internet.utils import getProcessOutput
from twisted.internet.error import ProcessExitedAlready
from twisted.internet.protocol import ProcessProtocol
from .basemixin import BaseMixin
from .config import ConfigMixin


class ProcessClient(ProcessProtocol):
    def __init__(self, line_handler=None, exit_handler=None,
                 name=None, *args, **kwargs):
        super(ProcessClient, self).__init__(*args, **kwargs)
        self._line_handler = line_handler
        self._exit_handler = exit_handler
        self._name = name

    def connectionMade(self):
        pass

    def outReceived(self, data: bytes):
        if self._line_handler:
            self._line_handler(data.strip().decode())

    def errReceived(self, data):
        pass

    def inConnectionLost(self):
        # stdin is closed. (we probably did it)"
        pass

    def outConnectionLost(self):
        # The child closed their stdout.
        pass

    def errConnectionLost(self):
        # The child closed their stderr.
        pass

    def processExited(self, reason):
        pass

    def processEnded(self, reason):
        if self._exit_handler:
            self._exit_handler(reason.value.exitCode)


class BaseShellMixin(ConfigMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        self._shell_processes = {}
        super(BaseShellMixin, self).__init__(*args, **kwargs)

    def _shell_execute(self, command, response_handler):
        if len(command) > 1:
            args = command[1:]
        else:
            args = []
        d = getProcessOutput(command[0], args, env=environ)
        d.addCallback(response_handler)
        return d

    def shell_process(self, executable, args=None, env=None,
                      protocol=None, usePTY=True,
                      line_handler=None, exit_handler=None, name=None):
        if not name:
            name = executable

        if protocol:
            client = protocol()
        elif line_handler:
            usePTY = True
            client = ProcessClient(
                exit_handler=exit_handler,
                line_handler=line_handler,
                name=name
            )
        else:
            raise AttributeError("Either protocol or line_handler must be provided")

        self._shell_processes[name] = client
        if not args:
            args = []
        if not len(args) or args[0] != executable:
            args.insert(0, executable)
        self.reactor.spawnProcess(client, executable, args=args, env=env, usePTY=usePTY)

    def stop(self):
        super(BaseShellMixin, self).stop()
        for name, process in self._shell_processes.items():
            try:
                process.transport.signalProcess('TERM')
                process.transport.loseConnection()
                self.log.info(f"Terminated child process {name}")
            except ProcessExitedAlready:
                self.log.info(f"Child process {name} not running")
