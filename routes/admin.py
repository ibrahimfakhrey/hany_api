from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/meals')
def admin_meals():
    """
    Admin page for managing meals
    """
    return render_template('admin_meals.html')
