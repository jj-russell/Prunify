const slideCount = document.querySelectorAll('.swiper .swiper-slide').length;

if (slideCount > 0) {
    const swiper = new Swiper('.swiper', {
        loop: slideCount > 1,
        mousewheel: true,

        slidesPerView: 1,
        centeredSlides: slideCount > 1,
        spaceBetween: 30,

        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },

        breakpoints: {
            700: {
                slidesPerView: Math.min(2, slideCount)
            },
            1100: {
                slidesPerView: Math.min(3, slideCount)
            }
        }
    });
}

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