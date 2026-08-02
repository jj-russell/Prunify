from flask import Flask, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/select_playlist")
def select_playlist():
    scope="user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                        client_secret=CLIENT_SECRET,
                                                        redirect_uri=REDIRECT_URI,
                                                        scope=scope))
    playlists_info = sp.current_user_playlists()
    playlists = []

    for playlist in playlists_info["items"]:
        playlists.append(playlist)
        name = playlist["name"]
        playlist_id = playlist["id"]
        # print(name)

    print(playlists)

    return render_template("select_playlist.html", playlists=playlists)

def generate_playlist_array():
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

        return tracks
     

@app.route("/track_swipe")
def track_swipe():
    scope="user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                        client_secret=CLIENT_SECRET,
                                                        redirect_uri=REDIRECT_URI,
                                                        scope=scope))
    tracks = generate_playlist_array()
    
    print(f"Found {len(tracks)} tracks.")
    for track in tracks:
        track = sp.track(track["id"]) # get track info
        image_url = track["album"]["images"][0]["url"]
        print(image_url)
        break

    return render_template("track_swipe.html", image_url=image_url)

if __name__ == "__main__":
    app.run(debug=True)