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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(notifications_bp)
    
    # Serve uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'message': 'Coach Hany Ellithy API is running'}
    
    # Root endpoint with API documentation
    @app.route('/')
    def index():
        return {
            'name': 'Coach Hany Ellithy API',
            'version': '1.0.0',
            'endpoints': {
                'auth': {
                    'POST /api/auth/register': 'Register new user',
                    'POST /api/auth/login': 'User login'
                },
                'coach': {
                    'POST /api/coach/login': 'Coach login',
                    'POST /api/coach/notifications': 'Create notification (coach auth required)',
                    'GET /api/coach/users': 'List all users (coach auth required)',
                    'PUT /api/coach/users/<id>/paid': 'Update user paid status (coach auth required)'
                },
                'notifications': {
                    'GET /api/notifications': 'Get user notifications (user auth required)'
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
