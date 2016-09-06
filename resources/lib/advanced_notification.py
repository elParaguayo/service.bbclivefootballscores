import glob
import os
import requests
from StringIO import StringIO
import time
import urllib2

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import xbmcaddon, xbmc

from .image_cache import getCachedImage
from .pillow_textbox import pillow_textbox
from .utils import debug, localise

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
pluginPath = _A_.getAddonInfo("path")

ADDON_PROFILE = xbmc.translatePath(_A_.getAddonInfo('profile')).decode('utf-8')

# TheSportsDB API Key - Please do not use this for your own projects!
API_KEY = "1420851239712"

IMAGE_FOLDER = ADDON_PROFILE

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
SIZE_MATCHTIME = (225, 20)
SIZE_DETAIL = (225, 60)
SIZE_MARGIN = 5
SIZE_OVERLAY = (20, 26)
SIZE_TEAM_BADGE = (40, 40)
OFFSET_OVERLAY = (SIZE_IMAGE[0] - SIZE_OVERLAY[0],
                  SIZE_IMAGE[1] - SIZE_OVERLAY[1])

MEDIA_FOLDER = os.path.join(pluginPath, "resources", "media")
UNKNOWN_PLAYER_FILE = os.path.join(MEDIA_FOLDER, "unknown.gif")

UNKNOWN_PLAYER = Image.open(UNKNOWN_PLAYER_FILE).convert("RGBA").resize(SIZE_IMAGE)

UNKNOWN_TEAM = Image.new("RGBA", SIZE_TEAM_BADGE)

OVERLAY_RED_FILE = os.path.join(MEDIA_FOLDER, "red-card.png")
OVERLAY_YELLOW_FILE = os.path.join(MEDIA_FOLDER, "yellow-card.png")

IMG_OVERLAY_RED = Image.open(OVERLAY_RED_FILE).resize(SIZE_OVERLAY)
IMG_OVERLAY_YELLOW = Image.open(OVERLAY_YELLOW_FILE).resize(SIZE_OVERLAY)

IMG_PLAYER_CUTOUT = 1
IMG_PLAYER_THUMB = 2
IMG_TEAM_BADGE = 3

# Tidy up any images that weren't removed on last run
for img in glob.glob(os.path.join(IMAGE_FOLDER, "*.jpg")):
    os.remove(img)


def addOverlay(img_player, alert_type):

    if alert_type == EVENT_YELLOW:
        overlay = IMG_OVERLAY_YELLOW

    elif alert_type == EVENT_RED:
        overlay = IMG_OVERLAY_RED

    else:
        return img_player

    img_player.paste(overlay, OFFSET_OVERLAY, mask=overlay)

    return img_player

def getTeamBadge(team, size=(160, 160)):

    badge = False
    url = ("http://thesportsdb.com/api/v1/json/{0}/searchteams.php"
           "?t={1}").format(API_KEY, urllib2.quote(team.encode("utf-8")))
    try:
        r = requests.get(url).json()
        badge = r["teams"][0].get("strTeamBadge", False)
        debug(badge)

    except:
        return False

    if badge:
        img_badge = getCachedImage(badge, IMG_TEAM_BADGE, resize=size)
        return img_badge
    else:
        return False

def getMatchBadges(match, size=(160, 160)):

    hometeam = getTeamBadge(match.HomeTeam, size=size)
    awayteam = getTeamBadge(match.AwayTeam, size=size)

    if hometeam and awayteam:
        return (hometeam, awayteam)

    else:
        return False

def matchPlayer(results, term, teams, default=None):

    players = results["player"]



    if not players:
        return None

    # If there's only one result, it's *probably* the right one but there's
    # nothing that the filters below can add!
    if len(players) == 1:
        return players[0]

    else:
        print "START"
        print [x["strPlayer"] for x in players]

    # Filter out unwanted results

    print ["costa" in x["strPlayer"].lower().split(" ") for x in players]
    players = [x for x in players if term.split(".")[1].lower() in x["strPlayer"].lower().split(" ")]
    print players

    # TEST 1
    # We just want football players!
    players = [x for x in players if x["strSport"].lower() == "soccer"]

    if len(players) == 1:
        return players[0]

    else:
        print "TEST1"
        print [x["strPlayer"] for x in players]

    # TEST 3
    # Match first initial
    players = [x for x in players if x["strPlayer"][0].lower() == term[0].lower()]

    if len(players) == 1:
        return players[0]

    else:
        print "TEST3"
        print [x["strPlayer"] for x in players]

    list_copy = players[:]
    # TEST 2
    # Check that the player plays for one of the two teams

    # The first three letters of the team name should be enough
    short_teams = [x[:3].lower() for x in teams]

    players = [x for x in players if x.get("strTeam","@@@").lower()[:3] in short_teams]

    if len(players) == 1:
        return players[0]

    else:
        print "TEST2"
        print [x["strPlayer"] for x in players]

    # TEST 4
    # Check that the player plays for one of the two teams

    # The first three letters of the team name should be enough
    short_teams = [x[:3].lower() for x in teams]

    players = [x for x in list_copy if x.get("strNationality","@@@").lower()[:3] in short_teams]

    if len(players) == 1:
        return players[0]

    else:
        print "TEST4"
        print [x["strPlayer"] for x in players]

    # Looks like we can't find the player with any certainty
    return None


    # players = results["player"]
    #
    # xbmc.log(u"{}".format(results))
    #
    # if not players:
    #     return default
    #
    # # If there's only one result, it's *probably* the right one but there's
    # # nothing that the filters below can add!
    # if len(players) == 1:
    #     return players[0]
    #
    # # Filter out unwanted results
    #
    # # TEST 1
    # # We just want football players!
    # players = [x for x in players if x["strSport"].lower() == "soccer"]
    #
    # if len(players) == 1:
    #     return players[0]
    #
    # # TEST 2
    # # Check that the player plays for one of the two teams
    #
    # # The first three letters of the team name should be enough
    # short_teams = [x[:3].lower() for x in teams]
    #
    # players = [x for x in players if x.get("strTeam","@@@").lower()[:3] in short_teams]
    #
    # if len(players) == 1:
    #     return players[0]
    #
    # # TEST 3
    # # Match first initial
    # players = [x for x in players if x["strPlayer"][0].lower() == term[0].lower()]
    #
    # if len(players) == 1:
    #     return players[0]
    #
    # # Looks like we can't find the player with any certainty
    # return default

