from flask import Flask, render_template, session, redirect, request, url_for, g
from flask_session import Session
from database import get_db, close_db
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import spotipy.util as util
import os
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timezone

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

    spotify_user_id = sp.current_user()['id']
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    user_exists = db.execute("""SELECT id
                            FROM users
                            WHERE spotify_user_id = ?""", (spotify_user_id,)).fetchone()

    if not user_exists:
        db.execute("""INSERT INTO users (spotify_user_id) 
                      VALUES (?);""", (spotify_user_id,))

    db.execute("""UPDATE users
                  SET updated_at = ?
                  WHERE spotify_user_id = ?;""", (current_time, spotify_user_id))
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

def load_playlist(spotify_playlist_id):
    spotify_user_id = g.user.current_user()['id']
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    playlist_name = g.user.playlist(spotify_playlist_id)["name"]

    db = get_db()
    playlist_exists = db.execute("""SELECT id
                                    FROM playlists
                                    WHERE spotify_playlist_id = ?""", (spotify_playlist_id,)).fetchone()

    user_id = db.execute("""SELECT id
                            FROM users
                            WHERE spotify_user_id = ?;""", (spotify_user_id,)).fetchone()
    user_id = user_id["id"]

    if not playlist_exists:
        db.execute("""INSERT INTO playlists (user_id, spotify_playlist_id, name) 
                      VALUES (?, ?, ?);""", (user_id, spotify_playlist_id, playlist_name,))

    db.execute("""UPDATE playlists
                  SET updated_at = ?
                  WHERE user_id = ?;""", (current_time, user_id))
    db.commit()

def load_tracks(spotify_playlist_id):
    db = get_db()

    playlist_id = db.execute("""SELECT id
                                FROM playlists
                                WHERE spotify_playlist_id = ?;""", (spotify_playlist_id,)).fetchone()

    playlist_id = playlist_id["id"]

    playlist_loaded = db.execute("""SELECT loaded_at
                                    FROM playlists
                                    WHERE id = ?;""", (playlist_id,)).fetchone()
    
    # prevents loading tracks for a playlist into DB multiple times
    if playlist_loaded["loaded_at"]:
        return

    tracks = g.user.playlist_items(
        spotify_playlist_id,
        additional_types=["track"]
    )

    all_tracks = tracks["items"]

    while tracks["next"]:
        tracks = g.user.next(tracks)
        all_tracks.extend(tracks["items"])

    rows = []

    unavailable_track_count = 0
    for position, item in enumerate(all_tracks):
        track = item["track"]
        if track is None:
            continue
        
        spotify_track_id = track.get("id")

        if spotify_track_id is None:
            unavailable_track_count += 1
            continue

        track_name = track["name"]
        track_artists = ", ".join(artist["name"] for artist in track["artists"])
        track_image = track["album"]["images"][0]["url"]

        rows.append((
            playlist_id,
            spotify_track_id,
            track_name,
            track_artists,
            track_image,
            position
        ))

    db.executemany("""INSERT INTO playlist_tracks 
                      (playlist_id, spotify_track_id, track_name, track_artists, track_image, position)
                      VALUES (?, ?, ?, ?, ?, ?);""", rows)
    
    # finished loading tracks, update playlist table to indicate it has been loaded
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""UPDATE playlists
                  SET loaded_at = ?;""", (current_time,))
    db.commit()

@app.route("/track_swipe/<spotify_playlist_id>")
def track_swipe(spotify_playlist_id):
    load_playlist(spotify_playlist_id)
    load_tracks(spotify_playlist_id)

    track_image = None
    track_title = None
    track_artist = None

    return render_template("track_swipe.html", 
                           track_image=track_image, 
                           track_title=track_title, 
                           track_artist=track_artist)

@app.route("/test")
def test():
    user_id = g.user.current_user()['id']

    return f"{user_id}"