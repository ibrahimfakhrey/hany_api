
import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from config import Config
from models import db


def create_app():
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.coach import coach_bp
    from routes.notifications import notifications_bp
    from routes.meals import meals_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(admin_bp)
    
    # Serve uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'message': 'Coach Hany Ellithy API is running'}

    # Privacy policy endpoint
    @app.route('/privacy')
    def privacy():
        return {
            'title': 'Privacy Policy',
            'app_name': 'Coach Hany Ellithy',
            'last_updated': '2026-01-05',
            'content': {
                'introduction': 'This Privacy Policy describes how Coach Hany Ellithy ("we", "us", or "our") collects, uses, and shares your personal information when you use our mobile application.',
                'information_we_collect': [
                    'Account Information: Name, phone number, and password when you register.',
                    'Device Information: Device tokens for push notifications.',
                    'Usage Data: Information about how you use the app.'
                ],
                'how_we_use_information': [
                    'To provide and maintain our service.',
                    'To send you push notifications about meals, workouts, and updates.',
                    'To manage your account and subscription status.',
                    'To communicate with you about our services.'
                ],
                'data_security': 'We implement appropriate security measures to protect your personal information. Passwords are encrypted and stored securely.',
                'your_rights': [
                    'Access your personal data.',
                    'Request correction of your data.',
                    'Request deletion of your account.',
                    'Opt-out of push notifications.'
                ],
                'contact': 'For any questions about this Privacy Policy, please contact Coach Hany Ellithy.'
            }
        }
    
    # Root endpoint with API documentation
    @app.route('/')
    def index():
        return {
            'name': 'Coach Hany Ellithy API',
            'version': '1.0.0',
            'endpoints': {
                'auth': {
                    'POST /api/auth/register': 'Register new user',
                    'POST /api/auth/login': 'User login',
                    'GET /api/auth/me': 'Get current user profile (user auth required)'
                },
                'coach': {
                    'POST /api/coach/login': 'Coach login',
                    'POST /api/coach/notifications': 'Create notification (coach auth required)',
                    'GET /api/coach/users': 'List all users (coach auth required)',
                    'PUT /api/coach/users/<id>/paid': 'Update user paid status (coach auth required)'
                },
                'notifications': {
                    'GET /api/notifications': 'Get user notifications (user auth required)'
                },
                'meals': {
                    'GET /api/meals': 'Get all meals',
                    'GET /api/meals/<id>': 'Get single meal',
                    'POST /api/meals': 'Create meal (coach auth required)',
                    'DELETE /api/meals/<id>': 'Delete meal (coach auth required)'
                },
                'admin': {
                    'GET /admin/meals': 'Admin page for managing meals'
                }
            }
        }
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
