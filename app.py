# app.py - StayIN (fixed & consistent)
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)



from datetime import datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request,session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from functools import wraps
from urllib.parse import urlparse, urljoin
from authlib.integrations.flask_client import OAuth





app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('STAYIN_SECRET', 'dev_secret_key')
# default to sqlite for local development; your production DATABASE_URL will override
app.config['SQLALCHEMY_DATABASE_URI'] = ('postgresql://neondb_owner:npg_tDOVFP2gi5nZ@ep-cold-math-adbioacl-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

#google-auth login

oauth = OAuth(app)

google = oauth.register(
   name='google',
   client_id=os.environ.get('GOOGLE_CLIENT_ID'),
   client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
   server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
   client_kwargs={'scope': 'openid email profile'}
)

# -----------------------------
# MODELS
# -----------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')

    hotels = db.relationship('Hotel', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    rooms = db.relationship('Room', backref='hotel', lazy=True)


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_type = db.Column(db.String(100), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)

    bookings = db.relationship('Booking', backref='room', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    adults = db.Column(db.Integer, default=1, nullable=False)
    children = db.Column(db.Integer, default=0, nullable=False)



# -----------------------------
# Login loader
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None


# -----------------------------
# Helpers
# -----------------------------
def is_safe_redirect(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ("http", "https") and host_url.netloc == redirect_url.netloc


def role_required(role):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role != role:
                flash("You are not authorized to access this page.", "danger")
                return redirect(url_for('user_dashboard'))
            return func(*args, **kwargs)
        return decorated
    return wrapper


# -----------------------------
# ROUTES: Home + Auth
# -----------------------------
@app.route('/')
def index():
    hotels = Hotel.query.all()
    # compute min price per hotel
    hotel_min = {}
    for h in hotels:
        prices = [r.price_per_night for r in h.rooms] if h.rooms else []
        hotel_min[h.id] = int(min(prices)) if prices else None
    return render_template('index.html', hotels=hotels, hotel_min=hotel_min)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        raw_password = request.form['password']
        role = request.form.get('role', 'user')

        if not name or not email or not raw_password:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))

        hashed = bcrypt.generate_password_hash(raw_password).decode('utf-8')
        user = User(name=name, email=email, password=hashed, role=role)
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('owner_dashboard') if current_user.role == 'owner' else url_for('user_dashboard'))

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            if next_page and is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for('owner_dashboard') if user.role == 'owner' else url_for('user_dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/callback')
def google_callback():
    token = google.authorize_access_token()

    # Fetch Google user info
    resp = google.get("https://openidconnect.googleapis.com/v1/userinfo")
    user_info = resp.json()

    email = user_info.get("email")
    name = user_info.get("name")

    if not email:
        flash("Google login failed. Try again.", "danger")
        return redirect(url_for('login'))

    # Save temp session data
    session['google_name'] = name
    session['google_email'] = email

    # If user already exists → auto login
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        login_user(existing_user)
        flash("Welcome back!", "success")
        return redirect(url_for('user_dashboard'))

    # New user → choose role
    return redirect(url_for('choose_role'))


@app.route('/choose_role', methods=['GET', 'POST'])
def choose_role():
    name = session.get('google_name')
    email = session.get('google_email')

    if not email:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        selected_role = request.form.get('role')

        # Create user with chosen role
        user = User(
            name=name,
            email=email,
            password=bcrypt.generate_password_hash("google_oauth_dummy").decode('utf-8'),
            role=selected_role
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created using Google!", "success")

        if selected_role == "owner":
            return redirect(url_for('owner_dashboard'))
        return redirect(url_for('user_dashboard'))

    return render_template('choose_role.html', name=name, email=email)





@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))


# -----------------------------
# USER & OWNER DASHBOARDS
# -----------------------------
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html', user=current_user)


@app.route('/owner_dashboard')
@login_required
@role_required('owner')
def owner_dashboard():
    hotels = Hotel.query.filter_by(owner_id=current_user.id).all()
    total_hotels = len(hotels)
    total_rooms = sum(len(h.rooms) for h in hotels)
    total_bookings = Booking.query.join(Room).join(Hotel).filter(Hotel.owner_id == current_user.id).count()
    return render_template('owner_dashboard.html', total_hotels=total_hotels, total_rooms=total_rooms,
                           total_bookings=total_bookings, hotels=hotels)


