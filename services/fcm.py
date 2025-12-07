import firebase_admin
from firebase_admin import credentials, messaging
from config import Config
import os

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    if os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)


def send_push_notification(tokens, title, body, data=None):
    """
    Send push notification via Firebase Admin SDK
    
    Args:
        tokens: List of FCM device tokens
        title: Notification title
        body: Notification body text
        data: Optional dict of additional data
    
    Returns:
        dict with success/failure counts
    """
    if not tokens:
        return {'success': 0, 'failure': 0, 'message': 'No tokens provided'}
    
    # Filter out empty tokens
    valid_tokens = [t for t in tokens if t]
    if not valid_tokens:
        return {'success': 0, 'failure': 0, 'message': 'No valid tokens'}
    
    # Check if Firebase is initialized
    if not firebase_admin._apps:
        return {'success': 0, 'failure': 0, 'message': 'Firebase not initialized'}
    
    success_count = 0
    failure_count = 0
    
    # Create notification message
    notification = messaging.Notification(
        title=title,
        body=body
    )
    
    # Send to each token
    for token in valid_tokens:
        try:
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            success_count += 1
        except Exception as e:
            print(f'FCM Error for token {token[:10]}...: {e}')
            failure_count += 1
    
    return {
        'success': success_count,
        'failure': failure_count,
        'total': len(valid_tokens)
    }


def send_notification_to_users(users, notification):
    """
    Send push notification for a new notification to target users
    
    Args:
        users: List of User objects
        notification: Notification object
    """
    # Get FCM tokens from users
    tokens = [user.fcm_token for user in users if user.fcm_token]
    
    if not tokens:
        return {'success': 0, 'failure': 0, 'message': 'No users with FCM tokens'}
    
    # Build notification content
    title = 'كوتش هاني الليثي'  # Coach Hany Ellithy
    body = notification.text or 'لديك إشعار جديد'  # You have a new notification
    
    # Additional data
    data = {
        'notification_id': str(notification.id),
        'type': 'coach_notification'
    }
    
    if notification.image_url:
        data['image_url'] = notification.image_url
    
    return send_push_notification(tokens, title, body, data)
