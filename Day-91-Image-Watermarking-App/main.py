import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from PIL import Image, ImageTk, ImageDraw, ImageFont


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Image Watermarking App"

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 720

BACKGROUND = "#f4f6f8"
DARK = "#202124"
PRIMARY = "#4f46e5"
SECONDARY = "#374151"
TEXT_COLOR = "#202124"
MUTED = "#6b7280"


# ============================================================
# GLOBAL VARIABLES
# ============================================================

original_image = None
preview_image = None
preview_photo = None
selected_image_path = None


# ============================================================
# MAIN WINDOW
# ============================================================

window = tk.Tk()

window.title(APP_TITLE)
window.geometry(
    f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
)

window.minsize(
    800,
    600
)

window.configure(
    bg=BACKGROUND
)


# ============================================================
# FUNCTIONS
# ============================================================

def open_image():
    """
    Opens an image selected by the user.
    """

    global original_image
    global selected_image_path

    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[
            (
                "Image Files",
                "*.jpg *.jpeg *.png *.bmp *.gif *.webp"
            ),
            (
                "JPEG Files",
                "*.jpg *.jpeg"
            ),
            (
                "PNG Files",
                "*.png"
            ),
            (
                "All Files",
                "*.*"
            )
        ]
    )

    if not file_path:
        return

    try:

        original_image = Image.open(
            file_path
        ).convert("RGBA")

        selected_image_path = file_path

        file_name_label.config(
            text=Path(file_path).name
        )

        update_preview()

        status_label.config(
            text="Image loaded successfully."
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            f"Could not open image.\n\n{error}"
        )


def get_font(size):
    """
    Returns a suitable font for the watermark.
    """

    possible_fonts = [
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf"
    ]

    for font_name in possible_fonts:

        try:

            return ImageFont.truetype(
                font_name,
                size
            )

        except OSError:
            continue

    return ImageFont.load_default()


