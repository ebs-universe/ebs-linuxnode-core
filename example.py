

from twisted.internet import reactor
from ebs.linuxnode.core.basenode import BaseIoTNode
from ebs.linuxnode.core import config


class ExampleNode(BaseIoTNode):
    def start(self):
        self.install()
        super(ExampleNode, self).start()
        self.config.print()
        reactor.callLater(10, self.stop)
        reactor.run()

    def stop(self):
        super(ExampleNode, self).stop()
        reactor.stop()


def main():
    nodeconfig = config.IoTNodeConfig('iotnode-bare')
    config.current_config = nodeconfig

    node = ExampleNode(reactor=reactor)
    node.start()


if __name__ == '__main__':
    main()
