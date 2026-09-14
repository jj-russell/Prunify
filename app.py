from flask import Flask, render_template, session, redirect, request, url_for, g, jsonify
from flask_session import Session
from flask_cors import CORS
from database import get_db, close_db
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timezone

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
SPOTIFY_SCOPE = "user-library-read playlist-modify-public playlist-modify-private"

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = FLASK_SECRET_KEY
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)

def create_oauth():
    return SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SPOTIFY_SCOPE)


@app.route("/login")
def login():
    oauth = create_oauth()
    auth_url = oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    oauth = create_oauth()
    code = request.args.get("code")
    if code is None:
        return redirect(url_for("index"))

    token_info = oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("index"))


def get_spotify_client():
    token_info = session.get("token_info")
    if not token_info:
        return None

    oauth = create_oauth()
    # refresh if expired
    try:
        if oauth.is_token_expired(token_info):
            token_info = oauth.refresh_access_token(token_info.get("refresh_token"))
            session["token_info"] = token_info
    except Exception:
        # any failure means user must re-auth
        session.pop("token_info", None)
        return None

    return spotipy.Spotify(auth=token_info.get("access_token"))


@app.before_request
def load_user():
    # allow unauthenticated access to these endpoints
    public_paths = ("/", "/login", "/callback", "/test", "/attribution")
    if request.path.startswith("/static") or request.path in public_paths:
        return

    sp = get_spotify_client()
    if sp is None:
        return redirect(url_for("login"))

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

    num_deleted = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                            WHERE playlist_id = ?
                            AND status = "delete";""", (playlist_id,)).fetchone()
    num_deleted = num_deleted[0]

    num_kept = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                         WHERE playlist_id = ? 
                         AND status = "keep";""", (playlist_id,)).fetchone()
    num_kept = num_kept[0]

    num_unswiped = db.execute("""SELECT COUNT(*) FROM playlist_tracks
                             WHERE playlist_id = ?
                             AND status IS NULL;""", (playlist_id,)).fetchone()
    num_unswiped = num_unswiped[0]

    return num_kept, num_deleted, num_unswiped

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
    playlist_image = g.user.playlist(spotify_playlist_id)["images"][0]["url"]
    if not playlist_exists:
        db.execute("""INSERT INTO playlists (user_id, spotify_playlist_id, name, image_url) 
                      VALUES (?, ?, ?, ?);""", (user_id, spotify_playlist_id, playlist_name, playlist_image))

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""UPDATE playlists
                  SET name = ?,
                  image_url = ?,
                  updated_at = ?
                  WHERE user_id = ?;""", (playlist_name, playlist_image, current_time, user_id))
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

def get_tracks(spotify_playlist_id, status):
    db = get_db()
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None

    tracks = db.execute("""SELECT spotify_track_id, track_name, track_artists, track_image
                          FROM playlist_tracks
                          WHERE playlist_id = ?
                          AND status = ?
                          AND confirmed = 0
                          ORDER BY position;""", (playlist_id, status)).fetchall()

    if tracks is None:
        return None
    return tracks

@app.route("/track_swipe/<spotify_playlist_id>")
def track_swipe(spotify_playlist_id):
    load_playlist(spotify_playlist_id)
    load_tracks(spotify_playlist_id)

    track = get_next_unswiped_track(spotify_playlist_id)
    if track is None:
        spotify_track_id = None
        track_name = None
        track_artists = None
        track_image = None
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
    db = get_db()
    playlist_name = db.execute("""SELECT name
                                   FROM playlists
                                   WHERE spotify_playlist_id = ?""", (spotify_playlist_id,)).fetchone()
    playlist_name = playlist_name["name"]

    num_kept, num_deleted, _ = playlist_stats(spotify_playlist_id)

    deleted_tracks = get_tracks(spotify_playlist_id, 'delete')
    kept_tracks = get_tracks(spotify_playlist_id, 'keep')

    return render_template("playlist_completed.html",
                           spotify_playlist_id=spotify_playlist_id,
                           deleted_tracks=deleted_tracks,
                           kept_tracks=kept_tracks,
                           playlist_name=playlist_name,
                           num_kept=num_kept,
                           num_deleted=num_deleted)

def apply_changes(spotify_playlist_id, track_ids):
    db = get_db()
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None

    deleted_track_ids = track_ids[0]
    kept_track_ids = track_ids[1]

    if deleted_track_ids:
        g.user.playlist_remove_all_occurrences_of_items(spotify_playlist_id, deleted_track_ids)
    for track_id in deleted_track_ids:
        db.execute("""UPDATE playlist_tracks
                        SET confirmed = 1
                        WHERE playlist_id = ?
                        AND spotify_track_id = ?""", (playlist_id, track_id))
        db.commit()

    for track_id in kept_track_ids:
        db.execute("""UPDATE playlist_tracks
                        SET confirmed = 1
                        WHERE playlist_id = ?
                        AND spotify_track_id = ?""", (playlist_id, track_id))
        db.commit()

def discard_changes(spotify_playlist_id, track_ids):
    db = get_db()
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None

    for track_id in track_ids:
        db.execute("""UPDATE playlist_tracks
                      SET status = NULL,
                          swiped_at = NULL
                      WHERE playlist_id = ?
                      AND spotify_track_id = ?""", (playlist_id, track_id))
        db.commit()
        

@app.route("/handle_playlist_changes", methods=["POST"])
def handle_playlist_changes():
    data = request.get_json()
    spotify_playlist_id = data["playlist_id"]
    track_ids = data["track_ids"]
    action = data["action"]

    if action == "apply":
        apply_changes(spotify_playlist_id, track_ids)
    elif action == "discard":
        discard_changes(spotify_playlist_id, track_ids)

    return jsonify({"success": True})

@app.route("/playlist_history/<spotify_playlist_id>")
def playlist_history(spotify_playlist_id):
    playlist_id = get_playlist_db_id(spotify_playlist_id)
    if playlist_id is None:
        return None
    
    db = get_db()
    playlist_info = db.execute("""SELECT name, image_url
                                   FROM playlists
                                   WHERE spotify_playlist_id = ?""", (spotify_playlist_id,)).fetchone()
    playlist_name = playlist_info["name"]
    playlist_image = playlist_info["image_url"]

    deleted_tracks = db.execute("""SELECT spotify_track_id, track_name, track_artists, track_image
                                  FROM playlist_tracks
                                  WHERE status = 'delete'
                                  AND confirmed = 1
                                  AND playlist_id = ?;""", (playlist_id,)).fetchall()

    kept_tracks = db.execute("""SELECT spotify_track_id, track_name, track_artists, track_image
                                  FROM playlist_tracks
                                  WHERE status = 'keep'
                                  AND confirmed = 1
                                  AND playlist_id = ?;""", (playlist_id,)).fetchall()

    return render_template("playlist_history.html",
                            playlist_name=playlist_name,
                            playlist_image=playlist_image,
                            deleted_tracks=deleted_tracks,
                            kept_tracks=kept_tracks)

@app.route("/attribution")
def attribution():
    return render_template("attribution.html")

@app.route("/test")
def test():
    return "test"