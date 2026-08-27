CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spotify_user_id TEXT NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE playlists;
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    spotify_playlist_id TEXT NOT NULL,
    name TEXT NOT NULL,
    loaded_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE (user_id, spotify_playlist_id)
);

DROP TABLE playlist_tracks;
CREATE TABLE IF NOT EXISTS playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    playlist_id INTEGER NOT NULL,

    -- Spotify identifiers
    spotify_track_id TEXT NOT NULL,

    -- Track metadata
    track_name TEXT NOT NULL,
    track_artists TEXT NOT NULL,
    track_image TEXT,

    -- Position in the Spotify playlist when the snapshot was created
    position INTEGER NOT NULL,

    -- NULL = not swiped, 'left' = delete, 'right' = keep
    status TEXT CHECK (status IN ('left', 'right') OR status IS NULL),

    swiped_at DATETIME,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (playlist_id)
        REFERENCES playlists(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_playlist_tracks_next
    ON playlist_tracks(playlist_id, status, position);