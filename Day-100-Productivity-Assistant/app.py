from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = "productivity_data.json"


def load_data():
    """Load productivity data from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {
            "tasks": [],
            "sessions": [],
            "notes": []
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {
            "tasks": [],
            "sessions": [],
            "notes": []
        }


def save_data(data):
    """Save productivity data to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


@app.route("/")
def index():
    data = load_data()

    completed_tasks = sum(
        1 for task in data["tasks"]
        if task.get("completed", False)
    )

    total_tasks = len(data["tasks"])

    today = datetime.now().strftime("%Y-%m-%d")

    today_sessions = [
        session for session in data["sessions"]
        if session.get("date") == today
    ]

    focus_minutes = sum(
        session.get("minutes", 0)
        for session in today_sessions
    )

    return render_template(
        "index.html",
        tasks=data["tasks"],
        notes=data["notes"],
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        focus_minutes=focus_minutes
    )


@app.route("/analytics")
def analytics():
    data = load_data()

    total_tasks = len(data["tasks"])

    completed_tasks = sum(
        1 for task in data["tasks"]
        if task.get("completed", False)
    )

    pending_tasks = total_tasks - completed_tasks

    total_focus_minutes = sum(
        session.get("minutes", 0)
        for session in data["sessions"]
    )

    completion_rate = (
        round((completed_tasks / total_tasks) * 100, 1)
        if total_tasks > 0
        else 0
    )

    daily_focus = {}

    for session in data["sessions"]:
        date = session.get("date", "Unknown")
        minutes = session.get("minutes", 0)

        daily_focus[date] = daily_focus.get(date, 0) + minutes

    sorted_focus = sorted(
        daily_focus.items(),
        key=lambda item: item[0]
    )

    return render_template(
        "analytics.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        total_focus_minutes=total_focus_minutes,
        completion_rate=completion_rate,
        focus_dates=[item[0] for item in sorted_focus],
        focus_values=[item[1] for item in sorted_focus]
    )


@app.route("/add-task", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()

    if not title:
        return redirect(url_for("index"))

    data = load_data()

    task = {
        "id": int(datetime.now().timestamp() * 1000),
        "title": title,
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["tasks"].append(task)
    save_data(data)

    return redirect(url_for("index"))


@app.route("/complete-task/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    data = load_data()

    for task in data["tasks"]:
        if task.get("id") == task_id:
            task["completed"] = not task.get("completed", False)
            break

    save_data(data)

    return redirect(url_for("index"))


@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    data = load_data()

    data["tasks"] = [
        task for task in data["tasks"]
        if task.get("id") != task_id
    ]

    save_data(data)

    return redirect(url_for("index"))


@app.route("/add-note", methods=["POST"])
def add_note():
    content = request.form.get("content", "").strip()

    if not content:
        return redirect(url_for("index"))

    data = load_data()

    note = {
        "id": int(datetime.now().timestamp() * 1000),
        "content": content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["notes"].append(note)
    save_data(data)

    return redirect(url_for("index"))


@app.route("/delete-note/<int:note_id>", methods=["POST"])
def delete_note(note_id):
    data = load_data()

    data["notes"] = [
        note for note in data["notes"]
        if note.get("id") != note_id
    ]

    save_data(data)

    return redirect(url_for("index"))


@app.route("/add-session", methods=["POST"])
def add_session():
    minutes_raw = request.form.get("minutes", "0")

    try:
        minutes = int(minutes_raw)
    except ValueError:
        minutes = 0

    if minutes <= 0:
        return redirect(url_for("index"))

    data = load_data()

    session = {
        "id": int(datetime.now().timestamp() * 1000),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "minutes": minutes
    }

    data["sessions"].append(session)
    save_data(data)

    return redirect(url_for("index"))


@app.route("/api/stats")
def stats():
    data = load_data()

    total_tasks = len(data["tasks"])

    completed_tasks = sum(
        1 for task in data["tasks"]
        if task.get("completed", False)
    )

    focus_minutes = sum(
        session.get("minutes", 0)
        for session in data["sessions"]
    )

    return jsonify({
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": total_tasks - completed_tasks,
        "focus_minutes": focus_minutes
    })


if __name__ == "__main__":
    app.run(debug=True)