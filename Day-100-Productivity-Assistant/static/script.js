async function getSuggestion(taskId, button) {

    const box = document.getElementById(
        `suggestion-${taskId}`
    );

    if (!box) {
        return;
    }

    button.disabled = true;
    button.textContent = "Thinking...";

    box.classList.add("visible");
    box.textContent = "Generating a productivity suggestion...";

    try {

        const response = await fetch(
            `/ai-suggestion/${taskId}`
        );

        if (!response.ok) {
            throw new Error("Request failed");
        }

        const data = await response.json();

        box.textContent = `✦ ${data.suggestion}`;

    } catch (error) {

        box.textContent =
            "Unable to generate a suggestion right now.";

    } finally {

        button.disabled = false;
        button.textContent = "✦ AI Suggestion";
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        const cards =
            document.querySelectorAll(".task-card");

        cards.forEach((card, index) => {

            card.style.opacity = "0";
            card.style.transform =
                "translateY(10px)";

            setTimeout(() => {

                card.style.transition =
                    "opacity .35s ease, transform .35s ease";

                card.style.opacity = "1";
                card.style.transform =
                    "translateY(0)";

            }, index * 50);
        });


        const flashes =
            document.querySelectorAll(".flash");

        flashes.forEach((flash) => {

            setTimeout(() => {

                flash.style.opacity = "0";

                setTimeout(() => {
                    flash.remove();
                }, 300);

            }, 3500);
        });

    }
);