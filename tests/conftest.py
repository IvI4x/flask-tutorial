import os
import docker
import time
import psycopg2

import pytest
from flask import g
from flaskr import create_app
from flaskr.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    # Spin up a fresh psql container
    client = docker.from_env()
    pg_container = client.containers.run(
        'postgres:12.1',
        ports = {5432:5433},
        detach = True,
        auto_remove = True,
        environment = ["POSTGRES_PASSWORD=dev"]
    )

    app = create_app({
        'TESTING': True,
        'DATABASE': {
            "dbname":"postgres",
            "user":"postgres",
            "password":"dev",
            "host":"localhost",
            "port":5433
        },
    })

    with app.app_context():
        # Try connecting until docker is up and running
        while 'db' not in g:
            try:
                init_db()
            except psycopg2.OperationalError:
                print("Waiting for docker container...")
                time.sleep(1)
        cur = get_db().cursor()
        cur.execute(_data_sql)
        get_db().commit()
        cur.close()

    yield app

    pg_container.stop()


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
                '/auth/login',
                data={'username':username, 'password':password}
        )

    def logout(self):
        return self._client.get('/auth/logout')

@pytest.fixture
def auth(client):
    return AuthActions(client)
