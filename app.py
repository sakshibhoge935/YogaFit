import os
import json
import random
from datetime import datetime
from flask import Flask, request, redirect, render_template_string, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, flash, url_for

app = Flask(__name__)
app.secret_key = "yogora_super_secret_key_123"

# ================= DATABASE =================
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'yogafit.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Default Local User ID since login is removed
LOCAL_USER_ID = 1

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=LOCAL_USER_ID)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)

class Steps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=LOCAL_USER_ID)
    steps = db.Column(db.Integer)

class Water(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=LOCAL_USER_ID)
    glasses = db.Column(db.Integer)

class Sleep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=LOCAL_USER_ID)
    hours = db.Column(db.Float)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=LOCAL_USER_ID)
    target = db.Column(db.Float)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, default=LOCAL_USER_ID)
    exercise_id = db.Column(db.String(50), nullable=False)

class CustomWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, default=LOCAL_USER_ID)
    category = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10), default="✨")
    name = db.Column(db.String(100), nullable=False)
    reps = db.Column(db.String(50), nullable=False)
    mins = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# ================= UI & THEMING =================
BASE_STYLE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YogaFit</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<style>
    :root {
        --bg-cream: #FEFCF5; 
        --header-olive: #8F9B69; 
        --header-olive-dark: #778353;
        --card-bg: #FFFFFF;
        --text-dark: #3A3A3A;
        --text-muted: #7A7A7A;
        --border-soft: #E6E2D6;
    }
    body { background-color: var(--bg-cream); color: var(--text-dark); font-family: 'Lato', sans-serif; min-height: 100vh; }
    h1, h2, h3, h4, h5, .serif-font { font-family: 'Playfair Display', serif; color: var(--text-dark); }
    .navbar { background-color: var(--header-olive); padding: 1.2rem 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .navbar-brand { font-weight: 700; color: #FFFFFF !important; font-size: 1.8rem; letter-spacing: 1px; font-family: 'Playfair Display', serif; }
    .nav-link { color: rgba(255,255,255,0.85) !important; transition: 0.3s; font-weight: 400; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px;}
    .nav-link:hover { color: #FFFFFF !important; }
    .card { background: var(--card-bg); border: 1px solid var(--border-soft); border-radius: 12px; padding: 30px; margin-top: 20px; box-shadow: 0 8px 24px rgba(143, 155, 105, 0.08); transition: all 0.3s ease; }
    .card-hover:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(143, 155, 105, 0.15); border-color: var(--header-olive); cursor: pointer; }
    .form-control, .form-select { background: #FAFAFA; border: 1px solid var(--border-soft); color: var(--text-dark); border-radius: 8px; padding: 12px; margin-bottom: 15px; }
    .form-control:focus, .form-select:focus { background: #FFFFFF; border-color: var(--header-olive); box-shadow: 0 0 0 3px rgba(143, 155, 105, 0.2); }
    .btn-success { background-color: var(--header-olive); color: #ffffff; border: none; border-radius: 30px; padding: 10px 25px; font-weight: 600; width: 100%; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem; transition: 0.3s; }
    .btn-success:hover { background-color: var(--header-olive-dark); transform: translateY(-2px); box-shadow: 0 5px 15px rgba(143, 155, 105, 0.3); }
    .stat-highlight { color: var(--header-olive); font-family: 'Playfair Display', serif; font-size: 3.5rem; line-height: 1; }
    .emoji-icon { font-size: 2.2rem; margin-bottom: 12px; }
    .list-styled li { background: var(--bg-cream); margin-bottom: 12px; padding: 15px 20px; border-radius: 10px; border: 1px solid var(--border-soft); list-style: none; display: flex; align-items: center; gap: 15px; }
</style>
</head>
<body>
"""

def render_page(content, show_nav=True):
    nav = f"""
    <nav class="navbar navbar-expand-lg mb-4">
        <a class="navbar-brand" href="/"><span style="font-size: 1.2rem; margin-right: 8px;">🪷</span>YogaFit</a>
        <div class="ms-auto d-flex align-items-center">
            <span class="text-white me-3 d-none d-md-block small">Hi, {session.get('username', 'User')}</span>
            <a href="/" class="nav-link me-3 d-none d-md-block">Home</a>
            <a href="/profile" class="nav-link me-3 d-none d-md-block">Profile</a>
            <a href="/logout" class="nav-link"><i class="bi bi-box-arrow-right"></i> Logout</a>
        </div>
    </nav>
    """ if show_nav and 'user_id' in session else ""
    return BASE_STYLE + nav + '<div class="container pb-5">' + content + "</div></body></html>"


# ================= MAIN DASHBOARD =================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    
    # Fetch latest data for overview
    latest_steps = Steps.query.filter_by(user_id=LOCAL_USER_ID).order_by(Steps.id.desc()).first()
    latest_water = Water.query.filter_by(user_id=LOCAL_USER_ID).order_by(Water.id.desc()).first()
    latest_sleep = Sleep.query.filter_by(user_id=LOCAL_USER_ID).order_by(Sleep.id.desc()).first()
    
    s_val = latest_steps.steps if latest_steps else 0
    w_val = latest_water.glasses if latest_water else 0
    sl_val = latest_sleep.hours if latest_sleep else 0

    hero_banner = """
    <div class="hero-section mb-4 rounded-4 overflow-hidden position-relative" style="background-image: url('https://images.unsplash.com/photo-1545205597-3d9d02c29597?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center; padding: 60px 20px; text-align: center;">
        <div class="position-absolute top-0 start-0 w-100 h-100" style="background: linear-gradient(to bottom, rgba(254, 252, 245, 0.4), rgba(254, 252, 245, 0.8));"></div>
        <div class="position-relative" style="z-index: 1;">
            <p style="font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.2rem; color: #5a6341; margin-bottom: 5px;">welcome back to your sanctuary</p>
            <h1 style="font-family: 'Playfair Display', serif; color: #3A3A3A; font-weight: 700; font-size: 2.5rem;">Witness the Ethereal Beauty</h1>
        </div>
    </div>
    """

    overview_html = f"""
    <h5 class="fw-bold text-muted mb-3 ps-2">Today's Overview</h5>
    <div class="row g-3 mb-5">
        <div class="col-4"><div class="card p-3 text-center border-0 shadow-sm" style="background: #e0f7fa;"><div class="fs-3 mb-1">💧</div><h3 class="mb-0 fw-bold">{w_val}</h3><small class="text-muted fw-bold" style="font-size: 0.7rem;">GLASSES</small></div></div>
        <div class="col-4"><div class="card p-3 text-center border-0 shadow-sm" style="background: #f1f8e9;"><div class="fs-3 mb-1">👣</div><h3 class="mb-0 fw-bold">{s_val}</h3><small class="text-muted fw-bold" style="font-size: 0.7rem;">STEPS</small></div></div>
        <div class="col-4"><div class="card p-3 text-center border-0 shadow-sm" style="background: #ede7f6;"><div class="fs-3 mb-1">🛌</div><h3 class="mb-0 fw-bold">{sl_val}</h3><small class="text-muted fw-bold" style="font-size: 0.7rem;">HOURS</small></div></div>
    </div>
    <h5 class="fw-bold text-muted mb-3 ps-2">Explore Modules</h5>
    """

    modules = [
        ("Diet Plan", "/diet", "🥗"), ("Workout", "/yoga", "🧘"), 
        ("Analytics", "/analytics", "📊"), ("Steps", "/activity", "👣"), 
        ("Water", "/water", "💧"), ("Sleep", "/sleep", "🛌"), 
        ("Goals", "/goals", "🎯"), ("Yoga Library", "/library", "📚"),
        ("Insights", "/insights", "🧠"), ("Routine", "/routine", "📅"), 
        ("Profile", "/profile", "👤"), ("Calories", "/calories", "🔥"), 
        ("Trophies", "/achievements", "🏆"), ("Reminders", "/reminders", "🔔"), 
        ("Export Data", "/export/data", "📥")
    ]
    
    grid_html = "".join([f'<div class="col-6 col-md-4 col-lg-3"><a href="{link}" style="text-decoration:none; color:inherit;"><div class="card card-hover text-center h-100 p-4 shadow-sm border-0"><div class="emoji-icon">{emoji}</div><h5 class="mb-0 text-dark font-weight-bold" style="font-size: 1rem;">{title}</h5></div></a></div>' for title, link, emoji in modules])

    return render_page(hero_banner + overview_html + f"<div class='row g-3'>{grid_html}</div>")
# ================= AUTHENTICATION =================

@app.before_request
def protect_routes():
    # List of routes that don't require login
    allowed_routes = ['login', 'register', 'static']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))
    
    # Dynamically set the LOCAL_USER_ID for your existing queries
    if 'user_id' in session:
        global LOCAL_USER_ID
        LOCAL_USER_ID = session['user_id']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        if User.query.filter_by(username=username).first():
            return render_page("<div class='alert alert-danger'>Username already exists!</div>", show_nav=False)
        
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_page("""
    <div class="row justify-content-center mt-5"><div class="col-md-4"><div class="card p-4">
        <h2 class="text-center mb-4">Register</h2>
        <form method="POST">
            <input name="username" class="form-control" placeholder="Username" required>
            <input name="password" type="password" class="form-control" placeholder="Password" required>
            <button class="btn btn-success">Create Account</button>
        </form>
        <p class="mt-3 text-center small">Already have an account? <a href="/login">Login here</a></p>
    </div></div></div>""", show_nav=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        return render_page("<div class='alert alert-danger'>Invalid credentials!</div>", show_nav=False)

    return render_page("""
    <div class="row justify-content-center mt-5"><div class="col-md-4"><div class="card p-4">
        <h2 class="text-center mb-4">Login</h2>
        <form method="POST">
            <input name="username" class="form-control" placeholder="Username" required>
            <input name="password" type="password" class="form-control" placeholder="Password" required>
            <button class="btn btn-success">Login</button>
        </form>
        <p class="mt-3 text-center small">New user? <a href="/register">Register here</a></p>
    </div></div></div>""", show_nav=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================= SMART TRACKER ENGINE =================
def render_tracker(title, emoji, unit, db_model, field_name, input_name, daily_goal=None, tip=""):
    error_msg = ""
    
    if request.method == 'POST':
        try:
            input_val = float(request.form[input_name])
            new_entry = db_model(user_id=LOCAL_USER_ID, **{field_name: input_val})
            db.session.add(new_entry)
            db.session.commit()
        except ValueError:
            error_msg = "<div class='alert alert-danger py-2 mt-3 small rounded-3'>⚠️ Please enter a valid number.</div>"

    history_data = db_model.query.filter_by(user_id=LOCAL_USER_ID).order_by(db_model.id.desc()).limit(7).all()
    
    chart_values, chart_labels = [], []
    if history_data:
        chrono_data = list(reversed(history_data))
        chart_values = [getattr(item, field_name) for item in chrono_data]
        chart_labels = [f"Log {i+1}" for i in range(len(chrono_data))]
    
    last_val = chart_values[-1] if chart_values else 0
    display_val = int(last_val) if float(last_val).is_integer() else last_val

    # Smart Feedback
    feedback_html = ""
    if last_val > 0:
        msg, color = "", "info"
        if title == "Hydration":
            if last_val < 4: msg, color = "You are dehydrated. Drink up! 🏜️", "danger"
            elif last_val >= 8: msg, color = "Perfectly hydrated! 🌊", "success"
            else: msg, color = "Almost there, keep sipping! 💧", "warning"
        elif title == "Sleep Tracker":
            if last_val < 6: msg, color = "You need more rest for recovery! 🥱", "danger"
            elif last_val >= 7: msg, color = "Great sleep! Fully charged. 🔋", "success"
        elif title == "Steps Tracker":
            if last_val >= 10000: msg, color = "Goal crushed! Amazing job! 🏃‍♂️", "success"
            elif last_val >= 5000: msg, color = "Good active day! 🚶", "info"
        if msg:
            feedback_html = f"<div class='alert alert-{color} mt-3 py-2 small fw-bold rounded-pill border-0 shadow-sm'>{msg}</div>"

    progress_html = ""
    if daily_goal and last_val > 0:
        pct = min(int((last_val / daily_goal) * 100), 100)
        p_color = "success" if pct >= 100 else "warning" if pct > 50 else "info"
        progress_html = f"""
        <div class="mt-4 text-start">
            <div class="d-flex justify-content-between small text-muted mb-2 fw-bold text-uppercase" style="font-size: 0.75rem;">
                <span>Daily Goal: {daily_goal} {unit}</span><span class="text-{p_color}">{pct}%</span>
            </div>
            <div class="progress rounded-pill shadow-sm" style="height: 12px; background-color: var(--border-soft);">
                <div class="progress-bar bg-{p_color} rounded-pill progress-bar-striped progress-bar-animated" style="width: {pct}%;"></div>
            </div>
        </div>
        """

    chart_html = ""
    if len(chart_values) > 1:
        chart_html = f"""
        <div class="mt-4 pt-3 border-top border-light">
            <h6 class="text-muted fw-bold small text-uppercase mb-3 text-start">7-Day Trend</h6>
            <canvas id="trackerChart" height="150"></canvas>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                new Chart(document.getElementById('trackerChart').getContext('2d'), {{
                    type: 'line',
                    data: {{ labels: {json.dumps(chart_labels)}, datasets: [{{ label: '{title}', data: {json.dumps(chart_values)}, borderColor: '#8F9B69', backgroundColor: 'rgba(143, 155, 105, 0.2)', fill: true, tension: 0.4, pointBackgroundColor: '#fff', pointRadius: 4 }}] }},
                    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ display: false }} }}, x: {{ grid: {{ display: false }} }} }} }}
                }});
            }});
        </script>
        """

    tip_html = f"<div class='alert alert-info mt-3 small text-start shadow-sm border-0'><i class='bi bi-lightbulb-fill text-warning me-2'></i> <b>Pro Tip:</b> {tip}</div>" if tip else ""

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
            <div class='card text-center p-4 shadow-sm border-0' style="border-top: 5px solid var(--header-olive) !important;">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h4 class="mb-0 fw-bold">{title}</h4>
                    <span class="badge bg-light text-dark border shadow-sm">🔥 Streak: {len(chart_values)}</span>
                </div>
                <div class="emoji-icon" style="font-size: 3.5rem;">{emoji}</div>
                <div class="my-3"><span class="stat-highlight">{display_val}</span> <span class="fs-5 text-muted">{unit}</span></div>
                {feedback_html}
                {tip_html}
                <form method='POST' class="mt-4">
                    <div class="input-group input-group-lg shadow-sm">
                        <input name='{input_name}' type="number" step="0.1" class='form-control border-0 bg-light' placeholder='Log new amount...' required>
                        <button class='btn btn-success px-4' style="border-radius: 0 8px 8px 0;">Log</button>
                    </div>
                    {error_msg}
                </form>
                {progress_html}
                {chart_html}
            </div>
        </div>
    </div>
    """)

