import errno
import os
import requests
from StringIO import StringIO
import urllib2

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import xbmcaddon, xbmc

IMG_PLAYER_CUTOUT = 1
IMG_PLAYER_THUMB = 2
IMG_TEAM_BADGE = 3

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")

ADDON_PROFILE = xbmc.translatePath(_A_.getAddonInfo('profile')).decode('utf-8')

CACHE_PATH = os.path.join(ADDON_PROFILE, "cache")

CACHE_LOCATIONS = {IMG_PLAYER_CUTOUT: os.path.join(CACHE_PATH, "cutouts"),
                   IMG_PLAYER_THUMB: os.path.join(CACHE_PATH, "thumbs"),
                   IMG_TEAM_BADGE: os.path.join(CACHE_PATH, "badges")}

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def getCachedImage(url, img_type, resize=False):

    subfolder = CACHE_LOCATIONS.get(img_type, "unknown")
    folder = os.path.join(CACHE_PATH, subfolder)

    make_sure_path_exists(folder)

    img_name = url.split("/")[-1]
    cached_file = os.path.join(folder, img_name)

    if os.path.exists(cached_file):
        img = Image.open(cached_file)

    else:
        raw = requests.get(url)
        img = Image.open(StringIO(raw.content))
        img.save(cached_file)

    if resize:
        return img.resize(resize)

    else:
        return img
