from mech import create_app
from mech.models import db

app=create_app('DevelopmentConfig')

with app.app_context():
    db.create_all()

app.run()