# ================= TRACKER ROUTES =================
HEALTH_TIPS = {
    "activity": ["Take a 10-minute walk after meals to aid digestion.", "Take the stairs instead of the elevator today!", "Aim for at least 250 steps every hour to avoid sedentary stiffness."],
    "water": ["Drink a glass of water immediately after waking up.", "Sometimes thirst disguises itself as hunger. Drink water before snacking!", "Keep a reusable water bottle at your desk."],
    "sleep": ["Avoid screens 30 minutes before bed to improve sleep quality.", "Keep your bedroom cool, dark, and quiet.", "Try to go to sleep and wake up at the exact same time every day."]
}

@app.route('/activity', methods=['GET','POST'])
def activity():
    return render_tracker("Steps Tracker", "👣", "steps", Steps, "steps", "s", 10000, random.choice(HEALTH_TIPS["activity"]))

@app.route('/water', methods=['GET','POST'])
def water():
    profile = Profile.query.filter_by(user_id=LOCAL_USER_ID).first()
    dynamic_goal = int((profile.weight * 0.033 * 1000) / 250) if profile and profile.weight else 8
    return render_tracker("Hydration", "💧", "glasses", Water, "glasses", "g", dynamic_goal, random.choice(HEALTH_TIPS["water"]))

@app.route('/sleep', methods=['GET','POST'])
def sleep():
    return render_tracker("Sleep Tracker", "🛌", "hours", Sleep, "hours", "h", 8.0, random.choice(HEALTH_TIPS["sleep"]))

