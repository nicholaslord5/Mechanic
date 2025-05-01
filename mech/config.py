class DevelopmentConfig:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost/mechanic_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a super secret, secret key'

class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a super secret, secret key'
    JWT_ALGO = 'HS256'

class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = ''
    CACHE_TYPE = "SimpleCache"