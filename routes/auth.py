from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import RegisterForm, LoginForm

auth_bp = Blueprint('auth', __name__)

def donor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if current_user.role != 'donor':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def receiver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if current_user.role != 'receiver':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'donor':
            return redirect(url_for('main.my_activity'))
        return redirect(url_for('donations.list_donations'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip(),
            role=form.role.data,
            area=form.area.data.strip()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Account created successfully! Welcome, {user.name}.', 'success')

        if user.role == 'donor':
            return redirect(url_for('main.my_activity'))
        else:
            return redirect(url_for('donations.list_donations'))

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'donor':
            return redirect(url_for('main.my_activity'))
        return redirect(url_for('donations.list_donations'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')

            next_page = request.args.get('next')
            if (next_page and next_page.startswith('/')
                    and not next_page.startswith('//')
                    and '\\' not in next_page
                    and not any(ord(char) < 32 for char in next_page)):
                return redirect(next_page)

            if user.role == 'donor':
                return redirect(url_for('main.my_activity'))
            else:
                return redirect(url_for('donations.list_donations'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))
