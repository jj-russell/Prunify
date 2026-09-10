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

let pendingAction = null;

function showConfirmModal(action) {
  const modal = document.getElementById("confirmModal");
  const title = document.getElementById("confirmModalTitle");
  const text = document.getElementById("confirmModalText");
  const confirmButton = document.getElementById("confirmDecision");

  if (!modal || !title || !text || !confirmButton) return;

  pendingAction = action;

  if (action === "apply") {
    title.textContent = "Apply changes?";
    text.textContent =
      "This will finalize the changes you made to this playlist.";
    confirmButton.textContent = "Apply changes";
    confirmButton.classList.remove("discard");
    confirmButton.classList.add("apply");
  } else {
    title.textContent = "Discard changes?";
    text.textContent =
      "This will reset the songs in the current selection and undo your changes.";
    confirmButton.textContent = "Discard changes";
    confirmButton.classList.remove("apply");
    confirmButton.classList.add("discard");
  }

  modal.classList.remove("hidden");
}

function closeConfirmModal() {
  const modal = document.getElementById("confirmModal");
  if (modal) {
    modal.classList.add("hidden");
  }
  pendingAction = null;
}

function applyChanges() {
  const activeTab = getActiveTab();
  if (!activeTab) return;
  showConfirmModal("apply");
}

function discardChanges() {
  const activeTab = getActiveTab();
  if (!activeTab) return;
  showConfirmModal("discard");
}

function bindModalControls() {
  const confirmButton = document.getElementById("confirmDecision");
  const cancelButton = document.getElementById("cancelConfirmation");
  const closeBackdrop = document.querySelector(".confirm-modal-backdrop");

  if (confirmButton) {
    confirmButton.addEventListener("click", function () {
      const action = pendingAction;
      closeConfirmModal();
      const activeTab = getActiveTab();
      if (action && activeTab) {
        sendDecision(activeTab, action);
      }
    });
  }

  if (cancelButton) {
    cancelButton.addEventListener("click", closeConfirmModal);
  }

  if (closeBackdrop) {
    closeBackdrop.addEventListener("click", closeConfirmModal);
  }
}

document.addEventListener("DOMContentLoaded", bindModalControls);

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
        window.location.reload();
      }
    })
    .catch((error) => {
      console.error("Error sending decision:", error);
    });
}
