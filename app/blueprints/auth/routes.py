from . import auth_bp
from flask import abort
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from flask import Flask, abort, render_template, redirect, url_for, flash
from app.extensions import db 
from app.forms import RegisterFrom, LoginFrom
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from app.models import User


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403)
            if current_user.role not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route("/register", methods=['POST','GET'])
def register():
    form = RegisterFrom()
    if current_user.is_authenticated:
        return redirect(url_for('pages.home'))
    else:
        if form.validate_on_submit():
            email = form.email.data
            name = form.name.data
            existing_user= db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none() 
            if existing_user:
                flash("Email aldready registered", "error")
                return redirect(url_for('auth.login'))
            try:
                encrypted_password = generate_password_hash(
                    form.password.data, 
                    method='pbkdf2:sha256',
                    salt_length=8)
                new_user=User(name=name,
                            email=email,
                            password=encrypted_password,
                            )
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Email aldready registered (DB conflict)", 'error')
                return redirect(url_for('register'))

            login_user(new_user)
            return redirect(url_for('pages.home'))
        return render_template('register.html', form=form, logged_in= current_user.is_authenticated)



@auth_bp.route("/login", methods=['POST','GET'])
def login():
    form = LoginFrom()
    if not current_user.is_authenticated:
        if form.validate_on_submit():
            email = form.email.data
            password=form.password.data
            user = db.session.execute(db.select(User).where(User.email==email)).scalar_one_or_none()
            if user and check_password_hash(user.password,password):
                login_user(user)
                flash('Loged in with success', 'success')
                return redirect(url_for('pages.home'))
            else:
                flash('Invalid password or email', 'error')

        return render_template("login.html", form=form)
        
    else:
        return redirect(url_for('auth.profile', id=current_user.id))
        

@auth_bp.route("/profile/<int:id>")
def profile(id):
    user = db.session.execute(db.select(User).where(User.email==current_user.email)).scalar_one_or_none()

    return render_template('profile.html', user=user)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.home'))

