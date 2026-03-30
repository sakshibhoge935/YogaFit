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

# ================= UI & THEMING =================
BASE_STYLE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yogora Health</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-deep: #1a1d1a;
        --accent-green: #2d4a3e;
        --text-gold: #e2e8f0;
        --glass: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    body { 
        background: linear-gradient(135deg, #1a1d1a 0%, #0a0c0a 100%); 
        color: #f8fafc; 
        font-family: 'Inter', sans-serif; 
        min-height: 100vh;
    }

    h1, h2, .navbar-brand { 
        font-family: 'Playfair Display', serif; 
    }

    .navbar { 
        background: transparent; 
        backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--glass-border);
        padding: 1.2rem 2rem; 
    }

    .navbar-brand { font-weight: 700; color: #ffffff !important; font-size: 1.8rem; }
    
    .card { 
        background: var(--glass); 
        backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border); 
        border-radius: 24px; 
        padding: 35px; 
        margin-top: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
    }

    .card-hover:hover { 
        transform: translateY(-10px); 
        border-color: rgba(255,255,255,0.3);
        background: rgba(255, 255, 255, 0.05);
        cursor: pointer;
    }

    .form-control { 
        background: rgba(0,0,0,0.2); 
        border: 1px solid var(--glass-border); 
        color: white; 
        border-radius: 10px; 
        padding: 14px; 
        margin-bottom: 15px;
    }

    .form-control:focus { 
        background: rgba(0,0,0,0.3); 
        color: white; 
        border-color: #ffffff; 
        box-shadow: none;
    }

    .form-control::placeholder { color: #64748b; }

    .btn-success { 
        background: #ffffff; 
        color: #000;
        border: none; 
        border-radius: 50px; 
        padding: 12px 30px; 
        font-weight: 600; 
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s; 
    }

    .btn-success:hover { 
        background: #e2e8f0; 
        transform: scale(1.02);
        color: #000;
    }

    a.text-link { color: #ffffff; text-decoration: none; font-weight: 500; border-bottom: 1px solid #ffffff; }
    a.text-link:hover { color: #cbd5e1; border-color: #cbd5e1; }
    
    .nav-link { color: #cbd5e1 !important; transition: 0.3s; font-weight: 500; }
    .nav-link:hover { color: #ffffff !important; }

    .stat-highlight { 
        color: #ffffff; 
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem; 
        line-height: 1;
    }

    .emoji-icon { 
        font-size: 2.5rem; 
        opacity: 0.9;
        margin-bottom: 15px;
    }

    .list-styled li { 
        background: rgba(255,255,255,0.02); 
        margin-bottom: 12px; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid var(--glass-border); 
        list-style: none; 
        display: flex; 
        align-items: center; 
        gap: 20px; 
    }
    
    /* Smooth Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-deep); }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
</style>
</head>
<body>
"""

def render_page(content, show_nav=True):
    nav = """
    <nav class="navbar navbar-expand-lg mb-4">
        <a class="navbar-brand" href="/dashboard">🌿 Yogora</a>
        <div class="ms-auto d-flex align-items-center">
            <a href="/dashboard" class="nav-link me-3 d-none d-md-block">Dashboard</a>
            <a href="/profile" class="nav-link me-3 d-none d-md-block">Profile</a>
            <a href="/logout" class="btn btn-outline-light btn-sm rounded-pill px-4 py-2" style="font-weight:500;">Logout</a>
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
            <div class='card text-center'>
                <div class="emoji-icon mb-2">🌿</div>
                <h2 class="mb-4">Welcome Back</h2>
                <form method='POST'>
                    <input name='u' class='form-control' placeholder='Username' required>
                    <input name='p' type='password' class='form-control' placeholder='Password' required>
                    <button class='btn btn-success mt-2'>Login</button>
                </form>
                {error}
                <p class="mt-4 mb-0 text-secondary">New here? <a href='/register' class="text-link">Create an account</a></p>
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
            <div class='card text-center'>
                <h2 class="mb-4">Create Account</h2>
                <form method='POST'>
                    <input name='u' class='form-control' placeholder='Choose Username' required>
                    <input name='p' type='password' class='form-control' placeholder='Create Password' required>
                    <button class='btn btn-success mt-2'>Register</button>
                </form>
                <p class="mt-4 mb-0 text-secondary">Already have an account? <a href='/' class="text-link">Login</a></p>
            </div>
        </div>
    </div>
    """, show_nav=False)

# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/')
    
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
                    <h5 class="mb-0">{title}</h5>
                </div>
            </a>
        </div>
    """ for title, link, emoji in modules])

    return render_page(f"""
    <div class="text-center mb-5 mt-3">
        <h1 style="font-size: 3rem;">Your Hub</h1>
        <p class="text-secondary fs-5">Track, improve, and conquer your day.</p>
    </div>
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
                    <label class="text-secondary mb-1 ms-1">Age</label>
                    <input name='age' value="{p_age}" class='form-control' required>
                    <label class="text-secondary mb-1 ms-1">Gender</label>
                    <input name='gender' value="{p_gen}" class='form-control' required>
                    <label class="text-secondary mb-1 ms-1">Height (cm)</label>
                    <input name='height' value="{p_hgt}" class='form-control' required>
                    <label class="text-secondary mb-1 ms-1">Weight (kg)</label>
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
        <div class="row text-center mt-5 g-3">
            <div class="col-4"><div class="p-3 bg-dark rounded-4 border border-secondary" style="background: rgba(0,0,0,0.3) !important; border-color: rgba(255,255,255,0.1) !important;"><h5 class="text-secondary">BMI</h5><h3 class="text-white">{bmi}</h3></div></div>
            <div class="col-4"><div class="p-3 bg-dark rounded-4 border border-secondary" style="background: rgba(0,0,0,0.3) !important; border-color: rgba(255,255,255,0.1) !important;"><h5 class="text-secondary">BMR</h5><h3 class="text-white">{int(bmr)}</h3></div></div>
            <div class="col-4"><div class="p-3 bg-dark rounded-4 border border-secondary" style="background: rgba(0,0,0,0.3) !important; border-color: rgba(255,255,255,0.1) !important;"><h5 class="text-secondary">TDEE</h5><h3 class="text-white">{tdee}</h3></div></div>
        </div>
        <div class="alert mt-4 text-center border-light" style="background: rgba(255,255,255,0.05); color:#fff;">
            <h4 class="mb-0">Recommended: {plan}</h4>
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
                    <button class='btn btn-success mt-2'>Calculate Needs</button>
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
    return render_page("""
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class='card'>
                <div class="text-center mb-4"><div class="emoji-icon">🧘</div><h2>Daily Routine</h2></div>
                <ul class="list-styled p-0">
                    <li><span class="fs-4">🌞</span> <h5>Surya Namaskar (Sun Salutation)</h5></li>
                    <li><span class="fs-4">💪</span> <h5>Pushups - 3 sets of 15</h5></li>
                    <li><span class="fs-4">🦵</span> <h5>Squats - 3 sets of 20</h5></li>
                    <li><span class="fs-4">🪵</span> <h5>Plank - 60 seconds</h5></li>
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
                    <p class="text-secondary mb-1">Current Log</p>
                    <span class="stat-highlight">{last}</span> <span class="fs-5 text-secondary">{unit}</span>
                </div>
                <form method='POST' class="mt-2">
                    <input name='{input_name}' class='form-control text-center' placeholder='Enter new value' required>
                    <button class='btn btn-success'>Log Entry</button>
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
# Replace 'YOUR_GEMINI_API_KEY_HERE' with your actual key from Google AI Studio
genai.configure(api_key="AIzaSyC6_xpvbALpSNv6bI6nMrg_ZVCQCvFf2RA")

# Set up the model with instructions to act like a fitness coach
generation_config = {"temperature": 0.7, "max_output_tokens": 500}

# Changed model_name to "gemini-pro" to fix the 404 error
model = genai.GenerativeModel(
    model_name="gemini-pro",
    generation_config=generation_config,
    system_instruction="You are Yogora, a friendly, expert AI health and fitness coach. Keep your answers concise (1-3 sentences), motivating, and strictly focused on wellness, diet, exercise, yoga, and sleep. Use emojis occasionally."
)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session: return redirect('/')

    # Initialize a chat history list in the user's session if it doesn't exist
    # We keep the last 10 messages to avoid exceeding Flask's cookie size limit
    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "bot", "text": "Namaste! I am your Yogora AI coach. Ask me anything about fitness, diet, or sleep!"}
        ]

    if request.method == 'POST':
        user_msg = request.form['m']
        
        # 1. Add user message to history
        session['chat_history'].append({"role": "user", "text": user_msg})
        
        try:
            # 2. Convert session history into the format Gemini expects (excluding the very first greeting)
            history_for_gemini = []
            for msg in session['chat_history'][1:-1]: # Skip greeting and the message just added
                role = "user" if msg['role'] == "user" else "model"
                history_for_gemini.append({"role": role, "parts": [msg['text']]})
                
            # 3. Start chat session and send message
            chat_session = model.start_chat(history=history_for_gemini)
            response = chat_session.send_message(user_msg)
            bot_reply = response.text
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            bot_reply = "I'm having trouble connecting to my AI brain right now. Please check the API key!"

        # 4. Add bot response to history
        session['chat_history'].append({"role": "bot", "text": bot_reply})
        
        # Keep only the last 10 messages to save session space
        if len(session['chat_history']) > 11:
            session['chat_history'] = [session['chat_history'][0]] + session['chat_history'][-10:]
            
        session.modified = True # Tell Flask to save the session

    # Generate the HTML for the chat bubbles
    chat_bubbles_html = ""
    for msg in session['chat_history']:
        if msg['role'] == 'user':
            chat_bubbles_html += f"<div class='msg-user'>{msg['text']}</div>"
        else:
            chat_bubbles_html += f"<div class='msg-bot'>{msg['text']}</div>"

    return render_page(f"""
    <style>
        .chat-container {{ height: 450px; overflow-y: auto; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 12px; margin-bottom: 15px; display: flex; flex-direction: column; border: 1px solid var(--glass-border); }}
        .msg-user {{ background: #ffffff; color: #000; padding: 12px 18px; border-radius: 18px 18px 0 18px; max-width: 85%; align-self: flex-end; margin-bottom: 12px; font-size: 0.95rem; box-shadow: 0 2px 5px rgba(0,0,0,0.2);}}
        .msg-bot {{ background: rgba(255,255,255,0.1); color: #f8fafc; padding: 12px 18px; border-radius: 18px 18px 18px 0; max-width: 85%; align-self: flex-start; margin-bottom: 12px; font-size: 0.95rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid var(--glass-border);}}
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
                    <button class='btn btn-success w-auto px-4 mt-0'>Send</button>
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
        res = f"<h1 class='stat-highlight mt-4'>{t*5} <span class='fs-4 text-secondary' style='font-family: Inter, sans-serif;'>kcal</span></h1>"

    return render_page(f"""
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class='card text-center'>
                <div class="emoji-icon">🔥</div>
                <h2>Burn Calculator</h2>
                <p class="text-secondary">Enter workout duration in minutes</p>
                <form method='POST'>
                    <input name='t' type="number" class='form-control text-center' placeholder='Minutes' required>
                    <button class='btn btn-success'>Calculate</button>
                </form>
                {res}
            </div>
        </div>
    </div>
    """)

# ================= STATIC INFO ROUTES =================
def render_static_card(title, emoji, items):
    list_html = "".join([f"<li>{item}</li>" for item in items])
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
                <p class="text-secondary mt-3">Integration with Google Maps for local gyms and parks coming soon.</p>
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