from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError,
)

from src.models import User
from wtforms import TextAreaField
from wtforms.validators import Optional

class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=30),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128),
        ],
    )

    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    submit = SubmitField("Create account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("This username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("This email is already registered.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()],
    )

    remember_me = BooleanField("Remember me")

    submit = SubmitField("Log in")
    
class ProfileForm(FlaskForm):
    display_name = StringField(
        "Display name",
        validators=[Optional(), Length(max=60)],
    )

    bio = TextAreaField(
        "About me",
        validators=[Optional(), Length(max=500)],
    )

    avatar_url = StringField(
        "Profile picture URL",
        validators=[Optional(), Length(max=500)],
    )

    website_url = StringField(
        "Website",
        validators=[Optional(), Length(max=500)],
    )

    instagram_url = StringField(
        "Instagram URL",
        validators=[Optional(), Length(max=500)],
    )

    favorite_genres = TextAreaField("Favorite genres")

    top_movies = TextAreaField("Top 5 movies")

    top_actors = TextAreaField("Top 5 actors")

    submit = SubmitField("Save changes")