
class DevelopmentConfig:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost/mechanic_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig:
    pass

class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:password@localhost/mechanic_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False