from flask import Flask, render_template, session, redirect, request, url_for, g, jsonify
from flask_session import Session
from flask_cors import CORS
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
CORS(app)

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

    spotify_user_id = sp.current_user()["id"]
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

def get_playlist_db_id(spotify_playlist_id):
    db = get_db()
    
    playlist_id = db.execute("""SELECT id
                                FROM playlists
                                WHERE spotify_playlist_id = ?;""", (spotify_playlist_id,)).fetchone()
    if playlist_id is None:
        return None
    return playlist_id["id"]

def get_next_unswiped_track(spotify_playlist_id):
    db = get_db()
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None

    track = db.execute("""SELECT id, spotify_track_id, track_name, track_artists, track_image, position
                          FROM playlist_tracks
                          WHERE playlist_id = ?
                          AND status IS NULL
                          ORDER BY position
                          LIMIT 1;""", (playlist_id,)).fetchone()
    if track is None:
        return None

    return {
        "id": track["id"],
        "spotify_track_id": track["spotify_track_id"],
        "track_name": track["track_name"],
        "track_artists": track["track_artists"],
        "track_image": track["track_image"],
        "position": track["position"],
    }


def playlist_stats(spotify_playlist_id):
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return 0, 0, 0

    db = get_db()

    deleted = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                            WHERE playlist_id = ?
                            AND status = "left";""", (playlist_id,)).fetchone()
    deleted = deleted[0]

    kept = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                         WHERE playlist_id = ? 
                         AND status = "right";""", (playlist_id,)).fetchone()
    kept = kept[0]

    unswiped = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                             WHERE playlist_id = ?
                             AND status IS NULL;""", (playlist_id,)).fetchone()
    unswiped = unswiped[0]

    return kept, deleted, unswiped

def load_playlist(spotify_playlist_id):
    db = get_db()
    playlist_exists = db.execute("""SELECT id
                                    FROM playlists
                                    WHERE spotify_playlist_id = ?""", (spotify_playlist_id,)).fetchone()

    spotify_user_id = g.user.current_user()["id"]
    user_id = db.execute("""SELECT id
                            FROM users
                            WHERE spotify_user_id = ?;""", (spotify_user_id,)).fetchone()
    user_id = user_id["id"]

    playlist_name = g.user.playlist(spotify_playlist_id)["name"]
    if not playlist_exists:
        db.execute("""INSERT INTO playlists (user_id, spotify_playlist_id, name) 
                      VALUES (?, ?, ?);""", (user_id, spotify_playlist_id, playlist_name,))

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""UPDATE playlists
                  SET updated_at = ?
                  WHERE user_id = ?;""", (current_time, user_id))
    db.commit()

def load_tracks(spotify_playlist_id):
    db = get_db()

    playlist = db.execute("""SELECT id, loaded_at
                                FROM playlists
                                WHERE spotify_playlist_id = ?;""", (spotify_playlist_id,)).fetchone()
    if playlist is None:
        return

    playlist_id = playlist["id"]
    if playlist["loaded_at"]:
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
    
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""UPDATE playlists
                  SET loaded_at = ?
                  WHERE id = ?;""", (current_time, playlist_id))
    db.commit()

def get_deleted_tracks(spotify_playlist_id):
    db = get_db()
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None

    tracks = db.execute("""SELECT spotify_track_id, track_name, track_artists, track_image
                          FROM playlist_tracks
                          WHERE playlist_id = ?
                          AND status = 'left'
                          ORDER BY position;""", (playlist_id,)).fetchall()

    if tracks is None:
        return None
    return tracks

@app.route("/track_swipe/<spotify_playlist_id>")
def track_swipe(spotify_playlist_id):
    load_playlist(spotify_playlist_id)
    load_tracks(spotify_playlist_id)

    track = get_next_unswiped_track(spotify_playlist_id)
    if track is None:
        return redirect(url_for("playlist_completed",
                                spotify_playlist_id=spotify_playlist_id))
    else:
        spotify_track_id = track["spotify_track_id"]
        track_name = track["track_name"]
        track_artists = track["track_artists"]
        track_image = track["track_image"]

    kept, deleted, unswiped = playlist_stats(spotify_playlist_id)

    return render_template("track_swipe.html",
                           spotify_playlist_id=spotify_playlist_id,
                           spotify_track_id=spotify_track_id,
                           track_image=track_image, 
                           track_name=track_name, 
                           track_artists=track_artists,
                           kept=kept,
                           deleted=deleted,
                           unswiped=unswiped)

def handle_swipes(spotify_playlist_id, spotify_track_id, decision):
    db = get_db()

    playlist_id = db.execute("""SELECT id
                                FROM playlists
                                WHERE spotify_playlist_id = ?;""", (spotify_playlist_id,)).fetchone()
    if playlist_id is None:
        return None
    playlist_id = playlist_id["id"]

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""UPDATE playlist_tracks
                  SET status = ?,
                  swiped_at = ?
                  WHERE playlist_id = ?
                  AND spotify_track_id = ?;""", (decision, current_time, playlist_id, spotify_track_id))
    db.commit()

    next_track = get_next_unswiped_track(spotify_playlist_id)
    stats = playlist_stats(spotify_playlist_id)
    return {
        "next_track": next_track,
        "stats": {
            "kept": stats[0],
            "deleted": stats[1],
            "unswiped": stats[2],
        },
    }


@app.route("/track_decision", methods=["POST"])
def track_decision():
    data = request.get_json()

    spotify_playlist_id = data["playlist_id"]
    spotify_track_id = data["track_id"]
    decision = data["decision"]

    result = handle_swipes(spotify_playlist_id, spotify_track_id, decision)

    return jsonify({"success": True, "track": result["next_track"] if result else None, "stats": result["stats"] if result else {"kept": 0, "deleted": 0, "unswiped": 0}})

@app.route("/playlist_completed/<spotify_playlist_id>")
def playlist_completed(spotify_playlist_id):
    playlist = g.user.playlist(spotify_playlist_id)
    playlist_name = playlist["name"]

    kept, deleted, _ = playlist_stats(spotify_playlist_id)


    tracks = get_deleted_tracks(spotify_playlist_id)

    return render_template("playlist_completed.html",
                           tracks=tracks,
                           playlist_name=playlist_name,
                           kept=kept,
                           deleted=deleted)

@app.route("/attribution")
def attribution():
    return render_template("attribution.html")

@app.route("/test")
def test():
    return "test"