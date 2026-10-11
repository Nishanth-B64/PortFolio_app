import os
import re
import uuid
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "student-skill-portfolio-secure-key-2026")

MONGODB_URI = os.environ.get("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI must be set in the environment or .env file.")

MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "student_skill_portfolio")
STATE_DOCUMENT_ID = "portfolio"
mongo_client = MongoClient(MONGODB_URI)
state_collection = mongo_client[MONGODB_DATABASE]["app_state"]

VALID_SKILL_CATEGORIES = [
    "Programming",
    "Web Development",
    "Database",
    "Tools",
    "Soft Skills"
]

DEFAULT_DATABASE_STRUCTURE = {
    "users": []
}


def load_db():
    """Load portfolio data from Atlas, initializing an empty user list when needed."""
    document = state_collection.find_one({"_id": STATE_DOCUMENT_ID})
    if document is None:
        state_collection.update_one(
            {"_id": STATE_DOCUMENT_ID},
            {"$setOnInsert": DEFAULT_DATABASE_STRUCTURE},
            upsert=True
        )
        document = state_collection.find_one({"_id": STATE_DOCUMENT_ID})
        if document is None:
            raise RuntimeError("Could not initialize portfolio data in MongoDB.")

    users = document.get("users", [])
    if not isinstance(users, list):
        raise ValueError("MongoDB portfolio data must contain a users list.")
    return {"users": users}


def save_db(data):
    """Persist portfolio data to Atlas."""
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        raise ValueError("Portfolio data must contain a users list.")

    state_collection.replace_one(
        {"_id": STATE_DOCUMENT_ID},
        {"_id": STATE_DOCUMENT_ID, "users": data["users"]},
        upsert=True
    )
    return True


def get_current_user_and_db():
    """Return tuple of (current_user_dict, db_dict)."""
    user_id = session.get("user_id")
    if not user_id:
        return None, None
    db = load_db()
    for u in db.get("users", []):
        if u.get("id") == user_id:
            return u, db
    return None, db


