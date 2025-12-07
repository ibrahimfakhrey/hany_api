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

