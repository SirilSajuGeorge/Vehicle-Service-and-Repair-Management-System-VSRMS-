from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import backref,relationship
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(50), nullable=False)

    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)
    services = db.relationship('Service', backref='customer', lazy=True)
    
    def get_id(self):
        return f"user_{self.id}"
    
    @property
    def real_id(self):
        return self.id

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    license_plate = db.Column(db.String(20), unique=True)
    vin = db.Column(db.String(17), unique=True)
    odo_reading = db.Column(db.Integer)
    last_service_date = db.Column(db.DateTime)
    next_service_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    services = db.relationship('Service', backref='vehicle', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50))
    scheduled_date = db.Column(db.DateTime)
    actual_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in-progress, completed, cancelled
    cost = db.Column(db.Float)
    odometer_reading = db.Column(db.Integer)
    notes = db.Column(db.Text)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    history = db.relationship('ServiceHistory', backref='service', lazy=True)
    payment = db.relationship('Payment', backref='service', uselist=False)
    user = db.relationship('User', backref='user_services', lazy=True)

class ServiceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    amount = db.Column(db.Float)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    transaction_id = db.Column(db.String(100))

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def is_admin(self):
        return True
    
    def get_id(self):
        return f"admin_{self.id}"
    
    @property
    def real_id(self):
        return self.id

    def __repr__(self):
        return f"Admin('{self.name}', '{self.email}')"

# Calendar Slot Booking Models
class BookingSlot(db.Model):
    __tablename__ = 'booking_slots'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)  # e.g., "09:00 AM"
    max_bookings = db.Column(db.Integer, default=1)
    current_bookings = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('SlotBooking', backref='slot', lazy=True)
    
    def is_fully_booked(self):
        return self.current_bookings >= self.max_bookings

class SlotBooking(db.Model):
    __tablename__ = 'slot_bookings'
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('booking_slots.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    service_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='slot_bookings')
    vehicle = db.relationship('Vehicle', backref='slot_bookings')

class SlotSettings(db.Model):
    __tablename__ = 'slot_settings'
    id = db.Column(db.Integer, primary_key=True)
    default_slots_per_day = db.Column(db.Integer, default=5)
    slot_times = db.Column(db.Text)  # JSON string of time slots e.g., ["09:00 AM", "11:00 AM", ...]
    max_bookings_per_slot = db.Column(db.Integer, default=1)
    booking_advance_days = db.Column(db.Integer, default=30)  # How many days in advance can book
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class NonWorkingDay(db.Model):
    __tablename__ = 'non_working_days'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    reason = db.Column(db.String(200))
    is_recurring = db.Column(db.Boolean, default=False)  # For recurring holidays
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
