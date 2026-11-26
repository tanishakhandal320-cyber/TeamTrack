# TeamTrack – Student Teamwork & Project Management System

TeamTrack is a lightweight Flask web application that helps student teams manage projects.
Members can be added, tasks can be assigned with priorities and deadlines, progress is tracked
(To Do, In Progress, Done), a dashboard shows overall completion, and every task has its own comments.

Domain: Education / Student Collaboration · Course: Leadership, Team Building & Interpersonal Skills (25MULCHM3201) · Experiment 6

## Features
- Dashboard with total / To Do / In Progress / Completed / Overdue counts and a progress percentage bar
- Three-column task board (To Do, In Progress, Done) sorted by priority and due date
- Create, edit, assign, prioritise, set deadline, change status and delete tasks
- Filter the board by team member or unassigned tasks
- Team page: add and remove members, see assigned and completed task counts
- Task-wise comments (discussion area on each task)
- SQLite database created automatically with sample data on first run
- Server-side validation, parameterized SQL, escaped output

## Technology
| Part | Technology |
|---|---|
| Frontend | HTML5, CSS3, Jinja2 templates |
| Backend | Python 3.10+ and Flask 3 |
| Database | SQLite (file `teamtrack.db`) |
| Tools | VS Code, pip, virtual environment, Chrome or any browser |

## How to run (Windows, macOS, Linux)
1. Install Python 3.10 or newer (https://www.python.org). On Windows tick "Add Python to PATH".
2. Unzip the project and open the folder in VS Code (or open a terminal inside the folder).
3. Create a virtual environment:
   - Windows: `py -m venv .venv`
   - macOS / Linux: `python3 -m venv .venv`
4. Activate it:
   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`  (Command Prompt: `.venv\Scripts\activate.bat`)
   - macOS / Linux: `source .venv/bin/activate`
5. Install Flask: `pip install -r requirements.txt`
6. Start the application: `python app.py`
7. Open **http://127.0.0.1:5000** in your browser.
8. Press `Ctrl + C` in the terminal to stop the server.

The file `teamtrack.db` is created automatically on the first run, together with 3 sample members and
3 sample tasks. To start again with a fresh database, stop the server and delete `teamtrack.db`.

> On Windows, if PowerShell blocks the activation script, use Command Prompt or run
> `Set-ExecutionPolicy -Scope Process RemoteSigned` first.

## Run the automated tests
With the virtual environment active, run: `python tests/test_app.py`

The tests use a temporary database (your real data is not touched) and check pages, task creation,
validation, status updates, editing, comments, members, deletion and database relationships.
Expected result: `26/26 tests passed`.

## Project structure
```
app.py                  Flask application: routes, validation, database code
templates/              Jinja2 pages (base, index, task, team)
static/style.css        Styling
tests/test_app.py       Automated tests
screenshots/            Screenshots of the running application
TeamTrack_Architecture.png   Architecture diagram (source: architecture.dot)
sample_data.sql         Reference database schema
requirements.txt        Python dependency (Flask)
```

## Main routes
| Route | Purpose |
|---|---|
| `/` | Dashboard, board, task creation form, member filter (`/?member=<id>` or `/?member=none`) |
| `/tasks/<id>` | Task details, edit form and comments |
| `/team` | Team members and add-member form |

## Settings (optional environment variables)
- `TEAMTRACK_SECRET_KEY` – secret key for sessions/flash messages (set this before any real deployment)
- `TEAMTRACK_DEBUG` – `1` (default, development) or `0` to switch debug mode off
- `TEAMTRACK_DB` – path of a different database file

## Notes
This is an academic demonstration project and runs only on localhost; it has not been deployed.
Before public use, add user login, role-based permissions, HTTPS, a production server and a private secret key.
The sample members (Aarav Sharma, Meera Singh, Kabir Verma) are only demonstration data.
