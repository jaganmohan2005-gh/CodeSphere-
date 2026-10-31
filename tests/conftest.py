"""
CodeSphere - Pytest Test Configuration & Fixtures
-------------------------------------------------
Sets up an in-memory SQLite database for test isolation and provides
helper fixtures for authentication, client requests, and pre-seeded fixtures.
"""

import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, StudentProfile
from app.services.seed_service import seed_database


@pytest.fixture
def app():
    """Initializes a clean Flask test application with in-memory database."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Seed standard curriculum & accounts
        seed_database(
            admin_username='admin',
            admin_email='admin@codesphere.io',
            admin_password='Admin@CodeSphere2026!'
        )
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Provides a test HTTP client with session support."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Logs in as the default seeded student account."""
    client.post('/login', data={
        'email_or_username': 'student',
        'password': 'Student@CodeSphere2026!'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client):
    """Logs in as the default seeded administrator account."""
    client.post('/admin/login', data={
        'email_or_username': 'admin',
        'password': 'Admin@CodeSphere2026!'
    }, follow_redirects=True)
    return client
