import re
import utils
import json

"""
    Prints a list of Non-Steam games added to your Steam library
    Each entry contains the game's name, exe, appid
"""

# Go through every user on Steam
for user in utils.get_steam_users():
    # Open the shortcuts.vdf file that contains a list of Non-Steam games
    f = open(utils.get_steam_install_path() + r"\\userdata\\" + user + "\\config\\shortcuts.vdf", "rb")
    allbytes = []
    try:
        byte = f.read(1)
        while byte != b'':
            # do stuff
            allbytes.append(byte)
            byte = f.read(1)
    finally:
        f.close()

    # Decode the bytes to ASCII
    decoded = ""
    for b in allbytes:
        decoded += b.decode('ascii')

    # To use for separating elements
    b01 = bytearray.fromhex('01').decode()
    b02 = bytearray.fromhex('02').decode()

    # Find iternations of "AppName" for each game
    iters = []
    for iter in re.finditer("AppName", decoded):
        iters.append({'start': iter.start(), 'end': iter.end()})

    # Iterate over the AppNames to make a list of the games
    # (every game has one AppName)
    iters_length = len(iters)
    games = []
    i = 0
    for iter in iters:
        if i + 1 < iters_length:
            # If there is another game on the file, cut from this AppName's end to the
            # next game's AppName's start
            games.append(decoded[iter['start']:iters[i + 1]['start']])
        else:
            # If this is the last game on the file, cut from this AppName's end to
            # the end of the file
            games.append(decoded[iter['start']:])

        i += 1

    # Make a list of games, in the right format, by going
    # through the games and getting each game's details.
    # For example:
    # {
    #   "name": "Minecraft",
    #   "exe": "C:\Games\Minecraft.exe"
    # }
    games_list = []
    for game in games:
        """
        The contents of the game info can contain some of the following:
        AppName  Overwatch ☺Exe "D:\Program Files\Overwatch\Overwatch Launcher.exe" ☺StartDir "D:\Program Files\Overwatch\" ☺icon
        ☺ShortcutPath  ☺LaunchOptions  ☻IsHidden     ☻AllowDesktopConfig ☺   ☻AllowOverlay ☺   ☻OpenVR     ☻Devkit     ☺DevkitGameID
        ☻LastPlayTime      tags
        """
        
        indices = {}
        indices["AppName"] = (0, len("AppName") + 1)
        indices["Exe"] = (game.index(b01 + "Exe"), game.index(b01 + "Exe") + len(b01 + "Exe") + 1)
        indices["StartDir"] = (game.index(b01 + "StartDir"), game.index(b01 + "StartDir") + len(b01 + "StartDir") + 1)

        # Get the contents of the indices (the app name, exe, etc.)
        name = game[indices["AppName"][1]:indices["Exe"][0]].rstrip('\x00')
        exe = game[indices["Exe"][1]:indices["StartDir"][0]].rstrip('\x00')
        games_list.append({
            "name": name,
            "exe": exe,
            "appid": utils.generate_appid_for_nonsteam_game(name, exe)
        })

print(games_list)