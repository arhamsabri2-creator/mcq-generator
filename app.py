from flask import Flask, request
import openai
import os
import re

app = Flask(__name__)

SYSTEM_PROMPT = """You are an MCQ generator for Indian judicial services exam preparation.

The user will give you the actual text of a law section and a topic name.
Generate exactly 10 MCQs based ONLY on the text provided — do not use any outside knowledge.

Follow this format STRICTLY for every question — no exceptions:

Q1. Question here
A) Option 1
B) Option 2
C) Option 3
D) Option 4
Answer: A
Explanation: Brief explanation here

Rules:
- Generate exactly 10 questions
- Base questions ONLY on the text provided
- Always use Q1 through Q10
- Always give exactly 4 options
- Always mark the correct answer
- Always give a brief explanation
- Never deviate from the format above"""

@app.route("/", methods=["GET"])
def home():
    return """<!DOCTYPE html><html><head><style>
    body{background-color:#1a1a2e;color:white;font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}
    .box{background-color:#16213e;padding:40px;border-radius:15px;text-align:center;width:600px;}
    h1{color:#e94560;}
    input{width:80%;padding:10px;border-radius:8px;border:none;margin-top:15px;font-size:16px;}
    textarea{width:80%;padding:10px;border-radius:8px;border:none;margin-top:15px;font-size:14px;height:150px;resize:vertical;}
    button{margin-top:15px;padding:10px 30px;background-color:#e94560;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;}
    p{color:#aaa;font-size:14px;}
    </style></head><body><div class="box">
    <h1>⚖️ MCQ Generator</h1>
    <p>Paste the actual text of the law section — get 10 accurate MCQs</p>
    <form action="/generate" method="POST">
    <input type="text" name="topic" placeholder="Topic name — e.g. Section 23 BNSS">
    <br>
    <textarea name="lawtext" placeholder="Paste the actual text of the section here..."></textarea>
    <br>
    <button type="submit">Generate 10 MCQs</button>
    </form></div></body></html>"""

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic")
    lawtext = request.form.get("lawtext")
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Topic: {topic}\n\nLaw Text:\n{lawtext}\n\nGenerate 10 MCQs based only on this text."}
        ]
    )
    raw = response.choices[0].message.content
    questions = re.split(r'Q\d+\.', raw)
    questions = [q.strip() for q in questions if q.strip()]

    cards_html = ""
    for i, q in enumerate(questions):
        lines = q.strip().split("\n")
        question_text = lines[0] if lines else ""
        rest = "<br>".join(lines[1:]) if len(lines) > 1 else ""
        cards_html += f"""
        <div class='card'>
            <p class='qnum'>Question {i+1}</p>
            <p class='qtext'>{question_text}</p>
            <p class='options'>{rest}</p>
        </div>"""

    return f"""<!DOCTYPE html><html><head><style>
    body{{background-color:#1a1a2e;color:white;font-family:Arial;margin:0;padding:20px;}}
    h1{{color:#e94560;text-align:center;}}
    .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;max-width:900px;margin:0 auto;}}
    .card{{background-color:#16213e;padding:20px;border-radius:10px;border-left:4px solid #e94560;}}
    .qnum{{color:#e94560;font-weight:bold;margin:0;}}
    .qtext{{font-size:15px;margin:8px 0;}}
    .options{{font-size:14px;color:#ccc;line-height:1.8;}}
    .back{{display:block;text-align:center;margin:20px auto;color:#e94560;font-size:16px;}}
    </style></head><body>
    <h1>⚖️ MCQs on {topic}</h1>
    <div class='grid'>{cards_html}</div>
    <a class='back' href='/'>Generate More MCQs</a>
    </body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
