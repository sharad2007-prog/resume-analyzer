# Resume Analyzer

A Flask web app that compares your resume (PDF) against a job description and gives you a match score, matched and missing keywords, and improvement tips.

## How it works

1. Extracts text from the uploaded PDF (`pypdf`)
2. Computes TF-IDF cosine similarity between resume and job description (`scikit-learn`)
3. Checks which job-description keywords appear in your resume
4. Blends both signals into a 0-100 score and generates suggestions

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Project structure

```
resume-analyzer/
├── app.py              # Flask backend + scoring logic
├── requirements.txt
├── templates/
│   └── index.html      # Upload page + results dashboard
└── static/
    ├── style.css
    └── script.js       # Sends the form, renders results
```

## Ideas to extend it

- Skill categories (languages, frameworks, tools) instead of flat keywords
- Synonym handling (JS = JavaScript, ML = machine learning)
- Section detection (education, projects, experience)
- Save past analyses with a database and user login
- Deploy on Render or Railway
