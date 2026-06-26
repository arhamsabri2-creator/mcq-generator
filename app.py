from flask import Flask, request, session, redirect, url_for
import openai
import os
import re

app = Flask(__name__)
app.secret_key = "mcq-secret-key"

SYSTEM_PROMPT = """You are an MCQ generator for Indian judicial services exam preparation.
The user will give you the actual text of a law section and a topic name.
Generate exactly 10 MCQs based ONLY on the text provided.
Follow this format STRICTLY for every question:
Q1. Question here
A) Option 1
B) Option 2
C) Option 3
D) Option 4
Answer: A
Explanation: Brief explanation here
Rules:
- Generate exactly 10 questions numbered Q1 to Q10
- Base questions ONLY on the text provided
- Always give exactly 4 options
- Always mark correct answer as single letter A B C or D
- Always give one line explanation
- Never deviate from this format"""

def parse_questions(raw):
    questions = re.split(r'Q\d+\.', raw)
    questions = [q.strip() for q in questions if q.strip()]
    parsed = []
    for q in questions:
        lines = [l.strip() for l in q.strip().split('\n') if l.strip()]
        question_text = lines[0] if lines else ""
        options = []
        answer = ""
        explanation = ""
        for line in lines[1:]:
            if line.startswith("A)") or line.startswith("B)") or line.startswith("C)") or line.startswith("D)"):
                options.append(line)
            elif line.startswith("Answer:"):
                answer = line.replace("Answer:", "").strip()
            elif line.startswith("Explanation:"):
                explanation = line.replace("Explanation:", "").strip()
        parsed.append({"question": question_text, "options": options, "answer": answer, "explanation": explanation})
    return parsed

@app.route("/", methods=["GET"])
def home():
    session.clear()
    return """<!DOCTYPE html><html><head><style>
body{background-color:#0d1117;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}
.box{background-color:#161b22;padding:40px;border-radius:15px;width:600px;text-align:center;}
h1{color:#f78166;font-size:28px;}
p{color:#8b949e;font-size:14px;}
input{width:85%;padding:12px;border-radius:8px;border:1px solid #30363d;background:#0d1117;color:white;font-size:15px;margin-top:15px;}
textarea{width:85%;padding:12px;border-radius:8px;border:1px solid #30363d;background:#0d1117;color:white;font-size:14px;height:180px;margin-top:15px;resize:vertical;}
button{margin-top:20px;padding:12px 40px;background-color:#f78166;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;width:90%;}
label{display:block;text-align:left;margin-top:15px;color:#8b949e;font-size:13px;width:85%;margin-left:auto;margin-right:auto;}
</style></head><body><div class="box">
<h1>⚖️ Judicial MCQ Quiz</h1>
<p>Paste the actual law text — get an interactive 10 question quiz</p>
<form action="/generate" method="POST">
<label>Topic Name</label>
<input type="text" name="topic" placeholder="e.g. Section 173 BNSS — Investigation">
<label>Paste Law Text Here</label>
<textarea name="lawtext" placeholder="Paste the actual text of the section here..."></textarea>
<button type="submit">⚡ Generate Quiz</button>
</form></div></body></html>"""

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic")
    lawtext = request.form.get("lawtext")
    session["topic"] = topic
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Topic: {topic}\n\nLaw Text:\n{lawtext}\n\nGenerate 10 MCQs based only on this text."}
        ]
    )
    raw = response.choices[0].message.content
    questions = parse_questions(raw)
    session["questions"] = questions
    session["current"] = 0
    session["score"] = 0
    session["total"] = len(questions)
    return redirect(url_for("question"))
    @app.route("/question", methods=["GET", "POST"])
