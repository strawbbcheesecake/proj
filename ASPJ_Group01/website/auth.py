import base64
import os

# from Crypto.Cipher import PKCS1_OAEP
# from Crypto.PublicKey import RSA
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, session, current_app
from .Forms import Signup, Login, ResetPasswordForm, RequestResetForm, Updatestaff
from flask_login import login_user, logout_user, current_user, login_required
import pymysql
from .models import User, Staff, db
from flask_mail import Message
import random
from datetime import datetime, timedelta
import bcrypt
from flask_mail import Mail

auth = Blueprint('auth', __name__)
mail = Mail()

# # File paths for the keys
# PRIVATE_KEY_FILE = 'private.pem'
# PUBLIC_KEY_FILE = 'public.pem'
#
# def generate_and_save_keys():
#     if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
#         key = RSA.generate(1024)
#         with open(PRIVATE_KEY_FILE, 'wb') as f:
#             f.write(key.export_key())
#         with open(PUBLIC_KEY_FILE, 'wb') as f:
#             f.write(key.publickey().export_key())
#
# def load_keys():
#     with open(PRIVATE_KEY_FILE, 'rb') as f:
#         private_key = RSA.import_key(f.read())
#     with open(PUBLIC_KEY_FILE, 'rb') as f:
#         public_key = RSA.import_key(f.read())
#     return private_key, public_key
#
# def encrypt_data(data, public_key):
#     cipher = PKCS1_OAEP.new(public_key)
#     encrypted_data = cipher.encrypt(data.encode('utf-8'))
#     return base64.b64encode(encrypted_data).decode('utf-8')
#
# def decrypt_data(encrypted_data, private_key):
#     cipher = PKCS1_OAEP.new(private_key)
#     encrypted_data = base64.standard_b64decode(encrypted_data)
#     decrypted_data = cipher.decrypt(encrypted_data)
#     return decrypted_data
#
# @auth.context_processor
# def utility_processor():
#     def decrypt_data(encrypted_data, private_key):
#         encrypted_data = base64.b64decode(encrypted_data)
#         cipher = PKCS1_OAEP.new(private_key)
#         decrypted_data = cipher.decrypt(encrypted_data)
#         return decrypted_data.decode('utf-8')
#     return dict(decrypt_data=decrypt_data)

def redact_email(email):
    local, domain = email.split('@')
    return local[0] + '*****@' + domain

def generate_otp():
    return str(random.randint(100000, 999999))

