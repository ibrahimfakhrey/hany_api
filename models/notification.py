from datetime import datetime
from . import db


class Notification(db.Model):
    """Notification model for coach-to-user notifications"""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=True)  # Optional text content
    image_path = db.Column(db.String(500), nullable=True)  # Optional uploaded image
    image_url = db.Column(db.String(500), nullable=True)  # Optional external image URL
    
    # Targeting: 'all', 'paid', or 'specific'
    target_type = db.Column(db.String(20), nullable=False, default='all')
    
    # If target_type is 'specific', this is the target user's ID
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to target user (for specific notifications)
    target_user = db.relationship('User', backref='targeted_notifications')
    
    def to_dict(self, base_url=''):
        """Convert notification to dictionary for JSON response"""
        result = {
            'id': self.id,
            'text': self.text,
            'image_url': self.image_url,
            'target_type': self.target_type,
            'created_at': self.created_at.isoformat()
        }
        
        # Include full URL for uploaded images
        if self.image_path:
            result['image'] = f"{base_url}/uploads/{self.image_path}"
        else:
            result['image'] = None
            
        return result
    
    def __repr__(self):
        return f'<Notification {self.id}>'
