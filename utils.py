import config
import winreg
import platform
import vdf
import requests
import os
import subprocess
import crc_algorithms
import re
import colorama
import urllib
import math
from PIL import Image, ImageFilter, ImageEnhance, ImageFont, ImageDraw

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
            print("Could not find shortcuts.vdf for user " + user)
            continue

        allbytes = []
        try:
            byte = f.read(1)
            while byte != b'':
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
        # TODO: Sometimes it's "appname" and not "AppName", need to normalize it
        # to search for both
        iters = []
        for iter in re.finditer("appname", decoded):
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

def create_grid_image(game, file_name):
    """
        Creates a grid image for a game by looking for a big image
        on IGDB, and then manipulating it to look good as a grid image

        Paramaters:
            game - A dictionary containing the Non-Steam game information
            file_name - A string telling the function where to save the image to
    """

    headers = {"user-key": config.IGDB_API_KEY}
    
    # Search IGDB for the game ID by providing the game name
    content = "search \"{}\"; fields artworks,cover,slug;".format(game["name"])
    try:
        r = requests.post("https://api-v3.igdb.com/games/", headers=headers, data=content).json()
    except:
        print("{}[X]{} Could not find {} on IGDB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        return

    if not r:
        print("{}[X]{} Could not find {} on IGDB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        return

    # Save the game's slug to use as text for the grid image
    slug = r[0]["slug"]

    # Set the cover image url from IGDB
    cover = r[0]["cover"]
    content = "fields *; where id={};".format(cover)
    try:
        r = requests.post("https://api-v3.igdb.com/covers", headers=headers, data=content).json()
    except:
        print("{}[X]{} Could not find a cover image for {} on IGDB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        return False

    if not r:
        print("{}[X]{} Could not find a cover image for {} on IGDB.".format(colorama.Back.RED, colorama.Style.RESET_ALL, game["name"]))
        return False

    # Fix the cover image URL and set the link to the "screenshot_huge" template
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
    cover_url = "http://" + r[0]["url"].replace("//", "").replace("t_thumb", "t_screenshot_huge")
    temp_location = "{}.temp.png".format(file_name, game["name"])
    
    # Set urllib with the user agent to download the image to the temporary location
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", user_agent)]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(cover_url, temp_location)

    # Open the temporary image to edit it
    im = Image.open(temp_location)
    width, height = im.size

    # Blur the image
    im = im.filter(ImageFilter.GaussianBlur(radius=6))

    # Darken the image
    im = ImageEnhance.Brightness(im).enhance(0.5)

    # Draw the game's name on the image
    name_text = game["name"]
    if slug != "":
        name_text = slug.replace('-', ' ')
    if len(name_text) > 15:
        # Don't write the game's name if it's long
        name_text=''

    font = ImageFont.truetype("grid-font.ttf", 120)

    # Position the game's name (Align horizontally)
    text_width, text_height = ImageDraw.Draw(im).textsize(name_text, font=font)
    ImageDraw.Draw(im).text(((width - text_width) / 2, 108), name_text, font=font, fill=(0, 0, 0, 100))
    ImageDraw.Draw(im).text(((width - text_width) / 2, 100), name_text, font=font)

    im.save(file_name, "PNG")

    os.remove(temp_location)

    return True