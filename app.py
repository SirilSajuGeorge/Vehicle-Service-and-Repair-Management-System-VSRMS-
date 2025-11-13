import os
from flask import Flask
from models import db
from routes import app

# Configuration for the SQLite database connection (easier setup)
# Using SQLite for development - no separate database server needed
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vehicle_management.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'thisisasecretkey')

# Initialize the database extension with the application
db.init_app(app)

# Create the database tables if they don't exist
with app.app_context():
    # This creates all tables defined in models.py within the connected database
    db.create_all()

if __name__ == "__main__":
    # Docker-friendly configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
