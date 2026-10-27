from datetime import datetime, timezone, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from models import User

IST = timezone(timedelta(hours=5, minutes=30))

class RegisterForm(FlaskForm):
    name = StringField('Full Name or Organization Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=80, message="Name must be between 2 and 80 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    phone = StringField('Phone Number', validators=[
        DataRequired(message="Phone number is required."),
        Length(min=10, max=15, message="Please enter a valid phone number (10-15 digits).")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords do not match.")
    ])
    role = SelectField('Register As', choices=[
        ('donor', 'Food Donor (Hotel, Hostel, Caterer, Family)'),
        ('receiver', 'Food Receiver (NGO, Charity, Volunteer)')
    ], validators=[DataRequired(message="Please select your role.")])
    area = StringField('Area / Neighborhood / City', validators=[
        DataRequired(message="Area is required."),
        Length(min=2, max=80, message="Area must be between 2 and 80 characters.")
    ])

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data.strip().lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please log in or use another email.')


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])


class DonationForm(FlaskForm):
    title = StringField('Food Title / Description', validators=[
        DataRequired(message="Food title is required."),
        Length(min=3, max=100, message="Title must be between 3 and 100 characters.")
    ], render_kw={"placeholder": "e.g., 50 Packets Vegetable Biryani & Dal"})

    food_type = SelectField('Food Type', choices=[
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian')
    ], validators=[DataRequired(message="Please select food type.")])

    quantity = IntegerField('Quantity (People it can feed)', validators=[
        DataRequired(message="Quantity is required."),
        NumberRange(min=1, max=500, message="Quantity must be between 1 and 500 people.")
    ], render_kw={"placeholder": "e.g., 25"})

    address = TextAreaField('Full Pickup Address', validators=[
        DataRequired(message="Full pickup address is required."),
        Length(min=5, max=200, message="Address must be between 5 and 200 characters.")
    ], render_kw={"rows": 2, "placeholder": "Door number, street name, landmark"})

    area = StringField('Area / Locality', validators=[
        DataRequired(message="Area is required."),
        Length(min=2, max=80, message="Area must be between 2 and 80 characters.")
    ], render_kw={"placeholder": "e.g., Indiranagar, Koramangala, etc."})

    safe_until = DateTimeLocalField('Safe Until (Consume Before)', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message="Please specify safe-until date and time.")
    ])

    notes = TextAreaField('Optional Notes', validators=[
        Optional(),
        Length(max=300, message="Notes cannot exceed 300 characters.")
    ], render_kw={"rows": 2, "placeholder": "e.g., Packed in foil containers, carry your own bags"})

    def validate_safe_until(self, field):
        if not field.data:
            return

        # The input datetime is submitted in local time (IST).
        # We attach IST timezone and convert to UTC for validation.
        naive_dt = field.data
        local_dt = naive_dt.replace(tzinfo=IST)
        utc_dt = local_dt.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)

        diff_seconds = (utc_dt - now_utc).total_seconds()
        # Must be in the future
        if diff_seconds <= 0:
            raise ValidationError("Safe-until date and time must be in the future.")

        # Max 12 hours ahead (with a small 2-minute grace margin for form filling)
        max_seconds = 12 * 3600 + 120
        if diff_seconds > max_seconds:
            raise ValidationError("Safe-until time must be within 12 hours from now for cooked food safety.")
