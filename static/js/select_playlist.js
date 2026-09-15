const swiper = new Swiper('.swiper', {
    loop: true,
    mousewheel: true,

    slidesPerView: 3,
    centeredSlides: true,
    spaceBetween: 30,

    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },

    breakpoints: {
        0: {
            slidesPerView: 1
        },
        700: {
            slidesPerView: 2
        },
        1100: {
            slidesPerView: 3
        }
    }
});

function deletePlaylist() {
    const deleteBtn = document.querySelector(".playlist-action.delete");
    const spotify_playlist_id = deleteBtn?.dataset.playlistId;
    
    fetch("/delete_playlist", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
        playlist_id: spotify_playlist_id
    }),
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