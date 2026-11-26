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