def question():
    if "questions" not in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        selected = request.form.get("selected")
        current = session["current"]
        q = session["questions"][current]
        correct = q["answer"]
        is_correct = selected == correct
        if is_correct:
            session["score"] += 1
        session["current"] += 1
        session.modified = True
        next_num = session["current"]
        total = session["total"]
        feedback_color = "#238636" if is_correct else "#da3633"
        feedback_text = "✅ Correct!" if is_correct else f"❌ Wrong! Correct answer: {correct}"
        options_html = ""
        for opt in q["options"]:
            letter = opt[0]
            bg = "#238636" if letter == correct else ("#da3633" if letter == selected else "#21262d")
            options_html += f'<div style="background:{bg};padding:12px;border-radius:8px;margin:8px 0;font-size:15px;">{opt}</div>'
        return f"""<!DOCTYPE html><html><head><style>
body{{background-color:#0d1117;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}}
.box{{background-color:#161b22;padding:40px;border-radius:15px;width:600px;}}
h2{{color:#f78166;}}
.feedback{{background:{feedback_color};padding:15px;border-radius:8px;margin:15px 0;font-size:15px;}}
.explanation{{background:#21262d;padding:15px;border-radius:8px;margin:15px 0;font-size:14px;color:#8b949e;}}
.next-btn{{display:block;width:100%;padding:12px;background:#f78166;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;margin-top:15px;text-align:center;text-decoration:none;}}
</style></head><body><div class="box">
<h2>Question {current+1} of {total}</h2>
<p style="font-size:16px;line-height:1.6;">{q["question"]}</p>
{options_html}
<div class="feedback">{feedback_text}</div>
<div class="explanation">💡 {q["explanation"]}</div>
{"<a class='next-btn' href='/question'>Next Question →</a>" if next_num < total else "<a class='next-btn' href='/score'>See Final Score →</a>"}
</div></body></html>"""
    current = session["current"]
    if current >= session["total"]:
        return redirect(url_for("score"))
    q = session["questions"][current]
    total = session["total"]
    options_html = ""
    for opt in q["options"]:
        options_html += f'<button name="selected" value="{opt[0]}" style="display:block;width:100%;padding:12px;background:#21262d;color:white;border:1px solid #30363d;border-radius:8px;margin:8px 0;font-size:15px;cursor:pointer;text-align:left;">{opt}</button>'
    return f"""<!DOCTYPE html><html><head><style>
body{{background-color:#0d1117;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}}
.box{{background-color:#161b22;padding:40px;border-radius:15px;width:600px;}}
h2{{color:#f78166;}}
.timer{{font-size:24px;font-weight:bold;color:#f78166;text-align:right;}}
.progress{{background:#21262d;border-radius:8px;height:8px;margin-bottom:20px;}}
.progress-bar{{background:#f78166;height:8px;border-radius:8px;width:{int((current/total)*100)}%;}}
</style>
<script>
var time = 30;
function countdown(){{
    document.getElementById("timer").innerText = time + "s";
    if(time <= 0){{document.getElementById("autosubmit").click();}}
    time--;
    setTimeout(countdown, 1000);
}}
window.onload = countdown;
</script>
</head><body><div class="box">
<div style="display:flex;justify-content:space-between;align-items:center;">
<h2>Question {current+1} of {total}</h2>
<div class="timer" id="timer">30s</div>
</div>
<div class="progress"><div class="progress-bar"></div></div>
<p style="font-size:16px;line-height:1.6;">{q["question"]}</p>
<form method="POST">
{options_html}
<button id="autosubmit" name="selected" value="" style="display:none;">Auto</button>
</form>
</div></body></html>"""

@app.route("/score")
def score():
    s = session.get("score", 0)
    total = session.get("total", 10)
    topic = session.get("topic", "Unknown")
    percentage = int((s / total) * 100)
    if percentage >= 80:
        grade = "🏆 Excellent"
        color = "#238636"
    elif percentage >= 60:
        grade = "👍 Good"
        color = "#e3b341"
    else:
        grade = "📚 Keep Studying"
        color = "#da3633"
    return f"""<!DOCTYPE html><html><head><style>
body{{background-color:#0d1117;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;}}
.box{{background-color:#161b22;padding:40px;border-radius:15px;width:500px;text-align:center;}}
h1{{color:#f78166;}}
.score{{font-size:60px;font-weight:bold;color:{color};margin:20px 0;}}
.grade{{background:{color};padding:10px 20px;border-radius:20px;font-size:18px;display:inline-block;margin:10px 0;}}
.btn{{display:block;padding:12px;background:#f78166;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;margin-top:20px;text-decoration:none;}}
</style></head><body><div class="box">
<h1>Quiz Complete!</h1>
<p style="color:#8b949e;">Topic: {topic}</p>
<div class="score">{s}/{total}</div>
<div class="grade">{grade}</div>
<p style="color:#8b949e;font-size:14px;">You scored {percentage}%</p>
<a class="btn" href="/">🔄 Start New Quiz</a>
</div></body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