def create_watermarked_image():
    """
    Creates a copy of the original image and
    applies the watermark.
    """

    if original_image is None:

        return None

    image = original_image.copy()

    watermark_text = watermark_entry.get().strip()

    if not watermark_text:

        return image

    opacity = opacity_scale.get()

    font_size = max(
        12,
        int(min(image.size) * 0.05)
    )

    font = get_font(font_size)

    # Create transparent watermark layer
    watermark_layer = Image.new(
        "RGBA",
        image.size,
        (255, 255, 255, 0)
    )

    draw = ImageDraw.Draw(
        watermark_layer
    )

    # Calculate text dimensions
    bbox = draw.textbbox(
        (0, 0),
        watermark_text,
        font=font
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    margin = max(
        20,
        int(min(image.size) * 0.03)
    )

    position = position_var.get()

    # Determine watermark position
    if position == "Top Left":

        x = margin
        y = margin

    elif position == "Top Right":

        x = image.width - text_width - margin
        y = margin

    elif position == "Center":

        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2

    elif position == "Bottom Left":

        x = margin
        y = image.height - text_height - margin

    else:

        x = image.width - text_width - margin
        y = image.height - text_height - margin

    # Draw shadow
    draw.text(
        (
            x + 2,
            y + 2
        ),
        watermark_text,
        font=font,
        fill=(0, 0, 0, opacity // 2)
    )

    # Draw watermark
    draw.text(
        (
            x,
            y
        ),
        watermark_text,
        font=font,
        fill=(255, 255, 255, opacity)
    )

    return Image.alpha_composite(
        image,
        watermark_layer
    )


def update_preview(*args):
    """
    Updates the image preview whenever
    watermark settings change.
    """

    global preview_image
    global preview_photo

    if original_image is None:

        return

    try:

        preview_image = create_watermarked_image()

        preview = preview_image.copy()

        max_width = 700
        max_height = 470

        preview.thumbnail(
            (
                max_width,
                max_height
            ),
            Image.Resampling.LANCZOS
        )

        preview_photo = ImageTk.PhotoImage(
            preview
        )

        image_label.config(
            image=preview_photo,
            text=""
        )

    except Exception as error:

        status_label.config(
            text=f"Preview error: {error}"
        )


def save_image():
    """
    Saves the watermarked image to disk.
    """

    if original_image is None:

        messagebox.showwarning(
            "No Image",
            "Please select an image first."
        )

        return

    try:

        result = create_watermarked_image()

        file_path = filedialog.asksaveasfilename(
            title="Save Watermarked Image",
            defaultextension=".png",
            filetypes=[
                (
                    "PNG Image",
                    "*.png"
                ),
                (
                    "JPEG Image",
                    "*.jpg"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not file_path:
            return

        # JPEG doesn't support RGBA
        if file_path.lower().endswith(
            (".jpg", ".jpeg")
        ):

            result = result.convert(
                "RGB"
            )

        result.save(
            file_path
        )

        status_label.config(
            text="Watermarked image saved successfully."
        )

        messagebox.showinfo(
            "Success",
            "Your watermarked image has been saved successfully."
        )

    except Exception as error:

        messagebox.showerror(
            "Save Error",
            f"Could not save the image.\n\n{error}"
        )


def clear_watermark():
    """
    Clears the watermark text.
    """

    watermark_entry.delete(
        0,
        tk.END
    )

    update_preview()


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    window,
    bg=DARK,
    height=95
)

header.pack(
    fill="x"
)

header.pack_propagate(
    False
)


title_label = tk.Label(
    header,
    text="🖼️ Image Watermarking App",
    font=(
        "Arial",
        25,
        "bold"
    ),
    fg="white",
    bg=DARK
)

title_label.pack(
    pady=(17, 2)
)


subtitle_label = tk.Label(
    header,
    text="Protect your images with a custom watermark",
    font=(
        "Arial",
        11
    ),
    fg="#d1d5db",
    bg=DARK
)

subtitle_label.pack()


# ============================================================
# MAIN CONTENT
# ============================================================

main_frame = tk.Frame(
    window,
    bg=BACKGROUND
)

main_frame.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=20
)


# ============================================================
# CONTROL PANEL
# ============================================================

control_frame = tk.Frame(
    main_frame,
    bg="white",
    width=270
)

control_frame.pack(
    side="left",
    fill="y",
    padx=(0, 20)
)

control_frame.pack_propagate(
    False
)


control_title = tk.Label(
    control_frame,
    text="Watermark Settings",
    font=(
        "Arial",
        16,
        "bold"
    ),
    fg=TEXT_COLOR,
    bg="white"
)

control_title.pack(
    anchor="w",
    padx=20,
    pady=(20, 20)
)


# Open image button
open_button = tk.Button(
    control_frame,
    text="📂 Choose Image",
    command=open_image,
    font=(
        "Arial",
        11,
        "bold"
    ),
    bg=PRIMARY,
    fg="white",
    activebackground=PRIMARY,
    activeforeground="white",
    relief="flat",
    padx=15,
    pady=10,
    cursor="hand2"
)

open_button.pack(
    fill="x",
    padx=20
)


file_name_label = tk.Label(
    control_frame,
    text="No image selected",
    font=(
        "Arial",
        9
    ),
    fg=MUTED,
    bg="white",
    wraplength=220
)

file_name_label.pack(
    padx=20,
    pady=(8, 20)
)


# Watermark text
watermark_label = tk.Label(
    control_frame,
    text="Watermark Text",
    font=(
        "Arial",
        10,
        "bold"
    ),
    fg=TEXT_COLOR,
    bg="white"
)

watermark_label.pack(
    anchor="w",
    padx=20
)


watermark_entry = tk.Entry(
    control_frame,
    font=(
        "Arial",
        11
    ),
    relief="solid",
    borderwidth=1
)

watermark_entry.insert(
    0,
    "© My Brand"
)

watermark_entry.pack(
    fill="x",
    padx=20,
    pady=(6, 18)
)


# Position
position_label = tk.Label(
    control_frame,
    text="Position",
    font=(
        "Arial",
        10,
        "bold"
    ),
    fg=TEXT_COLOR,
    bg="white"
)

position_label.pack(
    anchor="w",
    padx=20
)


position_var = tk.StringVar(
    value="Bottom Right"
)


position_menu = tk.OptionMenu(
    control_frame,
    position_var,
    "Top Left",
    "Top Right",
    "Center",
    "Bottom Left",
    "Bottom Right"
)

position_menu.config(
    font=(
        "Arial",
        10
    ),
    bg="#f3f4f6",
    relief="flat"
)

position_menu.pack(
    fill="x",
    padx=20,
    pady=(6, 18)
)


# Opacity
opacity_label = tk.Label(
    control_frame,
    text="Opacity",
    font=(
        "Arial",
        10,
        "bold"
    ),
    fg=TEXT_COLOR,
    bg="white"
)

opacity_label.pack(
    anchor="w",
    padx=20
)


opacity_scale = tk.Scale(
    control_frame,
    from_=50,
    to=255,
    orient="horizontal",
    bg="white",
    highlightthickness=0,
    command=update_preview
)

opacity_scale.set(
    180
)

opacity_scale.pack(
    fill="x",
    padx=20,
    pady=(0, 20)
)


# Buttons
clear_button = tk.Button(
    control_frame,
    text="Clear Watermark",
    command=clear_watermark,
    font=(
        "Arial",
        10,
        "bold"
    ),
    bg=SECONDARY,
    fg="white",
    relief="flat",
    padx=10,
    pady=9,
    cursor="hand2"
)

clear_button.pack(
    fill="x",
    padx=20,
    pady=(0, 8)
)


save_button = tk.Button(
    control_frame,
    text="💾 Save Image",
    command=save_image,
    font=(
        "Arial",
        11,
        "bold"
    ),
    bg=PRIMARY,
    fg="white",
    relief="flat",
    padx=10,
    pady=11,
    cursor="hand2"
)

save_button.pack(
    fill="x",
    padx=20
)


# ============================================================
# PREVIEW PANEL
# ============================================================

preview_frame = tk.Frame(
    main_frame,
    bg="white"
)

preview_frame.pack(
    side="right",
    fill="both",
    expand=True
)


preview_title = tk.Label(
    preview_frame,
    text="Image Preview",
    font=(
        "Arial",
        16,
        "bold"
    ),
    fg=TEXT_COLOR,
    bg="white"
)

preview_title.pack(
    anchor="w",
    padx=20,
    pady=(20, 10)
)


image_container = tk.Frame(
    preview_frame,
    bg="#eef0f3"
)

image_container.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=(0, 10)
)


image_label = tk.Label(
    image_container,
    text="📷\n\nChoose an image to preview it here",
    font=(
        "Arial",
        13
    ),
    fg=MUTED,
    bg="#eef0f3",
    justify="center"
)

image_label.pack(
    fill="both",
    expand=True
)


status_label = tk.Label(
    preview_frame,
    text="Ready",
    font=(
        "Arial",
        9
    ),
    fg=MUTED,
    bg="white"
)

status_label.pack(
    anchor="w",
    padx=20,
    pady=(0, 15)
)


# ============================================================
# EVENT BINDINGS
# ============================================================

watermark_entry.bind(
    "<KeyRelease>",
    update_preview
)

position_var.trace_add(
    "write",
    update_preview
)


# ============================================================
# START APPLICATION
# ============================================================

window.mainloop()