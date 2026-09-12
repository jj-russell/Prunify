const swipeButtons = document.querySelector(".swipe-buttons");
const spotify_playlist_id = swipeButtons?.getAttribute("data-playlist-id");
const trackCard = document.querySelector(".track-card");
const trackImage = trackCard?.querySelector("img");
const trackTitleWrapper = document.querySelector(".track-title-scroll");
const trackName = trackTitleWrapper
  ? trackTitleWrapper.querySelector(".track-title")
  : null;
const trackArtist = document.querySelector(".track-artist");
const trackStatus = document.querySelector(".track-status");
const statsEls = {
  deleted: document.querySelector(".swipe-statistics p:nth-of-type(1) i"),
  kept: document.querySelector(".swipe-statistics p:nth-of-type(2) i"),
  unswiped: document.querySelector(".swipe-statistics p:nth-of-type(3) i"),
};

function updateMarquee() {
  if (!trackTitleWrapper || !trackName) return;

  const overflowDistance = Math.max(
    trackName.scrollWidth - trackTitleWrapper.clientWidth,
    0,
  );
  trackTitleWrapper.style.setProperty(
    "--scroll-distance",
    `${overflowDistance}px`,
  );
  const hasOverflow = overflowDistance > 0;
  trackTitleWrapper.classList.toggle("marquee-active", hasOverflow);
}

function setSwipeButtonsVisible(isVisible) {
  if (!swipeButtons) return;
  swipeButtons.style.display = isVisible ? "" : "none";
}

function setArtistVisibility(isVisible, text = "") {
  if (trackArtist) {
    trackArtist.textContent = text;
    trackArtist.style.display = isVisible ? "" : "none";
  }

  if (trackStatus) {
    trackStatus.style.display = isVisible ? "none" : "block";
    if (!isVisible) {
      trackStatus.textContent = "All songs have been swiped on.";
    }
  }
}

function updateTrack(track) {
  if (!track) {
    if (trackName) trackName.textContent = "No tracks left";
    if (trackImage) trackImage.src = "/static/images/placeholder.png";
    if (swipeButtons) swipeButtons.setAttribute("data-track-id", "");
    setSwipeButtonsVisible(false);
    setArtistVisibility(false);
    updateMarquee();
    return;
  }

  if (trackName) trackName.textContent = track.track_name;
  if (trackImage)
    trackImage.src = track.track_image || "/static/images/placeholder.png";
  if (swipeButtons) {
    swipeButtons.setAttribute("data-track-id", track.spotify_track_id);
    setSwipeButtonsVisible(Boolean(track.track_artists));
  }

  if (track.track_artists) {
    setArtistVisibility(true, track.track_artists);
  } else {
    setArtistVisibility(false);
  }

  requestAnimationFrame(updateMarquee);
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
      track_id: swipeButtons?.getAttribute("data-track-id"),
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

window.addEventListener("resize", updateMarquee);
requestAnimationFrame(updateMarquee);
