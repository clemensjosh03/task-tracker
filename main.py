from fastapi import FastAPI, Form, UploadFile, File, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import hash_password, verify_password
import pandas as pd
from datetime import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def render_page(content, show_sidebar=True):
    sidebar = """
    <div class="sidebar">
        <h3>Task Tracker</h3>
        <a href="/dashboard">Dashboard</a>
        <a href="/upload-page">Upload</a>
        <a href="/">Logout</a>
    </div>
    """ if show_sidebar else ""

    return f"""
    <html>
    <head>
        <title>Task Tracker</title>
        <style>
            body {{ font-family: Arial; background:#f5f7fb; margin:0; display:flex; }}
            .sidebar {{ width:220px; background:#111827; color:white; padding:20px; height:100vh; }}
            .sidebar a {{ display:block; color:#9ca3af; margin:12px 0; text-decoration:none; }}
            .sidebar a:hover {{ color:white; }}
            .main {{ flex:1; padding:40px; display:flex; justify-content:center; }}
            .container {{ width:100%; max-width:1100px; }}
            .card {{ background:white; padding:25px; border-radius:12px; margin-bottom:20px; }}
            .stats {{ display:flex; gap:15px; margin-bottom:20px; }}
            .stat {{ flex:1; background:white; padding:20px; border-radius:10px; }}
            table {{ width:100%; border-collapse:collapse; }}
            td, th {{ padding:10px; border-top:1px solid #eee; }}
            tr:hover {{ background:#f9fafb; }}
            .badge {{ padding:5px 10px; border-radius:999px; font-size:12px; }}
            .overdue {{ background:#fee2e2; color:#dc2626; }}
            .upcoming {{ background:#dcfce7; color:#16a34a; }}
            input, select {{ padding:10px; width:100%; margin:6px 0 12px; border:1px solid #ddd; border-radius:6px; }}
            button {{ padding:8px 14px; background:#16a34a; color:white; border:none; border-radius:6px; cursor:pointer; }}
            .actions a {{ margin-right:10px; color:#2563eb; text-decoration:none; }}
        </style>
    </head>
    <body>
        {sidebar}
        <div class="main">
            <div class="container">
                {content}
            </div>
        </div>
    </body>
    </html>
    """

# ---------------- LOGIN ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return render_page("""
        <div class="card">
            <h2>Login</h2>
            <form action="/login" method="post">
                <input name="email" placeholder="Email">
                <input name="password" type="password" placeholder="Password">
                <button>Login</button>
            </form>
            <p><a href="/signup-page">Sign up</a></p>
        </div>
    """, False)

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password):
        return HTMLResponse("Invalid login")

    res = RedirectResponse("/dashboard", status_code=303)
    res.set_cookie("user_email", email)
    return res
# ---------------- SIGNUP ----------------
@app.get("/signup-page", response_class=HTMLResponse)
def signup_page():
    return render_page("""
        <div class="card">
            <h2>Sign Up</h2>
            <form action="/signup" method="post">
                <input name="email" placeholder="Email">
                <input name="password" type="password" placeholder="Password">
                <button>Create Account</button>
            </form>
            <p><a href="/">Back to login</a></p>
        </div>
    """, False)


@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return HTMLResponse("User already exists")

    user = models.User(
        email=email,
        password=hash_password(password)
    )
    db.add(user)
    db.commit()

    return RedirectResponse("/", status_code=303)
# ---------------- DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    email = request.cookies.get("user_email")
    user = db.query(models.User).filter(models.User.email == email).first()
    tasks = db.query(models.Task).filter(models.Task.user_email == email).all()

    now = datetime.now()

    # ✅ SORTING ADDED HERE
    tasks = sorted(tasks, key=lambda t: t.due_date)

    total = len(tasks)
    overdue = len([t for t in tasks if t.due_date < now])
    upcoming = total - overdue

    rows = ""
    for t in tasks:
        badge = "overdue" if t.due_date < now else "upcoming"
        rows += f"""
        <tr>
            <td>{t.task_name}</td>
            <td>{t.due_date.strftime("%d %b %Y")}</td>
            <td><span class="badge {badge}">{badge}</span></td>
        </tr>
        """

    return render_page(f"""
        <div class="stats">
            <div class="stat"><h3>{total}</h3><p>Total</p></div>
            <div class="stat"><h3>{overdue}</h3><p>Overdue</p></div>
            <div class="stat"><h3>{upcoming}</h3><p>Upcoming</p></div>
        </div>

        <div class="card">
            <h3>Tasks</h3>
            <a href="/add-task"><button>Add Task</button></a>
            <table>
                <tr><th>Task</th><th>Due</th><th>Status</th></tr>
                {rows}
            </table>
        </div>
    """)
