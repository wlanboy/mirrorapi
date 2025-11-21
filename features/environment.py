from mirror_api import db, MirrorPair
from main import app
from mirror_api import db, MirrorPair

db_url = 'sqlite:///mirror_data.db';

def before_scenario(context, scenario):
    with app.app_context():
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        db.session.query(MirrorPair).delete()
        db.session.commit()

def after_scenario(context, scenario):
    with app.app_context():
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        db.session.query(MirrorPair).delete()
        db.session.commit()

