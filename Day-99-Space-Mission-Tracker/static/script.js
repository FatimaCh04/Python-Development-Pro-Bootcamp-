document.addEventListener("DOMContentLoaded", () => {

    const cards = document.querySelectorAll(
        ".mission-card"
    );

    cards.forEach((card, index) => {

        card.style.opacity = "0";
        card.style.transform = "translateY(12px)";

        setTimeout(() => {

            card.style.transition =
                "opacity .4s ease, transform .4s ease";

            card.style.opacity = "1";
            card.style.transform = "translateY(0)";

        }, index * 70);

    });


    const forms = document.querySelectorAll(
        "form"
    );

    forms.forEach((form) => {

        form.addEventListener("submit", () => {

            const button = form.querySelector(
                "button[type='submit']"
            );

            if (
                button &&
                !button.classList.contains(
                    "delete-button"
                )
            ) {
                button.disabled = true;
                button.style.opacity = "0.7";
            }

        });

    });

});