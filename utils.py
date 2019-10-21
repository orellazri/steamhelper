import config
import winreg
import platform
import vdf
import requests
import os
import subprocess
import crc_algorithms
import re

def get_request(url):

    """
        Sends a GET request and returns the result as JSON
        
        Parameters:
            url - URL to send the GET request to
    """

    r = requests.get(url)
    return r.json()

def get_id_by_username(username):

    """
        Gets a Steam ID by the username
        Returns ID or None if could not retrieve.

        Parameters:
            username - Steam username
    """

    result = get_request("http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=" + config.STEAM_API_KEY + "&vanityurl=" + username)
    id = None

    try:
        if result["response"]["success"] == 1:
            id = result["response"]["steamid"]
        else:
            raise Exception
    except:
        print("An error occured while trying to get your Steam ID.")
        return None

    return id

def get_libraries(install_dir, including_install=True):

    """
        Gets the steam libary locations installed on the system
        and returns them as a list

        Parameters:
            install_dir - Steam installation directory
            including_install - Whether to include the installation directory as a library or not.
                                Defaults to True.
    """

    # Parse the vdf file into JSON
    try:
        f = vdf.parse(open(install_dir + "\\steamapps\\libraryfolders.vdf"))
    except:
        print("Could not find libraryfoldes.vdf")
        return
    
    libraries = []

    # Include the installation directory as a library, if wanted
    if including_install:
        libraries.append(install_dir)

    # Loop through the LibraryFolders entry
    for i in range(0, len(f["LibraryFolders"])):
        # Skip the first and second entries
        if i == 0 or i == 1:
            continue

        libraries.append(f["LibraryFolders"][str(i - 1)])

    return libraries

def get_steam_install_path():

    """
        Gets the steam installation path on the system
        by looking in the registry.

        Returns:
            The path, or None if it could not find the installatino
    """

    try:
        # Set the key path according to the architecture - 32/64 bits

        key_path = "SOFTWARE\\WOW6432Node\\Valve\\Steam"
        if not is_64():
            key_path = "SOFTWARE\\Valve\\Steam"

        # Open the registry key and query the value of InstallPath
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        k = winreg.OpenKey(reg, key_path)
        value = winreg.QueryValueEx(k, "InstallPath")
        winreg.CloseKey(k)

        return value[0]
    except Exception as e:
        print("Could not find Steam installation directory.")
        print(e)
        return None

def get_steam_users():
    """
        Gets the users ID's on Steam by checking in the
        Steam installation directory under the "userdata" folder

        Returns:
            A list of the user ID's on Steam
    """

    return os.listdir(get_steam_install_path() + "\\userdata")

def is_64():

    """
        Checks if the computer running the program is 64bits.
        If so, returns True. Otherwise, returns False.
    """

    return platform.machine().endswith("64")

def get_installed_games():

    """
        Finds Steam games installed on the system,
        by searching each Steam library.

        Returns:
            A list of dictionary entries of games installed on the system.
            For example:
            {
                id: 228980
                name: Steamworks Common Redistributables
            }
    """

    games = []

    for library in get_libraries(get_steam_install_path()):
        # Add \steamapps to the library folder
        library += "\\steamapps\\"

        # Search for manifest files (.acf)
        files = os.listdir(library)
        for file in files:
            if file.endswith("acf"):
                # Get the game details from the manifest file
                f = vdf.parse(open(library + file))
                appid = f["AppState"]["appid"]
                name = f["AppState"]["name"]

                games.append({"name": name, "appid": appid})

    return games

def launch_steam_game(id):
    
    """
        Launches a Steam game by its ID

        Paramteres:
            id - Steam game ID
    """

    path = get_steam_install_path() + "\\Steam.exe"
    subprocess.call(path + " -applaunch " + id)

def generate_appid_for_nonsteam_game(name, target):
    """
        (Thanks to github.com/scottrice)

        Generates the app ID for a Non-Steam game.
        This ID is a 64bit integer, where the first 32bits are
        a CRC32 based off of the name and target (with the added
        condition that the first bit is always high), and
        the last 32bits are 0x02000000.

        Paramteters:
            name - Game name
            target - Exe file location

        Returns:
            The app ID as a string
    """

    algorithm = crc_algorithms.Crc(width = 32, poly = 0x04C11DB7, reflect_in = True, xor_in = 0xffffffff, reflect_out = True, xor_out = 0xffffffff)
    input_string = ''.join([target,name])
    top_32 = algorithm.bit_by_bit(input_string) | 0x80000000
    full_64 = (top_32 << 32) | 0x02000000
    return str(full_64)

def get_non_steam_games():
    games_list = []

    # Go through every user on Steam
    for user in get_steam_users():
        # Open the shortcuts.vdf file that contains a list of Non-Steam games
        try:
            f = open(get_steam_install_path() + r"\\userdata\\" + user + "\\config\\shortcuts.vdf", "rb")
        except:
            print("Could not find shortcuts.vdf")
            break

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
                "appid": generate_appid_for_nonsteam_game(name, exe),
                "user": user
            })

    return games_list