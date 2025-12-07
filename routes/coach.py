import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from werkzeug.utils import secure_filename
from models import db
from models.notification import Notification
from models.user import User
from config import Config
from services.fcm import send_notification_to_users

coach_bp = Blueprint('coach', __name__, url_prefix='/api/coach')


def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@coach_bp.route('/login', methods=['POST'])
def coach_login():
    """
    Login as coach
    
    Request body:
    {
        "username": "hany",
        "password": "Admin@123"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Check hardcoded coach credentials
    if username != Config.COACH_USERNAME or password != Config.COACH_PASSWORD:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create JWT token for coach
    access_token = create_access_token(
        identity='coach',
        additional_claims={'type': 'coach'}
    )
    
    return jsonify({
        'message': 'Coach login successful',
        'token': access_token,
        'coach': {
            'username': Config.COACH_USERNAME,
            'name': 'Coach Hany Ellithy'
        }
    }), 200


@coach_bp.route('/notifications', methods=['POST'])
@jwt_required()
def create_notification():
    """
    Create a new notification (coach only)
    
    Request body (form-data or JSON):
    {
        "text": "Optional text message",
        "image": <file>,  // Optional uploaded image
        "image_url": "https://...",  // Optional external image URL
        "target_type": "all" | "paid" | "specific",
        "target_user_id": 123  // Required if target_type is "specific"
    }
    """
    # Verify the request is from a coach
    claims = get_jwt()
    if claims.get('type') != 'coach':
        return jsonify({'error': 'Coach authorization required'}), 403
    
    # Handle both JSON and form-data for image uploads
    if request.content_type and 'multipart/form-data' in request.content_type:
        text = request.form.get('text')
        image_url = request.form.get('image_url')
        target_type = request.form.get('target_type', 'all')
        target_user_id = request.form.get('target_user_id')
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        text = data.get('text')
        image_url = data.get('image_url')
        target_type = data.get('target_type', 'all')
        target_user_id = data.get('target_user_id')
        image_file = None
    
    # Validate target_type
    if target_type not in ['all', 'paid', 'specific']:
        return jsonify({'error': 'target_type must be "all", "paid", or "specific"'}), 400
    
    # Validate target_user_id for specific notifications
    if target_type == 'specific':
        if not target_user_id:
            return jsonify({'error': 'target_user_id is required for specific notifications'}), 400
        
        # Check if target user exists
        target_user = User.query.get(int(target_user_id))
        if not target_user:
            return jsonify({'error': 'Target user not found'}), 404
    
    # At least one content type must be provided
    if not text and not image_url and not image_file:
        return jsonify({'error': 'At least one of text, image, or image_url is required'}), 400
    
    # Handle image upload
    image_path = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        # Add timestamp to filename to avoid conflicts
        import time
        filename = f"{int(time.time())}_{filename}"
        
        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the file
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        image_path = filename
    
    # Create notification
    notification = Notification(
        text=text,
        image_path=image_path,
        image_url=image_url,
        target_type=target_type,
        target_user_id=int(target_user_id) if target_type == 'specific' else None
    )
    
    db.session.add(notification)
    db.session.commit()
    
    # Send push notifications to target users
    push_result = {'success': 0, 'failure': 0}
    try:
        if target_type == 'all':
            target_users = User.query.filter(User.fcm_token.isnot(None)).all()
        elif target_type == 'paid':
            target_users = User.query.filter(User.is_paid == True, User.fcm_token.isnot(None)).all()
        else:  # specific
            target_users = [User.query.get(int(target_user_id))]
        
        if target_users:
            push_result = send_notification_to_users(target_users, notification)
    except Exception as e:
        print(f'Push notification error: {e}')
    
    return jsonify({
        'message': 'Notification created successfully',
        'notification_id': notification.id,
        'notification': notification.to_dict(request.host_url.rstrip('/')),
        'push_result': push_result
    }), 201


@coach_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """
    List all users (coach only) - useful for selecting specific users for notifications
    """
    # Verify the request is from a coach
    claims = get_jwt()
    if claims.get('type') != 'coach':
        return jsonify({'error': 'Coach authorization required'}), 403
    
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }), 200


@coach_bp.route('/users/<int:user_id>/paid', methods=['PUT'])
@jwt_required()
def update_user_paid_status(user_id):
    """
    Update user's paid status (coach only)
    
    Request body:
    {
        "is_paid": true | false
    }
    """
    # Verify the request is from a coach
    claims = get_jwt()
    if claims.get('type') != 'coach':
        return jsonify({'error': 'Coach authorization required'}), 403
    
    data = request.get_json()
    if not data or 'is_paid' not in data:
        return jsonify({'error': 'is_paid field is required'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_paid = bool(data['is_paid'])
    db.session.commit()
    
    return jsonify({
        'message': 'User paid status updated',
        'user': user.to_dict()
    }), 200
