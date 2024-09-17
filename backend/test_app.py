import unittest
from app import app, db, User
from werkzeug.security import generate_password_hash

class FlaskAuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Flask Auth App", response.data)

    def test_signup(self):
        response = self.client.post('/signup', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)

    def test_login_logout(self):
        # Create a test user
        with app.app_context():
            hashed_password = generate_password_hash('testpassword')
            user = User(username='testuser', password=hashed_password)
            db.session.add(user)
            db.session.commit()

        # Test login
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome, testuser!", response.data)

        # Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Welcome, testuser!", response.data)

    def test_invalid_login(self):
        response = self.client.post('/login', data=dict(
            username='wronguser',
            password='wrongpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

if __name__ == '__main__':
    unittest.main()