# -----------------------------
# OWNER: Manage Hotels & Rooms
# -----------------------------
@app.route('/owner/hotels')
@login_required
@role_required('owner')
def owner_hotels():
    hotels = Hotel.query.filter_by(owner_id=current_user.id).all()
    return render_template('owner_hotels.html', hotels=hotels)


@app.route('/owner/hotels/add', methods=['GET', 'POST'])
@login_required
@role_required('owner')
def add_hotel():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not name or not location:
            flash('Please provide name and location.', 'danger')
            return redirect(url_for('add_hotel'))

        hotel = Hotel(name=name, location=location, description=description, owner_id=current_user.id,
                      image_url=image_url or None)
        db.session.add(hotel)
        db.session.commit()

        flash('Hotel added successfully!', 'success')
        return redirect(url_for('owner_hotels'))

    return render_template('add_hotel.html')


@app.route('/owner/hotels/<int:hotel_id>/rooms/add', methods=['GET', 'POST'])
@login_required
@role_required('owner')
def add_room(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    if hotel.owner_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        room_type = request.form.get('room_type', '').strip()
        price = request.form.get('price', '').strip()
        available = (request.form.get('available') == 'on')

        try:
            price_float = float(price)
        except:
            flash('Invalid price', 'danger')
            return redirect(url_for('add_room', hotel_id=hotel_id))

        room = Room(room_type=room_type, price_per_night=price_float, available=available, hotel_id=hotel_id)
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('owner_hotels'))

    return render_template('add_room.html', hotel=hotel)


# -----------------------------
# USER: Browse Hotels
# -----------------------------
@app.route('/hotels')
def list_hotels():
    q = request.args.get('q', '').strip()
    loc = request.args.get('location', '').strip()

    query = Hotel.query

    if q:
        query = query.filter(Hotel.name.ilike(f"%{q}%"))
    if loc:
        query = query.filter(Hotel.location.ilike(f"%{loc}%"))

    hotels = query.all()
    hotel_min = {}
    for h in hotels:
        prices = [r.price_per_night for r in h.rooms] if h.rooms else []
        hotel_min[h.id] = int(min(prices)) if prices else None

    return render_template('list_hotels.html', hotels=hotels, hotel_min=hotel_min)


@app.route('/hotels/<int:hotel_id>')
def hotel_detail(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotel_detail.html', hotel=hotel, rooms=rooms)


# -----------------------------
# USER: Bookings
# -----------------------------
@app.route('/user_bookings')
@login_required
def user_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/rooms/<int:room_id>/book', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    hotel = room.hotel

    if request.method == 'POST':
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')

        # Convert dates
        try:
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        except:
            flash("Enter valid dates.", "danger")
            return redirect(url_for('book_room', room_id=room_id))

        # Validate dates
        if check_in >= check_out:
            flash("Check-out must be after check-in.", "danger")
            return redirect(url_for('book_room', room_id=room_id))

        # ✅ GET GUEST VALUES HERE
        adults = int(request.form.get("adults", 1))
        children = int(request.form.get("children", 0))

        # OPTIONAL VALIDATION
        if adults < 1:
            flash("At least 1 adult is required.", "danger")
            return redirect(url_for('book_room', room_id=room_id))

        # Check for overlapping bookings
        overlapping = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()

        if overlapping:
            flash("Room is already booked for selected dates.", "danger")
            return redirect(url_for('hotel_detail', hotel_id=hotel.id))

        # Calculate total price
        nights = (check_out - check_in).days
        total_price = nights * float(room.price_per_night)

        # Create booking with guest details
        booking = Booking(
            user_id=current_user.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            adults=adults,
            children=children
        )

        db.session.add(booking)
        db.session.commit()

        flash(f"Booking successful — ₹{total_price:.2f}", "success")
        return redirect(url_for('user_bookings'))

    return render_template('book_room.html', hotel=hotel, room=room)


# -----------------------------
# Init DB & Run
# -----------------------------
with app.app_context():
    db.create_all()
    print("✅ DB ready:", db.engine.url)

if __name__ == "__main__":
    app.run(debug=True)
    
if __name__ == "__main__":
    from os import environ
    port = int(environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