@app.route('/goals', methods=['GET','POST'])
def goals():
    profile = Profile.query.filter_by(user_id=LOCAL_USER_ID).first()
    tip = f"Based on your height, an optimal target weight is ~{round(22.0 * ((profile.height/100)**2), 1)}kg." if profile and profile.height else "Set a realistic and healthy target!"
    return render_tracker("Target Weight", "🎯", "kg", Goal, "target", "g", tip=tip)

# ================= WORKOUT & YOGA ROUTES =================
@app.route('/update_progress', methods=['POST'])
def update_progress():
    data = request.json
    exercise_id, is_checked = data.get('exercise_id'), data.get('completed')
    existing_record = Progress.query.filter_by(user_id=LOCAL_USER_ID, exercise_id=exercise_id).first()
    if is_checked and not existing_record:
        db.session.add(Progress(user_id=LOCAL_USER_ID, exercise_id=exercise_id))
    elif not is_checked and existing_record:
        db.session.delete(existing_record)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/add_workout', methods=['POST'])
def add_workout():
    data = request.json
    db.session.add(CustomWorkout(user_id=LOCAL_USER_ID, category=data.get('category'), icon=data.get('icon', '✨'), name=data.get('name'), reps=data.get('reps'), mins=int(data.get('mins', 5))))
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/yoga')
def yoga():
    saved_progress = Progress.query.filter_by(user_id=LOCAL_USER_ID).all()
    completed_ids = [record.exercise_id for record in saved_progress]
    custom_workouts = CustomWorkout.query.filter_by(user_id=LOCAL_USER_ID).all()

    workout_plan = {
        "Warmup": [{"id": "w1", "icon": "🌞", "name": "Surya Namaskar", "reps": "12 Rounds", "mins": 5}, {"id": "w2", "icon": "🪢", "name": "Dynamic Stretching", "reps": "Full Body", "mins": 3}],
        "Main Routine": [{"id": "m1", "icon": "💪", "name": "Pushups", "reps": "3 x 15", "mins": 5}, {"id": "m2", "icon": "🦵", "name": "Squats", "reps": "3 x 20", "mins": 5}, {"id": "m3", "icon": "🪵", "name": "Plank", "reps": "60 Sec", "mins": 1}],
        "Cool Down": [{"id": "c1", "icon": "🧘", "name": "Child's Pose", "reps": "Hold", "mins": 2}]
    }

    for cw in custom_workouts:
        if cw.category in workout_plan:
            workout_plan[cw.category].append({"id": f"custom_{cw.id}", "icon": cw.icon, "name": cw.name, "reps": cw.reps, "mins": cw.mins})

    total_time = sum(ex['mins'] for cat in workout_plan.values() for ex in cat)
    total_exercises = sum(len(cat) for cat in workout_plan.values())

    workout_html = ""
    for category, exercises in workout_plan.items():
        workout_html += f"<h5 class='mt-4 mb-3 text-secondary fw-bold'>{category}</h5><ul class='list-group shadow-sm mb-4'>"
        for ex in exercises:
            is_checked = "checked" if ex['id'] in completed_ids else ""
            text_style = "text-decoration: line-through; opacity: 0.5;" if is_checked else ""
            workout_html += f"""
            <li class="list-group-item d-flex justify-content-between align-items-center p-3">
                <div class="d-flex align-items-center form-check m-0 p-0 ps-4">
                    <input class="form-check-input me-3 fs-4 exercise-checkbox" style="margin-left: -1.5em;" type="checkbox" id="{ex['id']}" {is_checked}>
                    <label class="form-check-label d-flex align-items-center w-100" for="{ex['id']}" style="cursor: pointer;">
                        <span class="fs-3 me-3">{ex['icon']}</span>
                        <div class="exercise-text" style="{text_style}">
                            <h6 class="mb-0 fw-bold text-dark">{ex['name']}</h6><small class="text-muted"><i class="bi bi-clock"></i> ~{ex['mins']} mins</small>
                        </div>
                    </label>
                </div>
                <span class="badge bg-dark rounded-pill px-3 py-2">{ex['reps']}</span>
            </li>"""
        workout_html += "</ul>"

    header_html = f"""
    <div class="position-relative mb-4 rounded-4 overflow-hidden shadow-sm" style="height: 180px; background-image: url('https://images.unsplash.com/photo-1599901860904-17e082b4df01?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center;">
        <div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0.2));"></div>
        <div class="position-absolute bottom-0 start-0 p-4 text-white w-100">
            <h2 class="fw-bolder mb-1 text-white">Daily Routine</h2>
            <div class="d-flex justify-content-between align-items-end"><p class="mb-0 opacity-75">{total_exercises} Exercises • {total_time} Min Total</p><span id="progress-text" class="fw-bold fs-5">0%</span></div>
            <div class="progress mt-2" style="height: 8px; background-color: rgba(255,255,255,0.2);"><div id="workout-progress" class="progress-bar bg-success" style="width: 0%;"></div></div>
        </div>
    </div>
    """

    modal_html = """
    <button class="btn btn-success btn-lg rounded-circle shadow-lg position-fixed bottom-0 end-0 m-4 d-flex align-items-center justify-content-center" style="width: 60px; height: 60px; z-index: 1000;" data-bs-toggle="modal" data-bs-target="#addWorkoutModal"><span class="fs-2 text-white" style="line-height: 1; margin-top: -4px;">+</span></button>
    <div class="modal fade" id="addWorkoutModal" tabindex="-1" aria-hidden="true"><div class="modal-dialog modal-dialog-centered"><div class="modal-content rounded-4 border-0 shadow-lg">
        <div class="modal-header border-0 pb-0"><h5 class="modal-title fw-bold">Add Custom Exercise</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
            <form id="addWorkoutForm">
                <div class="mb-3"><label class="form-label text-muted small fw-bold">Category</label><select class="form-select bg-light border-0" id="newCategory"><option value="Warmup">Warmup</option><option value="Main Routine" selected>Main Routine</option><option value="Cool Down">Cool Down</option></select></div>
                <div class="mb-3"><label class="form-label text-muted small fw-bold">Exercise Name</label><input type="text" class="form-control bg-light border-0" id="newName" placeholder="e.g., Jumping Jacks" required></div>
                <div class="row"><div class="col-6 mb-3"><label class="form-label text-muted small fw-bold">Reps / Time</label><input type="text" class="form-control bg-light border-0" id="newReps" placeholder="e.g., 3 x 15" required></div><div class="col-6 mb-3"><label class="form-label text-muted small fw-bold">Est. Minutes</label><input type="number" class="form-control bg-light border-0" id="newMins" placeholder="5" required></div></div>
                <button type="submit" class="btn btn-success w-100 rounded-pill mt-3 shadow-sm">Save Exercise</button>
            </form>
        </div>
    </div></div></div>
    """

    js_logic = """
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const checkboxes = document.querySelectorAll('.exercise-checkbox');
            const progressBar = document.getElementById('workout-progress');
            const progressText = document.getElementById('progress-text');
            function updateProgressBar() {
                if (checkboxes.length === 0) return;
                const pct = Math.round((document.querySelectorAll('.exercise-checkbox:checked').length / checkboxes.length) * 100);
                progressBar.style.width = pct + '%'; progressText.innerText = pct + '%';
            }
            updateProgressBar();
            checkboxes.forEach(box => {
                box.addEventListener('change', function() {
                    updateProgressBar();
                    const textDiv = this.nextElementSibling.querySelector('.exercise-text');
                    textDiv.style.textDecoration = this.checked ? 'line-through' : 'none';
                    textDiv.style.opacity = this.checked ? '0.5' : '1';
                    fetch('/update_progress', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exercise_id: this.id, completed: this.checked }) });
                });
            });
            document.getElementById('addWorkoutForm').addEventListener('submit', function(e) {
                e.preventDefault();
                fetch('/add_workout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: document.getElementById('newCategory').value, name: document.getElementById('newName').value, reps: document.getElementById('newReps').value, mins: document.getElementById('newMins').value, icon: "✨" }) })
                .then(r => r.json()).then(data => { if(data.status === "success") window.location.reload(); });
            });
        });
    </script>
    """

    return render_page(f"<div class='row justify-content-center'><div class='col-lg-6 col-md-8'>{header_html}<div class='px-2'>{workout_html}</div><div class='mt-4 mb-5 text-center px-2'><button class='btn btn-success btn-lg w-100 rounded-pill shadow fw-bold' onclick='alert(\"Great job finishing your workout! 🎉\")'>Complete Workout</button></div></div></div>{modal_html}{js_logic}")

