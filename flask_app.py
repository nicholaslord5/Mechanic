import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

from mech import create_app
app = create_app("DevelopmentConfig")
app.debug = True

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)