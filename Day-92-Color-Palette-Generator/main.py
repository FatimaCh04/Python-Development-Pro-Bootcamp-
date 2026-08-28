from flask import Flask, render_template, request
from PIL import Image
from collections import Counter
from pathlib import Path
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)


def allowed_file(filename):
    """Check whether the uploaded file has a supported extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_color_palette(image_path, number_of_colors=10):
    """
    Extract the most common colors from an image.

    Returns a list of dictionaries containing
    RGB and HEX color values.
    """

    image = Image.open(image_path).convert("RGB")

    # Resize image to make color analysis faster
    image.thumbnail((300, 300))

    pixels = list(image.getdata())

    # Count the most common RGB colors
    color_counts = Counter(pixels)

    most_common = color_counts.most_common(number_of_colors)

    palette = []

    for rgb, count in most_common:
        red, green, blue = rgb

        hex_color = "#{:02X}{:02X}{:02X}".format(
            red,
            green,
            blue
        )

        palette.append({
            "rgb": f"RGB({red}, {green}, {blue})",
            "hex": hex_color,
            "count": count
        })

    return palette


@app.route("/", methods=["GET", "POST"])
def index():

    palette = []
    image_url = None
    error = None

    if request.method == "POST":

        if "image" not in request.files:
            error = "Please select an image."
            return render_template(
                "index.html",
                palette=palette,
                image_url=image_url,
                error=error
            )

        file = request.files["image"]

        if file.filename == "":
            error = "Please select an image."
            return render_template(
                "index.html",
                palette=palette,
                image_url=image_url,
                error=error
            )

        if not allowed_file(file.filename):
            error = (
                "Unsupported file format. "
                "Please upload PNG, JPG, JPEG, WEBP or BMP."
            )

            return render_template(
                "index.html",
                palette=palette,
                image_url=image_url,
                error=error
            )

        try:

            filename = file.filename

            # Prevent unsafe filename/path characters
            filename = os.path.basename(filename)

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            file.save(image_path)

            palette = get_color_palette(
                image_path,
                number_of_colors=10
            )

            image_url = f"/uploads/{filename}"

        except Exception as e:

            error = f"Could not process the image: {e}"

    return render_template(
        "index.html",
        palette=palette,
        image_url=image_url,
        error=error
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """
    Serve uploaded images to the browser.
    """

    from flask import send_from_directory

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


if __name__ == "__main__":
    app.run(
        debug=True
    )