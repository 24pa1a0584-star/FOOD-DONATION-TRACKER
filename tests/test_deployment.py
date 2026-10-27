from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app import create_app
from models import db
from test_app import app, client, create_user


def test_health_database_success_and_failure(app, client):
    assert client.get('/healthz').json == {'status': 'ok'}
    with patch.object(db.session, 'execute', side_effect=OperationalError('SELECT 1', {}, Exception())):
        response = client.get('/healthz')
        assert response.status_code == 503
        assert response.json == {'status': 'unavailable'}


def test_csrf_enabled_by_default():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    assert app.test_client().post('/login', data={}).status_code == 400


def test_demo_credentials_hidden(client):
    assert b'demo123' not in client.get('/login').data


@pytest.mark.parametrize('target', ['//example.com', '/\\example.com', '/\n/example.com'])
def test_external_login_redirect_blocked(app, client, target):
    create_user(app, 'Donor', 'redirect@example.com', 'donor')
    response = client.post('/login', query_string={'next': target}, data={
        'email': 'redirect@example.com', 'password': 'password123',
    })
    assert response.location == '/my'


def test_local_login_redirect_allowed(app, client):
    create_user(app, 'Donor', 'redirect@example.com', 'donor')
    response = client.post('/login?next=/donations/new', data={
        'email': 'redirect@example.com', 'password': 'password123',
    })
    assert response.location == '/donations/new'


def test_render_rejects_development_secret(monkeypatch):
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app()


def test_render_rejects_sqlite(monkeypatch):
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.setenv('SECRET_KEY', 'a' * 40)
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    with pytest.raises(RuntimeError, match='DATABASE_URL'):
        create_app()


@pytest.mark.parametrize('prefix', ['postgres://', 'postgresql://'])
def test_render_postgres_configuration(monkeypatch, prefix):
    monkeypatch.setenv('RENDER', 'true')
    monkeypatch.setenv('SECRET_KEY', 'a' * 40)
    monkeypatch.setenv('DATABASE_URL', prefix + 'user:password@localhost/example')
    # Verify configuration without pretending a PostgreSQL server is available.
    with patch.object(db, 'create_all'):
        app = create_app()
    assert app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql+psycopg://')
    assert app.config['SESSION_COOKIE_SECURE'] is True


def test_seed_disabled_on_render(monkeypatch):
    from seed import seed_database
    monkeypatch.setenv('RENDER', 'true')
    with pytest.raises(RuntimeError, match='disabled on Render'):
        seed_database()
