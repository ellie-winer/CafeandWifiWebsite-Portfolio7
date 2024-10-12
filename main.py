from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap
from flask_login import (LoginManager, login_user, logout_user, login_required, current_user, UserMixin,)
from forms import RegistrationForm, LoginForm, CafeForm
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import os
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'FLASK_KEY'
Bootstrap()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

UPLOAD_FOLDER = 'static/assets'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(256), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    cafes = db.session.execute(db.select(Cafe).order_by(Cafe.name)).scalars().all()
    return render_template("index.html", cafes=cafes)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# main.py

@app.route("/add", methods=["GET", "POST"])
@login_required
def post_new_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        img_url = form.img_url.data
        image_file = form.img_file_path.data

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            img_url = url_for('static', filename=f'assets/{filename}')
            img_file_path = filename
        elif not img_url:
            flash('Please provide either an image URL or upload an image file.', 'danger')
            return redirect(url_for('post_new_cafe'))

        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=img_url,
            img_file_path=img_file_path,
            location=form.location.data,
            has_sockets=form.has_sockets.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            can_take_calls=form.can_take_calls.data,
            seats=form.seats.data,
            coffee_price=form.coffee_price.data,
        )
        try:
            db.session.add(new_cafe)
            db.session.commit()
            flash('Successfully added the new cafe.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding cafe. Please try again.', 'danger')
            return redirect(url_for('post_new_cafe'))
    return render_template("add.html", form=form)

@app.route("/report-closed/<int:cafe_id>", methods=["POST"])
@login_required
def delete_cafe(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)
    if cafe:
        db.session.delete(cafe)
        db.session.commit()
        flash('Successfully deleted the cafe from the database.', 'success')
    else:
        flash('Sorry, a cafe with that id was not found in the database.', 'danger')
    return redirect(url_for('index'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = db.session.execute(db.select(User).where(User.username == form.username.data)).scalar_one_or_none()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Your account has been created and you are now logged in!', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.username == form.username.data)).scalar_one_or_none()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route("/edit/<int:cafe_id>", methods=["GET", "POST"])
@login_required
def edit(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)
    form = CafeForm(obj=cafe)

    if form.validate_on_submit():
        cafe.name = form.name.data
        cafe.map_url = form.map_url.data
        cafe.location = form.location.data
        cafe.seats = form.seats.data
        cafe.has_wifi = form.has_wifi.data
        cafe.has_sockets = form.has_sockets.data
        cafe.can_take_calls = form.can_take_calls.data
        cafe.has_toilet = form.has_toilet.data
        cafe.coffee_price = form.coffee_price.data

        img_url = form.img_url.data
        image_file = form.img_file_path.data

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            img_url = url_for('static', filename=f'assets/{filename}')
            cafe.img_file_path = filename

        elif not img_url:
            flash('Please provide either an image URL or upload an image file.', 'danger')
            return redirect(url_for('edit', cafe_id=cafe_id))

        if img_url:
            cafe.img_url = img_url

        try:
            db.session.commit()
            flash('Cafe updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating cafe. Please try again.', 'danger')
            return redirect(url_for('edit', cafe_id=cafe_id))

    if form.validate_on_submit():
        print("Form validated successfully!")
        print("Name:", form.name.data)
        # Continue printing other fields as needed
    else:
        print("Form validation failed.")
        print(form.errors)  # This will show any validation errors
        print("Form data:", form.data)  # Print form data to debug

    return render_template('edit.html', cafe=cafe, form=form)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
