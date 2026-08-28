document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.querySelector(
        ".search-box input"
    );

    if (searchInput) {
        searchInput.focus();
    }


    const cards = document.querySelectorAll(
        ".news-card"
    );

    cards.forEach((card, index) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(10px)";

        setTimeout(() => {
            card.style.transition =
                "opacity 0.4s ease, transform 0.4s ease";

            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, index * 70);
    });

});