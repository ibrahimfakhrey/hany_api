from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import or_, and_
from models.notification import Notification
from models.user import User

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get notifications for the authenticated user
    
    Returns notifications that:
    - target_type is 'all' (for everyone)
    - target_type is 'paid' and user.is_paid is True
    - target_type is 'specific' and target_user_id matches user's id
    """
    # Verify the request is from a user (not coach)
    claims = get_jwt()
    if claims.get('type') != 'user':
        return jsonify({'error': 'User authorization required'}), 403
    
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Build query for user's notifications
    # 1. All notifications targeted to everyone
    # 2. Paid notifications if user is paid
    # 3. Specific notifications for this user
    
    if user.is_paid:
        # Paid users see: all, paid, and their specific notifications
        notifications = Notification.query.filter(
            or_(
                Notification.target_type == 'all',
                Notification.target_type == 'paid',
                and_(
                    Notification.target_type == 'specific',
                    Notification.target_user_id == user_id
                )
            )
        ).order_by(Notification.created_at.desc()).all()
    else:
        # Free users see: all and their specific notifications
        notifications = Notification.query.filter(
            or_(
                Notification.target_type == 'all',
                and_(
                    Notification.target_type == 'specific',
                    Notification.target_user_id == user_id
                )
            )
        ).order_by(Notification.created_at.desc()).all()
    
    base_url = request.host_url.rstrip('/')
    
    return jsonify({
        'notifications': [n.to_dict(base_url) for n in notifications],
        'total': len(notifications)
    }), 200
