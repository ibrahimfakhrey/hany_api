from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    """User model for mobile app users"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    fcm_token = db.Column(db.String(500), nullable=True)  # Firebase Cloud Messaging token
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'is_paid': self.is_paid,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.name}>'
