import xbmc
import json


def closeAddonSettings():
    current_window = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"GUI.GetProperties","params":{"properties":["currentwindow"]}}'))

    if current_window["result"]["currentwindow"]["id"] == 10140:
        xbmc.executebuiltin("Action(Back)")
        xbmc.sleep(1000)
        xbmc.executebuiltin("Action(Back)")
