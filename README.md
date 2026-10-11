# Student Skill Portfolio Manager

A modern, responsive, and lightweight web application built with **Python Flask**, **Vanilla CSS3**, **HTML5**, and **MongoDB Atlas**. Designed for undergraduate and postgraduate students to track, categorize, and showcase technical competencies, academic coursework, verified certifications, and software projects—with instant print-to-PDF portfolio and resume generation.

---

## 1. Project Overview & College Submission Documentation

### A. Problem Statement
In academic institutions, students frequently acquire diverse competencies across varied domains—programming languages, full-stack frameworks, cloud certifications, and capstone projects. However, this data is often scattered across disparate platforms (LinkedIn, GitHub, local folders, course portals), leading to:
- Disorganized records when applying for competitive internships and campus placements.
- Lack of self-assessment regarding portfolio readiness and missing profile components.
- Inability to quickly generate an executive, clean, verified curriculum vitae / portfolio document tailored for technical recruiters.

### B. Project Objectives
1. **Centralized Competency Repository**: Provide a single, authenticated dashboard to manage skills, ratings, certifications, and software projects.
2. **Readiness Tracking**: Calculate and visualize dynamic portfolio completion percentages and pending task checklists in real time.
3. **Categorized Proficiencies**: Organize skills across 5 defined disciplines (*Programming*, *Web Development*, *Database*, *Tools*, and *Soft Skills*) with 1–5 level ratings.
4. **Credential Verification**: Store verified certificate credential IDs and direct validation URLs.
5. **Print-to-PDF Portfolio Generation**: Provide an executive portfolio presentation with responsive print media stylesheets (`@media print`) enabling 1-click PDF resume creation without external dependencies.
6. **Cloud Persistence**: Store user portfolio data in MongoDB Atlas, configured through environment variables.

### C. System Architecture
```
                         +-----------------------------+
                         |       Client Browser        |
                         |  (HTML5 / CSS3 / ES6 JS)   |
                         +--------------+--------------+
                                        |  HTTP / REST
                                        v
                         +-----------------------------+
                         |      Flask Backend App      |
                         |          (app.py)           |
                         +--------------+--------------+
                                        |
                 +----------------------+----------------------+
                 |                      |                      |
                 v                      v                      v
        +----------------+     +----------------+     +----------------+
        | Session Auth   |     | Jinja2 Engine  |     | MongoDB Atlas  |
        | & Route Guard  |     | (Templates)    |     | Persistence    |
        +----------------+     +----------------+     +--------+-------+
```

---

## 2. Technology Stack

- **Backend Framework**: Python 3 (Flask 3.1+)
- **Security & Hashing**: Werkzeug (`generate_password_hash`, `check_password_hash`)
- **Data Persistence**: MongoDB Atlas using PyMongo
- **Frontend / Templating**: HTML5, Jinja2 Templates
- **Styling**: Vanilla CSS3 (Custom Design System with Deep Navy, Royal Blue, and Slate Palette)
- **Client Scripting**: Vanilla JavaScript (ES6+) for live filtering, search, and accessible `<dialog>` modals
- **Icons**: Font Awesome 6 (Free CDN)
- **Typography**: Plus Jakarta Sans & Inter (Google Fonts)

---

## 3. Folder Structure

```
student_skill_portfolio/
│
├── app.py                  # Core Flask server, routes, validation, and MongoDB persistence
├── .env                    # Local MongoDB connection settings (not committed)
├── requirements.txt        # Python dependency manifest
├── test_app.py             # Automated unit & integration test suite
├── README.md               # Project documentation, college submission details & setup guide
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout with responsive sidebar, topbar & flash notifications
│   ├── login.html          # Authentication portal with register link
│   ├── register.html       # User registration page for creating new student accounts
│   ├── dashboard.html      # Overview with metric cards, completion meter & activity timeline
│   ├── profile.html        # Academic & contact details form with live preview card
│   ├── skills.html         # Skills management, 1-5 ratings, progress bars & category pills
│   ├── certificates.html   # Certifications with credential chips & external verify links
│   ├── projects.html       # Project showcase cards, tech badges, sorting & repository links
│   └── portfolio.html      # Executive CV / Portfolio document with print-to-PDF optimization
│
└── static/                 # Static web assets
    ├── style.css           # Modern CSS3 design system, responsive breakpoints & @media print
    └── script.js           # Client-side search filters, sorting, modals & toast timers
```

---

## 4. User Registration & Authentication System

The application features a clean, dynamic registration and authentication system with **zero hardcoded credentials or details**:

