const resumeInput =
    document.getElementById("resume");

const fileName =
    document.getElementById("fileName");

const form =
    document.getElementById("resumeForm");

const button =
    document.getElementById("analyzeButton");


if (resumeInput) {

    resumeInput.addEventListener(
        "change",
        function () {

            if (this.files.length > 0) {

                fileName.textContent =
                    this.files[0].name;

            } else {

                fileName.textContent =
                    "Maximum file size: 10 MB";
            }
        }
    );
}


if (form) {

    form.addEventListener(
        "submit",
        function () {

            button.classList.add(
                "loading"
            );

            button.querySelector(
                "span"
            ).textContent =
                "Analyzing Resume...";
        }
    );
}