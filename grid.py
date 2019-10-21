import config
import utils
import requests
import os
import colorama
import urllib

"""
    Generates grid images for Non-Steam games
    by retrieveing existing images from SteamGridDB,
    and creating custom images for games that have no
    images on SteamGridDB.
"""
colorama.init()

# Get all the Non-Steam games
games = utils.get_non_steam_games()
if not games:
    print("Could not find any Non-Steam games in your Steam library.")
    exit()

headers = {"Authorization": "Bearer {}".format(config.STEAMGRIDDB_API_KEY)}

# To keep track if the program updated anything
dirty = False

# To keep track of the games that the script could not find images for
# on SteamGridDB. Can try to search other different criteria
not_found_image = []

# To keep track of the games that the script could not find any images
# for on SteamGridDB. Can create an image by ourselves.
not_found_anything = []

# Go through every game in the Non-Steam games list
for game in games:
    grid_folder = utils.get_steam_install_path() + "\\userdata\\" + game["user"] + "\\config\\grid\\"

    # Check if an image already exists. If so, skip this game
    if os.path.isfile("{}{}.png".format(grid_folder, game["appid"])):
        print("{}[O]{} {} - Image already exists.".format(colorama.Back.MAGENTA, colorama.Style.RESET_ALL, game["name"]))
        continue

    name = game["name"]

    # Search the game on SteamGridDB by the game name in the library
    try:
        url = "https://www.steamgriddb.com/api/v2/search/autocomplete/{}".format(name)
        r = requests.get(url, headers=headers).json()
    except:
        print("{}[X]{} {} - Could not get find game on Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        # TODO: Add to not_found at all
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("{}[X]{} {} - Could not get find game on Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        # TODO: Add to not_found at all
        continue

    r = r["data"]
    game_id = r[0]["id"]

    # Search grid images on SteamGridDB
    try:
        url = "https://www.steamgriddb.com/api/v2/grids/game/{}&dimensions=460x215&920x430".format(game_id)
        r = requests.get(url, headers=headers).json()
    except:
        print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        not_found_image.append(game)
        continue

    # Check if the request was not successful or nothing was found
    if r["success"] != True or not r["data"]:
        print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        not_found_image.append(game)
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
    print("{}[V]{} {} - Grid image downloaded successfully from Steam Grid DB.".format(colorama.Back.GREEN, colorama.Style.RESET_ALL, game["name"]))
    dirty = True

# Try to find any other image for the games that the script
# could not find images for on SteamGridDB
if len(not_found_image) > 0:
    print("\nTrying to find different grid images on SteamGridDB...\n")

    for game in not_found_image:
        grid_folder = utils.get_steam_install_path() + "\\userdata\\" + game["user"] + "\\config\\grid\\"

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
            url = "https://www.steamgriddb.com/api/v2/grids/game/{}".format(game_id)
            r = requests.get(url, headers=headers).json()
        except:
            print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
            not_found_anything.append(game)
            continue

        # Check if the request was not successful or nothing was found
        if r["success"] != True or not r["data"]:
            print("{}[X]{} {} - Could not get images from Steam Grid DB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
            not_found_anything.append(game)
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
        print("{}[V]{} {} - Alternative grid image downloaded successfully from Steam Grid DB.".format(colorama.Back.GREEN, colorama.Style.RESET_ALL, game["name"]))
        dirty = True

# Create custom images for all the games that have no images
# on SteamGridDB.
if len(not_found_anything) > 0:
    print("\nTrying to create custom images for the games that have no images on Steam Grid DB...\n")

    for game in not_found_anything:
        grid_folder = utils.get_steam_install_path() + "\\userdata\\" + game["user"] + "\\config\\grid\\"

        # Create the grid folder if it doesn't exist
        if not os.path.isdir(grid_folder):
            os.mkdir(grid_folder)

        # Create and save the image in the grid folder
        file_name = "{}{}.png".format(grid_folder, game["appid"])
        if utils.create_grid_image(game, file_name) == True:
            print("{}[V]{} {} - Custom grid image created successfully.".format(colorama.Back.GREEN, colorama.Style.RESET_ALL, game["name"]))
            dirty = True
        else:
            print("{}[X]{} {} - Could not get create custom grid image.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))

if dirty == True:
    print("\nGrid images updated. Please restart Steam to see the changes.")
else:
    print("\nNothing was updated.\n")