1. **Register New User**: Visit `/register` to create a personal account (Full Name, Username, Email, College, Course, and Password).
2. **Account Security**: Passwords are encrypted using Scrypt hashing (`werkzeug.security.generate_password_hash`).
3. **Multi-User Isolation**: Each registered student gets an independent portfolio, skills list, project showcase, and certificate records stored in MongoDB Atlas.
4. **Login**: Sign in using your registered username or email address and password at `/login`.

---

## 5. Installation and Execution Instructions

### Prerequisites
- Python 3.9 or higher installed on your computer.
- Terminal / PowerShell / Command Prompt.

### Step 1: Clone or Navigate to the Project Directory
```bash
cd "d:\web pgrm"
```

### Step 2: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure MongoDB Atlas
Set `MONGODB_URI` to your Atlas connection string in a local `.env` file. The app uses the `student_skill_portfolio` database by default; optionally set `MONGODB_DATABASE` to use another database name. Add the machine's IP address to the Atlas project's network access list and ensure the database user has read/write access.

The application does not import any previous local JSON data. It starts with an empty portfolio in Atlas and stores registrations and updates there from then on.

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Access in Your Browser
Open your preferred web browser and navigate to:
```
http://127.0.0.1:5000
```
Register a new account or log in with an account that has been migrated to Atlas.

### Deploying on Render
1. Push this project to a GitHub repository. Keep `.env` out of Git; `.gitignore` already excludes it.
2. In Render, create a **New Web Service** from that repository and select the Python runtime.
3. Use `pip install -r requirements.txt` as the build command and `gunicorn app:app --bind 0.0.0.0:$PORT` as the start command.
4. In the Render service's **Environment** settings, add `MONGODB_URI` with the Atlas connection string and `FLASK_SECRET_KEY` with a newly generated secret. Optionally set `MONGODB_DATABASE` (defaults to `student_skill_portfolio`). Do not commit these values to Git.
5. In MongoDB Atlas, allow connections from Render. For a Render service without static outbound IPs, Atlas may require `0.0.0.0/0`; use a dedicated database user with only the required read/write permissions and a strong password. If you have static outbound IPs, allow only those instead.
6. Deploy the service and open its `onrender.com` URL. Check Render's logs if startup or Atlas connection fails.

---

## 6. Running Automated Tests

To verify that all routes, validation checks, CRUD operations, and session guards function as expected:

```bash
python test_app.py
```

Expected output:
```
Ran 12 tests
OK
```

---

## 7. Step-by-Step Feature Testing Guide

| Feature | Action to Test | Expected Behavior |
| :--- | :--- | :--- |
| **Authentication** | Access `http://127.0.0.1:5000/dashboard` without logging in. | Redirected to `/login` with an informational warning. |
| **Login Validation** | Enter incorrect password on `/login`. | An error alert displays: *"Invalid username or password"*. |
| **Login Success** | Enter the username or email and password for a registered account. | Authenticated into the dashboard with a welcome flash alert. |
| **Dashboard Metrics** | Check the 4 metric cards and readiness meter. | Displays total counts, dynamic completion score, and category distribution. |
| **Skills Filter & Search** | Go to **Skills**, click category pills (*Programming*, *Web Development*) or type in search. | Cards filter instantly in real time without page reloads. |
| **Add / Edit Skill** | Click **Add New Skill**, provide name and 1–5 rating. | Skill is persisted to MongoDB Atlas, activity is logged, card renders with 5-star rating. |
| **Certificates** | Click **Add Certificate**, provide title, issuer, credential ID, and URL. | Card displays verified issuer badge, copyable ID button, and direct external verification link. |
| **Projects Showcase** | Add a project with comma-separated tech stack and repo URL. Select **Sort by Title** or **Date**. | Cards rearrange dynamically and display formatted pill badges. |
| **Profile Settings** | Edit career objective and name in **Profile Settings**. | Live preview card updates instantly; changes persist to database. |
| **Portfolio Print to PDF** | Click **View Portfolio** (topbar or sidebar), then click **Print / Save as PDF**. | Browser print dialog opens. Action bars and sidebars hide, rendering a pristine, multi-page PDF document. |
| **Logout** | Click **Logout** from topbar or sidebar. | Session is destroyed, redirects to `/login`. |

---

## 8. Conclusion
The **Student Skill Portfolio Manager** delivers a robust, accessible management system tailored for university submissions and career preparation. Flask and MongoDB Atlas provide persistent cloud storage while the app produces recruiter-ready portfolio exports.
