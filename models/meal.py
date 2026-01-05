from datetime import datetime
from . import db


class Meal(db.Model):
    """Meal model for coach meal plans"""

    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(500), nullable=True)  # Uploaded image
    link = db.Column(db.String(500), nullable=True)  # External link (e.g., recipe URL)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, base_url=''):
        """Convert meal to dictionary for JSON response"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'link': self.link,
            'created_at': self.created_at.isoformat()
        }

        # Include full URL for uploaded images
        if self.image_path:
            result['image'] = f"{base_url}/uploads/{self.image_path}"
        else:
            result['image'] = None

        return result

    def __repr__(self):
        return f'<Meal {self.id}: {self.title}>'
