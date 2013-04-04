import xml.etree.ElementTree as et
import sys
import os
import importlib

bot_version = "1.0.0"


class Manager(object):
    """The simple plugin system"""
    def __init__(self, config):
        self._config = et.parse(config)
        self._plugindir = 'plugins'
        self._plugins = {}
        self._plugins_info = {}
        self._delayedplugins = []
        self._allunloaded = False
        self._stopstate = None

        log.info("WaterBot Started")

    def loadPlugins(self):
        elemPlugins = self._config.find('plugins')
        #load the plugins, if bot has been reloaded
        for plugin in elemPlugins.findall('plugin'):
            self._loadPlugin(plugin.get('name'))

    def unloadPlugins(self):
        self.commandmanager.unRegisterAllPlugins()
        for plugin in self._plugins.keys():
            if self._unloadPlugin(plugin):
                self._delayedplugins.append(plugin)
        self._allunloaded = True

    def _loadPlugin(self, plugin):
        plugin = plugin.lower()
        base = self._plugindir + '.' + plugin
        try:
            log.manager("loading", base)
            #not already loaded just import
            importlib.import_module(base)
            self._setupPlugin(base, plugin)
        except ImportError as e:
            log.error("Cannot load plugin %s, error follows: %s" % (base, e))
            raise

    #internal doesnt check if loaded
    def _unloadPlugin(self, plugin):
        plugin = plugin.lower()
        base = self._plugindir + '.' + plugin
        delayreload = False
        try:
            if plugin in self._plugins_info:
                del self._plugins_info[plugin]
            if plugin in self._plugins:
                if hasattr(self._plugins[plugin], "destroy"):
                    callback = self._destoryCallback
                    ret = self._plugins[plugin].destroy(callback)
                    if ret:
                        #delay the reloading if the destroy returned true
                        delayreload = True
                del self._plugins[plugin]
            if hasattr(self, plugin):
                delattr(self, plugin)
        except:
            log.error("Error unloading plugin %s." % (base))
            raise
        return delayreload

    #used for networked modules as a delayed loader
    def _destoryCallback(self, plugin):
        plugin = plugin.lower()
        log.manager("Plugins waiting to unload", self._delayedplugins)
        self._delayedplugins.remove(plugin)
        if len(self._delayedplugins) == 0 and self._allunloaded:
            self._handleRestart()

    #init plugin and set properties
    def _setupPlugin(self, base, plugin):
        plugin = plugin.lower()
        try:
            plugincfg = et.parse(os.path.join(self._plugindir, plugin, "plugin.xml"))
        except IOError:
            log.error("Plugin", plugin, "needs a plugin.xml")
            raise IOError("Plugin " + plugin + " needs plugin.xml")
        #set some info
        plugininfo = plugincfg.find('info')
        self._plugins_info[plugin] = {"pluginname": plugininfo.get('name'), "author": plugininfo.get('author')}
        #instance plugin
        if hasattr(sys.modules[base], "main_class"):
            inst = sys.modules[base].main_class(plugincfg.find("pluginconfig"))
        else:
            log.error("Plugin", plugin, "doesnt have main_class attr, please put main_class = MainClassName in plugin __init__.py")
            raise AttributeError("Plugin " + plugin + " is missing main_class")
        #set attr
        if not hasattr(self, plugin):
            setattr(self, plugin, inst)
        else:
            log.error("Plugin", plugin, "overides a manager object, please pick a diffrent name")
            raise StandardError("Plugin " + plugin + " overides a manager object")
        self._plugins[plugin] = inst

    #return plugin by name
    def get(self, plugin):
        plugin = plugin.lower()
        """Returns the plugin instance associated with the given name"""
        if plugin in self._plugins:
            return self._plugins[plugin]
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.____class__.__name__, plugin,))

    #get config data out of main xml by key
    def getSubConfig(self, key):
        return self._config.find('subconfigs').find(key)

    #returns all plugin inffos
    def getPluginsInfo(self):
        returnlist = []
        for plugin in self._plugins_info.keys():
            tempstr = '%-20s %-4s' % (self._plugins_info[plugin]['pluginname'], self._plugins_info[plugin]['author'])
            returnlist.append(tempstr)
        return returnlist

    #returns bot version number
    def getVersion(self):
        return bot_version

    #used by restart
    def restartBot(self):
        self.unloadPlugins()
        #if there are no plugins waiting to do callbacks then restart now
        if len(self._delayedplugins) == 0:
            self._handleRestart()

    def _handleRestart(self):
        log.info("Restarting WaterBot")
        sys.exit()

    #used to make read only objects
    def __setattr__(self, attr, value):
        if hasattr(self, "_plugins") and attr in self._plugins:
            if self._plugins[attr] is None:
                raise AttributeError("Read only attribute: %s" % (attr,))
            else:
                object.__setattr__(self, attr, value)
        else:
            object.__setattr__(self, attr, value)
