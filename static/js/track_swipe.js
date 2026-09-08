const spotify_playlist_id = document.querySelector('.swipe-buttons').getAttribute('data-playlist-id');
const spotify_track_id = document.querySelector('.swipe-buttons').getAttribute('data-track-id');

function deleteTrack() {
  sendDecision("left");
}

function keepTrack() {
  sendDecision("right");
}

function sendDecision(decision) {
    fetch("/track_decision", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            playlist_id: spotify_playlist_id,
            track_id: spotify_track_id,
            decision: decision
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
          window.location.reload();
        }
    });
}