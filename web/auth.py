import hashlib
import hmac
from functools import wraps
from flask import session, redirect, url_for, request
from settings import settings


def verify_telegram_auth(auth_data: dict) -> bool:
    check_hash = auth_data.get('hash')
    if not check_hash:
        return False
    
    auth_data_copy = auth_data.copy()
    del auth_data_copy['hash']
    
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data_copy.items())]
    data_check_string = '\n'.join(data_check_arr)
    
    secret_key = hashlib.sha256(settings.telegram_token.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    return hash_value == check_hash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'telegram_user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'telegram_user' not in session:
            return redirect(url_for('login', next=request.url))
        
        telegram_user = session.get('telegram_user')
        if telegram_user.get('id') != settings.admin_user_id:
            return "Access denied. Admin privileges required.", 403
        
        return f(*args, **kwargs)
    return decorated_function
