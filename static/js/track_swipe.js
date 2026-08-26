let index = 0;
const playlistId = "{{ playlist_id }}";

async function loadTrack() {
    const response = await fetch(`/get_track/${playlistId}/${index}`);
    const track = await response.json();

    if (track.finished) {
        alert("Finished!");
        return;
    }

    document.getElementById("cover").src = track.image;
    document.getElementById("title").textContent = track.title;
    document.getElementById("artist").textContent = track.artist;
}

function nextTrack() {
    index++;
    loadTrack();
}

loadTrack();