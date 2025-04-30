class DevelopmentConfig:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost/mechanic_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a super secret, secret key'

class ProductionConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'add production secret key here'

class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a super secret, secret key'
    JWT_ALGO = 'HS256'