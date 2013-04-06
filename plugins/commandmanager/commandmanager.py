import shlex
import inspect
from bin.shared.perms import Perm


class CommandManager:
    def __init__(self, xml):
        self._commands = {}
        self._plugins = {}
        self.registerCommand("help", self.listCommands)

    def listCommands(self, command, args, source):
        ret = "Available Commands:\n"
        ret += ", ".join(self._commands.keys())
        return ret, self._commands.keys()

    def registerCommand(self, command, callback, perm=Perm.User):
        if not command in self._commands:
            frm = inspect.stack()[1]
            mod = inspect.getmodule(frm[0])
            plugin = mod.__name__
            splitplugin = plugin.split(".")
            #get plugin dir
            plugin = splitplugin[2]
            if plugin not in self._plugins:
                self._plugins[plugin] = []
            self._plugins[plugin].append(command)
            self._commands[command] = {"callback": callback, "perm": perm}
        else:
            log.error("Command:", command, "is already registered")

    def unRegisterCommand(self, command):
        if command in self._commands:
            del self._commands[command]

    def unRegisterPlugin(self, plugin):
        if plugin in self._plugins:
            for command in self._plugins[plugin]:
                self.unRegisterCommand(command)

    def unRegisterAllPlugins(self):
        for plugin in self._plugins.keys():
            for command in self._plugins[plugin]:
                self.unRegisterCommand(command)

    def fireCommand(self, command, args, source):
        if command in self._commands:
            return self._commands[command]["callback"](command, args, source)
        else:
            return False

    def processCommand(self, source, data):
        src = "%s, %s" % (source['SourceID'], source['SourceRank'])
        prodata = data
        if not isinstance(data, list):
            prodata = self._processCommandArguments(data)
        #is there really prodata
        if prodata and len(prodata) > 0:
            #clean up the command
            cmd = self._prepareCommandArgument(prodata[0])
            if len(prodata) > 1:
                #remove the command leaving the arguments
                prodata.pop(0)
                #turn arguments into a list
                for index, arg in enumerate(prodata):
                    #clean up the args
                    prodata[index] = self._prepareCommandArgument(arg)
                args = prodata
            else:
                #no args
                args = []

            #fire command
            log.info("command from", src, "COMMAND", cmd, "ARGS", args)
            result = False
            if cmd in self._commands:
                if self._commands[cmd]["perm"] <= source['SourceRank']:
                    result = self.fireCommand(cmd, args, source)
            return result

    def _processCommandArguments(self, arguments):
        lex = shlex.shlex(arguments, None, True)

        lex.quotes = '"'
        lex.whitespace_split = True
        lex.commenters = ''

        return list(lex)

    def _prepareCommandArgument(self, argument):
        if argument is None:
            return argument

        argument = str(argument)

        if argument[0] == '"' and argument[len(argument) - 1] == '"':
            return argument[1:-1].strip()

        return argument

    def destroy(self, callback):
        for command in self._commands.values():
            del command
