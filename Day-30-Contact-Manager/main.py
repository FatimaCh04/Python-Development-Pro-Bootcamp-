import json
from tkinter import *
from tkinter import messagebox

FILE_NAME = "contacts.json"


# ---------------- SAVE CONTACT ---------------- #
def save_contact():
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    email = email_entry.get().strip()

    if not name or not phone or not email:
        messagebox.showwarning("Warning", "Please fill all fields!")
        return

    new_contact = {
        name: {
            "phone": phone,
            "email": email
        }
    }

    try:
        with open(FILE_NAME, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data.update(new_contact)

    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

    messagebox.showinfo("Success", "Contact Saved Successfully!")

    name_entry.delete(0, END)
    phone_entry.delete(0, END)
    email_entry.delete(0, END)


# ---------------- SEARCH CONTACT ---------------- #
def search_contact():
    name = name_entry.get().strip()

    try:
        with open(FILE_NAME, "r") as file:
            data = json.load(file)

        if name in data:
            info = data[name]
            messagebox.showinfo(
                "Contact Found",
                f"Phone: {info['phone']}\nEmail: {info['email']}"
            )
        else:
            messagebox.showerror("Not Found", "Contact does not exist.")

    except (FileNotFoundError, json.JSONDecodeError):
        messagebox.showerror("Error", "No contact file found.")


# ---------------- UI ---------------- #
window = Tk()
window.title("Contact Manager")
window.geometry("400x300")
window.config(padx=20, pady=20)

Label(text="Name").grid(row=0, column=0, pady=5)
name_entry = Entry(width=30)
name_entry.grid(row=0, column=1)

Label(text="Phone").grid(row=1, column=0, pady=5)
phone_entry = Entry(width=30)
phone_entry.grid(row=1, column=1)

Label(text="Email").grid(row=2, column=0, pady=5)
email_entry = Entry(width=30)
email_entry.grid(row=2, column=1)

Button(text="Save Contact", command=save_contact, width=15).grid(row=3, column=0, pady=15)

Button(text="Search Contact", command=search_contact, width=15).grid(row=3, column=1)

window.mainloop()