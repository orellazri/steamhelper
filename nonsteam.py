import utils

"""
    Prints a list of Non-Steam games added to your Steam library
    Each entry contains the game's name, exe, appid
"""

games = utils.get_non_steam_games()
if not games:
    print("Could not find any Non-Steam games installed on your system.")
    exit()

print(games)