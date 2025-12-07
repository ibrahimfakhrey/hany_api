import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hany-elithy-secret-key-2024')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hany_elithy.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-hany-elithy-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Coach credentials (hardcoded as per requirements)
    COACH_USERNAME = 'hany'
    COACH_PASSWORD = 'Admin@123'
    
    # Firebase Admin SDK credentials
    FIREBASE_CREDENTIALS_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        'firebase-credentials.json'
    )
