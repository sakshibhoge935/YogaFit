import os
from datetime import datetime
from flask import Flask, request, redirect, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'yogafit.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)

class Steps(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    steps = db.Column(db.Integer)

class Water(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    glasses = db.Column(db.Integer)

class Sleep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    hours = db.Column(db.Float)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    target = db.Column(db.Float)

with app.app_context():
    db.create_all()

# ================= UI & THEMING (KRIYA YOGA THEME) =================
BASE_STYLE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yogora | Ethereal Beauty</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-cream: #FEFCF5; /* Warm earthy cream background */
        --header-olive: #8F9B69; /* Kriya Olive Green */
        --header-olive-dark: #778353;
        --card-bg: #FFFFFF;
        --text-dark: #3A3A3A;
        --text-muted: #7A7A7A;
        --border-soft: #E6E2D6;
    }

    body { 
        background-color: var(--bg-cream); 
        color: var(--text-dark); 
        font-family: 'Lato', sans-serif; 
        min-height: 100vh;
    }

    h1, h2, h3, h4, h5, .serif-font { 
        font-family: 'Playfair Display', serif; 
        color: var(--text-dark);
    }

    .navbar { 
        background-color: var(--header-olive); 
        padding: 1.2rem 2rem; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .navbar-brand { 
        font-weight: 700; 
        color: #FFFFFF !important; 
        font-size: 1.8rem; 
        letter-spacing: 1px;
        font-family: 'Playfair Display', serif;
    }
    
    .nav-link { color: rgba(255,255,255,0.85) !important; transition: 0.3s; font-weight: 400; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 1px;}
    .nav-link:hover { color: #FFFFFF !important; }

    .btn-outline-light { border-color: rgba(255,255,255,0.5); }
    .btn-outline-light:hover { background-color: #FFFFFF; color: var(--header-olive); }

    .card { 
        background: var(--card-bg); 
        border: 1px solid var(--border-soft); 
        border-radius: 12px; 
        padding: 30px; 
        margin-top: 20px;
        box-shadow: 0 8px 24px rgba(143, 155, 105, 0.08);
        transition: all 0.3s ease; 
    }

    .card-hover:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 12px 30px rgba(143, 155, 105, 0.15);
        border-color: var(--header-olive);
        cursor: pointer;
    }

    .form-control { 
        background: #FAFAFA; 
        border: 1px solid var(--border-soft); 
        color: var(--text-dark); 
        border-radius: 8px; 
        padding: 12px; 
        margin-bottom: 15px;
    }

    .form-control:focus { 
        background: #FFFFFF; 
        border-color: var(--header-olive); 
        box-shadow: 0 0 0 3px rgba(143, 155, 105, 0.2);
    }

    .btn-success { 
        background-color: var(--header-olive); 
        color: #ffffff;
        border: none; 
        border-radius: 30px; 
        padding: 10px 25px; 
        font-weight: 600; 
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.85rem;
        transition: 0.3s; 
    }

    .btn-success:hover { 
        background-color: var(--header-olive-dark); 
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(143, 155, 105, 0.3);
    }

    a.text-link { color: var(--header-olive); text-decoration: none; font-weight: 700; }
    a.text-link:hover { text-decoration: underline; }

    .stat-highlight { 
        color: var(--header-olive); 
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem; 
        line-height: 1;
    }

    .emoji-icon { 
        font-size: 2.2rem; 
        margin-bottom: 12px;
    }

    .list-styled li { 
        background: var(--bg-cream); 
        margin-bottom: 12px; 
        padding: 15px 20px; 
        border-radius: 10px; 
        border: 1px solid var(--border-soft);
        list-style: none; 
        display: flex; 
        align-items: center; 
        gap: 15px; 
    }
    
    /* Smooth Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-cream); }
    ::-webkit-scrollbar-thumb { background: var(--header-olive); border-radius: 10px; }
</style>
</head>
<body>
"""

def render_page(content, show_nav=True):
    nav = """
    <nav class="navbar navbar-expand-lg mb-4">
        <a class="navbar-brand" href="/dashboard">
            <span style="font-size: 1.2rem; margin-right: 8px;">🪷</span>YOGORA
        </a>
        <div class="ms-auto d-flex align-items-center">
            <a href="/dashboard" class="nav-link me-3 d-none d-md-block">Home</a>
            <a href="/profile" class="nav-link me-4 d-none d-md-block">Profile</a>
            <a href="/logout" class="btn btn-outline-light btn-sm rounded-pill px-4 py-2" style="font-weight:600; letter-spacing: 1px; font-size: 0.8rem; text-transform: uppercase;">Logout</a>
        </div>
    </nav>
    """ if show_nav else ""
    return BASE_STYLE + nav + '<div class="container pb-5">' + content + "</div></body></html>"

# ================= AUTH =================
@app.route('/', methods=['GET','POST'])
def login():
    error = ""
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['u']).first()
        if u and check_password_hash(u.password, request.form['p']):
            session['user'] = u.id
            return redirect('/dashboard')
        else:
            error = "<div class='alert alert-danger mt-3 bg-transparent border-danger text-danger rounded-4'>❌ Invalid Username or Password</div>"

    return render_page(f"""
    <div class="row justify-content-center align-items-center" style="min-height: 80vh;">
        <div class="col-md-5 col-lg-4">
            <div class='card text-center' style="border-top: 5px solid var(--header-olive);">
                <div class="emoji-icon mb-2">🪷</div>
                <h2 class="mb-4">Welcome Back</h2>
                <form method='POST'>
                    <input name='u' class='form-control' placeholder='Username' required>
                    <input name='p' type='password' class='form-control' placeholder='Password' required>
                    <button class='btn btn-success mt-3'>Login</button>
                </form>
                {error}
                <p class="mt-4 mb-0 text-muted" style="font-size: 0.9rem;">New here? <a href='/register' class="text-link">Create an account</a></p>
            </div>
        </div>
    </div>
    """, show_nav=False)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db.session.add(User(username=request.form['u'], password=generate_password_hash(request.form['p'])))
        db.session.commit()
        return redirect('/')
    return render_page("""
    <div class="row justify-content-center align-items-center" style="min-height: 80vh;">
        <div class="col-md-5 col-lg-4">
            <div class='card text-center' style="border-top: 5px solid var(--header-olive);">
                <h2 class="mb-4">Begin Your Journey</h2>
                <form method='POST'>
                    <input name='u' class='form-control' placeholder='Choose Username' required>
                    <input name='p' type='password' class='form-control' placeholder='Create Password' required>
                    <button class='btn btn-success mt-3'>Register</button>
                </form>
                <p class="mt-4 mb-0 text-muted" style="font-size: 0.9rem;">Already have an account? <a href='/' class="text-link">Login</a></p>
            </div>
        </div>
    </div>
    """, show_nav=False)

# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    
    # Beautiful Image Hero Banner inspired by the screenshot
    hero_banner = """
    <div class="hero-section mb-5 rounded-4 overflow-hidden position-relative" style="background-image: url('https://images.unsplash.com/photo-1545205597-3d9d02c29597?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center; padding: 100px 20px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <div class="position-absolute top-0 start-0 w-100 h-100" style="background: linear-gradient(to bottom, rgba(254, 252, 245, 0.4), rgba(254, 252, 245, 0.8));"></div>
        <div class="position-relative" style="z-index: 1;">
            <p style="font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.5rem; color: #5a6341; margin-bottom: 5px;">your mind & soul is beautiful</p>
            <h1 style="font-family: 'Playfair Display', serif; color: #3A3A3A; font-weight: 700; font-size: 2.8rem; text-shadow: 0px 2px 4px rgba(255,255,255,0.8);">Witness the Ethereal Beauty with Yogora</h1>
        </div>
    </div>
    """

    # Dashboard Grid Items
    modules = [
        ("Profile", "/profile", "👤"), ("Diet Plan", "/diet", "🥗"), ("Workout", "/yoga", "🧘"),
        ("Steps", "/activity", "👣"), ("Water", "/water", "💧"), ("Sleep", "/sleep", "🛌"),
        ("Goals", "/goals", "🎯"), ("Insights", "/insights", "🧠"), ("AI Chat", "/chat", "🤖"),
        ("Calories", "/calories", "🔥"), ("Routine", "/routine", "📅"), ("Achievements", "/achievements", "🏆"),
        ("Reminders", "/reminders", "🔔"), ("Nearby", "/nearby", "📍")
    ]
    
    grid_html = "".join([f"""
        <div class="col-6 col-md-4 col-lg-3">
            <a href="{link}" style="text-decoration:none; color:inherit;">
                <div class="card card-hover text-center h-100 p-4">
                    <div class="emoji-icon">{emoji}</div>
                    <h5 class="mb-0 text-dark font-weight-bold" style="font-size: 1.05rem;">{title}</h5>
                </div>
            </a>
        </div>
    """ for title, link, emoji in modules])

    return render_page(hero_banner + f"""
    <div class="row g-4">
        {grid_html}
    </div>
    """)

# ================= PROFILE =================
@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'user' not in session: return redirect('/')
    user_profile = Profile.query.filter_by(user_id=session['user']).first()

    if request.method == 'POST':
        if user_profile:
            user_profile.age = request.form['age']
            user_profile.gender = request.form['gender']
            user_profile.height = request.form['height']
            user_profile.weight = request.form['weight']
        else:
            db.session.add(Profile(user_id=session['user'], age=request.form['age'], gender=request.form['gender'], height=request.form['height'], weight=request.form['weight']))
        db.session.commit()
        return redirect('/dashboard')

    # Pre-fill values if they exist
    p_age = user_profile.age if user_profile else ""
    p_gen = user_profile.gender if user_profile else ""
    p_hgt = user_profile.height if user_profile else ""
    p_wgt = user_profile.weight if user_profile else ""

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class='card'>
                <div class="text-center mb-4">
                    <div class="emoji-icon">👤</div>
                    <h2>Your Profile</h2>
                </div>
                <form method='POST'>
                    <label class="text-muted mb-1 ms-1 text-uppercase fw-bold" style="font-size: 0.75rem;">Age</label>
                    <input name='age' value="{p_age}" class='form-control' required>
                    <label class="text-muted mb-1 ms-1 text-uppercase fw-bold" style="font-size: 0.75rem;">Gender</label>
                    <input name='gender' value="{p_gen}" class='form-control' required>
                    <label class="text-muted mb-1 ms-1 text-uppercase fw-bold" style="font-size: 0.75rem;">Height (cm)</label>
                    <input name='height' value="{p_hgt}" class='form-control' required>
                    <label class="text-muted mb-1 ms-1 text-uppercase fw-bold" style="font-size: 0.75rem;">Weight (kg)</label>
                    <input name='weight' value="{p_wgt}" class='form-control' required>
                    <button class='btn btn-success mt-3'>Save Profile</button>
                </form>
            </div>
        </div>
    </div>
    """)

# ================= DIET =================
@app.route('/diet', methods=['GET','POST'])
def diet():
    if 'user' not in session: return redirect('/')
    result = ""
    if request.method == 'POST':
        w, h, age = float(request.form['w']), float(request.form['h'])/100, int(request.form['age'])
        bmi = round(w/(h*h),2)
        bmr = 10*w + 6.25*(h*100) - 5*age + 5
        tdee = round(bmr*1.55)
        
        if bmi < 18.5: plan = "High Calorie Diet 🍞"
        elif bmi < 25: plan = "Balanced Diet 🥗"
        else: plan = "Low Calorie Diet 🥦"

        result = f"""
        <div class="row text-center mt-4 g-3">
            <div class="col-4"><div class="p-3 rounded-3" style="background: var(--bg-cream); border: 1px solid var(--border-soft);"><h6 class="text-muted mb-1" style="font-size:0.8rem;text-transform:uppercase;">BMI</h6><h4 class="mb-0 text-dark serif-font">{bmi}</h4></div></div>
            <div class="col-4"><div class="p-3 rounded-3" style="background: var(--bg-cream); border: 1px solid var(--border-soft);"><h6 class="text-muted mb-1" style="font-size:0.8rem;text-transform:uppercase;">BMR</h6><h4 class="mb-0 text-dark serif-font">{int(bmr)}</h4></div></div>
            <div class="col-4"><div class="p-3 rounded-3" style="background: var(--bg-cream); border: 1px solid var(--border-soft);"><h6 class="text-muted mb-1" style="font-size:0.8rem;text-transform:uppercase;">TDEE</h6><h4 class="mb-0 text-dark serif-font">{tdee}</h4></div></div>
        </div>
        <div class="alert mt-4 text-center" style="background: rgba(143, 155, 105, 0.1); color: var(--header-olive-dark); border: none; border-radius: 8px;">
            <h5 class="mb-0 serif-font fw-bold">Recommended: {plan}</h5>
        </div>
        """

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
            <div class='card'>
                <div class="text-center mb-4"><div class="emoji-icon">🥗</div><h2>Diet Calculator</h2></div>
                <form method='POST'>
                    <div class="row g-2">
                        <div class="col-12"><input name='w' placeholder="Weight (kg)" class='form-control' required></div>
                        <div class="col-6"><input name='h' placeholder="Height (cm)" class='form-control' required></div>
                        <div class="col-6"><input name='age' placeholder="Age" class='form-control' required></div>
                    </div>
                    <button class='btn btn-success mt-3'>Calculate Needs</button>
                </form>
                {result}
            </div>
        </div>
    </div>
    """)

# ================= WORKOUT =================
@app.route('/yoga')
def yoga():
    if 'user' not in session: return redirect('/')
    
    image_banner = """
    <div class="mb-4 rounded-3 overflow-hidden shadow-sm" style="height: 150px; background-image: url('https://images.unsplash.com/photo-1599901860904-17e082b4df01?q=80&w=2070&auto=format&fit=crop'); background-size: cover; background-position: center;">
    </div>
    """
    
    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class='card'>
                {image_banner}
                <div class="text-center mb-4"><h2>Daily Routine</h2></div>
                <ul class="list-styled p-0">
                    <li><span class="fs-4">🌞</span> <h6 class="mb-0 text-dark serif-font fs-5">Surya Namaskar (Sun Salutation)</h6></li>
                    <li><span class="fs-4">💪</span> <h6 class="mb-0 text-dark serif-font fs-5">Pushups - 3 sets of 15</h6></li>
                    <li><span class="fs-4">🦵</span> <h6 class="mb-0 text-dark serif-font fs-5">Squats - 3 sets of 20</h6></li>
                    <li><span class="fs-4">🪵</span> <h6 class="mb-0 text-dark serif-font fs-5">Plank - 60 seconds</h6></li>
                </ul>
            </div>
        </div>
    </div>
    """)

# ================= TRACKERS (Activity, Water, Sleep, Goals) =================
def render_tracker(title, emoji, unit, db_model, field_name, input_name, user_id):
    if request.method == 'POST':
        new_entry = db_model(user_id=user_id, **{field_name: request.form[input_name]})
        db.session.add(new_entry)
        db.session.commit()
    
    data = db_model.query.filter_by(user_id=user_id).all()
    last = getattr(data[-1], field_name) if data else 0

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class='card text-center'>
                <div class="emoji-icon">{emoji}</div>
                <h2>{title}</h2>
                <div class="my-4">
                    <p class="text-muted mb-1 text-uppercase fw-bold" style="font-size: 0.8rem;">Current Log</p>
                    <span class="stat-highlight">{last}</span> <span class="fs-5 text-muted serif-font">{unit}</span>
                </div>
                <form method='POST' class="mt-2">
                    <input name='{input_name}' class='form-control text-center' placeholder='Enter new value' required>
                    <button class='btn btn-success mt-2'>Log Entry</button>
                </form>
            </div>
        </div>
    </div>
    """)

@app.route('/activity', methods=['GET','POST'])
def activity():
    if 'user' not in session: return redirect('/')
    return render_tracker("Steps Tracker", "👣", "steps", Steps, "steps", "s", session['user'])

@app.route('/water', methods=['GET','POST'])
def water():
    if 'user' not in session: return redirect('/')
    return render_tracker("Hydration", "💧", "glasses", Water, "glasses", "g", session['user'])

@app.route('/sleep', methods=['GET','POST'])
def sleep():
    if 'user' not in session: return redirect('/')
    return render_tracker("Sleep Tracker", "🛌", "hours", Sleep, "hours", "h", session['user'])

@app.route('/goals', methods=['GET','POST'])
def goals():
    if 'user' not in session: return redirect('/')
    return render_tracker("Target Weight", "🎯", "kg", Goal, "target", "g", session['user'])


# Configure the Gemini API
genai.configure(api_key="AIzaSyC6_xpvbALpSNv6bI6nMrg_ZVCQCvFf2RA")

# Set up the model
generation_config = {"temperature": 0.7, "max_output_tokens": 500}
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    system_instruction="You are Yogora, a friendly, expert AI health and fitness coach. Keep your answers concise (1-3 sentences), motivating, and strictly focused on wellness, diet, exercise, yoga, and sleep. Use emojis occasionally."
)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session: return redirect('/')

    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "bot", "text": "Namaste! I am your Yogora AI coach. Ask me anything about fitness, diet, or sleep!"}
        ]

    if request.method == 'POST':
        user_msg = request.form['m']
        session['chat_history'].append({"role": "user", "text": user_msg})
        
        try:
            history_for_gemini = []
            for msg in session['chat_history'][1:-1]:
                role = "user" if msg['role'] == "user" else "model"
                history_for_gemini.append({"role": role, "parts": [msg['text']]})
                
            chat_session = model.start_chat(history=history_for_gemini)
            response = chat_session.send_message(user_msg)
            bot_reply = response.text
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            bot_reply = "I'm having trouble connecting to my AI brain right now. Please check the API key!"

        session['chat_history'].append({"role": "bot", "text": bot_reply})
        
        if len(session['chat_history']) > 11:
            session['chat_history'] = [session['chat_history'][0]] + session['chat_history'][-10:]
            
        session.modified = True 

    chat_bubbles_html = ""
    for msg in session['chat_history']:
        if msg['role'] == 'user':
            chat_bubbles_html += f"<div class='msg-user'>{msg['text']}</div>"
        else:
            chat_bubbles_html += f"<div class='msg-bot'>{msg['text']}</div>"

    return render_page(f"""
    <style>
        .chat-container {{ height: 450px; overflow-y: auto; padding: 20px; background: #FAFAFA; border-radius: 12px; border: 1px solid var(--border-soft); margin-bottom: 20px; display: flex; flex-direction: column; }}
        .msg-user {{ background: var(--header-olive); color: #ffffff; padding: 12px 18px; border-radius: 18px 18px 0 18px; max-width: 85%; align-self: flex-end; margin-bottom: 15px; font-size: 0.95rem; box-shadow: 0 4px 10px rgba(143, 155, 105, 0.2);}}
        .msg-bot {{ background: #ffffff; color: var(--text-dark); padding: 12px 18px; border-radius: 18px 18px 18px 0; max-width: 85%; align-self: flex-start; margin-bottom: 15px; font-size: 0.95rem; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05); border: 1px solid var(--border-soft);}}
    </style>
    
    <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
            <div class='card'>
                <div class="text-center mb-3">
                    <div class="emoji-icon" style="font-size: 2rem; margin-bottom: 5px;">🤖</div>
                    <h3 class="mb-0">Yogora AI Coach</h3>
                </div>
                
                <div class="chat-container" id="chatWindow">
                    {chat_bubbles_html}
                </div>
                
                <form method='POST' class="d-flex gap-2 mb-0">
                    <input name='m' class='form-control mb-0' placeholder='Ask about diets, workouts, or sleep...' required autocomplete="off">
                    <button class='btn btn-success w-auto px-4 mt-0' style="border-radius: 8px;">Send</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        var chatWindow = document.getElementById("chatWindow");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    </script>
    """)

# ================= CALORIES =================
@app.route('/calories', methods=['GET','POST'])
def calories():
    if 'user' not in session: return redirect('/')
    res = ""
    if request.method == 'POST':
        t = int(request.form['t'])
        res = f"<h1 class='stat-highlight mt-4'>{t*5} <span class='fs-4 text-muted' style='font-family: Lato, sans-serif;'>kcal</span></h1>"

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class='card text-center'>
                <div class="emoji-icon">🔥</div>
                <h2>Burn Calculator</h2>
                <p class="text-muted">Enter workout duration in minutes</p>
                <form method='POST'>
                    <input name='t' type="number" class='form-control text-center' placeholder='Minutes' required>
                    <button class='btn btn-success mt-2'>Calculate</button>
                </form>
                {res}
            </div>
        </div>
    </div>
    """)

# ================= STATIC INFO ROUTES =================
def render_static_card(title, emoji, items):
    list_html = "".join([f"<li><h6 class='mb-0 text-dark serif-font fs-5'>{item}</h6></li>" for item in items])
    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class='card'>
                <div class="text-center mb-4"><div class="emoji-icon">{emoji}</div><h2>{title}</h2></div>
                <ul class="list-styled p-0">{list_html}</ul>
            </div>
        </div>
    </div>
    """)

@app.route('/insights')
def insights(): return render_static_card("Health Insights", "🧠", ["💧 Drink 8 glasses of water", "🚶 Aim for 8000+ steps daily", "😴 Rest for 7 hours to recover"])

@app.route('/routine')
def routine(): return render_static_card("Daily Routine", "📅", ["🌞 07:00 - Morning Yoga", "🥗 13:00 - Healthy Lunch", "👟 17:00 - 10K Steps Walk", "💧 All Day - Stay Hydrated", "🛌 22:30 - Sleep"])

@app.route('/achievements')
def achievements(): return render_static_card("Your Trophies", "🏆", ["🔥 7 Day Login Streak", "⭐ Fitness Beginner Badge", "💧 Hydration Master"])

@app.route('/reminders')
def reminders(): return render_static_card("Active Reminders", "🔔", ["⏰ 08:00 AM - Drink Water", "⏰ 05:00 PM - Evening Exercise", "⏰ 10:00 PM - Wind down for sleep"])

@app.route('/nearby')
def nearby():
    return render_page("""
    <div class="row justify-content-center">
        <div class="col-md-6 text-center">
            <div class='card'>
                <div class="emoji-icon">📍</div>
                <h2>Nearby Fitness</h2>
                <p class="text-muted mt-3">Integration with Google Maps for local gyms and parks coming soon.</p>
            </div>
        </div>
    </div>
    """)

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= RUN =================
if __name__ == '__main__':
    print("🚀 Yogora running on http://127.0.0.1:5000")
    app.run(debug=True)
