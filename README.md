# Prunify

Prunify is a Flask app that helps you quickly review and clean a Spotify playlist by swiping tracks into `keep` or `delete` buckets before applying the changes to your playlist. Built with Flask, Spotipy, SQLite, and the Spotify Web API.

## Features

- Browse and select playlists from your Spotify account
- Load playlist tracks into a fast swipe-based review flow
- Mark tracks as `keep` or `delete` with quick decisions
- See progress and summary stats while reviewing a playlist
- Review final changes before confirming updates to Spotify
- Keep playlist history for completed cleanup sessions

## Quick Start

### Prerequisites

- Python 3.10+
- `pip` and a virtual environment
- A Spotify Developer app with `CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI`

### Installation

```bash
git clone <repo-url>
cd Prunify
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Go to `https://developer.spotify.com/dashboard` and create an app.

Create a `.env` file in the project root with the information from the developer app:

```env
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=your_secret_key
```

Initialize the SQLite database once:

```bash
sqlite3 app.db < schema.sql
```

### How to Run

```bash
# Windows
set FLASK_APP=app
flask run --debug
# macOS/Linux
export FLASK_APP=app
flask run --debug
```

Open `http://127.0.0.1:5000` in your browser.

### How to Use / Getting Started

1. Sign in with Spotify from the app home screen.
2. Select a playlist to review.
3. Swipe each track as `keep` or `delete`.
4. Review the result and apply the changes to the playlist.
