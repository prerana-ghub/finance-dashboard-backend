from flask import Flask
from models.db import db
from routes.auth import auth_bp
from routes.users import users_bp
from routes.records import records_bp
from routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "finance-secret-key-2024"

    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(records_bp, url_prefix="/records")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    with app.app_context():
        db.create_all()
        seed_default_admin()

    return app


def seed_default_admin():
    from models.user import User
    from werkzeug.security import generate_password_hash
    existing = User.query.filter_by(email="admin@finance.com").first()
    if not existing:
        admin = User(
            name="Admin User",
            email="admin@finance.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin seeded: admin@finance.com / admin123")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
