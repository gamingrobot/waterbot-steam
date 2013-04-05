import sys
import subprocess
import shlex
import time
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names


class WatchDog:
    def __init__(self, config):
        self.config = config
        self.bot = None

    def startBot(self):
        self._openBot()
        self._watcher()

    def _restartBot(self):
        self._updateBot()
        self._openBot()

    def _exec_shell(self, command):
        """Execute a shell command and get the output."""
        command = shlex.split(command)
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if result:
            result = result[:-1]  # strip newline if command returned anything
        return result

    def _updateBot(self):
        try:
            dry_fetch = self._exec_shell("git fetch --dry-run")
        except subprocess.CalledProcessError:
            print "Cannot fetch; do you have a remote repository configured correctly?"
            return
        try:
            last_commit = self._exec_shell("git log -n 1 --pretty=\"%ar\"")
        except subprocess.CalledProcessError:
            last_commit = "never"  # couldn't get a log, so no commits

        if not dry_fetch:  # no new changes to pull
            print "No new changes. Last commit was %s." % last_commit

        else:  # stuff has happened!
            print "There are new changes upstream..."
            status = self._exec_shell("git status")

            if status.endswith("nothing to commit (working directory clean)"):
                print "Pulling new changes..."
                result = self._exec_shell("git pull")
                print "The following changes have been made since %s:" % last_commit
                print result
            else:
                print "Warning: you have uncommitted changes in this repository!"
                print "Ignoring."

    def _openBot(self):
        self.bot = subprocess.Popen(["ipy", '-X:Frames', '-u', 'bot.py', config], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, close_fds=ON_POSIX)

    def _watcher(self):
        while True:
            try:
                # read line without blocking
                try:
                    line = self.bot.stdout.readline()
                except Empty:
                    pass
                else:  # got line
                    print line.rstrip()
                #polling
                status = self.bot.poll()
                if status is not None:
                    time.sleep(2)
                    print "-----------------------------"
                    self._restartBot()
                #thread sleep
                time.sleep(0.02)
            except KeyboardInterrupt:
                self.bot.terminate()
                sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        config = sys.argv[1]
    else:
        config = 'config.xml'

    watchdog = WatchDog(config)
    watchdog.startBot()