@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp = request.form['otp']
    if otp == session.get('otp'):
        flash('OTP verification successful', category='success')
        try:
            email = session['email']
            form_data = session['form_data']
            fname = form_data['fname']
            lname = form_data['lname']
            password = form_data['password1']
            security_answer = form_data['security_answer']

            # Hash the password and security answer
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            hashed_security_answer = bcrypt.hashpw(security_answer.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            user_type = 'customer'

            # Insert user into the database
            sql1 = "INSERT INTO user (email, password, fname, lname, security_answer, user_type) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (email, hashed_password, fname, lname, hashed_security_answer, user_type)
            my_cursor = g.mydb.cursor()
            my_cursor.execute(sql1, values)
            g.mydb.commit()
            flash('Account created successfully!', 'success')
            session.pop('otp', None)
            session.pop('email', None)
            session.pop('form_data', None)
            return redirect(url_for('auth.login'))
        except Exception as e:
            g.mydb.rollback()
            flash('Error creating account', category='error')
            print(e)
            return render_template('verify_otp.html')
        finally:
            my_cursor.close()
    else:
        flash('Invalid OTP', category='error')
        return render_template('verify_otp.html', csrf_token=g.csrf_token)

@auth.route('/verify-otp-page', methods=['GET'])
def verify_otp_page():
    return render_template('verify_otp.html', csrf_token=g.csrf_token)
@auth.context_processor
def inject_user():
    return dict(user=current_user)


@auth.route('/userdb', methods=['GET', 'POST'])
def userdb():
    if current_user.is_authenticated and current_user.user_type == 'staff':
        mydb = None
        my_cursor = None
        role_filter = request.args.get('role', '')

        my_cursor = g.mydb.cursor(pymysql.cursors.DictCursor)

        if role_filter:
            my_cursor.execute('SELECT * FROM user WHERE user_type = %s', (role_filter,))
            results = my_cursor.fetchall()
            my_cursor.execute('SELECT COUNT(*) FROM user WHERE user_type = %s', (role_filter,))
            count = my_cursor.fetchone()['COUNT(*)']

        else:
            my_cursor.execute('SELECT * FROM user')
            results = my_cursor.fetchall()
            my_cursor.execute('SELECT COUNT(*) FROM user')
            count = my_cursor.fetchone()['COUNT(*)']

        if my_cursor:
            my_cursor.close()

        return render_template('userDB.html', count=count, data=results, role_filter=role_filter)

    else:
        return redirect(url_for('views.home'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        password = form.password.data
        if user:
            if user.is_locked_out():
                flash('Account is locked. Please try again later.', 'danger')
                return render_template('login.html', form=form)

            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                login_user(user, remember=True)
                user.failed_login_attempts = 0
                user.lockout_time = None
                db.session.commit()
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password', category='error')
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 3:
                    user.lockout_time = datetime.utcnow() + timedelta(seconds=15)
                    flash('Too many failed attempts, account is locked for 15 seconds.', 'danger')
                db.session.commit()
        else:
            flash('Email does not exist', category='error')

    return render_template('login.html', form=form, csrf_token=g.csrf_token)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm(original_password_hash=user.password)
    if form.validate_on_submit():
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_token.html', title='Reset Password', form=form, token=token, csrf_token=g.csrf_token)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='your_email@example.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            # If security answer check is required, handle it here
            security_answer = form.security_answer.data

            # Initialize failed attempts if not present
            if 'failed_attempts' not in session:
                session['failed_attempts'] = 0

            if bcrypt.checkpw(security_answer.encode('utf-8'), user.security_answer.encode('utf-8')):
                # Correct security answer, allow password reset
                session.pop('failed_attempts', None)  # reset attempts
                flash('Security answer correct. You can now reset your password.', 'success')
                return redirect(url_for('auth.reset_token', token=user.get_reset_token()))
            else:
                # Incorrect security answer
                session['failed_attempts'] += 1
                if session['failed_attempts'] >= 3:
                    # Send reset email after 3 failed attempts
                    send_reset_email(user)
                    session.pop('failed_attempts', None)  # reset attempts
                    flash('Too many failed attempts. A reset link has been sent to your email.', 'danger')
                    return redirect(url_for('auth.login'))
                else:
                    flash(f'Incorrect security answer. {3 - session["failed_attempts"]} attempts left.', 'danger')

        else:
            flash('No account is associated with that email.', 'danger')
            return redirect(url_for('auth.reset_request'))

    return render_template('reset_request.html', title='Reset Password', form=form, csrf_token=g.csrf_token)


@auth.route('/sign-up', methods=['GET', 'POST'])
def signup():
    form = Signup()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already in use', category='error')
            return render_template('sign_up.html', form=form)

        # Include security question and answer in session data
        otp = generate_otp()
        session['otp'] = otp
        session['email'] = email
        session['form_data'] = request.form.to_dict()  # Store form data in the session
        msg = Message('Your OTP Code', sender='Kjiaxuan2005@gmail.com', recipients=[email])
        msg.body = f'Your OTP code is {otp}'
        try:
            mail.send(msg)
            flash('OTP sent to your email', category='success')
            return render_template('verify_otp.html')
        except Exception as e:
            print(e)
            flash('Error sending OTP', category='error')
            return render_template('sign_up.html', form=form)
    return render_template('sign_up.html', form=form, csrf_token=g.csrf_token)

@auth.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Logged out successfully!', category='success')
        return render_template('home.html')
    else:
        flash('You are not logged in. Unable to log out of guest account.', category='error')
        return redirect(url_for('views.home'))
@auth.route('/updateUser/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    if current_user.user_type == 'staff':
        user = User.query.filter_by(id=id).first()
        if user.user_type == 'customer':
            form = Signup(request.form)
            if request.method == 'POST':

                fname = request.form.get('fname', user.fname)
                lname = request.form.get('lname', user.lname)
                email = request.form.get('email', user.email)
                password = request.form.get('password1', user.password)
                user_type = 'customer'

                my_cursor = g.mydb.cursor()
                sql1 = "UPDATE user SET fname = %s, lname = %s, email = %s, password = %s, user_type = %s WHERE id = %s"
                values = (fname, lname, email, password, user_type, id)

                try:
                    my_cursor.execute(sql1, values)
                    g.mydb.commit()
                    flash('Account updated', category='success')
                    my_cursor.close()
                    return redirect(url_for('auth.userdb'))
                except Exception as e:
                    flash('Error updating account', category='error')
                    print(e)
                    return redirect(url_for('auth.userdb'))
            return render_template('updateCustomer.html', form=form)
        elif user.user_type == 'staff':
            form = Updatestaff(request.form)
            if request.method == 'POST':
                user = User.query.filter_by(id=id).first()
                staff = Staff.query.filter_by(user_id=id).first()

                fname = request.form.get('fname', user.fname)
                lname = request.form.get('lname', user.lname)
                email = request.form.get('email', user.email)
                password = request.form.get('password1', user.password)
                user_type = 'staff'
                role = request.form.get('role', staff.role)

                my_cursor = g.mydb.cursor()
                sql1 = "UPDATE user SET fname = %s, lname = %s, email = %s, password = %s, user_type = %s WHERE id = %s"
                sql2 = "UPDATE staff SET role = %s WHERE user_id = %s"
                values1 = (fname, lname, email, password, user_type, id)
                values2 = (role, id)

                try:
                    my_cursor.execute(sql1, values1)
                    my_cursor.execute(sql2, values2)
                    g.mydb.commit()
                    flash('Account updated', category='success')
                    my_cursor.close()
                    return redirect(url_for('auth.userdb'))
                except Exception as e:
                    flash('Error updating account', category='error')
                    print(f"ERROR:", e)
                    return redirect(url_for('auth.userdb'))
            return render_template('updateStaff.html', form=form, csrf_token=g.csrf_token)
    else:
        return redirect(url_for('views.home'))




@auth.route('/deleteUser/<int:id>', methods=['POST'])
def delete_user(id):
    if current_user.is_authenticated and current_user.user_type == 'staff':
        if request.method == 'POST':

            my_cursor = g.mydb.cursor()
            sql1 = "DELETE FROM user WHERE id = %s"

            try:
                my_cursor.execute(sql1, id)
                g.mydb.commit()
                flash('Account deleted', category='success')
                my_cursor.close()
                return redirect(url_for('auth.userdb'))
            except Exception as e:
                flash('Error deleting account', category='error')
                print(e)
                return redirect(url_for('auth.userdb'))
    else:
        return redirect(url_for('views.home'))


@auth.route('/staff-sign-up', methods=['GET', 'POST'])
def staffsignup():
    if current_user.is_authenticated and current_user.user_type == 'staff':
        form = Signup(request.form)
        if request.method == 'POST':

            my_cursor = g.mydb.cursor()
            email = form.email.data

            user = User.query.filter_by(email=email).first()
            print(user)
            my_cursor.execute('SELECT COUNT(*) FROM user')
            count = int(my_cursor.fetchone()[0])

            if user:
                flash('Email already in use', category='error')
            else:
                fname = form.fname.data
                lname = form.lname.data
                password = form.password1.data
                user_type = 'staff'
                sql1 = "INSERT INTO user (email, password, fname, lname, user_type) VALUES (%s, %s, %s, %s, %s)"
                sql2 = "INSERT INTO staff (user_id, role) VALUES (%s)"
                values = (email, password, fname, lname, user_type)

                try:
                    my_cursor.execute(sql1, values)
                    user_id = my_cursor.lastrowid
                    my_cursor.execute(sql2, (user_id, 'employee'))
                    g.mydb.commit()
                    flash('Account created', category='success')
                    return redirect(url_for('views.home'))
                except Exception as e:
                    flash('Error creating account', category='error')
                    print(e)
        return render_template('sign_up.html', form=form,csrf_token=g.csrf_token)
    else:
        return redirect(url_for('auth.signup'))

