from tkinter import *

# ---------------------------- CONSTANTS ------------------------------- #
WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60

timer = None
remaining_time = WORK_TIME

# ---------------------------- FUNCTIONS ------------------------------- #
def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"


def countdown():
    global remaining_time, timer

    timer_label.config(text=format_time(remaining_time))

    if remaining_time > 0:
        remaining_time -= 1
        timer = window.after(1000, countdown)
    else:
        status_label.config(text="✅ Session Complete!")


def start_timer():
    global remaining_time
    remaining_time = WORK_TIME
    status_label.config(text="📚 Study Session")
    countdown()


def break_timer():
    global remaining_time
    remaining_time = SHORT_BREAK
    status_label.config(text="☕ Break Time")
    countdown()


def reset_timer():
    global remaining_time

    if timer:
        window.after_cancel(timer)

    remaining_time = WORK_TIME
    timer_label.config(text="25:00")
    status_label.config(text="Ready")


# ---------------------------- UI ------------------------------- #
window = Tk()
window.title("Study Timer")
window.config(padx=30, pady=30)

status_label = Label(text="Ready", font=("Arial", 18, "bold"))
status_label.pack(pady=10)

timer_label = Label(text="25:00", font=("Arial", 40, "bold"))
timer_label.pack(pady=20)

Button(text="▶ Start Study", width=15, command=start_timer).pack(pady=5)
Button(text="☕ Short Break", width=15, command=break_timer).pack(pady=5)
Button(text="🔄 Reset", width=15, command=reset_timer).pack(pady=5)

window.mainloop()