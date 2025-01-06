from wtforms import *
from wtforms.fields import PasswordField, FileField
# from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from .models import User
from flask_wtf import FlaskForm
import bcrypt
def validate_password(form, field):
    password1 = field.data
    lower_case = False
    upper_case = False
    num = False
    special = False

    if len(password1) < 8:
        raise ValidationError('Password must be at least 8 characters long.')

    for char in password1:
        if char.isdigit():
            num = True
        if char.islower():
            lower_case = True
        if char.isupper():
            upper_case = True
        if not char.isalnum():
            special = True
    if not lower_case:
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not upper_case:
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not special:
        raise ValidationError('Password must contain at least one special character.')
    if not num:
        raise ValidationError('Password must contain at least one digit.')
    if not (lower_case and upper_case and num and special):
        raise ValidationError(
            'Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character.')


class Signup(FlaskForm):
    fname = StringField('First Name', validators=[Length(min=1, max=50), DataRequired()])
    lname = StringField('Last Name', validators=[Length(min=1, max=50), DataRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    password1 = PasswordField('Password', validators=[validate_password, DataRequired()])
    password2 = PasswordField('Password(Confirm)', validators=[validate_password,DataRequired(), EqualTo('password1')])
    security_answer = StringField('What your favourite food? ', validators=[DataRequired()])
    submit = SubmitField('Signup ')
    def validate_email(self, email):

        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use.')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    security_answer = StringField('Security Answer', validators=[DataRequired()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')

    def __init__(self, original_password_hash, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        self.original_password_hash = original_password_hash

    def validate_password(self, field):
        self.check_different_from_old(field)
        # Call the external password validation function
        validate_password(self, field)

    def check_different_from_old(self, field):
        """Check if the new password is different from the old one."""
        if bcrypt.checkpw(field.data.encode('utf-8'), self.original_password_hash.encode('utf-8')):
            raise ValidationError('Your new password cannot be the same as the old password.')
class Login(FlaskForm):
    email = StringField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit form')
class ProductForm(Form):
    product_name = StringField('Product Name', validators=[Length(min=1, max=100), DataRequired()])
    product_desc = StringField('Product Description', validators=[Length(min=5, max=250), DataRequired()])
    product_cat = SelectField('Category', validators=[DataRequired()], choices=[('', 'Select'), ('1', 'Shirt'), ('2', 'Pants')])
    product_price = FloatField('Price', validators=[DataRequired()])
    product_image = FileField('Image', validators=[])

class Feedback(Form):
    feedback_name = StringField('Feedback Name', validators=[Length(min=1, max=100), DataRequired()])
    feedback_email = StringField('Feedback Email', validators=[Email(), DataRequired()])
    feedback_text = TextAreaField('Feedback Text', validators=[DataRequired()])

class Addfaq(Form):
    question = StringField('Question', validators=[Length(min=1, max=50), DataRequired()])
    answer = TextAreaField('Answer', validators=[Length(min=1, max=1024), DataRequired()])

class Updatestaff(Form):
    fname = StringField('First Name', validators=[Length(min=1, max=50), DataRequired()])
    lname = StringField('Last Name', validators=[Length(min=1, max=50), DataRequired()])
    email = StringField('Email', validators=[Email(), DataRequired()])
    password1 = PasswordField('Password', validators=[validate_password, DataRequired()])
    password2 = PasswordField('Password(Confirm)', validators=[DataRequired(), EqualTo('password1')])
    role = SelectField('Role', validators=[DataRequired()], choices=[('', 'Select'), ('1', 'admin'), ('2', 'moderator'), ('3', 'employee')])