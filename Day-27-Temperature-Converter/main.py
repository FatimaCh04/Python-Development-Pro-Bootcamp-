from tkinter import *


# ---------------------------- FUNCTIONS ------------------------------- #
def convert_temperature():
    """Convert Celsius to Fahrenheit."""
    try:
        celsius = float(input_entry.get())
        fahrenheit = (celsius * 9 / 5) + 32
        result_label.config(text=f"{fahrenheit:.2f} °F")
    except ValueError:
        result_label.config(text="Invalid Input")


def clear_fields():
    input_entry.delete(0, END)
    result_label.config(text="0.00 °F")


# ---------------------------- WINDOW ------------------------------- #
window = Tk()
window.title("Temperature Converter")
window.config(padx=20, pady=20)

# Input
input_entry = Entry(width=15)
input_entry.grid(column=1, row=0)

celsius_label = Label(text="°C")
celsius_label.grid(column=2, row=0)

# Convert Button
convert_button = Button(text="Convert", command=convert_temperature)
convert_button.grid(column=1, row=1, pady=10)

# Clear Button
clear_button = Button(text="Clear", command=clear_fields)
clear_button.grid(column=2, row=1)

# Result
text_label = Label(text="Fahrenheit:")
text_label.grid(column=0, row=2)

result_label = Label(text="0.00 °F")
result_label.grid(column=1, row=2)

window.mainloop()