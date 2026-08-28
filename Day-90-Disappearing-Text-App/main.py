import tkinter as tk
from tkinter import messagebox


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "Disappearing Text Writing App"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650

DISAPPEAR_TIME = 5000  # milliseconds


# ============================================================
# MAIN WINDOW
# ============================================================

window = tk.Tk()
window.title(APP_TITLE)
window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
window.minsize(700, 500)
window.configure(bg="#f4f6f8")


# ============================================================
# VARIABLES
# ============================================================

timer_id = None
started = False


# ============================================================
# FUNCTIONS
# ============================================================

def start_timer(event=None):
    """
    Starts or resets the disappearing timer whenever
    the user types something.
    """

    global timer_id, started

    if not started:
        started = True

        instruction_label.config(
            text="Keep typing... Don't stop!"
        )

    # Cancel the previous timer
    if timer_id is not None:
        window.after_cancel(timer_id)

    # Start a new timer
    timer_id = window.after(
        DISAPPEAR_TIME,
        disappear_text
    )


def disappear_text():
    """
    Clears all text after the timer expires.
    """

    global timer_id, started

    text_area.delete(
        "1.0",
        tk.END
    )

    timer_id = None
    started = False

    instruction_label.config(
        text="Your text disappeared! Start again."
    )


def reset_app():
    """
    Manually clears the writing area and resets
    the application.
    """

    global timer_id, started

    if timer_id is not None:
        window.after_cancel(timer_id)
        timer_id = None

    text_area.delete(
        "1.0",
        tk.END
    )

    started = False

    instruction_label.config(
        text="Start typing to begin..."
    )

    text_area.focus_set()


def confirm_exit():
    """
    Confirms before closing the application.
    """

    answer = messagebox.askyesno(
        "Exit Application",
        "Are you sure you want to exit?"
    )

    if answer:
        window.destroy()


def update_word_count(event=None):
    """
    Updates the word counter whenever the user types.
    """

    content = text_area.get(
        "1.0",
        tk.END
    ).strip()

    if content:
        words = len(content.split())
    else:
        words = 0

    word_count_label.config(
        text=f"Words: {words}"
    )


def handle_typing(event=None):
    """
    Handles typing events.

    Every key press resets the timer and updates
    the word count.
    """

    start_timer()
    update_word_count()


# ============================================================
# HEADER
# ============================================================

header_frame = tk.Frame(
    window,
    bg="#202124",
    height=110
)

header_frame.pack(
    fill="x"
)

header_frame.pack_propagate(False)


title_label = tk.Label(
    header_frame,
    text="📝 Disappearing Text",
    font=("Arial", 26, "bold"),
    fg="white",
    bg="#202124"
)

title_label.pack(
    pady=(18, 2)
)


subtitle_label = tk.Label(
    header_frame,
    text="Keep writing. Don't stop.",
    font=("Arial", 12),
    fg="#d1d5db",
    bg="#202124"
)

subtitle_label.pack()


# ============================================================
# INSTRUCTION
# ============================================================

instruction_label = tk.Label(
    window,
    text="Start typing to begin...",
    font=("Arial", 14, "bold"),
    fg="#4f46e5",
    bg="#f4f6f8"
)

instruction_label.pack(
    pady=(25, 10)
)


# ============================================================
# WRITING AREA
# ============================================================

editor_frame = tk.Frame(
    window,
    bg="#f4f6f8"
)

editor_frame.pack(
    fill="both",
    expand=True,
    padx=40,
    pady=10
)


text_area = tk.Text(
    editor_frame,
    wrap="word",
    font=("Arial", 15),
    padx=20,
    pady=20,
    bg="white",
    fg="#202124",
    insertbackground="#202124",
    relief="solid",
    borderwidth=1,
    undo=True
)

text_area.pack(
    fill="both",
    expand=True
)


# ============================================================
# STATUS BAR
# ============================================================

status_frame = tk.Frame(
    window,
    bg="#f4f6f8"
)

status_frame.pack(
    fill="x",
    padx=40,
    pady=(5, 10)
)


word_count_label = tk.Label(
    status_frame,
    text="Words: 0",
    font=("Arial", 10),
    fg="#6b7280",
    bg="#f4f6f8"
)

word_count_label.pack(
    side="left"
)


timer_label = tk.Label(
    status_frame,
    text="Timer: 5 seconds",
    font=("Arial", 10),
    fg="#6b7280",
    bg="#f4f6f8"
)

timer_label.pack(
    side="right"
)


# ============================================================
# BUTTONS
# ============================================================

button_frame = tk.Frame(
    window,
    bg="#f4f6f8"
)

button_frame.pack(
    pady=(5, 25)
)


reset_button = tk.Button(
    button_frame,
    text="↻ Reset",
    command=reset_app,
    font=("Arial", 11, "bold"),
    padx=25,
    pady=10,
    bg="#4f46e5",
    fg="white",
    activebackground="#3730a3",
    activeforeground="white",
    relief="flat",
    cursor="hand2"
)

reset_button.pack(
    side="left",
    padx=6
)


exit_button = tk.Button(
    button_frame,
    text="Exit",
    command=confirm_exit,
    font=("Arial", 11, "bold"),
    padx=25,
    pady=10,
    bg="#374151",
    fg="white",
    activebackground="#1f2937",
    activeforeground="white",
    relief="flat",
    cursor="hand2"
)

exit_button.pack(
    side="left",
    padx=6
)


# ============================================================
# KEYBOARD EVENTS
# ============================================================

text_area.bind(
    "<KeyRelease>",
    handle_typing
)


# ============================================================
# WINDOW EVENTS
# ============================================================

window.protocol(
    "WM_DELETE_WINDOW",
    confirm_exit
)


# ============================================================
# START APPLICATION
# ============================================================

text_area.focus_set()

window.mainloop()