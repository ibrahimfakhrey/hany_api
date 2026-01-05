import os
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from functools import wraps
from models import db
from models.notification import Notification
from models.user import User
from models.meal import Meal
from config import Config
from services.fcm import send_notification_to_users

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def admin_required(f):
    """Decorator to require admin login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == Config.COACH_USERNAME and password == Config.COACH_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'بيانات الدخول غير صحيحة'

    return render_template('admin/login.html', error=error)


@admin_bp.route('/logout', methods=['POST'])
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    users = User.query.order_by(User.created_at.desc()).all()

    total_users = len(users)
    paid_users = len([u for u in users if u.is_paid])
    unpaid_users = total_users - paid_users

    # Get 5 most recent users
    recent_users = [u.to_dict() for u in users[:5]]

    # Format current date in Arabic
    current_date = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin/dashboard.html',
                         active_page='dashboard',
                         total_users=total_users,
                         paid_users=paid_users,
                         unpaid_users=unpaid_users,
                         recent_users=recent_users,
                         current_date=current_date,
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/users')
@admin_required
def users_list():
    """List all users with search functionality"""
    search_phone = request.args.get('phone', '').strip()

    if search_phone:
        users = User.query.filter(User.phone.contains(search_phone)).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()

    all_users = User.query.all()
    total = len(all_users)
    paid_count = len([u for u in all_users if u.is_paid])
    unpaid_count = total - paid_count

    return render_template('admin/users.html',
                         active_page='users',
                         users=[u.to_dict() for u in users],
                         total=total,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count,
                         search_phone=search_phone,
                         filter_type=None,
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/paid-users')
@admin_required
def paid_users_list():
    """List only paid users"""
    users = User.query.filter(User.is_paid == True).order_by(User.created_at.desc()).all()

    all_users = User.query.all()
    total = len(all_users)
    paid_count = len([u for u in all_users if u.is_paid])
    unpaid_count = total - paid_count

    return render_template('admin/users.html',
                         active_page='paid',
                         users=[u.to_dict() for u in users],
                         total=total,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count,
                         filter_type='paid',
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/unpaid-users')
@admin_required
def unpaid_users_list():
    """List only unpaid users"""
    users = User.query.filter(User.is_paid == False).order_by(User.created_at.desc()).all()

    all_users = User.query.all()
    total = len(all_users)
    paid_count = len([u for u in all_users if u.is_paid])
    unpaid_count = total - paid_count

    return render_template('admin/users.html',
                         active_page='unpaid',
                         users=[u.to_dict() for u in users],
                         total=total,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count,
                         filter_type='unpaid',
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """View user details"""
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.users_list', error='المستخدم غير موجود'))

    user_dict = user.to_dict()
    user_dict['fcm_token'] = user.fcm_token  # Include FCM token info

    return render_template('admin/user_detail.html',
                         active_page='users',
                         user=user_dict,
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/users/<int:user_id>/paid', methods=['POST'])
@admin_required
def make_user_paid(user_id):
    """Make user a paid subscriber"""
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.users_list', error='المستخدم غير موجود'))

    user.is_paid = True
    db.session.commit()

    return redirect(url_for('admin.user_detail', user_id=user_id, success=f'تم تفعيل اشتراك {user.name} بنجاح ✅'))


@admin_bp.route('/users/<int:user_id>/unpaid', methods=['POST'])
@admin_required
def make_user_unpaid(user_id):
    """Make user an unpaid user"""
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.users_list', error='المستخدم غير موجود'))

    user.is_paid = False
    db.session.commit()

    return redirect(url_for('admin.user_detail', user_id=user_id, success=f'تم إلغاء اشتراك {user.name} ❌'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin.users_list', error='المستخدم غير موجود'))

    user_name = user.name

    # Delete user's targeted notifications first
    Notification.query.filter_by(target_user_id=user_id).delete()

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin.users_list', success=f'تم حذف {user_name} بنجاح 🗑️'))


@admin_bp.route('/quick-manage')
@admin_required
def quick_manage():
    """Quick user status management page with AJAX"""
    filter_type = request.args.get('filter', 'unpaid')

    if filter_type == 'paid':
        users = User.query.filter(User.is_paid == True).order_by(User.created_at.desc()).all()
    elif filter_type == 'unpaid':
        users = User.query.filter(User.is_paid == False).order_by(User.created_at.desc()).all()
    else:
        users = User.query.order_by(User.created_at.desc()).all()

    all_users = User.query.all()
    total = len(all_users)
    paid_count = len([u for u in all_users if u.is_paid])
    unpaid_count = total - paid_count

    return render_template('admin/quick_manage.html',
                         active_page='quick',
                         users=[u.to_dict() for u in users],
                         filter=filter_type,
                         total=total,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count)


@admin_bp.route('/api/users/<int:user_id>/paid', methods=['POST'])
@admin_required
def api_make_user_paid(user_id):
    """AJAX API: Make user paid"""
    from flask import jsonify
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'المستخدم غير موجود'}), 404

    user.is_paid = True
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'تم تفعيل اشتراك {user.name} ✅',
        'user': user.to_dict()
    })


@admin_bp.route('/api/users/<int:user_id>/unpaid', methods=['POST'])
@admin_required
def api_make_user_unpaid(user_id):
    """AJAX API: Make user unpaid"""
    from flask import jsonify
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'المستخدم غير موجود'}), 404

    user.is_paid = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'تم إلغاء اشتراك {user.name} ❌',
        'user': user.to_dict()
    })


@admin_bp.route('/notifications/new')
@admin_required
def create_notification():
    """Create notification page"""
    users = User.query.order_by(User.name).all()

    all_users = User.query.all()
    total_users = len(all_users)
    paid_users = len([u for u in all_users if u.is_paid])
    unpaid_users = total_users - paid_users
    users_with_token = len([u for u in all_users if u.fcm_token])

    # Get preset values from query params
    preset_target = request.args.get('target')
    preset_user_id = request.args.get('user_id')
    preset_user_name = request.args.get('user_name')

    return render_template('admin/create_notification.html',
                         active_page='notifications',
                         users=[u.to_dict() for u in users],
                         total_users=total_users,
                         paid_users=paid_users,
                         unpaid_users=unpaid_users,
                         users_with_token=users_with_token,
                         preset_target=preset_target,
                         preset_user_id=preset_user_id,
                         preset_user_name=preset_user_name,
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/notifications/send', methods=['POST'])
@admin_required
def send_notification():
    """Send a notification"""
    text = request.form.get('text', '').strip()
    image_url = request.form.get('image_url', '').strip()
    target_type = request.form.get('target_type', 'all')
    target_user_id = request.form.get('target_user_id')
    image_file = request.files.get('image')

    # Validate target_type
    if target_type not in ['all', 'paid', 'specific']:
        return redirect(url_for('admin.create_notification', error='نوع الهدف غير صحيح'))

    # Validate target_user_id for specific notifications
    if target_type == 'specific':
        if not target_user_id:
            return redirect(url_for('admin.create_notification', error='يجب اختيار مستخدم'))

        target_user = User.query.get(int(target_user_id))
        if not target_user:
            return redirect(url_for('admin.create_notification', error='المستخدم غير موجود'))

    # At least one content type must be provided
    has_image_file = image_file and image_file.filename and allowed_file(image_file.filename)
    if not text and not image_url and not has_image_file:
        return redirect(url_for('admin.create_notification', error='يجب إدخال نص أو صورة'))

    # Handle image upload
    image_path = None
    if has_image_file:
        filename = secure_filename(image_file.filename)
        import time
        filename = f"{int(time.time())}_{filename}"

        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        image_path = filename

    # Create notification
    notification = Notification(
        text=text if text else None,
        image_path=image_path,
        image_url=image_url if image_url else None,
        target_type=target_type,
        target_user_id=int(target_user_id) if target_type == 'specific' else None
    )

    db.session.add(notification)
    db.session.commit()

    # Send push notifications
    push_result = {'success': 0, 'failure': 0, 'total': 0}

    try:
        if target_type == 'all':
            target_users = User.query.filter(User.fcm_token.isnot(None)).all()
        elif target_type == 'paid':
            target_users = User.query.filter(
                User.is_paid == True,
                User.fcm_token.isnot(None)
            ).all()
        else:  # specific
            specific_user = User.query.get(int(target_user_id))
            if specific_user and specific_user.fcm_token:
                target_users = [specific_user]
            else:
                target_users = []

        push_result['total'] = len(target_users)

        if target_users:
            push_result = send_notification_to_users(target_users, notification)

    except Exception as e:
        print(f'Push notification error: {e}')
        push_result = {'success': 0, 'failure': 0, 'total': 0, 'error': str(e)}

    return render_template('admin/notification_result.html',
                         success=True,
                         target_type=target_type,
                         push_result=push_result,
                         notification_text=text)


# ==================== MEALS MANAGEMENT ====================

@admin_bp.route('/meals')
@admin_required
def meals_list():
    """List all meals"""
    meals = Meal.query.order_by(Meal.created_at.desc()).all()
    base_url = request.host_url.rstrip('/')

    return render_template('admin/meals.html',
                         active_page='meals',
                         meals=[meal.to_dict(base_url) for meal in meals],
                         total=len(meals),
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/meals/new')
@admin_required
def create_meal_page():
    """Create meal page"""
    return render_template('admin/create_meal.html',
                         active_page='meals',
                         success_message=request.args.get('success'),
                         error_message=request.args.get('error'))


@admin_bp.route('/meals/create', methods=['POST'])
@admin_required
def create_meal():
    """Create a new meal"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    link = request.form.get('link', '').strip()
    category = request.form.get('category', 'breakfast')
    image_file = request.files.get('image')

    # Validate required fields
    if not title:
        return redirect(url_for('admin.create_meal_page', error='يجب إدخال عنوان الوجبة'))

    # Handle image upload
    image_path = None
    if image_file and image_file.filename and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        import time
        filename = f"{int(time.time())}_{filename}"

        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        image_path = filename

    # Create meal
    meal = Meal(
        title=title,
        description=description if description else None,
        image_path=image_path,
        link=link if link else None,
        category=category
    )

    db.session.add(meal)
    db.session.commit()

    return redirect(url_for('admin.meals_list', success=f'تم إضافة الوجبة "{title}" بنجاح ✅'))


@admin_bp.route('/meals/<int:meal_id>/delete', methods=['POST'])
@admin_required
def delete_meal(meal_id):
    """Delete a meal"""
    meal = Meal.query.get(meal_id)
    if not meal:
        return redirect(url_for('admin.meals_list', error='الوجبة غير موجودة'))

    meal_title = meal.title

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

    return redirect(url_for('admin.meals_list', success=f'تم حذف الوجبة "{meal_title}" بنجاح 🗑️'))
