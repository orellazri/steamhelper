import config
import utils
import requests
import urllib

"""
    Generates grid images for Non-Steam games.
"""

# Get all the Non-Steam games
games = utils.get_non_steam_games()
if not games:
    print("Could not find any Non-Steam games in your Steam library.")
    exit()


headers = {"Authorization": "Bearer {}".format(config.STEAMGRIDDB_API_KEY)}

# Go through every game in the Non-Steam games list
for game in games:
    name = game["name"]

    # Search the game on SteamGridDB by the game name in the library
    try:
        url = "https://www.steamgriddb.com/api/v2/search/autocomplete/{}".format(name)
        r = requests.get(url, headers=headers).json()
    except:
        print("Could not get find game on Steam Grid DB.")
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("Could not get find game on Steam Grid DB.")
        continue

    r = r["data"]
    game_id = r[0]["id"]

    # Search grid images on SteamGridDB
    try:
        url = "https://www.steamgriddb.com/api/v2/grids/game/{}&dimensions=460x215&920x430".format(game_id)
        r = requests.get(url, headers=headers).json()
    except:
        print("Could not get images from Steam Grid DB.")
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("Could not get images from Steam Grid DB.")
        continue

    r = r["data"]

    # Get the first grid image url and save it
    url = r[0]["url"]
    file_name = utils.get_steam_install_path() + "\\userdata\\" + game["user"] + "\\config\\grid\\" + game["appid"] + ".png"
    urllib.request.urlretrieve(url, file_name)
    print("{} - Grid downloaded successfully from Steam Grid DB.".format(game["name"]))