# ================= TOOLS (Diet, Profile, Calories) =================
@app.route('/profile', methods=['GET','POST'])
def profile():
    up = Profile.query.filter_by(user_id=LOCAL_USER_ID).first()
    if request.method == 'POST':
        if up:
            up.age, up.gender, up.height, up.weight = request.form['age'], request.form['gender'], request.form['height'], request.form['weight']
        else:
            db.session.add(Profile(user_id=LOCAL_USER_ID, age=request.form['age'], gender=request.form['gender'], height=request.form['height'], weight=request.form['weight']))
        db.session.commit()
        return redirect('/dashboard')
    return render_page(f"""
    <div class="row justify-content-center"><div class="col-md-6"><div class='card'>
        <div class="text-center mb-4"><div class="emoji-icon">👤</div><h2>Your Profile</h2></div>
        <form method='POST'>
            <input name='age' value="{up.age if up else ''}" class='form-control' placeholder="Age" required>
            <input name='gender' value="{up.gender if up else ''}" class='form-control' placeholder="Gender (M/F)" required>
            <input name='height' value="{up.height if up else ''}" class='form-control' placeholder="Height (cm)" required>
            <input name='weight' value="{up.weight if up else ''}" class='form-control' placeholder="Weight (kg)" required>
            <button class='btn btn-success mt-3'>Save</button>
        </form>
    </div></div></div>
    """)

