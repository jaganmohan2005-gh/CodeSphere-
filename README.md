# CodeSphere – AI-Powered Coding Assessment & Intelligent Placement Preparation Platform

> **A professional, enterprise-grade full-stack web application designed to help engineering students prepare for technical campus placements, attend timed assessments with strict server-enforced integrity, monitor topic proficiency, and receive 24/7 personalized AI coaching.**

---

## Table of Contents
1. [Platform Overview & Key Highlights](#platform-overview--key-highlights)
2. [Architectural Diagram & Design System](#architectural-diagram--design-system)
3. [Technology Stack](#technology-stack)
4. [Project Folder Structure](#project-folder-structure)
5. [Database Architecture & Entity Relationships](#database-architecture--entity-relationships)
6. [Installation & Windows / VS Code Setup](#installation--windows--vs-code-setup)
7. [Default User Accounts & Seeding](#default-user-accounts--seeding)
8. [Module-by-Module Walkthrough](#module-by-module-walkthrough)
   - [Module 1: Authentication & RBAC](#module-1-authentication--rbac)
   - [Module 2: Administrator Dashboard](#module-2-administrator-dashboard)
   - [Module 3: Student Management](#module-3-student-management)
   - [Module 4: Topic Category Management](#module-4-topic-category-management)
   - [Module 5: Coding Question Bank](#module-5-coding-question-bank)
   - [Module 6: Timed Assessment Engine & Security](#module-6-timed-assessment-engine--security)
   - [Module 7: Student Performance Analytics](#module-7-student-performance-analytics)
   - [Module 8: AI Learning Assistant & Fallback Engine](#module-8-ai-learning-assistant--fallback-engine)
   - [Module 9: Isolated Sandboxed Code Execution](#module-9-isolated-sandboxed-code-execution)
   - [Module 10: Notification Feed](#module-10-notification-feed)
9. [AI API Configuration & Cost Estimates](#ai-api-configuration--cost-estimates)
10. [Automated Test Suite (Pytest)](#automated-test-suite-pytest)
11. [Production Deployment & PostgreSQL Guide](#production-deployment--postgresql-guide)
12. [Beginner's Code Guide & Troubleshooting](#beginners-code-guide--troubleshooting)

---

## 1. Platform Overview & Key Highlights

CodeSphere bridges the gap between self-paced competitive programming and university campus recruitment drives:

- **Strict Server-Enforced Assessment Integrity:** Assessment timers and deadlines are computed server-side from `start_time + duration`. Client-side clock tampering or browser refresh cannot bypass the submission deadline.
- **Sandboxed Subprocess Execution:** Code solutions run in ephemeral subprocesses with hard CPU timeouts and pre-execution static analysis that halts forbidden calls (`os.system`, `subprocess`, `sockets`, `eval`, `exec`).
- **AI Tutor with 100% Offline Resilience:** Features the official OpenAI Python SDK (`gpt-4o-mini`) for progressive hints, error diagnosis, and study plan generation, backed by a comprehensive **Rule-Based Offline Tutor** that activates automatically if an API key is omitted or the network is offline.
- **Multi-Tenant Data Isolation:** Students can only view their own submissions, attempts, chat history, and analytics. Admin routes are guarded by `@admin_required` decorators with role-based session verification.
- **Real-Time Analytics:** All statistics, accuracy rates, and weak topic identifiers are calculated from active database rows, with defensive checks against division-by-zero.

---

## 2. Architectural Diagram & Design System

```
                         +-----------------------------------+
                         |   Client Browser (Desktop/Mobile)  |
                         | Bootstrap 5.3 + Chart.js + Custom |
                         +-----------------+-----------------+
                                           | HTTP / HTTPS / AJAX
                                           v
                         +-----------------------------------+
                         |      Flask Application Factory     |
                         |  CSRF Protection & Flask-Login    |
                         +-----------------+-----------------+
                                           |
         +-----------------+---------------+-----------------+-----------------+
         |                 |               |                 |                 |
         v                 v               v                 v                 v
   +-----------+     +-----------+   +-----------+     +-----------+     +-----------+
   |   Auth    |     |   Admin   |   |  Student  |     | Assessment|     |    AI     |
   | Blueprint |     | Blueprint |   | Blueprint |     | Blueprint |     | Blueprint |
   +-----------+     +-----------+   +-----------+     +-----------+     +-----------+
         |                 |               |                 |                 |
         +-----------------+---------------+-----------------+-----------------+
                                           |
                                           v
                   +-----------------------------------------------+
                   |                Services Layer                 |
                   |-----------------------------------------------|
                   | - CodeExecutor (Subprocess Sandbox & Scans)  |
                   | - AIService (OpenAI SDK + Fallback Engine)    |
                   | - AnalyticsService (Real-time DB Metrics)     |
                   | - SeedService (Standard Curriculum & Accounts)|
                   +-----------------------+-----------------------+
                                           |
                                           v
                   +-----------------------------------------------+
                   |            SQLAlchemy ORM Models              |
                   |-----------------------------------------------|
                   | User, StudentProfile, Category, Question,     |
                   | TestCase, Assessment, AssessmentAttempt,      |
                   | AttemptAnswer, Submission, AIConversation...  |
                   +-----------------------+-----------------------+
                                           |
                                           v
                   +-----------------------------------------------+
                   |          Database (SQLite / PostgreSQL)       |
                   +-----------------------------------------------+
```

### Color Palette & Design Theme
- **Navy Base:** `#060b17` (Deep Slate), `#0f172a` (Navy 900), `#1e293b` (Slate 800)
- **Crisp Neutral:** `#f8fafc` (Background), `#ffffff` (Card White), `#e2e8f0` (Borders)
- **Primary Sapphire:** `#2563eb` (Brand Primary), `#1d4ed8` (Hover State)
- **Accents:** Electric Cyan (`#06b6d4`), Emerald (`#10b981`), Amber (`#f59e0b`), Rose (`#ef4444`), Purple (`#8b5cf6`)
- **Typography:** `Inter` for clean UI readability, `JetBrains Mono` for code blocks.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript ES6 | Responsive structure, animations, and async Fetch API |
| **UI Framework** | Bootstrap 5.3 + Bootstrap Icons | Modern grid system, modals, dropdowns, and accessible UI |
| **Data Visuals** | Chart.js 4 | Real-time mastery doughnuts, topic accuracy bars, score timelines |
| **Backend** | Python Flask 3.0.3 | Application factory, modular route blueprints |
| **Database** | SQLite / PostgreSQL + SQLAlchemy 3.1 | Object-Relational Mapping (ORM) and migrations |
| **Security & Auth** | Flask-Login, Flask-WTF, Werkzeug | Session management, CSRF tokens, secure password hashing |
| **AI Integration** | Official OpenAI Python SDK (`openai>=1.14`) | Tutor prompt engineering, progressive hints, study plans |
| **Testing** | Pytest 8.1.1 | Automated unit and integration testing suite (35+ tests) |

---

## 4. Project Folder Structure

```
CodeSphere project/
│
├── app/                              # Main application package
│   ├── __init__.py                   # Application factory (create_app), error handlers, CLI
│   ├── extensions.py                 # db, login_manager, csrf instances
│   │
│   ├── models/                       # SQLAlchemy Database Entities
│   │   ├── __init__.py               # Exports all model classes
│   │   ├── user.py                   # User, StudentProfile
│   │   ├── question.py               # Category, Question, TestCase
│   │   ├── assessment.py             # Assessment, AssessmentQuestion, AssessmentAttempt, AttemptAnswer
│   │   ├── submission.py             # Submission, SubmissionTestResult, StudentProgress
│   │   ├── ai.py                     # AIConversation, AIMessage
│   │   └── notification.py           # Notification
│   │
│   ├── routes/                       # Modular Route Blueprints
│   │   ├── __init__.py               # Blueprint exports
│   │   ├── decorators.py             # @admin_required, @student_required
│   │   ├── auth.py                   # Register, login, admin login, logout, profile
│   │   ├── admin.py                  # Dashboard, student mgmt, questions, categories, assessments, CSV export
│   │   ├── student.py                # Dashboard, practice workbench, runner, analytics
│   │   ├── assessment.py             # Timed assessment flow, autosave, deadline validation, results
│   │   ├── ai.py                     # AI tutor chat, hints, error diagnosis, study plan
│   │   └── notification.py           # Notification feed, mark as read
│   │
│   ├── services/                     # Business Logic & External Integrations
│   │   ├── __init__.py               # Service exports
│   │   ├── code_executor.py          # Subprocess sandboxing, security scanner, test evaluator
│   │   ├── ai_service.py             # OpenAI API client + Rule-based offline tutor engine
│   │   ├── analytics_service.py      # Real-time metrics calculations (safe division)
│   │   └── seed_service.py           # Database initial curriculum & user seed script
│   │
│   ├── forms/                        # WTForms Server-Side Form Validation
│   │   ├── __init__.py               # Form exports
│   │   ├── auth_forms.py             # Registration, Login, AdminLogin, ProfileEdit
│   │   ├── question_forms.py         # CategoryForm, QuestionForm, TestCaseForm
│   │   └── assessment_forms.py       # AssessmentForm
│   │
│   ├── templates/                    # Jinja2 HTML Templates
│   │   ├── base.html                 # Main layout with navy navbar, notifications, status footer
│   │   ├── auth/                     # Authentication views (login, admin_login, register, profile)
│   │   ├── admin/                    # Admin views (dashboard, students, questions, categories, assessments)
│   │   ├── student/                  # Student views (dashboard, practice_list, practice_solve, analytics)
│   │   ├── assessments/              # Assessment views (list, take [live timer], result report)
│   │   ├── ai/                       # AI Learning Assistant interface (chat, hints, debugger, study plan)
│   │   ├── notifications/            # Notification center feed
│   │   └── errors/                   # Custom 403, 404, 500 pages
│   │
│   └── static/                       # Static Assets
│       ├── css/
│       │   └── codesphere.css        # Custom Navy & SaaS theme design system
│       └── js/
│           ├── main.js               # Global CSRF fetch, copy snippet, textarea indentation
│           ├── assessment.js         # Live countdown, autosave loop, auto-submission
│           ├── ai_assistant.js       # AI chat, progressive hints, debugger, study plan
│           └── analytics_charts.js   # Chart.js initializers
│
├── tests/                            # Automated Pytest Suite
│   ├── conftest.py                   # In-memory test db, fixtures, auth clients
│   ├── test_auth.py                  # Auth, hashing, deactivated account tests
│   ├── test_permissions.py           # Role protection, student data isolation
│   ├── test_categories.py            # Category CRUD & safe deletion
│   ├── test_questions.py             # Question management, test cases, code runner
│   ├── test_assessments.py           # Assessment creation, autosave, server deadline, CSV
│   ├── test_code_executor.py         # Subprocess isolation, security check, TLE
│   ├── test_analytics.py             # Performance math, zero-activity safety
│   └── test_ai_fallback.py           # Offline tutor engine, progressive hints, rate limits
│
├── config.py                         # App configuration (Dev, Test, Prod)
├── run.py                            # Development server and seed command entry point
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git exclusion rules
└── README.md                         # Project documentation
```

---

## 5. Database Architecture & Entity Relationships

The relational schema is implemented with SQLAlchemy ORM and supports SQLite (default) and PostgreSQL:

```
+--------------------+           +----------------------+
|       users        | 1       1 |   student_profiles   |
|--------------------|-----------|----------------------|
| id (PK)            |           | id (PK)              |
| username (Unique)  |           | user_id (FK -> users)|
| email (Unique)     |           | full_name            |
| password_hash      |           | college              |
| role (admin/stud)  |           | target_role          |
| is_active_account  |           | preferred_language   |
+--------------------+           +----------------------+
         | 1
         |
         +--------------------+ 1
         |                    |
         v *                  v *
+--------------------+   +----------------------+
|assessment_attempts |   |     submissions      |
|--------------------|   |----------------------|
| id (PK)            |   | id (PK)              |
| user_id (FK)       |   | user_id (FK)         |
| assessment_id (FK) |   | question_id (FK)     |
| start_time (UTC)   |   | status (Accepted/WA) |
| deadline_time (UTC)|   | execution_time_ms    |
| status             |   | source_code          |
| total_score        |   +----------------------+
| percentage         |              | 1
+--------------------+              v *
         | 1             +------------------------+
         |               | submission_test_results|
         v *             +------------------------+
+--------------------+   | id (PK)                |
|  attempt_answers   |   | submission_id (FK)     |
|--------------------|   | test_case_id (FK)      |
| id (PK)            |   | is_passed (Boolean)    |
| attempt_id (FK)    |   | actual_output          |
| question_id (FK)   |   +------------------------+
| code               |
| status             |
| score_awarded      |
+--------------------+
```

### Models Summary
1. **User:** Core auth model supporting password hashing with Werkzeug and Flask-Login integration.
2. **StudentProfile:** Academic profile (College, Degree, Graduation Year, Target Placement Role).
3. **Category:** DSA topics with question counters and `can_be_safely_deleted()` checks.
4. **Question:** Algorithmic problems with multi-language starter codes and complexity specifications.
5. **TestCase:** Supports both public sample test cases and hidden evaluation cases with points.
6. **Assessment:** Timed exam records with duration, passing score %, immediate result release settings, and retake toggles.
7. **AssessmentQuestion:** Junction model mapping questions to assessments with custom mark allocations.
8. **AssessmentAttempt:** Tracks attempts with server-calculated `deadline_time = start_time + timedelta(minutes=duration)`.
9. **AttemptAnswer:** Stores question code, autosave timestamps, and marks earned.
10. **Submission & SubmissionTestResult:** Stores execution history, runtime, and individual test results.
11. **StudentProgress:** Aggregates topic-wise questions attempted, solved, and accuracy rate.
12. **AIConversation & AIMessage:** Chat sessions with clear `is_fallback` indicators.
13. **Notification:** Updates for published assessments, results, and study suggestions.

---

## 6. Installation & Windows / VS Code Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Windows PowerShell or Command Prompt.

### Step-by-Step Setup

1. **Open PowerShell in the Project Directory:**
   ```powershell
   cd "c:\Users\cnrme\Desktop\PROJECTS\CodeSphere project"
   ```

2. **Create and Activate Virtual Environment:**
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled on your Windows machine, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize Database & Seed Initial Data:**
   ```powershell
   python run.py seed
   ```
   This initializes tables and seeds standard DSA categories, coding problems with public & hidden test cases, a sample timed assessment, an administrator account, and a student account.

5. **Start the Development Server:**
   ```powershell
   python run.py
   ```
   Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Running in VS Code
1. Open the project folder in VS Code (`File -> Open Folder...`).
2. Press `Ctrl + Shift + P` and select **Python: Select Interpreter**.
3. Choose the virtual environment: `.\venv\Scripts\python.exe`.
4. Open the integrated terminal (`Ctrl + ~`) and start the app: `python run.py`.

---

## 7. Default User Accounts & Seeding

Running `python run.py seed` creates two pre-configured accounts:

| Role | Username | Email | Password | Access Portal |
|---|---|---|---|---|
| **Administrator** | `admin` | `admin@codesphere.io` | `Admin@CodeSphere2026!` | [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login) |
| **Student** | `student` | `student@codesphere.io` | `Student@CodeSphere2026!` | [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login) |

*You can also register new student accounts on the registration page.*

---

## 8. Module-by-Module Walkthrough

### Module 1: Authentication & RBAC
- **Student Registration:** Validates unique username, email format, password matching, academic college, and target role.
- **Login Portals:** Distinct student login and administrator portals (`/admin/login`). Students attempting to authenticate into the admin console are rejected.
- **Account State Checking:** Administrators can deactivate accounts; deactivated users are barred from logging in.
- **Password Hashing:** Implemented with `werkzeug.security.generate_password_hash` using salt and PBKDF2/SHA256.

### Module 2: Administrator Dashboard
- Displays registered student count, total questions, assessments created, completed assessment attempts, and average student score.
- Includes dynamic Chart.js doughnut chart of questions by difficulty (Easy, Medium, Hard) and bar chart of questions by topic.
- Displays recent student submissions and assessment completions.

### Module 3: Student Management
- Administrators can search students by name, username, or email.
- Filter students by account status (Active vs. Deactivated).
- View individual student profiles with coding statistics, topic accuracy breakdown, and assessment history.
- Toggle account activation state with a single click.

### Module 4: Topic Category Management
- Includes core placement topics: Arrays, Strings, Searching, Sorting, Recursion, Linked Lists, Stacks, Queues, Trees, Graphs, Greedy Algorithms, Dynamic Programming, OOP, DBMS, SQL, Operating Systems, and Computer Networks.
- **Safe Deletion Protection:** Categories cannot be deleted if active coding questions reference them.

### Module 5: Coding Question Bank
- Author coding questions with detailed problem statements (Markdown supported), constraints, sample inputs, sample outputs, explanations, and expected complexities ($O(N)$, $O(1)$).
- Starter code templates for Python 3, Java, and C++.
- Manage public sample test cases and hidden evaluation test cases with custom mark weightings.
- Filter questions by difficulty and topic.

### Module 6: Timed Assessment Engine & Security
- **Authoring:** Select questions from the question bank, assign custom marks to each, configure duration (e.g. 60 or 90 minutes), pass %, and result release visibility.
- **Server-Side Deadline Enforcement:** When a student clicks "Start Assessment", `start_time = datetime.utcnow()` and `deadline_time = start_time + timedelta(minutes=duration)` are committed to the database. The client cannot forge or extend time.
- **Autosave & Safe Resumption:** Student code is autosaved via AJAX every 20 seconds. If a connection drops, the student can resume without losing saved work.
- **Timeout Submission:** If the student's deadline passes, the system finalizes the attempt as `timed_out` and grades all saved answers.
- **Hidden Test Case Protection:** Hidden test inputs/outputs are never returned to client AJAX requests during the assessment.
- **CSV Export:** Administrators can export complete attempt logs, marks, percentages, and timestamps in one click.

### Module 7: Student Performance Analytics
- Calculates total questions attempted, solved, and overall accuracy percentage from active database rows.
- **Defensive Math:** Handles new accounts with 0 activity safely without division-by-zero errors.
- Visualizes problem-solving mastery with a Chart.js doughnut, topic accuracy bars, and assessment score progression line charts.
- Identifies **Weak Topics** (accuracy < 50%) and highlights **Strong Topics** (accuracy $\ge$ 70%).

### Module 8: AI Learning Assistant & Fallback Engine
- **Concept Explainer:** Answers technical questions with analogies, Big-O analysis, and clean code examples.
- **Progressive Coding Hints:** Provides 3 graduated hint levels (Level 1: Intuition, Level 2: Strategy, Level 3: Edge Cases & Pseudo-logic).
- **Code Debugger:** Analyzes submitted code alongside runtime errors or output mismatches and explains bugs without giving away answers.
- **Adaptive Study Plan:** Analyzes real student accuracy and weak areas to generate a 2- to 12-week study plan for target roles.
- **100% Offline Fallback:** If `OPENAI_API_KEY` is not provided, the assistant continues working using its offline rule-based educational engine. Fallback answers are labeled: `Fallback Tutor Engine (Offline Mode)`.
- **Rate Limiting:** Protects endpoints with a sliding window rate limiter (max 15 requests/minute per student).

### Module 9: Isolated Sandboxed Code Execution
- Uses standard Python `subprocess.run` inside an isolated temporary directory.
- Never runs arbitrary code using `eval()` or `exec()` in the Flask web process.
- Hard timeout limits (default 4 seconds) to prevent infinite loops (TLE - Time Limit Exceeded).
- Pre-execution static analysis rejects forbidden modules (`os`, `subprocess`, `socket`, `shutil`).
- Compares normalized standard output with expected outputs.

### Module 10: Notification Feed
- Informs students about newly published assessments, completed test results, and focus recommendations.
- Interactive mark-as-read buttons and "Mark All as Read" actions.

---

## 9. AI API Configuration & Cost Estimates

CodeSphere uses the official OpenAI Python SDK. By default, it operates in offline fallback mode if no key is supplied.

### Configuring OpenAI
1. Get an API key from [platform.openai.com](https://platform.openai.com/api-keys).
2. Open your `.env` file and set your key:
   ```env
   OPENAI_API_KEY=sk-proj-your-actual-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Restart the server: `python run.py`.
4. The footer status will update to: **`OpenAI Engine Online`**.

### Expected Costs
- Model: `gpt-4o-mini` (approx. $0.15 per million input tokens, $0.60 per million output tokens).
- A typical concept explanation or hint uses ~300 to 600 tokens (~$0.0001 per query).
- A class of 100 students conducting 1,000 queries total costs less than **$0.15 to $0.25 USD**.

---

## 10. Automated Test Suite (Pytest)

The repository includes 35 comprehensive automated tests covering all functional requirements.

To run the complete test suite:
```powershell
.\venv\Scripts\python.exe -m pytest -v
```

### Test Coverage Highlights
- `tests/test_auth.py`: Registration, validation, duplicate prevention, student & admin logins, deactivation checks, logout.
- `tests/test_permissions.py`: Route protection, student data isolation on assessment attempts.
- `tests/test_categories.py`: Category creation, editing, safe deletion verification.
- `tests/test_questions.py`: Question creation, difficulty assignment, public vs hidden test case management, solution submission.
- `tests/test_assessments.py`: Assessment creation, question weighting, autosave, server deadline validation, CSV export.
- `tests/test_code_executor.py`: Subprocess sandboxing, security check (blocking malicious calls), TLE timeout.
- `tests/test_analytics.py`: Real-time calculations, zero-activity edge cases, admin platform statistics.
- `tests/test_ai_fallback.py`: Offline concept tutor, progressive hints, code debugging, study plan generation, rate limiting.

---

## 11. Production Deployment & PostgreSQL Guide

### Switching from SQLite to PostgreSQL
1. Install PostgreSQL driver:
   ```powershell
   pip install psycopg2-binary
   ```
2. In `.env`, change `DATABASE_URL`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/codespheredb
   ```
3. Run `python run.py seed` to create tables and seed initial records in PostgreSQL.

### Production Environment Settings
In production, set:
```env
FLASK_ENV=production
SECRET_KEY=generate-a-strong-random-key-with-openssl-rand-hex-32
```

Use a WSGI server like Gunicorn (on Linux) or Waitress (on Windows):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

---

## 12. Beginner's Code Guide & Troubleshooting

### How It Works Under the Hood
1. **Application Factory (`app/__init__.py`):** Creates the Flask application object, registers database extensions, and mounts route blueprints.
2. **Extensions Pattern (`app/extensions.py`):** Extensions like `db` and `login_manager` are defined unattached to prevent circular imports.
3. **Subprocess Runner (`app/services/code_executor.py`):** When you click "Run Sample Test", Flask writes your code to a temporary file, executes it in a separate Python process with input on `stdin`, and returns the output to the browser via JSON.

### Common Questions & Troubleshooting

- **Error: `ModuleNotFoundError: No module named 'app'` when running pytest**
  - **Solution:** Run pytest using the python module runner: `.\venv\Scripts\python.exe -m pytest -v`. This adds the workspace root to `sys.path`.
- **Autosave during assessments:**
  - Code answers autosave every 20 seconds. If you close your browser accidentally, navigate back to `/assessments` and click **"Resume Assessment"**.
- **Can students see hidden test cases?**
  - No. Hidden test cases are marked `is_hidden = True` and are withheld from student-facing API endpoints.
