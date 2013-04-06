from threading import Timer
from bin.shared.perms import Perm


class Base:
    def __init__(self, xml):
        manager.commandmanager.registerCommand("about", self.aboutCommand)
        manager.commandmanager.registerCommand("plugins", self.pluginsCommand)
        manager.commandmanager.registerCommand("restart", self.restartBot, perm=Perm.Super)
        manager.commandmanager.registerCommand("echo", self.echoCommand, perm=Perm.Mod)
        raise

    def aboutCommand(self, command, args, source):
        return "Dihydrogen Monoxide Bot, Version %s" % (manager.getVersion())

    def pluginsCommand(self, command, args, source):
        plugins = manager.getPluginsInfo()
        ret = "List of plugins: \n"
        ret += "\n".join(plugins)
        return "", ret

    def restartBot(self, command, args, source):
        t = Timer(1, manager.restartBot)
        t.start()
        return "", "Restarting WaterBot"

    def echoCommand(self, command, args, source):
        return " ".join(args)