def log_activity(user, text, activity_type="general"):
    """Record an action in user's recent activities list."""
    if "activities" not in user:
        user["activities"] = []

    activity = {
        "id": f"act_{uuid.uuid4().hex[:6]}",
        "text": text,
        "type": activity_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    user["activities"].insert(0, activity)
    user["activities"] = user["activities"][:25]


def calculate_completion(user):
    """
    Calculate portfolio completion percentage and checklist items for a user.
    """
    profile = user.get("profile", {})
    skills = user.get("skills", [])
    certificates = user.get("certificates", [])
    projects = user.get("projects", [])

    checks = [
        {
            "label": "Full Name Provided",
            "weight": 15,
            "completed": bool(profile.get("name", "").strip()),
            "tip": "Enter your full name in Profile Settings"
        },
        {
            "label": "Contact Information",
            "weight": 10,
            "completed": bool(profile.get("email", "").strip() and profile.get("phone", "").strip()),
            "tip": "Add both email and phone in Profile Settings"
        },
        {
            "label": "Academic & College Details",
            "weight": 15,
            "completed": bool(profile.get("college", "").strip() and profile.get("course", "").strip()),
            "tip": "Specify college and degree program"
        },
        {
            "label": "Career Objective & Summary",
            "weight": 15,
            "completed": bool(profile.get("career_objective", "").strip() and profile.get("profile_summary", "").strip()),
            "tip": "Draft your career objective and professional summary"
        },
        {
            "label": "Skills Added (Minimum 3)",
            "weight": 15,
            "completed": len(skills) >= 3,
            "tip": f"Currently {len(skills)}/3 skills added"
        },
        {
            "label": "Certificates Added (Minimum 1)",
            "weight": 15,
            "completed": len(certificates) >= 1,
            "tip": "Add at least one course or cloud certification"
        },
        {
            "label": "Projects Showcased (Minimum 1)",
            "weight": 15,
            "completed": len(projects) >= 1,
            "tip": "Showcase at least one software or capstone project"
        }
    ]

    total_pct = sum(c["weight"] for c in checks if c["completed"])
    total_pct = min(100, max(0, total_pct))
    return total_pct, checks


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in") or not session.get("user_id"):
            session.clear()
            flash("Please sign in or register to access the portfolio manager dashboard.", "warning")
            return redirect(url_for("login"))
        user, _ = get_current_user_and_db()
        if not user:
            session.clear()
            flash("Session expired or user not found. Please log in again.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
# Authentication & Registration Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if session.get("logged_in") and session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        college = request.form.get("college", "").strip()
        course = request.form.get("course", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validation
        if not name or not username or not email or not password or not college or not course:
            flash("Please fill in all required registration fields.", "danger")
            return render_template("register.html")

        if len(username) < 3 or not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            flash("Username must be at least 3 characters and contain only letters, numbers, dots, or underscores.", "danger")
            return render_template("register.html")

        if "@" not in email or "." not in email:
            flash("Please provide a valid email address.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter carefully.", "danger")
            return render_template("register.html")

        db = load_db()
        users = db.get("users", [])

        # Check uniqueness of username and email
        for u in users:
            if u.get("username", "").lower() == username.lower():
                flash(f"Username '{username}' is already taken. Please choose another.", "danger")
                return render_template("register.html")
            if u.get("email", "").lower() == email.lower():
                flash(f"An account with email '{email}' already exists. Please log in instead.", "danger")
                return render_template("register.html")

        # Create new user record
        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        new_user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "profile": {
                "name": name,
                "email": email,
                "phone": "",
                "college": college,
                "department": "",
                "course": course,
                "graduation_year": "",
                "location": "",
                "career_objective": "",
                "profile_summary": "",
                "github": "",
                "linkedin": ""
            },
            "skills": [],
            "certificates": [],
            "projects": [],
            "activities": [
                {
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"Account registered for {name}.",
                    "type": "profile",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            ]
        }

        db.setdefault("users", []).append(new_user)
        save_db(db)

        # Establish session
        session["logged_in"] = True
        session["user_id"] = user_id
        session["username"] = username

        flash(f"Registration successful! Welcome to Student Skill Portfolio Manager, {name}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in") and session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        login_id = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not login_id or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        db = load_db()
        users = db.get("users", [])

        matched_user = None
        for u in users:
            if u.get("username", "").lower() == login_id.lower() or u.get("email", "").lower() == login_id.lower():
                matched_user = u
                break

        if matched_user and check_password_hash(matched_user.get("password_hash", ""), password):
            session["logged_in"] = True
            session["user_id"] = matched_user.get("id")
            session["username"] = matched_user.get("username")
            user_name = matched_user.get("profile", {}).get("name", matched_user.get("username"))
            flash(f"Welcome back, {user_name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please verify your credentials or register a new account.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard Route
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    user, _ = get_current_user_and_db()
    profile = user.get("profile", {})
    skills = user.get("skills", [])
    certificates = user.get("certificates", [])
    projects = user.get("projects", [])
    activities = user.get("activities", [])

    completion_pct, checklist = calculate_completion(user)

    # Category breakdown for user's skills
    category_counts = {cat: 0 for cat in VALID_SKILL_CATEGORIES}
    category_ratings = {cat: [] for cat in VALID_SKILL_CATEGORIES}
    for s in skills:
        cat = s.get("category", "Tools")
        if cat in category_counts:
            category_counts[cat] += 1
            category_ratings[cat].append(int(s.get("proficiency", 1)))
        else:
            category_counts.setdefault(cat, 0)
            category_counts[cat] += 1
            category_ratings.setdefault(cat, []).append(int(s.get("proficiency", 1)))

    category_stats = []
    for cat in VALID_SKILL_CATEGORIES:
        count = category_counts.get(cat, 0)
        ratings = category_ratings.get(cat, [])
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0
        category_stats.append({
            "category": cat,
            "count": count,
            "avg_rating": avg_rating
        })

    recent_projects = projects[:3]

    return render_template(
        "dashboard.html",
        profile=profile,
        total_skills=len(skills),
        total_certificates=len(certificates),
        total_projects=len(projects),
        completion_pct=completion_pct,
        checklist=checklist,
        activities=activities[:10],
        category_stats=category_stats,
        recent_projects=recent_projects
    )


# ---------------------------------------------------------------------------
# Profile Management Routes
# ---------------------------------------------------------------------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user, db = get_current_user_and_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        college = request.form.get("college", "").strip()
        department = request.form.get("department", "").strip()
        course = request.form.get("course", "").strip()
        graduation_year = request.form.get("graduation_year", "").strip()
        location = request.form.get("location", "").strip()
        career_objective = request.form.get("career_objective", "").strip()
        profile_summary = request.form.get("profile_summary", "").strip()
        github = request.form.get("github", "").strip()
        linkedin = request.form.get("linkedin", "").strip()

        if not name or not email:
            flash("Full Name and Email are mandatory fields.", "danger")
            return redirect(url_for("profile"))

        user["profile"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "college": college,
            "department": department,
            "course": course,
            "graduation_year": graduation_year,
            "location": location,
            "career_objective": career_objective,
            "profile_summary": profile_summary,
            "github": github,
            "linkedin": linkedin
        }
        # Update user's primary email as well
        user["email"] = email

        log_activity(user, f"Profile updated for {name}.", "profile")
        save_db(db)
        flash("Your profile information has been successfully updated!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", profile=user.get("profile", {}))


@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not current_password or not new_password:
        flash("Please provide all required password fields.", "danger")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("New password and confirm password do not match.", "danger")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
        return redirect(url_for("profile"))

    user, db = get_current_user_and_db()
    if not check_password_hash(user.get("password_hash", ""), current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile"))

    user["password_hash"] = generate_password_hash(new_password)
    log_activity(user, "Account password successfully changed.", "security")
    save_db(db)
    flash("Password updated successfully! Please keep it secure.", "success")
    return redirect(url_for("profile"))


# ---------------------------------------------------------------------------
# Skills Management Routes
# ---------------------------------------------------------------------------

@app.route("/skills")
@login_required
def skills():
    user, _ = get_current_user_and_db()
    return render_template(
        "skills.html",
        skills=user.get("skills", []),
        categories=VALID_SKILL_CATEGORIES,
        profile=user.get("profile", {})
    )


@app.route("/skills/add", methods=["POST"])
@login_required
def add_skill():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    proficiency = request.form.get("proficiency", "1").strip()

    if not name:
        flash("Skill name cannot be empty.", "danger")
        return redirect(url_for("skills"))

    if category not in VALID_SKILL_CATEGORIES:
        category = "Tools"

    try:
        prof_val = int(proficiency)
        if prof_val < 1 or prof_val > 5:
            prof_val = 3
    except ValueError:
        prof_val = 3

    user, db = get_current_user_and_db()
    new_skill = {
        "id": f"sk_{uuid.uuid4().hex[:6]}",
        "name": name,
        "category": category,
        "proficiency": prof_val,
        "updated_at": datetime.now().strftime("%Y-%m-%d")
    }

    user.setdefault("skills", []).append(new_skill)
    log_activity(user, f"Added skill '{name}' ({category}) rated {prof_val}/5.", "skill")
    save_db(db)
    flash(f"Skill '{name}' added successfully!", "success")
    return redirect(url_for("skills"))


@app.route("/skills/edit/<skill_id>", methods=["POST"])
@login_required
def edit_skill(skill_id):
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    proficiency = request.form.get("proficiency", "1").strip()

    if not name:
        flash("Skill name cannot be empty.", "danger")
        return redirect(url_for("skills"))

    if category not in VALID_SKILL_CATEGORIES:
        category = "Tools"

    try:
        prof_val = int(proficiency)
        if prof_val < 1 or prof_val > 5:
            prof_val = 3
    except ValueError:
        prof_val = 3

    user, db = get_current_user_and_db()
    skills_list = user.get("skills", [])
    found = False
    for s in skills_list:
        if s.get("id") == skill_id:
            s["name"] = name
            s["category"] = category
            s["proficiency"] = prof_val
            s["updated_at"] = datetime.now().strftime("%Y-%m-%d")
            found = True
            break

    if found:
        log_activity(user, f"Updated skill '{name}' to {prof_val}/5 rating.", "skill")
        save_db(db)
        flash(f"Skill '{name}' updated successfully!", "success")
    else:
        flash("Skill record not found.", "warning")

    return redirect(url_for("skills"))


@app.route("/skills/delete/<skill_id>", methods=["POST"])
@login_required
def delete_skill(skill_id):
    user, db = get_current_user_and_db()
    skills_list = user.get("skills", [])
    initial_len = len(skills_list)
    removed_name = ""

    for s in skills_list:
        if s.get("id") == skill_id:
            removed_name = s.get("name", "Skill")
            break

    user["skills"] = [s for s in skills_list if s.get("id") != skill_id]

    if len(user["skills"]) < initial_len:
        log_activity(user, f"Deleted skill '{removed_name}'.", "skill")
        save_db(db)
        flash(f"Skill '{removed_name}' deleted.", "info")
    else:
        flash("Skill record could not be found.", "warning")

    return redirect(url_for("skills"))


# ---------------------------------------------------------------------------
# Certificate Management Routes
# ---------------------------------------------------------------------------

@app.route("/certificates")
@login_required
def certificates():
    user, _ = get_current_user_and_db()
    return render_template(
        "certificates.html",
        certificates=user.get("certificates", []),
        profile=user.get("profile", {})
    )


@app.route("/certificates/add", methods=["POST"])
@login_required
def add_certificate():
    title = request.form.get("title", "").strip()
    issuer = request.form.get("issuer", "").strip()
    issue_date = request.form.get("issue_date", "").strip()
    credential_id = request.form.get("credential_id", "").strip()
    url = request.form.get("url", "").strip()

    if not title or not issuer:
        flash("Certificate Title and Issuing Organization are required.", "danger")
        return redirect(url_for("certificates"))

    user, db = get_current_user_and_db()
    new_cert = {
        "id": f"cert_{uuid.uuid4().hex[:6]}",
        "title": title,
        "issuer": issuer,
        "issue_date": issue_date or datetime.now().strftime("%Y-%m-%d"),
        "credential_id": credential_id,
        "url": url,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    user.setdefault("certificates", []).append(new_cert)
    log_activity(user, f"Added certificate '{title}' issued by {issuer}.", "certificate")
    save_db(db)
    flash(f"Certificate '{title}' added successfully!", "success")
    return redirect(url_for("certificates"))


@app.route("/certificates/edit/<cert_id>", methods=["POST"])
@login_required
def edit_certificate(cert_id):
    title = request.form.get("title", "").strip()
    issuer = request.form.get("issuer", "").strip()
    issue_date = request.form.get("issue_date", "").strip()
    credential_id = request.form.get("credential_id", "").strip()
    url = request.form.get("url", "").strip()

    if not title or not issuer:
        flash("Certificate Title and Issuing Organization are required.", "danger")
        return redirect(url_for("certificates"))

    user, db = get_current_user_and_db()
    cert_list = user.get("certificates", [])
    found = False

    for c in cert_list:
        if c.get("id") == cert_id:
            c["title"] = title
            c["issuer"] = issuer
            c["issue_date"] = issue_date or c.get("issue_date")
            c["credential_id"] = credential_id
            c["url"] = url
            found = True
            break

    if found:
        log_activity(user, f"Updated certificate '{title}'.", "certificate")
        save_db(db)
        flash(f"Certificate '{title}' updated successfully!", "success")
    else:
        flash("Certificate record not found.", "warning")

    return redirect(url_for("certificates"))


@app.route("/certificates/delete/<cert_id>", methods=["POST"])
@login_required
def delete_certificate(cert_id):
    user, db = get_current_user_and_db()
    cert_list = user.get("certificates", [])
    initial_len = len(cert_list)
    removed_title = ""

    for c in cert_list:
        if c.get("id") == cert_id:
            removed_title = c.get("title", "Certificate")
            break

    user["certificates"] = [c for c in cert_list if c.get("id") != cert_id]

    if len(user["certificates"]) < initial_len:
        log_activity(user, f"Deleted certificate '{removed_title}'.", "certificate")
        save_db(db)
        flash(f"Certificate '{removed_title}' deleted.", "info")
    else:
        flash("Certificate record not found.", "warning")

    return redirect(url_for("certificates"))


# ---------------------------------------------------------------------------
# Project Management Routes
# ---------------------------------------------------------------------------

@app.route("/projects")
@login_required
def projects():
    user, _ = get_current_user_and_db()
    return render_template(
        "projects.html",
        projects=user.get("projects", []),
        profile=user.get("profile", {})
    )


@app.route("/projects/add", methods=["POST"])
@login_required
def add_project():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    technologies = request.form.get("technologies", "").strip()
    duration = request.form.get("duration", "").strip()
    github_url = request.form.get("github_url", "").strip()
    demo_url = request.form.get("demo_url", "").strip()

    if not title or not description:
        flash("Project Title and Description are required.", "danger")
        return redirect(url_for("projects"))

    user, db = get_current_user_and_db()
    new_project = {
        "id": f"proj_{uuid.uuid4().hex[:6]}",
        "title": title,
        "description": description,
        "technologies": technologies,
        "duration": duration,
        "github_url": github_url,
        "demo_url": demo_url,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    user.setdefault("projects", []).append(new_project)
    log_activity(user, f"Added project '{title}'.", "project")
    save_db(db)
    flash(f"Project '{title}' added successfully!", "success")
    return redirect(url_for("projects"))


@app.route("/projects/edit/<project_id>", methods=["POST"])
@login_required
def edit_project(project_id):
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    technologies = request.form.get("technologies", "").strip()
    duration = request.form.get("duration", "").strip()
    github_url = request.form.get("github_url", "").strip()
    demo_url = request.form.get("demo_url", "").strip()

    if not title or not description:
        flash("Project Title and Description are required.", "danger")
        return redirect(url_for("projects"))

    user, db = get_current_user_and_db()
    proj_list = user.get("projects", [])
    found = False

    for p in proj_list:
        if p.get("id") == project_id:
            p["title"] = title
            p["description"] = description
            p["technologies"] = technologies
            p["duration"] = duration
            p["github_url"] = github_url
            p["demo_url"] = demo_url
            found = True
            break

    if found:
        log_activity(user, f"Updated project '{title}'.", "project")
        save_db(db)
        flash(f"Project '{title}' updated successfully!", "success")
    else:
        flash("Project record not found.", "warning")

    return redirect(url_for("projects"))


@app.route("/projects/delete/<project_id>", methods=["POST"])
@login_required
def delete_project(project_id):
    user, db = get_current_user_and_db()
    proj_list = user.get("projects", [])
    initial_len = len(proj_list)
    removed_title = ""

    for p in proj_list:
        if p.get("id") == project_id:
            removed_title = p.get("title", "Project")
            break

    user["projects"] = [p for p in proj_list if p.get("id") != project_id]

    if len(user["projects"]) < initial_len:
        log_activity(user, f"Deleted project '{removed_title}'.", "project")
        save_db(db)
        flash(f"Project '{removed_title}' deleted.", "info")
    else:
        flash("Project record not found.", "warning")

    return redirect(url_for("projects"))


# ---------------------------------------------------------------------------
# Portfolio Preview Route (Print-Friendly & Resume Presentation)
# ---------------------------------------------------------------------------

@app.route("/portfolio")
@login_required
def portfolio():
    user, _ = get_current_user_and_db()
    profile = user.get("profile", {})
    skills = user.get("skills", [])
    certificates = user.get("certificates", [])
    projects = user.get("projects", [])

    # Group skills by category for neat portfolio sections
    skills_by_category = {}
    for cat in VALID_SKILL_CATEGORIES:
        matching = [s for s in skills if s.get("category") == cat]
        if matching:
            skills_by_category[cat] = matching

    other_skills = [s for s in skills if s.get("category") not in VALID_SKILL_CATEGORIES]
    if other_skills:
        skills_by_category["Other"] = other_skills

    completion_pct, _ = calculate_completion(user)

    # Note: Sensitive auth data is NEVER passed to the template
    return render_template(
        "portfolio.html",
        profile=profile,
        skills_by_category=skills_by_category,
        certificates=certificates,
        projects=projects,
        completion_pct=completion_pct,
        generated_date=datetime.now().strftime("%B %d, %Y")
    )


# ---------------------------------------------------------------------------
# Utility Routes
# ---------------------------------------------------------------------------

@app.route("/activity/clear", methods=["POST"])
@login_required
def clear_activities():
    user, db = get_current_user_and_db()
    user["activities"] = []
    log_activity(user, "Activity history cleared.", "system")
    save_db(db)
    flash("Activity history cleared.", "info")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
