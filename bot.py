import sys
import __builtin__
from threading import Timer

import bin.log
import bin.manager


class BOT:
    def __init__(self, config):
        self.config = config
        self.start()

    def start(self):
        #make logger global
        __builtin__.log = bin.log.Log(self.config)

        # Create the manager
        pluginmanager = bin.manager.Manager(self.config)

        #make manager global
        __builtin__.manager = pluginmanager

        pluginmanager.loadPlugins()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        config = sys.argv[1]
    else:
        config = 'config.xml'

    #start up bot
    BOT(config)
