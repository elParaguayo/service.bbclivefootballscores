import json

import xbmc, xbmcaddon

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")

# Define core generic funcitons

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

def debug(msg):
    '''Script for adding debug messages.

    Takes one argument:
    msg:    debug message to send to XBMC log
    '''
    msg = u"bbclivefootballscores: {0}".format(msg).encode("ascii", "ignore")
    xbmc.log(msg, xbmc.LOGDEBUG)

def closeAddonSettings():
    current_window = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.GetProperties","params":{"properties":["currentwindow"]}}'))

    if current_window["result"]["currentwindow"]["id"] == 10140:
        xbmc.executebuiltin("Action(Back)")
        xbmc.sleep(1000)
        xbmc.executebuiltin("Action(Back)")
