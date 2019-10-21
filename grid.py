import config
import utils
import requests
import urllib
import os
import colorama

"""
    Generates grid images for Non-Steam games.
"""

colorama.init()

# Get all the Non-Steam games
games = utils.get_non_steam_games()
if not games:
    print("Could not find any Non-Steam games in your Steam library.")
    exit()


headers = {"Authorization": "Bearer {}".format(config.STEAMGRIDDB_API_KEY)}

# Go through every game in the Non-Steam games list
for game in games:
    grid_folder = utils.get_steam_install_path() + "\\userdata\\" + game["user"] + "\\config\\grid\\"

    # Check if an image already exists. If so, skip this game
    if os.path.isfile("{}{}.png".format(grid_folder, game["appid"])):
        print("{}[O]{} {} - Image already exists.".format(colorama.Back.CYAN, colorama.Style.RESET_ALL, game["name"]))
        continue

    name = game["name"]

    # Search the game on SteamGridDB by the game name in the library
    try:
        url = "https://www.steamgriddb.com/api/v2/search/autocomplete/{}".format(name)
        r = requests.get(url, headers=headers).json()
    except:
        print("{}[X]{} {} - Could not get find game on Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("{}[X]{} {} - Could not get find game on Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        continue

    r = r["data"]
    game_id = r[0]["id"]

    # Search grid images on SteamGridDB
    try:
        url = "https://www.steamgriddb.com/api/v2/grids/game/{}&dimensions=460x215&920x430".format(game_id)
        r = requests.get(url, headers=headers).json()
    except:
        print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        continue

    r = r["data"]

    # Get the first grid image url
    url = r[0]["url"]

    # Create the grid folder if it doesn't exist
    if not os.path.isdir(grid_folder):
        os.mkdir(grid_folder)

    # Save the image in the grid folder
    file_name = "{}{}.png".format(grid_folder, game["appid"])
    urllib.request.urlretrieve(url, file_name)
    print("{}[V]{} {} - Grid downloaded successfully from Steam Grid DB.".format(colorama.Back.GREEN, colorama.Style.RESET_ALL, game["name"]))

print("\nGrid images updated. Please restart Steam to see the changes.")