from mech import create_app

if __name__ == "__main__":
    app = create_app("TestingConfig")
    app.run(debug=True)