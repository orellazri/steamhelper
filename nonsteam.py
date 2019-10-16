import binascii
import re

f = open(r'C:\Program Files (x86)\Steam\userdata\49817912\config\shortcuts.vdf', "rb")
allbytes = []
try:
    byte = f.read(1)
    while byte != b'':
        # do stuff
        allbytes.append(byte)
        byte = f.read(1)
finally:
    f.close()

decoded = ""
for b in allbytes:
    decoded += b.decode('ascii')

b01 = bytearray.fromhex('01').decode()

#print(decoded)
#print(decoded[decoded.index(b01) + 1:])
#print(decoded[decoded.index("AppName") + 1:])

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
        games.append(decoded[iter['end']:iters[i + 1]['start']])
    else:
        # If this is the last game on the file, cut from this AppName's end to
        # the end of the file
        games.append(decoded[iter['end']:])

    i += 1

for game in games:
    print(game)
    print("======================================================")