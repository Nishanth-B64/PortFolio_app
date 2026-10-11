import copy
import unittest
from unittest.mock import patch

import app as app_module
from app import app, load_db, save_db


class InMemoryCollection:
    def __init__(self):
        self.document = None

    def find_one(self, query):
        if self.document and self.document.get("_id") == query.get("_id"):
            return copy.deepcopy(self.document)
        return None

    def update_one(self, query, update, upsert=False):
        if self.document is None and upsert:
            self.document = {"_id": query["_id"], **update.get("$setOnInsert", {})}

    def replace_one(self, query, replacement, upsert=False):
        if self.document is not None or upsert:
            self.document = copy.deepcopy(replacement)

class StudentPortfolioTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.collection_patcher = patch.object(app_module, "state_collection", InMemoryCollection())
        self.collection_patcher.start()
        save_db({"users": []})

    def tearDown(self):
        self.collection_patcher.stop()

    def register_user(self, name="Sarah Connor", username="sarahc", email="sarah@tech.edu",
                      college="Cyberdyne Institute", course="B.Tech Computer Science",
                      password="secretPassword123", confirm_password="secretPassword123"):
        return self.client.post('/register', data={
            'name': name,
            'username': username,
            'email': email,
            'college': college,
            'course': course,
            'password': password,
            'confirm_password': confirm_password
        }, follow_redirects=True)

    def login_user(self, username="sarahc", password="secretPassword123"):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_unauthenticated_access_redirects(self):
        """Ensure protected pages redirect to login for guests."""
        for endpoint in ['/dashboard', '/skills', '/certificates', '/projects', '/profile', '/portfolio']:
            res = self.client.get(endpoint, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Endpoint {endpoint} should redirect unauthenticated users")
            self.assertIn('/login', res.headers['Location'])

    def test_registration_success(self):
        """Test registration of a new student without hardcoded credentials."""
        res = self.register_user()
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Registration successful", res.data)
        self.assertIn(b"Sarah Connor", res.data)
        
        db = load_db()
        self.assertEqual(len(db['users']), 1)
        user = db['users'][0]
        self.assertEqual(user['username'], 'sarahc')
        self.assertEqual(user['email'], 'sarah@tech.edu')
        self.assertEqual(user['profile']['name'], 'Sarah Connor')
        self.assertEqual(user['skills'], [])
        self.assertEqual(user['certificates'], [])
        self.assertEqual(user['projects'], [])

    def test_registration_duplicate_checks(self):
        """Test that registering duplicate username or email is prevented."""
        self.register_user(username="uniqueuser", email="user1@edu.com")
        self.client.get('/logout', follow_redirects=True)
        
        # Duplicate username
        res = self.register_user(name="Another User", username="uniqueuser", email="user2@edu.com")
        self.assertIn(b"already taken", res.data)

        # Duplicate email
        res = self.register_user(name="Another User", username="otheruser", email="user1@edu.com")
        self.assertIn(b"already exists", res.data)

    def test_registration_password_mismatch(self):
        """Test that mismatched passwords fail registration."""
        res = self.register_user(username="mismatchuser", password="passwordOne", confirm_password="passwordTwo")
        self.assertIn(b"Passwords do not match", res.data)

    def test_login_invalid_credentials(self):
        """Test login with incorrect password or unregistered username."""
        self.register_user()
        self.client.get('/logout', follow_redirects=True)

        res = self.client.post('/login', data={'username': 'sarahc', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid username or password", res.data)

    def test_login_valid_credentials(self):
        """Test login with registered student credentials."""
        self.register_user()
        self.client.get('/logout', follow_redirects=True)

        res = self.login_user(username="sarahc", password="secretPassword123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome back", res.data)
        self.assertIn(b"Sarah Connor", res.data)

    def test_dashboard_metrics_for_new_user(self):
        """Test dashboard initializes with 0 items for newly registered user."""
        self.register_user()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Total Skills", res.data)
        self.assertIn(b"Certificates", res.data)
        self.assertIn(b"Projects", res.data)
        self.assertIn(b"Portfolio Readiness", res.data)

    def test_skills_crud(self):
        """Test Add, Edit, Delete of skills for registered user."""
        self.register_user()

        # 1. Add Skill
        res = self.client.post('/skills/add', data={
            'name': 'TypeScript & React',
            'category': 'Web Development',
            'proficiency': '4'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"TypeScript &amp; React", res.data)

        db = load_db()
        user = db['users'][0]
        skill = user['skills'][0]
        self.assertEqual(skill['name'], 'TypeScript & React')
        self.assertEqual(skill['proficiency'], 4)
        skill_id = skill['id']

        # 2. Edit Skill
        res = self.client.post(f'/skills/edit/{skill_id}', data={
            'name': 'TypeScript & Next.js',
            'category': 'Web Development',
            'proficiency': '5'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        db = load_db()
        user = db['users'][0]
        self.assertEqual(user['skills'][0]['name'], 'TypeScript & Next.js')
        self.assertEqual(user['skills'][0]['proficiency'], 5)

        # 3. Delete Skill
        res = self.client.post(f'/skills/delete/{skill_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db = load_db()
        self.assertEqual(len(db['users'][0]['skills']), 0)

    def test_certificates_crud(self):
        """Test Add, Edit, Delete of certificates for registered user."""
        self.register_user()

        # 1. Add Certificate
        res = self.client.post('/certificates/add', data={
            'title': 'Certified Kubernetes Administrator',
            'issuer': 'Linux Foundation',
            'issue_date': '2026-05-10',
            'credential_id': 'CKA-991122',
            'url': 'https://cncf.io/verify/CKA-991122'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Certified Kubernetes Administrator", res.data)

        db = load_db()
        cert = db['users'][0]['certificates'][0]
        self.assertEqual(cert['title'], 'Certified Kubernetes Administrator')
        cert_id = cert['id']

        # 2. Edit Certificate
        res = self.client.post(f'/certificates/edit/{cert_id}', data={
            'title': 'Certified Kubernetes Application Developer',
            'issuer': 'Linux Foundation',
            'issue_date': '2026-05-10',
            'credential_id': 'CKAD-991122',
            'url': 'https://cncf.io/verify/CKAD-991122'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db = load_db()
        self.assertEqual(db['users'][0]['certificates'][0]['title'], 'Certified Kubernetes Application Developer')

        # 3. Delete Certificate
        res = self.client.post(f'/certificates/delete/{cert_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db = load_db()
        self.assertEqual(len(db['users'][0]['certificates']), 0)

    def test_projects_crud(self):
        """Test Add, Edit, Delete of projects for registered user."""
        self.register_user()

        # 1. Add Project
        res = self.client.post('/projects/add', data={
            'title': 'Distributed Key-Value Store',
            'description': 'Raft consensus based distributed store with replication.',
            'technologies': 'Go, Raft, gRPC, Docker',
            'duration': '3 Months',
            'github_url': 'https://github.com/sarahc/raft-kv',
            'demo_url': 'https://raft-kv.local'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Distributed Key-Value Store", res.data)

        db = load_db()
        proj = db['users'][0]['projects'][0]
        proj_id = proj['id']

        # 2. Edit Project
        res = self.client.post(f'/projects/edit/{proj_id}', data={
            'title': 'Distributed Key-Value Store v2',
            'description': 'Upgraded Raft consensus store with multi-raft partitions.',
            'technologies': 'Go, Raft, gRPC, Docker, Kubernetes',
            'duration': '4 Months',
            'github_url': 'https://github.com/sarahc/raft-kv',
            'demo_url': 'https://raft-kv.local'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db = load_db()
        self.assertEqual(db['users'][0]['projects'][0]['title'], 'Distributed Key-Value Store v2')

        # 3. Delete Project
        res = self.client.post(f'/projects/delete/{proj_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        db = load_db()
        self.assertEqual(len(db['users'][0]['projects']), 0)

    def test_profile_update(self):
        """Test profile editing for registered user."""
        self.register_user()
        res = self.client.post('/profile', data={
            'name': 'Dr. Sarah Connor',
            'email': 'sarah.updated@tech.edu',
            'phone': '+1 (555) 777-1111',
            'college': 'MIT',
            'department': 'EECS',
            'course': 'Ph.D. in Computer Science',
            'graduation_year': '2028',
            'location': 'Cambridge, MA',
            'career_objective': 'Distributed systems research and AI infrastructure.',
            'profile_summary': 'Systems engineer focused on fault tolerance and reliability.',
            'github': 'https://github.com/sarahc',
            'linkedin': 'https://linkedin.com/in/sarahc'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        db = load_db()
        user = db['users'][0]
        self.assertEqual(user['profile']['name'], 'Dr. Sarah Connor')
        self.assertEqual(user['profile']['college'], 'MIT')

    def test_portfolio_security(self):
        """Ensure password hash and authentication credentials are NEVER exposed in portfolio."""
        self.register_user()
        res = self.client.get('/portfolio')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b"password_hash", res.data)
        self.assertNotIn(b"scrypt:", res.data)
        self.assertNotIn(b"secretPassword123", res.data)
        self.assertIn(b"Print / Save as PDF", res.data)

if __name__ == '__main__':
    unittest.main()
