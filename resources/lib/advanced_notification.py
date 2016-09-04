import os
import requests
import urllib2

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import xbmcaddon, xbmc

from .pillow_textbox import pillow_textbox

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
pluginPath = _A_.getAddonInfo("path")

IMAGE_FOLDER = ""

FONT_PATH = os.path.join(pluginPath, "resources", "fonts", "noto-sans")
FONT_REGULAR = os.path.join(FONT_PATH, "NotoSans-Regular.ttf")
FONT_BOLD = os.path.join(FONT_PATH,"NotoSans-Bold.ttf")
FONT_ITALIC = os.path.join(FONT_PATH,"NotoSans-Italic.ttf")
FONT_BOLDITALIC = os.path.join(FONT_PATH,"NotoSans-BoldItalic.ttf")

# Event types for advanced notifications
EVENT_GOAL = 0
EVENT_YELLOW = 1
EVENT_RED = 2
EVENT_STATUS = 3

# Image sizes
# Note: if the SIZE_NOTIFICATION is changed then the skin xml files will also
# need to be updated
SIZE_NOTIFICATION = (350, 100)
SIZE_HEADING = (350, 20)
SIZE_IMAGE = (75, 75)
SIZE_DETAIL = (225, 75)
SIZE_MARGIN = 5


def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string


def matchPlayer(results, term, teams, default=None):

    players = results["player"]

    xbmc.log(u"{}".format(results))

    if not players:
        return default

    # If there's only one result, it's *probably* the right one but there's
    # nothing that the filters below can add!
    if len(players) == 1:
        return players[0]

    # Filter out unwanted results

    # TEST 1
    # We just want football players!
    players = [x for x in players if x["strSport"].lower() == "soccer"]

    if len(players) == 1:
        return players[0]

    # TEST 2
    # Check that the player plays for one of the two teams

    # The first three letters of the team name should be enough
    short_teams = [x[:3].lower() for x in teams]

    players = [x for x in players if x.get("strTeam","@@@").lower()[:3] in short_teams]

    if len(players) == 1:
        return players[0]

    # TEST 3
    # Match first initial
    players = [x for x in players if x["strPlayer"][0].lower() == term[0].lower()]

    if len(players) == 1:
        return players[0]

    # Looks like we can't find the player with any certainty
    return default

def getPlayerThumb(player, match, size=(160,160)):
    try:
        psearch = player.split(".")[1]
    except IndexError:
        psearch = player

    url = ("http://thesportsdb.com/api/v1/json/1/searchplayers.php"
           "?p={}").format(urllib2.quote(psearch.encode("utf-8")))

    # try:
    r = requests.get(url).json()
    teams = [match.HomeTeam, match.AwayTeam]
    player = matchPlayer(r, player, teams)["strThumb"]
    # except:
    #     player = None

    if player is None:
        return None
    else:
        p = requests.get(player)
        thumb = Image.open(StringIO(p.content))
        #scale = size[0] / float(thumb.size[0])
        thumb = thumb.resize(size)

        return thumb

def createPlayerThumb(alert_type, match):

    player = None


    if alert_type == EVENT_GOAL:
        xbmc.log("GOAL")
        try:
            player = match.LastGoalScorer[1]
            xbmc.log(u"{}".format(player))
        except (TypeError, IndexError):
            pass

    elif alert_type == EVENT_YELLOW:
        try:
            player = match.LastYellowCard[1]
        except (TypeError, IndexError):
            pass

    elif alert_type == EVENT_RED:
        try:
            player = match.LastRedCard[1]
        except (TypeError, IndexError):
            pass

    if player:
        if player.endswith("(pen)"):
            player = player[:-6]
            
        img_player = getPlayerThumb(player, match, size=SIZE_IMAGE)
        return img_player

    else:
        return None

def createHeading(title):

    img_title = pillow_textbox(title, SIZE_HEADING, justification=1,
                               font_path=FONT_BOLD, autofit=True)

    return img_title


def createAdvancedNotification(alert_type, title, match):

    notification_image = Image.new("RGBA", SIZE_NOTIFICATION, color=(0,0,0,0))

    img_title = createHeading(title)
    notification_image.paste(img_title, (0,0))

    img_player = createPlayerThumb(alert_type, match)
    if img_player:
        notification_image.paste(img_player, (5,25))

    score_detail = (u"{hometeam}: {homescore}\n"
                    u"{awayteam}: {awayscore}").format(**match.matchdict)
    img_score = pillow_textbox(score_detail, SIZE_DETAIL, justification=2,
                               vjustification=1, font_path=FONT_REGULAR,
                               max_font=30, word_wrap=True, autofit=True)
    img_score.save(os.path.join(pluginPath, "detail.jpg"))
    notification_image.paste(img_score, (90, 25))

    filename = match.HomeTeam.encode("ascii", "ignore")
    filename = os.path.join(pluginPath, "{}.jpg".format(filename))
    notification_image.save(filename)
    notification_image.save(os.path.join(pluginPath, "debug.jpg"))
    return filename
