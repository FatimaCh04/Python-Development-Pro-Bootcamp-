import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def local_suggestion(title, description, priority, due_date):
    if priority == "High":
        return (
            f"'{title}' is marked as high priority. "
            "Start this task first and break it into smaller steps."
        )

    if due_date:
        return (
            f"'{title}' has a deadline of {due_date}. "
            "Schedule focused work sessions before the deadline."
        )

    if description:
        return (
            f"For '{title}', begin by identifying the main goal, "
            "then divide the work into 2–3 actionable steps."
        )

    return (
        f"Start with '{title}' by defining the smallest "
        "actionable step you can complete today."
    )


def get_ai_suggestion(title, description, priority, due_date):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or OpenAI is None:
        return local_suggestion(
            title,
            description,
            priority,
            due_date
        )

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
You are a productivity assistant.

Task:
{title}

Description:
{description}

Priority:
{priority}

Due date:
{due_date}

Give one short, practical productivity suggestion.
Maximum 2 sentences.
"""

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        return response.output_text.strip()

    except Exception:
        return local_suggestion(
            title,
            description,
            priority,
            due_date
        )