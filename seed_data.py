# seed_data.py
from app import app, db, User, Hotel, Room, Booking, bcrypt
from datetime import date, timedelta

with app.app_context():
    print("🧹 Clearing existing data (safe delete)...")
    # Delete in order to avoid FK issues
    Booking.query.delete()
    Room.query.delete()
    Hotel.query.delete()
    User.query.delete()
    db.session.commit()

    print("➡️ Creating sample users (owners + users)...")
    owner1 = User(name="Hotel Owner 1", email="owner1@stayease.com",
                  password=bcrypt.generate_password_hash("owner123").decode('utf-8'), role="owner")
    owner2 = User(name="Hotel Owner 2", email="owner2@stayease.com",
                  password=bcrypt.generate_password_hash("owner123").decode('utf-8'), role="owner")
    user1 = User(name="Alice Johnson", email="alice@example.com",
                 password=bcrypt.generate_password_hash("user123").decode('utf-8'), role="user")

    db.session.add_all([owner1, owner2, user1])
    db.session.commit()

    print("➡️ Adding hotels...")
    hotels = [
        Hotel(name="Sunset Paradise Resort", location="Goa",
              description="A beachfront resort with sea views and tropical gardens.",
              image_url="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80",
              owner_id=owner1.id),
        Hotel(name="Mountain Escape Lodge", location="Manali",
              description="A cozy mountain retreat with panoramic views of the Himalayas.",
              image_url="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
              owner_id=owner1.id),
        Hotel(name="City Comfort Inn", location="Bangalore",
              description="Affordable comfort in the heart of the tech city.",
              image_url="https://images.unsplash.com/photo-1551776235-dde6d4829808?w=1200&q=80",
              owner_id=owner2.id),
    ]
    db.session.add_all(hotels)
    db.session.commit()

    print("➡️ Adding rooms...")
    rooms = [
        Room(room_type="Deluxe Suite", price_per_night=6500, available=True, hotel_id=hotels[0].id),
        Room(room_type="Sea View Room", price_per_night=5200, available=True, hotel_id=hotels[0].id),
        Room(room_type="Cozy Chalet", price_per_night=4200, available=True, hotel_id=hotels[1].id),
        Room(room_type="Luxury Cabin", price_per_night=5500, available=True, hotel_id=hotels[1].id),
        Room(room_type="Business Room", price_per_night=3500, available=True, hotel_id=hotels[2].id),
    ]
    db.session.add_all(rooms)
    db.session.commit()

    print("➡️ Adding a sample booking...")
    today = date.today()
    b = Booking(user_id=user1.id, room_id=rooms[0].id, check_in=today, check_out=today + timedelta(days=2),
                total_price=2 * rooms[0].price_per_night)
    db.session.add(b)
    db.session.commit()

    print("✅ Seed complete. Logins:")
    print("owner1@stayease.com / owner123")
    print("owner2@stayease.com / owner123")
    print("alice@example.com / user123")
