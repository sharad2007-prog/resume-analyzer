import re

from flask import Flask, jsonify, render_template, request
from pypdf import PdfReader
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from skills import SKILLS

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

# Words that show up in resumes/JDs but say nothing about skills
EXTRA_STOP_WORDS = {
    "experience", "work", "working", "team", "teams", "ability", "strong",
    "good", "years", "year", "required", "preferred", "role", "job",
    "skills", "skill", "knowledge", "understanding", "responsibilities",
    "looking", "candidate", "company", "including", "using", "use", "will",
}
STOP_WORDS = set(ENGLISH_STOP_WORDS) | EXTRA_STOP_WORDS


def build_patterns():
    """One regex per skill. Boundaries stop 'java' matching inside 'javascript'."""
    patterns = {}
    for skill, aliases in SKILLS.items():
        alt = "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
        patterns[skill] = re.compile(rf"(?<![a-z0-9+#])(?:{alt})(?![a-z0-9+#])")
    return patterns


PATTERNS = build_patterns()


def extract_pdf_text(file_storage):
    """Read all text out of an uploaded PDF."""
    reader = PdfReader(file_storage)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def clean(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./\-\s]", " ", text)  # keep c++, c#, node.js, ci/cd style tokens
    return re.sub(r"\s+", " ", text).strip()


def find_skills(text):
    """Return the set of known skills mentioned in the text."""
    t = clean(text)
    return {skill for skill, pat in PATTERNS.items() if pat.search(t)}


def analyze(resume_text, jd_text):
    resume_clean, jd_clean = clean(resume_text), clean(jd_text)

    # 1. Overall wording similarity (TF-IDF + cosine)
    vec = TfidfVectorizer(stop_words=list(STOP_WORDS), ngram_range=(1, 2))
    matrix = vec.fit_transform([resume_clean, jd_clean])
    similarity = float(cosine_similarity(matrix[0], matrix[1])[0][0])

    # 2. Skill coverage: how many of the job's skills appear in the resume
    jd_skills = find_skills(jd_text)
    resume_skills = find_skills(resume_text)
    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    extra = sorted(resume_skills - jd_skills)
    coverage = len(matched) / len(jd_skills) if jd_skills else 0.0

    # Skills carry most of the weight; similarity is a small bonus
    if jd_skills:
        score = round((0.8 * coverage + 0.2 * min(similarity * 2, 1.0)) * 100)
    else:
        score = round(similarity * 100)

    # 3. Tips
    tips = []
    if not jd_skills:
        tips.append("I couldn't find known tech skills in this job description. Paste the full posting, including requirements.")
    if score < 50 and jd_skills:
        tips.append("Your resume overlaps weakly with this job. Tailor your skills and project bullets to it.")
    if missing:
        tips.append("Add the missing skills below where they honestly apply (skills section, projects, experience).")
    if len(resume_text.split()) < 150:
        tips.append("Your resume looks short. Add detail on projects, tools used, and outcomes.")
    if not re.search(r"\d", resume_text):
        tips.append("Add numbers (users, speedups, accuracy, team size) to make your impact concrete.")
    if not re.search(r"github\.com|linkedin\.com", resume_text.lower()):
        tips.append("Include your GitHub and LinkedIn links.")
    if not tips:
        tips.append("Strong match. Double-check formatting and keep bullets short and results-focused.")

    return {
        "score": score,
        "similarity": round(similarity * 100),
        "coverage": round(coverage * 100),
        "matched": matched,
        "missing": missing,
        "extra": extra[:30],
        "tips": tips,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_route():
    jd_text = request.form.get("job_description", "").strip()
    file = request.files.get("resume")

    if not file or file.filename == "":
        return jsonify({"error": "Please upload your resume as a PDF."}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported."}), 400
    if len(jd_text) < 30:
        return jsonify({"error": "Please paste a longer job description."}), 400

    try:
        resume_text = extract_pdf_text(file)
    except Exception:
        return jsonify({"error": "Could not read that PDF. Try another file."}), 400

    if len(resume_text.strip()) < 50:
        return jsonify({"error": "No readable text found. Is the PDF a scanned image?"}), 400

    return jsonify(analyze(resume_text, jd_text))


if __name__ == "__main__":
    app.run(debug=True)
