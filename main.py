import tidalapi
from tidalapi import Config, Session, Quality
import cache
import sys
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import os
from dotenv import load_dotenv
load_dotenv() # because vsc was being stupid

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# config
CLEAR_CACHE_ON_START = False
PRINT_NAMES = False

if CLEAR_CACHE_ON_START:
    cache.clear()
qualityconfig = Config(quality=Quality('LOSSLESS')) # fix later to add support for free users.
session = tidalapi.Session(qualityconfig)
def connect_to_spotify():
    scope = 'user-library-read playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private user-read-private'
    token = util.prompt_for_user_token(
        scope=scope,
        client_id= CLIENT_ID,
        client_secret= CLIENT_SECRET,
        redirect_uri="http://localhost:8080"
    )

    if token:
        sp = spotipy.Spotify(auth=token)
        print("Logged in to Spotify")
    else:
        print("Can't get spotify token")
        sys.exit()

    return sp

def getos():
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform == "darwin":
        return "macosx"
    else:
        return "linux"

def clear():
    if getos() == "windows":
        os.system('cls')
    else:
        os.system("clear")

def openbrowser(info):
    link = "https://"+info.split(" ")[1]
    print(link)
    if getos() == "windows":
        webbrowser.get("windows-default").open_new_tab(link)
    elif getos() == "macosx":
        webbrowser.get("macosx").open_new_tab(link)
    else:
        print("You seem to be running Linux, so just open the link above in any browser")
    
    
def logintidal(id, token):
    ses = session.load_oauth_session(session_id = id, access_token = token, token_type = "Bearer", refresh_token=True)
    if ses:
        print("Logged in to TIDAL")
        cache.save(session.session_id, session.access_token)
    else:
        print("Attempting OAuth Login")
        session.login_oauth_simple(openbrowser)
        cache.save(session.session_id, session.access_token)




logintidal(cache.getid(), cache.gettoken())
sp = connect_to_spotify()

def search_spotify(isrc):
    results = sp.search(q="isrc:"+isrc, type='track')
    return results['tracks']['items'][0]

def alternativespotify(tracks, list):
    alternatives = []
    alt_names = []
    for track in tracks:
        try:
            song = search_spotify("name:"+track.name+" artist:"+track.artist.name)
            alternatives.append(song["id"])
            alt_names.append(song["name"])
        except:
            print(f"Could not find {track.name} in Spotify")
    print("Alternatives found: {}".format(alt_names))
    yesno = input("Would you like to use these alternatives? y/n: ")
    if "y" in yesno.lower():
        for i in range(0, round(len(alternatives)/100)+1):
            sp.user_playlist_add_tracks(sp.me()["id"], list["id"], alternatives[:100])
            alternatives = alternatives[100:]
        print("Added alternative tracks to playlist".format(len(alternatives)))
    else:
        print("Sorry we couldn't help")
        sys.exit()

def tidaltospotify(tidalList):
    tl = tidalList.tracks()
    newList = sp.user_playlist_create(sp.me()["id"], input("Enter your new playlists name: "), public=False, description="Test")
    failed = 0
    failedtracks = []
    failedtracksname = []
    succeeded = 0
    tracks = []
    for track in tl:
        try:
            song = search_spotify(track.isrc)
            # print(song["id"])
            tracks.append(song["id"])
            if PRINT_NAMES:
                print(f"Adding {song['name']} to playlist")
            succeeded += 1
        except:
            print(f"Could not find {track.name} in Spotify")
            failedtracksname.append(track.name)
            failedtracks.append(track)
            failed += 1
    for i in range(0, round(len(tracks)/100)+1):
        sp.user_playlist_add_tracks(sp.me()["id"], newList["id"], tracks[:100])
        tracks = tracks[100:]
    print(f"Added {succeeded} tracks to playlist")
    print(f"failed to add {failed} tracks")
    print(f"failed tracks: {failedtracksname}")
    alt = input("Would you like to try an alternate solution? (y/n) ")
    if "y" in alt.lower():
        alternativespotify(failedtracks, newList)
    else:
        sys.exit("Thank you!")
        
        
def spotifytotidal(spotifyList):
    #tidalList = session.create_playlist(name = spotifyList["name"], description = spotifyList["description"])
    failed = 0
    failedtracks = []
    failedtracksname = []
    succeeded = 0
    tracks = []
    print(len(spotifyList["tracks"]["items"]))
    for track in spotifyList["tracks"]["items"]:
        # print(track["track"]["external_ids"]["isrc"]) # why is spotify like this
        try:
            srch = session.search(query = track['track']['name'], models=[tidalapi.media.Track])
            # i = 0
            for item in srch["tracks"]:
                if item.isrc == track['track']['external_ids']['isrc']:
                    tracks.append(item)
                    if PRINT_NAMES:
                        print(f"Adding {item.name} to playlist")
                    succeeded += 1
                    break
                else:
                    print(f"{item.isrc} vs {track['track']['external_ids']['isrc']}")
        except Exception as e:
            print(e)


def tests():
    white = "\033[1;37;40m"    
    green = "\033[1;32;40m"
    red = "\033[1;31;40m"
    try:
        # basic tests (user info)
        session.user.username
        session.user.email
        sp.me()["display_name"]
        sp.me()["id"]
        sp.me()["product"]
        print(f"{green}TEST PASSED{white}")
    except Exception as e:
        print(f"{red}TEST FAILED")
        print(white + e)


def tidaltospotifyask():
    tidalList = session.playlist(input("Enter TIDAL playlist id: "))
    # spotifyList = sp.playlist(input("Enter SPOTIFY playlist id: "))
    #tidalList = session.playlist("a0018435-ea16-4da5-b265-9b59637b65c2")
    #spotifyList = sp.playlist("0u99yxQ2jkbu5ewK3KfhH6")
    print(f"Transferring TIDAL playlist {tidalList.name} songs to Spotify ")
    tidaltospotify(tidalList)

def spotifytotidalask():
    spotifyList = sp.playlist(input("Enter SPOTIFY playlist id: "))
    
    lname = spotifyList["name"]
    while spotifyList["tracks"]['next']:
        spotifyList["tracks"] = sp.next(spotifyList["tracks"])
        spotifyList["tracks"]["items"].extend(spotifyList["tracks"]['items'])
    print(f"Transferring songs from {lname} to TIDAL ")
    print("THIS IS UNDER DEVELOPMENT. COME BACK SOON.")
    spotifytotidal(spotifyList)



clear()
tests()
spotifytotidalask()