@app.route('/diet', methods=['GET','POST'])
def diet():
    result = ""
    if request.method == 'POST':
        w = float(request.form['w'])
        h_cm = float(request.form['h'])
        h_m = h_cm / 100
        age = int(request.form['age'])
        gender = request.form['gender'].upper()
        activity = float(request.form['activity'])
        food_type = request.form['food_type']

        bmi = round(w / (h_m * h_m), 1)

        if bmi < 18.5:
            bmi_status, advice = "Underweight ⚠️", "Increase calorie intake and focus on protein-rich foods."
            plan, target_cals = "Weight Gain 🍞", int(((10*w)+(6.25*h_cm)-(5*age)+ (5 if gender=='M' else -161))*activity) + 500
            if food_type == "veg":
                meals = "🍳 Breakfast: Milk + Banana + Dry Fruits<br>🍛 Lunch: Rice + Dal + Paneer<br>🥜 Snacks: Peanut Butter + Bread<br>🍲 Dinner: Roti + Sabzi + Curd"
            else:
                meals = "🍳 Breakfast: Eggs + Milk + Banana<br>🍛 Lunch: Rice + Chicken + Dal<br>🥜 Snacks: Boiled Eggs<br>🍲 Dinner: Roti + Chicken Curry"
        elif bmi < 25:
            bmi_status, advice = "Normal ✅", "Maintain balanced diet."
            plan, target_cals = "Maintenance 🥗", int(((10*w)+(6.25*h_cm)-(5*age)+ (5 if gender=='M' else -161))*activity)
            if food_type == "veg":
                meals = "🍳 Breakfast: Poha / Upma<br>🍛 Lunch: Roti + Sabzi + Dal<br>🍌 Snacks: Fruits + Nuts<br>🍲 Dinner: Light Veg Meal"
            else:
                meals = "🍳 Breakfast: Omelette + Toast<br>🍛 Lunch: Roti + Chicken<br>🍌 Snacks: Fruits + Eggs<br>🍲 Dinner: Chicken Soup + Salad"
        else:
            bmi_status, advice = "Overweight/Obese ❗", "Follow strict diet and reduce calories."
            plan, target_cals = "Weight Loss 🥦", int(((10*w)+(6.25*h_cm)-(5*age)+ (5 if gender=='M' else -161))*activity) - 500
            if food_type == "veg":
                meals = "🥣 Breakfast: Oats + Fruits<br>🥗 Lunch: Salad + Dal + 1 Roti<br>🍎 Snacks: Nuts<br>🥦 Dinner: Veg Soup"
            else:
                meals = "🥣 Breakfast: Boiled Eggs<br>🥗 Lunch: Grilled Chicken + Salad<br>🍎 Snacks: Egg Whites<br>🥦 Dinner: Chicken Soup"

        protein = int(w * 2.2)
        fat = int((target_cals * 0.25) / 9)
        carbs = int((target_cals - (protein * 4) - (fat * 9)) / 4)
        water = round(w * 0.033, 2)
        food_label = "Vegetarian 🥗" if food_type == "veg" else "Non-Vegetarian 🍗"

        result = f"""
        <div class="row text-center mt-4 g-2">
            <div class="col-6"><div class="p-3 border rounded"><h6>BMI</h6><h4>{bmi}</h4></div></div>
            <div class="col-6"><div class="p-3 border rounded"><h6>TDEE</h6><h4>{target_cals + (500 if plan=="Weight Loss 🥦" else -500 if plan=="Weight Gain 🍞" else 0)}</h4></div></div>
        </div>
        <div class="mt-2 text-center"><h6>Diet Type: {food_label}</h6></div>
        <div class="alert mt-3 text-center"><h5>{bmi_status}</h5><p>{advice}</p></div>
        <div class="alert text-center"><h4>{plan}</h4><h2>{target_cals} kcal/day</h2></div>
        <h5 class="text-center mt-3">Macros</h5>
        <div class="row text-center">
            <div class="col-4"><b>Protein</b><br>{protein}g</div>
            <div class="col-4"><b>Carbs</b><br>{carbs}g</div>
            <div class="col-4"><b>Fats</b><br>{fat}g</div>
        </div>
        <div class="mt-3 p-3 border rounded"><h5>🍽️ Meal Plan</h5>{meals}</div>
        <div class="mt-3 p-3 border rounded"><h6>💧 Water Intake: {water} L/day</h6></div>
        """

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
            <div class='card p-3 shadow'>
                <div class="text-center mb-4"><div style="font-size:40px;">🥗</div><h2>Smart Nutrition Planner</h2></div>
                <form method='POST'>
                    <div class="row g-2 mb-2">
                        <div class="col-6">
                            <select name="gender" class="form-control" required>
                                <option value="" disabled selected>Gender</option>
                                <option value="M">Male</option>
                                <option value="F">Female</option>
                            </select>
                        </div>
                        <div class="col-6"><input name='age' type="number" placeholder="Age" class='form-control' required></div>
                        <div class="col-6"><input name='w' type="number" step="0.1" placeholder="Weight (kg)" class='form-control' required></div>
                        <div class="col-6"><input name='h' type="number" placeholder="Height (cm)" class='form-control' required></div>
                        <div class="col-12">
                            <select name="activity" class="form-control" required>
                                <option value="" disabled selected>Activity Level</option>
                                <option value="1.2">Sedentary</option>
                                <option value="1.375">Lightly Active</option>
                                <option value="1.55">Moderately Active</option>
                                <option value="1.725">Heavy Active</option>
                            </select>
                        </div>
                        <div class="col-12">
                            <select name="food_type" class="form-control" required>
                                <option value="" disabled selected>Food Preference</option>
                                <option value="veg">Vegetarian 🥗</option>
                                <option value="nonveg">Non-Vegetarian 🍗</option>
                            </select>
                        </div>
                    </div>
                    <button class='btn btn-success w-100 mt-2'>Generate Plan</button>
                </form>
                {result}
            </div>
        </div>
    </div>
    """)

@app.route('/calories', methods=['GET','POST'])
def calories():
    res = f"<h1 class='stat-highlight mt-4'>{int(request.form['t'])*5} kcal</h1>" if request.method == 'POST' else ""
    return render_page(f"""
    <div class="row justify-content-center"><div class="col-md-5"><div class='card text-center'>
        <div class="emoji-icon">🔥</div><h2>Burn Calc</h2><p class="text-muted">Workout minutes</p>
        <form method='POST'><input name='t' type="number" class='form-control text-center' required><button class='btn btn-success mt-2'>Calculate</button></form>{res}
    </div></div></div>""")

# ================= ADVANCED FEATURES (Analytics, Export) =================
@app.route('/analytics')
def analytics():
    steps_data, water_data, sleep_data = Steps.query.filter_by(user_id=LOCAL_USER_ID).all(), Water.query.filter_by(user_id=LOCAL_USER_ID).all(), Sleep.query.filter_by(user_id=LOCAL_USER_ID).all()
    
    total_steps = sum([s.steps for s in steps_data]) if steps_data else 0
    avg_steps = int(total_steps / len(steps_data)) if steps_data else 0
    total_water = sum([w.glasses for w in water_data]) if water_data else 0
    avg_water = round(total_water / len(water_data), 1) if water_data else 0
    avg_sleep = round(sum([s.hours for s in sleep_data]) / len(sleep_data), 1) if sleep_data else 0

    return render_page(f"""
    <div class="row justify-content-center"><div class="col-lg-8"><div class='card shadow-sm border-0' style="border-top: 5px solid var(--header-olive);">
        <div class="text-center mb-4"><div class="emoji-icon">📊</div><h2 class="fw-bold">Health Analytics</h2><p class="text-muted">Lifetime wellness trends</p></div>
        <div class="row g-3 text-center">
            <div class="col-md-4"><div class="p-3 border rounded bg-light h-100"><h6 class="text-muted text-uppercase small fw-bold">Avg Daily Steps</h6><h2 class="text-dark mb-0">{avg_steps}</h2><small class="text-success">Total: {total_steps}</small></div></div>
            <div class="col-md-4"><div class="p-3 border rounded bg-light h-100"><h6 class="text-muted text-uppercase small fw-bold">Avg Hydration</h6><h2 class="text-dark mb-0">{avg_water} <span class="fs-6">gls</span></h2><small class="text-info">Total: {total_water} gls</small></div></div>
            <div class="col-md-4"><div class="p-3 border rounded bg-light h-100"><h6 class="text-muted text-uppercase small fw-bold">Avg Sleep</h6><h2 class="text-dark mb-0">{avg_sleep} <span class="fs-6">hrs</span></h2><small class="text-primary">Consistency is key</small></div></div>
        </div>
    </div></div></div>
    """)

@app.route('/export/data')
def export_data():
    steps, water = Steps.query.filter_by(user_id=LOCAL_USER_ID).all(), Water.query.filter_by(user_id=LOCAL_USER_ID).all()
    csv_data = "Type,Value,Entry_ID\n"
    for s in steps: csv_data += f"Steps,{s.steps},{s.id}\n"
    for w in water: csv_data += f"Water,{w.glasses},{w.id}\n"
    return Response(csv_data, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=yogora_data.csv"})

# ================= EDUCATIONAL CONTENT =================
@app.route('/library')
def library():
    poses = [
        {"name": "Balasana", "eng": "Child's Pose", "icon": "🧘‍♀️", "desc": "A resting pose that gently stretches the hips and calms the brain."},
        {"name": "Adho Mukha Svanasana", "eng": "Downward Dog", "icon": "🐕", "desc": "Energizes the body, stretches hamstrings, and strengthens arms."},
        {"name": "Vrikshasana", "eng": "Tree Pose", "icon": "🌳", "desc": "Improves balance and focus, strengthens thighs, calves, and spine."},
        {"name": "Savasana", "eng": "Corpse Pose", "icon": "🛌", "desc": "The ultimate relaxation pose. Calms the brain and relieves fatigue."}
    ]
    cards_html = "".join([f'<div class="col-md-6 mb-3"><div class="card h-100 p-3 shadow-sm border-0 border-start border-4" style="border-color: var(--header-olive) !important;"><div class="d-flex align-items-center mb-2"><span class="fs-2 me-3">{p["icon"]}</span><div><h5 class="mb-0 fw-bold">{p["name"]}</h5><small class="text-muted fst-italic">{p["eng"]}</small></div></div><p class="text-muted small mb-0">{p["desc"]}</p></div></div>' for p in poses])
    return render_page(f"<div class='text-center mb-4'><h2>Asana Library</h2><p class='text-muted'>Master the foundations</p></div><div class='row'>{cards_html}</div>")

@app.route('/insights')
def insights():
    return render_page("""<div class="row justify-content-center"><div class="col-md-8"><div class="card p-4 shadow-sm border-0"><div class="text-center mb-4"><div class="emoji-icon">🧠</div><h2 class="fw-bold">Wellness Insights</h2></div><ul class="list-group list-group-flush"><li class="list-group-item bg-transparent py-3"><b>💧 The Hydration Multiplier:</b> Drinking 500ml of water can boost your metabolic rate by 30%.</li><li class="list-group-item bg-transparent py-3"><b>🚶 The 10k Myth:</b> Health benefits rapidly increase starting at just 7,000 steps per day.</li><li class="list-group-item bg-transparent py-3"><b>😴 Circadian Rhythm:</b> Going to sleep at the exact same time every night is crucial for energy.</li></ul></div></div></div>""")

@app.route('/routine')
def routine():
    return render_page("""<div class="row justify-content-center"><div class="col-md-8"><div class="card p-4 shadow-sm border-0"><div class="text-center mb-4"><div class="emoji-icon">📅</div><h2 class="fw-bold">Daily Routine</h2><p class="text-muted">Ayurvedic principles (Dinacharya)</p></div><div class="timeline ps-3" style="border-left: 3px solid var(--border-soft);"><div class="mb-4 position-relative"><span class="position-absolute start-0 translate-middle badge rounded-pill bg-success" style="margin-left: -16px;">06:00</span><h6 class="ms-4 mb-1 fw-bold">Wake Up & Hydrate</h6></div><div class="mb-4 position-relative"><span class="position-absolute start-0 translate-middle badge rounded-pill bg-success" style="margin-left: -16px;">07:00</span><h6 class="ms-4 mb-1 fw-bold">Movement & Asanas</h6></div><div class="mb-4 position-relative"><span class="position-absolute start-0 translate-middle badge rounded-pill bg-success" style="margin-left: -16px;">13:00</span><h6 class="ms-4 mb-1 fw-bold">Largest Meal</h6></div><div class="mb-0 position-relative"><span class="position-absolute start-0 translate-middle badge rounded-pill bg-success" style="margin-left: -16px;">22:00</span><h6 class="ms-4 mb-1 fw-bold">Rest</h6></div></div></div></div></div>""")

@app.route('/achievements')
def achievements(): 
    list_html = "".join([f"<li><h6 class='mb-0 text-dark'>{item}</h6></li>" for item in ["🔥 7 Day Streak", "⭐ Beginner Badge", "💧 Hydration Master"]])
    return render_page(f"<div class='row justify-content-center'><div class='col-md-6'><div class='card text-center'><div class='emoji-icon'>🏆</div><h2>Trophies</h2><ul class='list-styled p-0'>{list_html}</ul></div></div></div>")

@app.route('/reminders')
def reminders(): 
    list_html = "".join([f"<li><h6 class='mb-0 text-dark'>{item}</h6></li>" for item in ["⏰ 08:00 AM - Drink Water", "⏰ 05:00 PM - Evening Exercise", "⏰ 10:00 PM - Wind down for sleep"]])
    return render_page(f"<div class='row justify-content-center'><div class='col-md-6'><div class='card text-center'><div class='emoji-icon'>🔔</div><h2>Reminders</h2><ul class='list-styled p-0'>{list_html}</ul></div></div></div>")

# ================= RUN =================
if __name__ == '__main__':
    print("🚀 Yogora running on http://127.0.0.1:5000")
    app.run(debug=True)
