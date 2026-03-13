import pytest
from app import create_app
from app.models import db as _db, User, UserRole


@pytest.fixture(scope="session")
def app():
    """Create a Flask app configured for testing (in-memory SQLite)."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "JWT_SECRET_KEY": "test-secret",
    })
    yield app


@pytest.fixture(autouse=True)
def db(app):
    """Give each test a clean database."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


# ----- helper factories -----

@pytest.fixture()
def make_user(db):
    """Factory fixture to create and persist a user."""
    def _make(name="Test User", email="test@example.com",
              password="password123", role=UserRole.TENANT, manager_id=None):
        user = User(name=name, email=email, role=role)
        if manager_id:
            user.manager_id = manager_id
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _make


@pytest.fixture()
def manager(make_user):
    return make_user(name="Manager One", email="manager@example.com", role=UserRole.MANAGER)


@pytest.fixture()
def tenant(make_user, manager):
    return make_user(name="Tenant One", email="tenant@example.com",
                     role=UserRole.TENANT, manager_id=manager.id)


@pytest.fixture()
def technician(make_user):
    return make_user(name="Tech One", email="tech@example.com", role=UserRole.TECHNICIAN)
