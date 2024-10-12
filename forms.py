from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, URLField, IntegerField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo, Optional


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class CafeForm(FlaskForm):
    name = StringField('Cafe Name', validators=[DataRequired()])
    map_url = URLField('Map URL', validators=[DataRequired()])
    img_url = URLField('Image URL', validators=[Optional()])
    img_file_path = FileField('Upload Image', validators=[Optional()])
    location = StringField('Location', validators=[DataRequired()])
    seats = StringField('Number of Seats', validators=[DataRequired()])
    has_wifi = BooleanField('Has Wifi')
    has_sockets = BooleanField('Has Sockets')
    can_take_calls = BooleanField('Can Take Calls')
    has_toilet = BooleanField('Has Toilet')
    coffee_price = StringField('Coffee Price', validators=[Optional()])
    submit = SubmitField('Save Changes')
