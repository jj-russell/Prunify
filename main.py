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

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope="user-library-read"))

