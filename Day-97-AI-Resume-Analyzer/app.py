import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename

from resume_analyzer import analyze_resume


app = Flask(__name__)

app.secret_key = "day97-resume-analyzer-secret"

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        return render_template(
            "index.html",
            result=None
        )

    resume = request.files.get("resume")
    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    if not resume:
        flash(
            "Please upload your resume.",
            "error"
        )

        return redirect(url_for("index"))

    if resume.filename == "":
        flash(
            "Please select a PDF file.",
            "error"
        )

        return redirect(url_for("index"))

    if not allowed_file(resume.filename):
        flash(
            "Only PDF files are supported.",
            "error"
        )

        return redirect(url_for("index"))

    if not job_description:
        flash(
            "Please enter a job description.",
            "error"
        )

        return redirect(url_for("index"))

    original_name = secure_filename(
        resume.filename
    )

    unique_name = (
        f"{uuid.uuid4().hex}_"
        f"{original_name}"
    )

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        unique_name
    )

    try:

        resume.save(file_path)

        result = analyze_resume(
            file_path,
            job_description
        )

        return render_template(
            "index.html",
            result=result,
            filename=original_name
        )

    except Exception as error:

        flash(
            f"Analysis failed: {error}",
            "error"
        )

        return redirect(url_for("index"))

    finally:

        if os.path.exists(file_path):

            try:
                os.remove(file_path)

            except OSError:
                pass


@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 10 MB.",
        "error"
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )