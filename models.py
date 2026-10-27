from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'donor' or 'receiver'
    area = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    donations = db.relationship('Donation', backref='donor', foreign_keys='Donation.donor_id', lazy=True)
    claimed_donations = db.relationship('Donation', backref='claimed_by', foreign_keys='Donation.claimed_by_id', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_donor(self):
        return self.role == 'donor'

    @property
    def is_receiver(self):
        return self.role == 'receiver'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    food_type = db.Column(db.String(10), nullable=False)  # 'veg' or 'nonveg'
    quantity = db.Column(db.Integer, nullable=False)       # people it can feed (1 to 500)
    address = db.Column(db.String(200), nullable=False)    # full pickup address
    area = db.Column(db.String(80), nullable=False)        # used for filtering
    notes = db.Column(db.String(300), nullable=True)       # optional
    ready_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    safe_until = db.Column(db.DateTime, nullable=False)    # must be in future, max 12 hours ahead
    status = db.Column(db.String(12), default='AVAILABLE', nullable=False)  # AVAILABLE, CLAIMED, DELIVERED, CANCELLED, EXPIRED
    claimed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    claimed_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_expired(self):
        now_utc = datetime.now(timezone.utc)
        safe_dt = self.safe_until
        if safe_dt.tzinfo is None:
            safe_dt = safe_dt.replace(tzinfo=timezone.utc)
        return self.status == 'EXPIRED' or (self.status == 'AVAILABLE' and safe_dt <= now_utc)

    @property
    def time_remaining_seconds(self):
        now_utc = datetime.now(timezone.utc)
        safe_dt = self.safe_until
        if safe_dt.tzinfo is None:
            safe_dt = safe_dt.replace(tzinfo=timezone.utc)
        rem = (safe_dt - now_utc).total_seconds()
        return max(0, int(rem))

    @property
    def formatted_time_remaining(self):
        seconds = self.time_remaining_seconds
        if seconds <= 0:
            return "Expired"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m left"
        return f"{minutes}m left"

    def to_dict(self):
        safe_dt = self.safe_until
        if safe_dt.tzinfo is None:
            safe_dt = safe_dt.replace(tzinfo=timezone.utc)
        ready_dt = self.ready_at
        if ready_dt.tzinfo is None:
            ready_dt = ready_dt.replace(tzinfo=timezone.utc)

        return {
            'id': self.id,
            'title': self.title,
            'food_type': self.food_type,
            'quantity': self.quantity,
            'area': self.area,
            'status': self.status,
            'ready_at': ready_dt.isoformat(),
            'safe_until': safe_dt.isoformat(),
            'time_remaining_seconds': self.time_remaining_seconds,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<Donation {self.id}: {self.title} ({self.status})>'
