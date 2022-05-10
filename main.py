import tidalapi
from tidalapi import Config, Session, Quality
import cache
import sys
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

qualityconfig = Config(quality=Quality('LOSSLESS'))
session = tidalapi.Session(qualityconfig)
#sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id="1498604f5cb24fc0b23ccc3a47eeb284", client_secret="6cfd4b58a0714e84902770cfe3eb4f70"))
def connect_to_spotify():
    scope = 'user-library-read playlist-read-collaborative playlist-modify-public playlist-read-private playlist-modify-private user-read-private'
    token = util.prompt_for_user_token(
        scope=scope,
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
        redirect_uri="http://localhost:8080"
    )

    if token:
        sp = spotipy.Spotify(auth=token)
        print("Logged in to Spotify")
    else:
        print("Can't get spotify token")
        sys.exit()

    return sp

def openbrowser(info):
    link = "https://"+info.split(" ")[1]
    print(link)
    webbrowser.get("windows-default").open_new_tab(link)
    
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

def alternate(tracks, list):
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

def transferPlaylist(tidalList):
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
        alternate(failedtracks, newList)
    else:
        sys.exit("Thank you!")
        
        


def askForPlaylists():
    tidalList = session.playlist(input("Enter TIDAL playlist id: "))
    # spotifyList = sp.playlist(input("Enter SPOTIFY playlist id: "))
    #tidalList = session.playlist("a0018435-ea16-4da5-b265-9b59637b65c2")
    #spotifyList = sp.playlist("0u99yxQ2jkbu5ewK3KfhH6")
    print(f"Transferring TIDAL playlist {tidalList.name} songs to Spotify ")
    transferPlaylist(tidalList)

askForPlaylists()


