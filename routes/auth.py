from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request body:
    {
        "name": "User Name",
        "phone": "01234567890",
        "password": "password123"
    }
    """
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')
    
    if not name or not phone or not password:
        return jsonify({'error': 'Name, phone, and password are required'}), 400
    
    # Check if phone already exists
    existing_user = User.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({'error': 'Phone number already registered'}), 409
    
    # Create new user
    user = User(name=name, phone=phone)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    Request body:
    {
        "phone": "01234567890",
        "password": "password123"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': 'Phone and password are required'}), 400
    
    # Find user by phone
    user = User.query.filter_by(phone=phone).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid phone or password'}), 401
    
    # Create JWT token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'type': 'user'}
    )
    
    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/device-token', methods=['POST'])
@jwt_required()
def save_device_token():
    """
    Save FCM device token for push notifications
    
    Request body:
    {
        "fcm_token": "device_fcm_token_here"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('fcm_token'):
        return jsonify({'error': 'fcm_token is required'}), 400
    
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.fcm_token = data['fcm_token']
    db.session.commit()
    
    return jsonify({
        'message': 'Device token saved successfully'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user profile including subscription status.

    Headers required:
        Authorization: Bearer <jwt_token>

    Returns:
        200: { "user": { "id", "name", "phone", "is_paid" } }
        401: { "error": "Token is missing or invalid" }
        404: { "error": "User not found" }
    """
    try:
        # Get user ID from JWT token
        current_user_id = int(get_jwt_identity())

        # Fetch user from database
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Return user data
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'is_paid': user.is_paid
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

