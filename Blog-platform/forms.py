from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_login import current_user
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64, message="Username must be between 3 and 64 characters long.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with that email address already exists.')


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500, message="Bio cannot exceed 500 characters.")
    ])
    avatar = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only! (jpg, jpeg, png, webp, gif)')
    ])
    submit = SubmitField('Save Profile Changes')

    def validate_username(self, username):
        if username.data.strip() != current_user.username:
            user = User.query.filter_by(username=username.data.strip()).first()
            if user:
                raise ValidationError('That username is already in use.')

    def validate_email(self, email):
        if email.data.strip().lower() != current_user.email:
            user = User.query.filter_by(email=email.data.strip().lower()).first()
            if user:
                raise ValidationError('That email address is already registered.')


class PostForm(FlaskForm):
    title = StringField('Post Title', validators=[
        DataRequired(),
        Length(min=3, max=140, message="Title must be between 3 and 140 characters.")
    ])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    tags = StringField('Tags', validators=[Optional()], description="Separate tags with commas (e.g. Python, WebDev, Flask)")
    summary = TextAreaField('Short Summary / Excerpt', validators=[
        DataRequired(),
        Length(min=10, max=300, message="Summary must be between 10 and 300 characters.")
    ])
    content = TextAreaField('Post Content', validators=[
        DataRequired(),
        Length(min=20, message="Post content must be at least 20 characters.")
    ])
    featured_image = FileField('Featured Cover Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Images only!')
    ])
    status = SelectField('Status', choices=[('published', 'Publish Immediately'), ('draft', 'Save as Draft')])
    submit = SubmitField('Save Post')


class CommentForm(FlaskForm):
    content = TextAreaField('Leave a Comment', validators=[
        DataRequired(message="Comment content cannot be empty."),
        Length(min=2, max=1000, message="Comment must be between 2 and 1000 characters.")
    ])
    submit = SubmitField('Post Comment')


class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')
