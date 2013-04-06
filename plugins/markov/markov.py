import clr


class Markov:
    def __init__(self, xml):
        manager.commandmanager.registerCommand("mk", self.markovCommand)

    def markovCommand(self, command, args, source):
        return "hi"
