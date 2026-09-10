function getActiveTab() {
  const deleteBtn = document.querySelector(".track-action-switcher .delete");
  const keepBtn = document.querySelector(".track-action-switcher .keep");

  if (!deleteBtn || !keepBtn) return null;
  if (deleteBtn.classList.contains("active")) return "delete";
  if (keepBtn.classList.contains("active")) return "keep";
  return null;
}

document.addEventListener("DOMContentLoaded", function () {
  const deleteBtn = document.querySelector(".track-action-switcher .delete");
  const keepBtn = document.querySelector(".track-action-switcher .keep");
  const deletedContainer = document.querySelector(".deleted-tracks");
  const keptContainer = document.querySelector(".kept-tracks");

  if (!deleteBtn || !keepBtn || !deletedContainer || !keptContainer) return;

  function showDeleted() {
    deletedContainer.style.display = "";
    keptContainer.style.display = "none";
    deleteBtn.classList.add("active");
    keepBtn.classList.remove("active");
  }

  function showKept() {
    deletedContainer.style.display = "none";
    keptContainer.style.display = "";
    deleteBtn.classList.remove("active");
    keepBtn.classList.add("active");
  }

  deleteBtn.addEventListener("click", showDeleted);
  keepBtn.addEventListener("click", showKept);

  // Initialize: show deleted by default if there are deleted tracks, otherwise show kept
  if (deletedContainer.querySelector("tbody tr")) {
    showDeleted();
  } else {
    showKept();
  }
});

// user clicks apply or discard
const deletedTracks = document.querySelectorAll(
  ".deleted-tracks tr[data-track-id]",
);
const keptTracks = document.querySelectorAll(".kept-tracks tr[data-track-id]");

const deletedTrackIds = [
  ...document.querySelectorAll(".deleted-tracks tr[data-track-id]"),
].map((tr) => tr.dataset.trackId);
const keptTrackIds = [
  ...document.querySelectorAll(".kept-tracks tr[data-track-id]"),
].map((tr) => tr.dataset.trackId);

function applyChanges() {
  const activeTab = getActiveTab();
  sendDecision(activeTab, "apply");
}

function discardChanges() {
  const activeTab = getActiveTab();
  sendDecision(activeTab, "discard");
}

const tableContainer = document.querySelector(".table-container");
const spotify_playlist_id = tableContainer.getAttribute("data-playlist-id");

function sendDecision(decision, action) {
  let trackIds = [];

  if (decision === "delete") {
    trackIds = deletedTrackIds;
  } else if (decision === "keep") {
    trackIds = keptTrackIds;
  }

  const payload = {
    playlist_id: spotify_playlist_id,
    track_ids: trackIds,
    action: action,
  };

  fetch("/handle_playlist_changes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.success) {
        console.log("Decision saved successfully", data);
      }
    })
    .catch((error) => {
      console.error("Error sending decision:", error);
    });
}
