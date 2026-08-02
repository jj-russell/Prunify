import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import os
from dotenv import load_dotenv
import json
from json.decoder import JSONDecodeError
import sys
import webbrowser

# USER ID: https://open.spotify.com/user/ns9uouw2p8h3uv4ywx844jqs5?si=5a27ab991a7f42b8
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

scope="user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))


playlists = sp.current_user_playlists()

for playlist in playlists["items"]:
    name = playlist["name"]
    playlist_id = playlist["id"]
    if name != "Music":
        continue

    results = sp.playlist_items(playlist_id, 
                              fields="items(track(id,name,artists(name))),next",
                              limit=100)
    
    # limited to 100 tracks per search, so must use a while loop to get more than 100 tracks
    tracks = []
    while True:
        for item in results["items"]:
            if item["track"] is not None:  # Ignore deleted/unavailable tracks
                tracks.append(item["track"])

        if results["next"]:
            results = sp.next(results)
        else:
            break

    print(f"Found {len(tracks)} tracks.")
    i = 0
    for track in tracks:
        if i == 0:
            i += 1
            continue
        track = sp.track(track["id"]) # get track info
        cover_art = track["album"]["images"][0]["url"]
        print(cover_art)
        break

    # for item in items["items"]:
    #     track = item["track"]
    #     print(f"{track['name']} - {track['artists'][0]['name']}")


# print(json.dumps(
#     items,
#     sort_keys=True,
#     indent=4,
#     separators=(',', ': ')
# ))

# saved_tracks = sp.current_user_saved_tracks(limit=50)
# for item in saved_tracks["items"]:
#     track = item["track"]
#     print(f"{track["name"]} - {track["artists"][0]["name"]}")