"""TeamTrack - Student Teamwork & Project Management System.

A small Flask + SQLite web application that lets a student team manage
members, tasks, priorities, deadlines, progress and task-wise comments.
"""
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("TEAMTRACK_DB", BASE_DIR / "teamtrack.db"))

STATUSES = ("To Do", "In Progress", "Done")
PRIORITIES = ("Low", "Medium", "High")
ROLES = ("Member", "Team Lead", "Developer", "Designer", "Researcher", "Presenter")

app = Flask(__name__)
# For local demonstration a default key is used. Set TEAMTRACK_SECRET_KEY
# as an environment variable before any real deployment.
app.config["SECRET_KEY"] = os.environ.get("TEAMTRACK_SECRET_KEY", "dev-key-change-before-deployment")


# ---------------------------------------------------------------- database
def get_db():
    """Open a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables if missing and add sample data on first run."""
    conn = get_db()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Member'
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assignee_id INTEGER,
            status TEXT NOT NULL DEFAULT 'To Do',
            priority TEXT NOT NULL DEFAULT 'Medium',
            due_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (assignee_id) REFERENCES members(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        """)
        if conn.execute("SELECT COUNT(*) FROM members").fetchone()[0] == 0:
            conn.executemany("INSERT INTO members(name, role) VALUES (?,?)", [
                ("Aarav Sharma", "Team Lead"),
                ("Meera Singh", "Developer"),
                ("Kabir Verma", "Designer"),
            ])
            today = date.today()
            now = now_text()
            conn.executemany(
                """INSERT INTO tasks (title, description, assignee_id, status,
                   priority, due_date, created_at) VALUES (?,?,?,?,?,?,?)""",
                [
                    ("Prepare project proposal", "Define scope, goals and deliverables.",
                     1, "In Progress", "High", str(today + timedelta(days=3)), now),
                    ("Create interface design", "Prepare a simple dashboard layout.",
                     3, "To Do", "Medium", str(today + timedelta(days=7)), now),
                    ("Set up project repository", "Create folders and share the starter code.",
                     2, "Done", "Low", str(today - timedelta(days=1)), now),
                ])
    conn.close()


def now_text():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


# ----------------------------------------------------------------- helpers
def clean_date(value):
    """Return a valid YYYY-MM-DD string, or '' if empty/invalid."""
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def read_task_form():
    """Read and validate task form values. Returns (data, error)."""
    title = request.form.get("title", "").strip()
    if not title:
        return None, "Task title is required."
    if len(title) > 120:
        return None, "Task title must be 120 characters or fewer."
    description = request.form.get("description", "").strip()[:1000]
    status = request.form.get("status", "To Do")
    priority = request.form.get("priority", "Medium")
    if status not in STATUSES:
        return None, "Invalid task status."
    if priority not in PRIORITIES:
        return None, "Invalid task priority."
    due = clean_date(request.form.get("due_date"))
    if due is None:
        return None, "Due date is not valid."
    assignee = request.form.get("assignee_id") or None
    if assignee is not None:
        with get_db() as db:
            if not db.execute("SELECT 1 FROM members WHERE id=?", (assignee,)).fetchone():
                return None, "Selected team member does not exist."
    return dict(title=title, description=description, assignee_id=assignee,
                status=status, priority=priority, due_date=due), None


def decorate(rows):
    """Add an 'overdue' flag to task rows (as dictionaries)."""
    today = date.today().isoformat()
    tasks = []
    for r in rows:
        t = dict(r)
        t["overdue"] = bool(t["due_date"]) and t["due_date"] < today and t["status"] != "Done"
        tasks.append(t)
    return tasks


TASK_SELECT = """SELECT tasks.*, members.name AS assignee
                 FROM tasks LEFT JOIN members ON tasks.assignee_id = members.id"""
PRIORITY_ORDER = "CASE tasks.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"


# ------------------------------------------------------------------ routes
@app.route("/")
def dashboard():
    member_filter = request.args.get("member", "")
    with get_db() as db:
        sql, params = TASK_SELECT, ()
        if member_filter == "none":
            sql += " WHERE tasks.assignee_id IS NULL"
        elif member_filter.isdigit():
            sql += " WHERE tasks.assignee_id = ?"
            params = (member_filter,)
        sql += f" ORDER BY {PRIORITY_ORDER}, tasks.due_date = '', tasks.due_date, tasks.id DESC"
        tasks = decorate(db.execute(sql, params).fetchall())
        members = db.execute("SELECT * FROM members ORDER BY name").fetchall()
        counts = {s: db.execute("SELECT COUNT(*) FROM tasks WHERE status=?", (s,)).fetchone()[0]
                  for s in STATUSES}
        overdue = db.execute("""SELECT COUNT(*) FROM tasks WHERE due_date != ''
                                AND due_date < ? AND status != 'Done'""",
                             (date.today().isoformat(),)).fetchone()[0]
    total = sum(counts.values())
    stats = {
        "total": total,
        "todo": counts["To Do"],
        "progress": counts["In Progress"],
        "done": counts["Done"],
        "percent": round(counts["Done"] * 100 / total) if total else 0,
        "overdue": overdue,
    }
    columns = {s: [t for t in tasks if t["status"] == s] for s in STATUSES}
    return render_template("index.html", columns=columns, members=members, stats=stats,
                           statuses=STATUSES, priorities=PRIORITIES, member_filter=member_filter)


@app.route("/tasks", methods=["POST"])
def add_task():
    data, error = read_task_form()
    if error:
        flash(error, "error")
        return redirect(url_for("dashboard"))
    with get_db() as db:
        db.execute("""INSERT INTO tasks (title, description, assignee_id, status,
                      priority, due_date, created_at) VALUES (?,?,?,?,?,?,?)""",
                   (data["title"], data["description"], data["assignee_id"], data["status"],
                    data["priority"], data["due_date"], now_text()))
    flash("Task created successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>")
def task_detail(task_id):
    with get_db() as db:
        row = db.execute(TASK_SELECT + " WHERE tasks.id=?", (task_id,)).fetchone()
        if row is None:
            flash("Task not found.", "error")
            return redirect(url_for("dashboard"))
        comments = db.execute("SELECT * FROM comments WHERE task_id=? ORDER BY id DESC",
                              (task_id,)).fetchall()
        members = db.execute("SELECT * FROM members ORDER BY name").fetchall()
    return render_template("task.html", task=decorate([row])[0], comments=comments,
                           members=members, statuses=STATUSES, priorities=PRIORITIES)


@app.route("/tasks/<int:task_id>/edit", methods=["POST"])
def edit_task(task_id):
    data, error = read_task_form()
    if error:
        flash(error, "error")
        return redirect(url_for("task_detail", task_id=task_id))
    with get_db() as db:
        db.execute("""UPDATE tasks SET title=?, description=?, assignee_id=?, status=?,
                      priority=?, due_date=? WHERE id=?""",
                   (data["title"], data["description"], data["assignee_id"], data["status"],
                    data["priority"], data["due_date"], task_id))
    flash("Task updated.", "success")
    return redirect(url_for("task_detail", task_id=task_id))


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_status(task_id):
    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Invalid task status.", "error")
    else:
        with get_db() as db:
            db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        flash("Task status updated.", "success")
    target = request.form.get("next", "")
    # only allow redirects to pages inside this application
    if not target.startswith("/") or target.startswith("//"):
        target = url_for("dashboard")
    return redirect(target)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    with get_db() as db:
        db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    flash("Task deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/tasks/<int:task_id>/comments", methods=["POST"])
def add_comment(task_id):
    author = request.form.get("author", "").strip()[:60]
    message = request.form.get("message", "").strip()[:500]
    if not author or not message:
        flash("Enter your name and a comment.", "error")
        return redirect(url_for("task_detail", task_id=task_id))
    with get_db() as db:
        if db.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone():
            db.execute("""INSERT INTO comments(task_id, author, message, created_at)
                          VALUES (?,?,?,?)""", (task_id, author, message, now_text()))
            flash("Comment posted.", "success")
    return redirect(url_for("task_detail", task_id=task_id))


@app.route("/team", methods=["GET", "POST"])
def team():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "Member")
        if not name:
            flash("Member name is required.", "error")
        elif len(name) > 60:
            flash("Member name must be 60 characters or fewer.", "error")
        elif role not in ROLES:
            flash("Invalid role selected.", "error")
        else:
            with get_db() as db:
                db.execute("INSERT INTO members(name, role) VALUES (?,?)", (name, role))
            flash("Team member added.", "success")
        return redirect(url_for("team"))
    with get_db() as db:
        members = db.execute("""SELECT members.*,
            (SELECT COUNT(*) FROM tasks WHERE tasks.assignee_id = members.id) AS task_count,
            (SELECT COUNT(*) FROM tasks WHERE tasks.assignee_id = members.id
                AND tasks.status = 'Done') AS done_count
            FROM members ORDER BY name""").fetchall()
    return render_template("team.html", members=members, roles=ROLES)


@app.route("/team/<int:member_id>/delete", methods=["POST"])
def delete_member(member_id):
    # Tasks of the removed member stay on the board as 'Unassigned'
    # because of ON DELETE SET NULL in the tasks table.
    with get_db() as db:
        db.execute("DELETE FROM members WHERE id=?", (member_id,))
    flash("Team member removed. Their tasks are now unassigned.", "success")
    return redirect(url_for("team"))


init_db()  # make sure the database exists, also when started with "flask run"

if __name__ == "__main__":
    app.run(debug=os.environ.get("TEAMTRACK_DEBUG", "1") == "1")
