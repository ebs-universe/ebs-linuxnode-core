

from twisted.internet import reactor
from ebs.linuxnode.core.basenode import BaseIoTNode
from ebs.linuxnode.core import config


def main():
    nodeconfig = config.IoTNodeCoreConfig()
    config.current_config = nodeconfig

    node = BaseIoTNode(reactor)
    node.start()


if __name__ == '__main__':
    main()
