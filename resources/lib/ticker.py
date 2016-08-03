'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

''' This script is part of the BBC Football Scores service by elParaguayo

'''
import os
import xbmc
import xbmcgui

class TickerOverlay(object):

    def __init__(self,windowid):

        self.showing = False
        self.window = xbmcgui.Window(windowid)
        self.windowid = windowid
        screen_w, screen_h = self._get_skin_resolution()
        self._ticker_label = xbmcgui.ControlFadeLabel(5,
                                                      screen_h - 50,
                                                      screen_w - 10,
                                                      screen_h,
                                                      font="font13")

    def show(self):

        self.showing=True
        self.window.addControl(self._ticker_label)
        self.id = self._ticker_label.getId()


    def hide(self):

        try:
            self.showing=False
            self.window.removeControl(self._ticker_label)
        except:
            pass

    def update(self,tickertext):

        if self.showing == True:
            self._ticker_label.addLabel(tickertext)

        else:
            pass

    def window_and_control(self):

        return (self.windowid, self.id)

    #Taken from xbmctorrent
    def _get_skin_resolution(self):

        import xml.etree.ElementTree as ET
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try: res = tree.findall("./res")[0]
        except: res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])
