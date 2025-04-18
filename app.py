from mech import create_app

if __name__ == "__main__":
    app = create_app("DevelopmentConfig")
    for rule in app.url_map.iter_rules():
        print(rule.methods, rule.rule)
    app.run(debug=True)