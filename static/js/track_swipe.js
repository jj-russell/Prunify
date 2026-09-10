const swipeButtons = document.querySelector(".swipe-buttons");
const spotify_playlist_id = swipeButtons.getAttribute("data-playlist-id");
const trackCard = document.querySelector(".track-card");
const trackImage = trackCard.querySelector("img");
const trackName = trackCard.querySelector("h1");
const trackArtists = trackCard.querySelector("p");
const statsEls = {
  deleted: document.querySelector(".swipe-statistics p:nth-of-type(1) i"),
  kept: document.querySelector(".swipe-statistics p:nth-of-type(2) i"),
  unswiped: document.querySelector(".swipe-statistics p:nth-of-type(3) i"),
};

function updateTrack(track) {
  if (!track) {
    if (trackName) trackName.textContent = "No tracks left";
    if (trackImage) trackImage.src = "/static/images/placeholder.png";
    if (swipeButtons) swipeButtons.setAttribute("data-track-id", "");
    return;
  }

  if (trackName) trackName.textContent = track.track_name;
  if (trackArtists) trackArtists.textContent = track.track_artists;
  if (trackImage)
    trackImage.src = track.track_image || "/static/images/placeholder.png";
  if (swipeButtons)
    swipeButtons.setAttribute("data-track-id", track.spotify_track_id);
}

function updateStats(stats) {
  if (!stats) return;

  if (statsEls.deleted) statsEls.deleted.textContent = stats.deleted;
  if (statsEls.kept) statsEls.kept.textContent = stats.kept;
  if (statsEls.unswiped) statsEls.unswiped.textContent = stats.unswiped;
}

function deleteTrack() {
  sendDecision("delete");
}

function keepTrack() {
  sendDecision("keep");
}

function sendDecision(decision) {
  fetch("/track_decision", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      playlist_id: spotify_playlist_id,
      track_id: swipeButtons.getAttribute("data-track-id"),
      decision: decision,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        updateTrack(data.track);
        updateStats(data.stats);
      }
    });
}
