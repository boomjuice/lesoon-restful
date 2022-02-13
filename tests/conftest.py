"""Defines fixtures available to all tests."""
import logging
import os
import sys

import pytest
from lesoon_common import LesoonFlask

sys.path.extend([os.path.join(os.getcwd(), 'src')])


class Config:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


@pytest.fixture
def app():
    """Create application for the tests."""
    app = LesoonFlask(__name__, config=Config)
    app.logger.setLevel(logging.CRITICAL)
    ctx = app.test_request_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture
def db(app: LesoonFlask):
    """Create database for the tests."""
    _db = app.db  # noqa
    with app.app_context():
        _db.create_all()
    yield _db

    _db.session.close()
    _db.drop_all()


@pytest.fixture
def test_client(app: LesoonFlask):
    _db = app.db  # noqa
    with app.test_client(load_response=False) as client:
        yield client
