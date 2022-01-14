from models import db, connect_db, User, Favorite
from app import app

# Create all tables
db.drop_all()
db.create_all()