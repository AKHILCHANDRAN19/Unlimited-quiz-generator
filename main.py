from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import datetime
import random
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Store questions in memory
questions_db = []

def parse_quiz_text(text):
    """Parse quiz text and return list of question dictionaries"""
    questions = []
    current_question = {}
    options = []
    
    # Split text into lines and clean them
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        # Check if line starts with number followed by dot (new question)
        if re.match(r'^\d+\.', line):
            if current_question:
                current_question['options'] = options
                questions.append(current_question)
            current_question = {'question': line.split('. ', 1)[1]}
            options = []
        # Check if line starts with option marker (a), b), etc.)
        elif re.match(r'^[a-d]\)', line):
            options.append(line.split(') ', 1)[1])
        # Check if line contains answer
        elif line.startswith('Answer:'):
            answer_text = line.split('Answer: ')[1]
            # Extract the actual answer text after the option letter
            answer = answer_text.split(') ')[1] if ') ' in answer_text else answer_text
            current_question['correct'] = answer
    
    # Add the last question
    if current_question:
        current_question['options'] = options
        questions.append(current_question)
    
    return questions

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        quiz_text = request.form.get("quiz_text", "")
        if quiz_text:
            global questions_db
            try:
                questions_db = parse_quiz_text(quiz_text)
                if questions_db:
                    return redirect(url_for('start_quiz'))
                else:
                    error = "No questions could be parsed from the text. Please check the format."
            except Exception as e:
                error = f"Error parsing quiz: {str(e)}"
    return render_template_string(index_template, error=error)

@app.route("/start_quiz", methods=["GET", "POST"])
def start_quiz():
    if not questions_db:
        return redirect(url_for('index'))
    
    session['score'] = 0
    session['current_question'] = 0
    session['start_time'] = datetime.now().timestamp()
    session['quiz_questions'] = questions_db.copy()
    return redirect(url_for('quiz'))

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if 'current_question' not in session or not questions_db:
        return redirect(url_for('index'))
        
    if request.method == "POST":
        answer = request.form.get('answer')
        current_q = session['quiz_questions'][session['current_question']]
        
        if answer == current_q['correct']:
            session['score'] += 1
            
        session['current_question'] += 1
        
        if session['current_question'] >= len(session['quiz_questions']):
            end_time = datetime.now().timestamp()
            time_taken = int(end_time - session['start_time'])
            return render_template_string(
                final_template,
                score=session['score'],
                total=len(session['quiz_questions']),
                time_taken=time_taken
            )
    
    if session['current_question'] >= len(session['quiz_questions']):
        return redirect(url_for('index'))
        
    question = session['quiz_questions'][session['current_question']]
    return render_template_string(
        quiz_template,
        question=question,
        current=session['current_question'] + 1,
        total=len(session['quiz_questions']),
        score=session['score']
    )

index_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Quiz Parser</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 16px;
            line-height: 1.5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #1a1a1a;
            margin-bottom: 24px;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        .btn {
            background: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        .btn:hover {
            background: #45a049;
        }
        .error {
            color: #dc3545;
            padding: 10px;
            margin-bottom: 16px;
            border: 1px solid #dc3545;
            border-radius: 4px;
            background: #ffe6e6;
        }
        .instructions {
            background: #f8f9fa;
            padding: 16px;
            border-radius: 4px;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Quiz Parser</h1>
        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}
        <div class="instructions">
            <h3>Paste your quiz in this format:</h3>
            <pre>
1. Question text
a) Option 1
b) Option 2
c) Option 3
d) Option 4
Answer: d) Correct answer text
            </pre>
        </div>
        <form method="POST">
            <textarea name="quiz_text" placeholder="Paste your quiz text here..." required></textarea>
            <button type="submit" class="btn">Create Quiz</button>
        </form>
    </div>
</body>
</html>
"""

quiz_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Quiz</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 16px;
            line-height: 1.5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .progress {
            margin-bottom: 20px;
            text-align: center;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }
        .progress-bar-fill {
            height: 100%;
            background: #4CAF50;
            width: {{ (current / total) * 100 }}%;
        }
        .question {
            margin: 20px 0;
        }
        .score {
            text-align: center;
            color: #4CAF50;
            font-weight: bold;
            margin-bottom: 16px;
        }
        .option-btn {
            display: block;
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            text-align: left;
            background: white;
            border: 1px solid #4CAF50;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        .option-btn:hover {
            background: #4CAF50;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="progress">
            <p>Question {{ current }} of {{ total }}</p>
            <div class="progress-bar">
                <div class="progress-bar-fill"></div>
            </div>
        </div>
        <div class="score">
            Score: {{ score }} / {{ current - 1 if current > 1 else 0 }}
        </div>
        <div class="question">
            <h2>{{ question.question }}</h2>
            <form method="POST">
                {% for option in question.options %}
                    <button type="submit" name="answer" value="{{ option }}" class="option-btn">
                        {{ option }}
                    </button>
                {% endfor %}
            </form>
        </div>
    </div>
</body>
</html>
"""

final_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Quiz Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 16px;
            line-height: 1.5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #1a1a1a;
        }
        .score-card {
            text-align: center;
            margin: 24px 0;
            padding: 24px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .score-text {
            font-size: 24px;
            color: #1a1a1a;
            margin: 16px 0;
        }
        .time-taken {
            color: #666;
            margin: 16px 0;
        }
        .performance {
            font-size: 18px;
            margin: 16px 0;
            padding: 12px;
            border-radius: 4px;
        }
        .excellent {
            background: #d4edda;
            color: #155724;
        }
        .good {
            background: #fff3cd;
            color: #856404;
        }
        .needs-improvement {
            background: #f8d7da;
            color: #721c24;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            font-size: 16px;
            color: white;
            background: #4CAF50;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            box-sizing: border-box;
        }
        .btn:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Quiz Complete!</h1>
        <div class="score-card">
            <div class="score-text">
                Score: {{ score }} / {{ total }}
            </div>
            <div class="time-taken">
                Time taken: {{ time_taken // 60 }}m {{ time_taken % 60 }}s
            </div>
            <div class="performance {{ 'excellent' if score == total else 'good' if score >= total * 0.7 else 'needs-improvement' }}">
                {% if score == total %}
                    Excellent! Perfect score!
                {% elif score >= total * 0.7 %}
                    Good job! Keep it up!
                {% else %}
                    Keep practicing, you'll improve!
                {% endif %}
            </div>
        </div>
        <a href="{{ url_for('index') }}" class="btn">Try Another Quiz</a>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
