from flask import Flask, render_template, session, redirect, request, url_for, g
from flask_session import Session
from database import get_db, close_db
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import os
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "super-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.before_request
def load_user():
    scope="user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                            client_secret=CLIENT_SECRET,
                                                            redirect_uri=REDIRECT_URI,
                                                            scope=scope))

    user_id = sp.current_user()['id']
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    user_exists = db.execute("""SELECT spotify_user_id
                            FROM users
                            WHERE spotify_user_id = ?""", (user_id,)).fetchone()

    if not user_exists:
        db.execute("""INSERT INTO users (spotify_user_id, created_at) 
                      VALUES (?, ?);""", (user_id, current_time))

    db.execute("""UPDATE users
                  SET updated_at = ?
                  WHERE spotify_user_id = ?;""", (current_time, user_id))
    db.commit()
    
    g.user = sp

def clear_session():
    for key in list(session.keys()):
        session.pop(key)
    session.modified = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/select_playlist")
def select_playlist():
    playlists_info = g.user.current_user_playlists()
    playlists = [playlist for playlist in playlists_info["items"]]

    return render_template("select_playlist.html", playlists=playlists)

def generate_playlist_array(playlist_id):
    results = g.user.playlist_items(playlist_id, 
                            fields="items(track(id,name,artists(name))),next",
                            limit=100)
    
    # limited to 100 tracks per search, so must use a while loop to get more than 100 tracks
    tracks = []
    while True:
        for item in results["items"]:
            if item["track"] is not None:  # Ignore deleted/unavailable tracks
                tracks.append(item["track"])

        if results["next"]:
            results = g.user.next(results)
        else:
            break

    return tracks
     

@app.route("/track_swipe/<playlist_id>")
def track_swipe(playlist_id):
    tracks = generate_playlist_array(playlist_id)

    track_image = None
    track_title = None
    track_artist = None

    if len(tracks) > 0:
        for track in tracks:
            track = g.user.track(track["id"]) # get track info
            track_title = track["name"]
            track_artist = [artist["name"] for artist in track["artists"]]
            track_image = track["album"]["images"][0]["url"]
            break

    return render_template("track_swipe.html", 
                           track_image=track_image, 
                           track_title=track_title, 
                           track_artist=track_artist)

@app.route("/test")
def test():
    user_id = g.user.current_user()['id']

    return f"{user_id}"