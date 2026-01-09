import os
import time
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from models import db
from models.meal import Meal
from config import Config

meals_bp = Blueprint('meals', __name__, url_prefix='/api/meals')


def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@meals_bp.route('', methods=['GET'])
def get_all_meals():
    """
    Get all meals
    Returns all meals ordered by creation date (newest first)
    Optional query param: ?category=breakfast|lunch|dinner|snacks
    """
    category = request.args.get('category')

    if category:
        meals = Meal.query.filter_by(category=category).order_by(Meal.created_at.desc()).all()
    else:
        meals = Meal.query.order_by(Meal.created_at.desc()).all()

    base_url = request.host_url.rstrip('/')

    return jsonify({
        'meals': [meal.to_dict(base_url) for meal in meals],
        'total': len(meals)
    }), 200


@meals_bp.route('/<int:meal_id>', methods=['GET'])
def get_meal(meal_id):
    """
    Get a single meal by ID
    """
    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({'error': 'Meal not found'}), 404

    base_url = request.host_url.rstrip('/')
    return jsonify({'meal': meal.to_dict(base_url)}), 200


@meals_bp.route('', methods=['POST'])
@jwt_required()
def create_meal():
    """
    Create a new meal (coach only)

    Request body (form-data):
    {
        "title": "Meal title",
        "description": "Meal description",
        "image": <file>,  // Optional uploaded image
        "link": "https://..."  // Optional external link
    }
    """
    # Verify the request is from a coach
    claims = get_jwt()
    if claims.get('type') != 'coach':
        return jsonify({'error': 'Coach authorization required'}), 403

    # Handle both JSON and form-data for image uploads
    if request.content_type and 'multipart/form-data' in request.content_type:
        title = request.form.get('title')
        description = request.form.get('description')
        link = request.form.get('link')
        category = request.form.get('category', 'breakfast')
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        title = data.get('title')
        description = data.get('description')
        link = data.get('link')
        category = data.get('category', 'breakfast')
        image_file = None

    # Validate required fields
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    # Handle image upload
    image_path = None
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        # Add timestamp to filename to avoid conflicts
        filename = f"{int(time.time())}_{filename}"

        # Ensure upload folder exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Save the file
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        image_path = filename

    # Create meal
    meal = Meal(
        title=title,
        description=description,
        image_path=image_path,
        link=link,
        category=category
    )

    db.session.add(meal)
    db.session.commit()

    return jsonify({
        'message': 'Meal created successfully',
        'meal': meal.to_dict(request.host_url.rstrip('/'))
    }), 201


@meals_bp.route('/search', methods=['GET'])
def search_meals():
    """
    Search meals by ingredient/keyword

    Query params:
    - query: The search term (ingredient name, e.g., "فول")
    - category: Optional filter by category (breakfast, lunch, dinner, snacks)

    Returns all meals where title or description contains the search term
    """
    query = request.args.get('query', '').strip()
    category = request.args.get('category')

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    # Build the search query - search in title and description
    search_filter = or_(
        Meal.title.ilike(f'%{query}%'),
        Meal.description.ilike(f'%{query}%')
    )

    if category:
        meals = Meal.query.filter(
            and_(
                Meal.category == category,
                search_filter
            )
        ).order_by(Meal.created_at.desc()).all()
    else:
        meals = Meal.query.filter(search_filter).order_by(Meal.created_at.desc()).all()

    base_url = request.host_url.rstrip('/')

    return jsonify({
        'meals': [meal.to_dict(base_url) for meal in meals],
        'total': len(meals),
        'query': query,
        'category': category
    }), 200


@meals_bp.route('/<int:meal_id>', methods=['DELETE'])
@jwt_required()
def delete_meal(meal_id):
    """
    Delete a meal (coach only)
    """
    # Verify the request is from a coach
    claims = get_jwt()
    if claims.get('type') != 'coach':
        return jsonify({'error': 'Coach authorization required'}), 403

    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({'error': 'Meal not found'}), 404

    # Delete the image file if it exists
    if meal.image_path:
        try:
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], meal.image_path)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f'Error deleting meal image: {e}')

    db.session.delete(meal)
    db.session.commit()

    return jsonify({'message': 'Meal deleted successfully'}), 200