def getPlayerThumb(player, match, size=(160,160)):
    try:
        psearch = player.split(".")[1]
    except IndexError:
        psearch = player

    url = ("http://thesportsdb.com/api/v1/json/{0}/searchplayers.php"
           "?p={1}").format(API_KEY, urllib2.quote(psearch.encode("utf-8")))

    try:
        r = requests.get(url).json()
        teams = [match.HomeTeam, match.AwayTeam]
        player = matchPlayer(r, player, teams)
    except:
        player = None

    if player is None:
        return UNKNOWN_PLAYER
    else:
        if player["strCutout"]:
            img_url = player["strCutout"]
            img_type = IMG_PLAYER_CUTOUT
        elif player["strThumb"]:
            img_url = player["strThumb"]
            img_type = IMG_PLAYER_THUMB
        else:
            return UNKNOWN_PLAYER

        thumb = getCachedImage(img_url, img_type, resize=size)

        return thumb

def createPlayerThumb(alert_type, match):

    player = None
    overlay = False

    if alert_type == EVENT_GOAL:

        try:
            player = match.LastGoalScorer[1]
            #xbmc.log(u"{}".format(player))
        except (TypeError, IndexError):
            img_player = UNKNOWN_PLAYER

    elif alert_type == EVENT_YELLOW:

        overlay = True

        try:
            player = match.LastYellowCard[1]
        except (TypeError, IndexError):
            img_player = UNKNOWN_PLAYER

    elif alert_type == EVENT_RED:

        overlay = True

        try:
            player = match.LastRedCard[1]
        except (TypeError, IndexError):
            img_player = UNKNOWN_PLAYER

    if player:
        if player.endswith("(pen)"):
            player = player[:-6]

        img_player = getPlayerThumb(player, match, size=SIZE_IMAGE)

    else:
        img_player = UNKNOWN_PLAYER

    if overlay:
        img_player = addOverlay(img_player, alert_type)

    return img_player

def createHeading(title, size=SIZE_HEADING):

    img_title = pillow_textbox(title, size, justification=1,
                               font_path=FONT_BOLD, autofit=True)

    return img_title


def event_layout(title, match, base):
    badges = getMatchBadges(match, size=SIZE_TEAM_BADGE)
    debug(str(badges))

    img_title = createHeading(title, (180,20))
    base.paste(img_title, (85,0))

    if badges:
        homebadge, awaybadge = badges
        base.paste(homebadge, (40,5), mask=homebadge)
        base.paste(awaybadge, (270,5), mask=awaybadge)

    img_home = pillow_textbox(match.HomeTeam, (130, 40), justification=2,
                              vjustification=1, autofit=True, word_wrap=False,
                              font_path=FONT_REGULAR, margin=5)

    img_away = pillow_textbox(match.AwayTeam, (130, 40), justification=0,
                              vjustification=1, autofit=True, word_wrap=False,
                              font_path=FONT_REGULAR, margin=5)

    score = "{homescore} - {awayscore}".format(**match.matchdict)
    img_score = pillow_textbox(score, (90, 40), justification=1,
                               vjustification=1, autofit=True, word_wrap=False,
                               font_path=FONT_BOLD)

    base.paste(img_home, (0,45))
    base.paste(img_away, (220,45))
    base.paste(img_score, (130, 45))
    return base

def player_layout(alert_type, title, match, base):

    img_title = createHeading(title)
    base.paste(img_title, (0,0))

    img_player = createPlayerThumb(alert_type, match)

    if img_player:
        base.paste(img_player, (5,25))

    match_time = "{0}: {1}".format(localise(32206), match.MatchTime)

    match_label = pillow_textbox(match_time, SIZE_MATCHTIME, justification=2,
                                 vjustification=1, font_path=FONT_REGULAR,
                                 max_font=25, word_wrap=False, autofit=True)

    score_detail = (u"{hometeam}: {homescore}\n"
                    u"{awayteam}: {awayscore}").format(**match.matchdict)

    img_score = pillow_textbox(score_detail, SIZE_DETAIL, justification=2,
                               vjustification=1, font_path=FONT_BOLD,
                               max_font=20, word_wrap=False, autofit=True)

    base.paste(img_score, (90, 25))
    base.paste(match_label, (90, 80))

    return base


def createAdvancedNotification(alert_type, title, match, simple=False):

    base = Image.new("RGBA", SIZE_NOTIFICATION, color=(0,0,0,0))
    img = None

    if alert_type == EVENT_STATUS or simple:
        img = event_layout(title, match, base)

    else:
        img = player_layout(alert_type, title, match, base)

    filename = "{0}_{1}.jpg".format(time.time(),
                                    match.HomeTeam.encode("ASCII", "ignore"))

    filename = os.path.join(IMAGE_FOLDER, filename)

    img.save(filename)
    return filename
