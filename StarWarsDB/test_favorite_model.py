"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_favorite_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from flask import g

from models import db, User, Favorite

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///starwarsdb_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

from contextlib import contextmanager
from flask import appcontext_pushed, g


@contextmanager
def set_user(app, user):
    def handler(sender, **kwargs):
        g.user=user
    with appcontext_pushed.connected_to(handler, app):
        yield


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 94566
        self.user = User.signup("testing", "testing@test.com", "password", None)
        self.user.id = self.uid
        set_user(app, self.user)
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

        fTest = Favorite(
            category="people",
            data = {"name": "Luke"},
            user_id=self.uid
        )
        
        db.session.add(fTest)
        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_favorite_model(self):
        """Does basic model work?"""
        
        f = Favorite(
            category="people",
            data = {"name": "Luke"},
            user_id=self.uid
        )

        db.session.add(f)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.u.favorites), 2)
        self.assertEqual(self.u.favorites[0].category, "people")
        self.assertEqual(self.u.favorites[0].data['name'], "Luke")

    def test_favorite_comments(self):
        """Can Comments be added to Favorites"""

        f2 = Favorite(
            category="people",
            data = {"name": "Anakin"},
            user_id=self.uid,
            comments="This is a Note"
        )

        db.session.add(f2)
        db.session.commit()

        self.assertEqual(self.u.favorites[1].comments, "This is a Note")

    def test_add_favorite_route(self):
        """Use the route to add a favorite"""
        
        with app.test_request_context('/'), app.app_context():

            
            fav = self.client.get('/categories/people/person?data=https://www.swapi.tech/api/people/4&fav=add', follow_redirects=True)
            

            self.assertEqual(len(self.u.favorites), 2)
            self.assertEqual(self.u.favorites[1].category, "people")
            self.assertEqual(self.u.favorites[1].data['name'], "Darth Vader")




        