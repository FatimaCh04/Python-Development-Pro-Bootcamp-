import re

from collections import Counter

from pypdf import PdfReader


SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "php",
    "dart",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "sqlite",
    "html",
    "css",
    "bootstrap",
    "tailwind",
    "react",
    "angular",
    "vue",
    "node.js",
    "express",
    "flask",
    "django",
    "fastapi",
    "flutter",
    "git",
    "github",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "firebase",
    "supabase",
    "rest api",
    "api",
    "machine learning",
    "artificial intelligence",
    "data analysis",
    "pandas",
    "numpy",
    "matplotlib",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "project management",
    "figma",
    "canva",
    "linux",
    "windows",
}


def extract_pdf_text(file_path):

    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def normalize_text(text):

    text = text.lower()

    text = text.replace(
        "\u00a0",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def find_skills(text):

    normalized = normalize_text(text)

    found = []

    for skill in SKILLS:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill)
            + r"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            normalized
        ):

            found.append(skill)

    return sorted(
        found,
        key=str.lower
    )


def extract_keywords(text):

    normalized = normalize_text(text)

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z+#.-]{2,}\b",
        normalized
    )

    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "you",
        "your",
        "are",
        "our",
        "this",
        "that",
        "from",
        "have",
        "has",
        "will",
        "can",
        "not",
        "but",
        "all",
        "job",
        "work",
        "role",
        "years",
        "year",
        "experience",
        "skills",
        "required",
        "looking",
        "candidate",
        "using",
    }

    filtered = [
        word
        for word in words
        if word not in stop_words
    ]

    counts = Counter(filtered)

    return [
        word
        for word, count
        in counts.most_common(30)
        if count >= 1
    ]


def calculate_score(
    matched_skills,
    required_skills,
    resume_text,
    job_description
):

    if required_skills:

        skill_score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100

    else:

        skill_score = 0

    resume_words = set(
        normalize_text(
            resume_text
        ).split()
    )

    job_words = set(
        normalize_text(
            job_description
        ).split()
    )

    if job_words:

        keyword_score = (
            len(
                resume_words
                & job_words
            )
            / len(job_words)
        ) * 100

    else:

        keyword_score = 0

    final_score = (
        skill_score * 0.75
        + keyword_score * 0.25
    )

    return round(
        min(final_score, 100),
        1
    )


def generate_recommendations(
    matched_skills,
    missing_skills,
    score,
    resume_text
):

    recommendations = []

    if missing_skills:

        recommendations.append(
            "Consider adding relevant missing "
            "skills if you genuinely have "
            "experience with them."
        )

    if score < 50:

        recommendations.append(
            "Tailor your resume more closely "
            "to the job description."
        )

    elif score < 75:

        recommendations.append(
            "Your match is moderate. Add "
            "relevant projects and measurable "
            "achievements where appropriate."
        )

    else:

        recommendations.append(
            "Your resume has a strong match "
            "with the provided job description."
        )

    normalized = normalize_text(
        resume_text
    )

    sections = [
        "education",
        "experience",
        "projects",
        "skills",
        "contact"
    ]

    missing_sections = [
        section
        for section in sections
        if section not in normalized
    ]

    if missing_sections:

        recommendations.append(
            "Consider reviewing these common "
            "resume sections: "
            + ", ".join(missing_sections)
            + "."
        )

    if "linkedin" not in normalized:

        recommendations.append(
            "Consider including your LinkedIn "
            "profile if it is relevant."
        )

    if "github" not in normalized:

        recommendations.append(
            "Consider adding your GitHub profile "
            "for technical roles."
        )

    return recommendations


def analyze_resume(
    file_path,
    job_description
):

    resume_text = extract_pdf_text(
        file_path
    )

    if not resume_text.strip():

        raise ValueError(
            "The PDF does not contain "
            "extractable text."
        )

    resume_skills = find_skills(
        resume_text
    )

    required_skills = find_skills(
        job_description
    )

    if not required_skills:

        required_skills = find_skills(
            job_description
        )

    matched_skills = sorted(
        set(resume_skills)
        & set(required_skills),
        key=str.lower
    )

    missing_skills = sorted(
        set(required_skills)
        - set(resume_skills),
        key=str.lower
    )

    score = calculate_score(
        matched_skills,
        required_skills,
        resume_text,
        job_description
    )

    keywords = extract_keywords(
        job_description
    )

    recommendations = generate_recommendations(
        matched_skills,
        missing_skills,
        score,
        resume_text
    )

    return {
        "score": score,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "keywords": keywords,
        "recommendations": recommendations,
        "resume_characters": len(resume_text),
    }