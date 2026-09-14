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