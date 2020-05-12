from flask import redirect, session
from functools import wraps

def logged_in(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'displayname' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapped
