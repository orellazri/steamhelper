import utils

"""
    Prints a list of installed Steam games
    Each entry contains the game's appid, name
"""

games = utils.get_installed_games()
if not games:
    print("Could not find any Steam games installed on your system.")
    exit()

print(games)