import xml.etree.ElementTree as et


class Config:
    def __init__(self, xml):
        pass

    def getValue(self, xml, tag, subkey='value', default=None):
        found = xml.find(tag)
        if found is None:
            retvar = default
        else:
            retvar = found.get(subkey)
            if retvar is None:
                retvar = default

        return retvar

    def getConfig(self, key):
        subconfig = manager.getSubConfig(key)
        afile = subconfig.get("file")
        if afile is None:
            return subconfig
        else:
            return et.parse(afile)
