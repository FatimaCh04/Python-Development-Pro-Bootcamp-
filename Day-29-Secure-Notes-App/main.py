from tkinter import *
from tkinter import messagebox


# ---------------- SAVE NOTE ---------------- #
def save_note():
    title = title_entry.get()
    note = note_text.get("1.0", END).strip()

    if title == "" or note == "":
        messagebox.showwarning("Warning", "Please fill all fields!")
        return

    with open("notes.txt", "a") as file:
        file.write(f"Title: {title}\n")
        file.write(f"Note: {note}\n")
        file.write("-" * 40 + "\n")

    messagebox.showinfo("Success", "Note saved successfully!")

    title_entry.delete(0, END)
    note_text.delete("1.0", END)


# ---------------- LOAD NOTES ---------------- #
def load_notes():
    try:
        with open("notes.txt", "r") as file:
            content = file.read()

        display.delete("1.0", END)
        display.insert(END, content)

    except FileNotFoundError:
        messagebox.showerror("Error", "No notes found!")


# ---------------- UI ---------------- #
window = Tk()
window.title("Secure Notes Manager")
window.geometry("500x550")
window.config(padx=20, pady=20)

Label(text="Title", font=("Arial", 12, "bold")).pack()

title_entry = Entry(width=50)
title_entry.pack(pady=5)

Label(text="Write Note", font=("Arial", 12, "bold")).pack()

note_text = Text(width=55, height=10)
note_text.pack()

Button(text="Save Note", command=save_note, width=20).pack(pady=10)

Button(text="View Notes", command=load_notes, width=20).pack()

Label(text="Saved Notes", font=("Arial", 12, "bold")).pack(pady=10)

display = Text(width=55, height=10)
display.pack()

window.mainloop()