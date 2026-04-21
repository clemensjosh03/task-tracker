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

# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- UI ----------------
def render_page(content, show_sidebar=True):
    sidebar = """
    <div class="sidebar">
        <h2>Task Tracker</h2>
        <a href="/dashboard">Dashboard</a>
        <a href="/upload-page">Upload</a>
        <a href="/logout">Logout</a>
    </div>
    """ if show_sidebar else ""

    return f"""
    <html>
    <head>
        <title>Task Tracker</title>
        <style>
            body {{ margin:0; display:flex; font-family:Arial; background:#0f172a; color:#e5e7eb; }}

            .sidebar {{
                width:220px; background:#111827; padding:20px;
                height:100vh; position:fixed;
            }}

            .sidebar a {{
                display:block; color:#9ca3af; margin:12px 0; text-decoration:none;
            }}

            .sidebar a:hover {{ color:white; }}

            .main {{
                margin-left:220px;
                width:100%;
                padding:80px 40px 40px;
            }}

            .topbar {{
                position:fixed;
                left:220px;
                right:0;
                height:60px;
                background:#111827;
                display:flex;
                align-items:center;
                padding:0 20px;
                border-bottom:1px solid #334155;
            }}

            .card {{
                background:#1e293b;
                padding:25px;
                border-radius:12px;
                margin-bottom:20px;
                border:1px solid #334155;
            }}

            table {{ width:100%; border-collapse:collapse; }}

            td, th {{ padding:10px; border-top:1px solid #334155; }}

            input {{
                padding:10px;
                width:100%;
                margin:6px 0 12px;
                border-radius:6px;
                border:none;
            }}

            button {{
                padding:10px 16px;
                background:#3b82f6;
                color:white;
                border:none;
                border-radius:6px;
                cursor:pointer;
            }}

            .success {{
                background:#16a34a;
                padding:10px;
                border-radius:6px;
                margin-bottom:15px;
            }}
        </style>
    </head>
    <body>
        {sidebar}
        <div class="topbar"><h3>Task Tracker</h3></div>
        <div class="main">
            {content}
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

# ---------------- LOGOUT ----------------
@app.get("/logout")
def logout():
    res = RedirectResponse("/")
    res.delete_cookie("user_email")
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
    if not email:
        return RedirectResponse("/")

    msg = request.query_params.get("msg")
    alert = "<div class='success'>Task added</div>" if msg == "added" else ""

    tasks = db.query(models.Task).filter(models.Task.user_email == email).all()
    tasks = sorted(tasks, key=lambda t: t.due_date)

    if not tasks:
        rows = "<tr><td colspan='2'>No tasks yet</td></tr>"
    else:
        rows = ""
        for t in tasks:
            rows += f"<tr><td>{t.task_name}</td><td>{t.due_date.date()}</td></tr>"

    return render_page(f"""
        {alert}

        <div class="card">
            <h3>Tasks</h3>
            <a href="/add-task"><button>Add Task</button></a>
            <table>
                <tr><th>Task</th><th>Due</th></tr>
                {rows}
            </table>
        </div>
    """)

# ---------------- ADD TASK ----------------
@app.get("/add-task", response_class=HTMLResponse)
def add_task_page():
    return render_page("""
        <div class="card">
            <h2>Add Task</h2>
            <form action="/add-task" method="post">
                <input name="task_name" placeholder="Task name">
                <input name="due_date" type="date">
                <button>Add</button>
            </form>
        </div>
    """)


@app.post("/add-task")
def add_task(request: Request, task_name: str = Form(...), due_date: str = Form(...), db: Session = Depends(get_db)):
    email = request.cookies.get("user_email")

    task = models.Task(
        task_name=task_name,
        due_date=datetime.strptime(due_date, "%Y-%m-%d"),
        user_email=email
    )

    db.add(task)
    db.commit()

    return RedirectResponse("/dashboard?msg=added", status_code=303)

# ---------------- UPLOAD ----------------
@app.get("/upload-page", response_class=HTMLResponse)
def upload_page():
    return render_page("""
        <div class="card">
            <h2>Upload CSV</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <button>Upload</button>
            </form>
        </div>
    """)


@app.post("/upload")
def upload(file: UploadFile = File(...), request: Request = None, db: Session = Depends(get_db)):
    email = request.cookies.get("user_email")

    df = pd.read_csv(file.file)

    for _, row in df.iterrows():
        try:
            task = models.Task(
                task_name=str(row[0]),
                due_date=pd.to_datetime(row[1]),
                user_email=email
            )
            db.add(task)
        except:
            continue

    db.commit()

    return RedirectResponse("/dashboard", status_code=303)
