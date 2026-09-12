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

function deletePlaylist(spotify_playlist_id) {
    console.log("hi")
}