import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from models import db, User, Donation
from forms import IST

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_user(app, name, email, role, area="Indiranagar", phone="9988776655", password="password123"):
    with app.app_context():
        user = User(name=name, email=email, role=role, area=area, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id

def login(client, email, password="password123"):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

# 1. Register and login works for both roles
def test_register_and_login_donor_and_receiver(app, client):
    # Register Donor
    res_reg_donor = client.post('/register', data={
        'name': 'Test Donor Hotel',
        'email': 'donor1@test.com',
        'phone': '9876543210',
        'role': 'donor',
        'area': 'Indiranagar',
        'password': 'secretpassword',
        'confirm_password': 'secretpassword'
    }, follow_redirects=True)
    assert res_reg_donor.status_code == 200
    assert b"Donor Dashboard & Activity" in res_reg_donor.data or b"donor1@test.com" in res_reg_donor.data

    # Log out
    client.get('/logout', follow_redirects=True)

    # Register Receiver
    res_reg_receiver = client.post('/register', data={
        'name': 'Test NGO Volunteer',
        'email': 'receiver1@test.com',
        'phone': '9876543211',
        'role': 'receiver',
        'area': 'Koramangala',
        'password': 'secretpassword',
        'confirm_password': 'secretpassword'
    }, follow_redirects=True)
    assert res_reg_receiver.status_code == 200
    assert b"Available Food Donations" in res_reg_receiver.data

    # Log out
    client.get('/logout', follow_redirects=True)

    # Log in as Donor
    res_login_donor = login(client, 'donor1@test.com', 'secretpassword')
    assert res_login_donor.status_code == 200
    assert b"Test Donor Hotel" in res_login_donor.data

    client.get('/logout', follow_redirects=True)

    # Log in as Receiver
    res_login_receiver = login(client, 'receiver1@test.com', 'secretpassword')
    assert res_login_receiver.status_code == 200
    assert b"Test NGO Volunteer" in res_login_receiver.data

# 2. Donor can create a donation; receiver cannot
def test_donor_can_create_donation_receiver_cannot(app, client):
    donor_id = create_user(app, "Donor One", "donor@app.com", "donor")
    receiver_id = create_user(app, "Receiver One", "receiver@app.com", "receiver")

    # Receiver attempt should be rejected with 403
    login(client, "receiver@app.com")
    res_receiver_get = client.get('/donations/new')
    assert res_receiver_get.status_code == 403

    future_time = (datetime.now(IST) + timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M')
    res_receiver_post = client.post('/donations/new', data={
        'title': 'Extra Meals',
        'food_type': 'veg',
        'quantity': 20,
        'address': 'Street 1, Area',
        'area': 'Indiranagar',
        'safe_until': future_time
    })
    assert res_receiver_post.status_code == 403

    client.get('/logout')

    # Donor attempt succeeds
    login(client, "donor@app.com")
    res_donor_get = client.get('/donations/new')
    assert res_donor_get.status_code == 200

    res_donor_post = client.post('/donations/new', data={
        'title': '40 Fresh Veg Pulao Packets',
        'food_type': 'veg',
        'quantity': 40,
        'address': 'Door 45, 12th Main, Indiranagar',
        'area': 'Indiranagar',
        'safe_until': future_time,
        'notes': 'Packed hot'
    }, follow_redirects=True)
    assert res_donor_post.status_code == 200

    with app.app_context():
        donation = Donation.query.filter_by(title='40 Fresh Veg Pulao Packets').first()
        assert donation is not None
        assert donation.quantity == 40
        assert donation.status == 'AVAILABLE'
        assert donation.donor_id == donor_id

# 3. Receiver can claim; a second claim on the same donation fails
def test_claim_with_double_claim_protection(app, client):
    donor_id = create_user(app, "Donor Hotel", "donor@hotel.com", "donor")
    rec1_id = create_user(app, "Receiver NGO", "ngo@test.com", "receiver")
    rec2_id = create_user(app, "Receiver Vol", "vol@test.com", "receiver")

    now_utc = datetime.now(timezone.utc)
    with app.app_context():
        d = Donation(
            donor_id=donor_id,
            title="30 Biryani Plates",
            food_type="nonveg",
            quantity=30,
            address="123 Road",
            area="Koramangala",
            safe_until=now_utc + timedelta(hours=3),
            status="AVAILABLE"
        )
        db.session.add(d)
        db.session.commit()
        d_id = d.id

    # Receiver 1 claims it
    login(client, "ngo@test.com")
    res_claim1 = client.post(f'/donations/{d_id}/claim', follow_redirects=True)
    assert res_claim1.status_code == 200
    assert b"You have successfully claimed this donation" in res_claim1.data

    with app.app_context():
        d_check = db.session.get(Donation, d_id)
        assert d_check.status == "CLAIMED"
        assert d_check.claimed_by_id == rec1_id

    client.get('/logout')

    # Receiver 2 tries to claim the already claimed donation
    login(client, "vol@test.com")
    res_claim2 = client.post(f'/donations/{d_id}/claim', follow_redirects=True)
    assert res_claim2.status_code == 200
    assert b"Sorry, this donation was just claimed or has expired." in res_claim2.data

    # Verify status unchanged
    with app.app_context():
        d_check = db.session.get(Donation, d_id)
        assert d_check.status == "CLAIMED"
        assert d_check.claimed_by_id == rec1_id

# 4. Expired donation cannot be claimed and does not appear in the list
def test_expired_donation_handling(app, client):
    donor_id = create_user(app, "Donor Fast", "donor@fast.com", "donor")
    rec_id = create_user(app, "Receiver Food", "rec@fast.com", "receiver")

    now_utc = datetime.now(timezone.utc)
    with app.app_context():
        expired_donation = Donation(
            donor_id=donor_id,
            title="Expired Sweets",
            food_type="veg",
            quantity=15,
            address="Sweet Shop, Indiranagar",
            area="Indiranagar",
            safe_until=now_utc - timedelta(hours=1),
            status="AVAILABLE"
        )
        db.session.add(expired_donation)
        db.session.commit()
        exp_id = expired_donation.id

    login(client, "rec@fast.com")

    # Does not appear in available list
    res_list = client.get('/donations')
    assert res_list.status_code == 200
    assert b"Expired Sweets" not in res_list.data

    # Claiming should fail
    res_claim = client.post(f'/donations/{exp_id}/claim', follow_redirects=True)
    assert b"Sorry, this donation was just claimed or has expired." in res_claim.data

    with app.app_context():
        d_check = db.session.get(Donation, exp_id)
        assert d_check.status == "EXPIRED"

# 5. Only the claiming receiver can mark delivered
def test_only_claiming_receiver_can_mark_delivered(app, client):
    donor_id = create_user(app, "Donor Caterer", "donor@caterer.com", "donor")
    rec1_id = create_user(app, "Claiming Receiver", "rec1@charity.com", "receiver")
    rec2_id = create_user(app, "Other Receiver", "rec2@charity.com", "receiver")

    now_utc = datetime.now(timezone.utc)
    with app.app_context():
        d = Donation(
            donor_id=donor_id,
            title="50 Meals for Shelter",
            food_type="veg",
            quantity=50,
            address="Caterer Hall, Whitefield",
            area="Whitefield",
            safe_until=now_utc + timedelta(hours=4),
            status="CLAIMED",
            claimed_by_id=rec1_id,
            claimed_at=now_utc
        )
        db.session.add(d)
        db.session.commit()
        d_id = d.id

    # Other receiver attempts to mark delivered -> 403 Forbidden
    login(client, "rec2@charity.com")
    res_other = client.post(f'/donations/{d_id}/deliver')
    assert res_other.status_code == 403

    client.get('/logout')

    # Claiming receiver marks delivered -> 200 Success
    login(client, "rec1@charity.com")
    res_claimer = client.post(f'/donations/{d_id}/deliver', follow_redirects=True)
    assert res_claimer.status_code == 200
    assert b"Donation marked as delivered!" in res_claimer.data

    with app.app_context():
        d_check = db.session.get(Donation, d_id)
        assert d_check.status == "DELIVERED"
        assert d_check.delivered_at is not None

# 6. Donor can cancel only AVAILABLE donations
def test_donor_cancel_donation(app, client):
    donor1_id = create_user(app, "Owner Donor", "owner@donor.com", "donor")
    donor2_id = create_user(app, "Other Donor", "other@donor.com", "donor")
    rec_id = create_user(app, "Receiver Volunteer", "volunteer@rec.com", "receiver")

    now_utc = datetime.now(timezone.utc)
    with app.app_context():
        d1 = Donation(
            donor_id=donor1_id,
            title="Available Salad Trays",
            food_type="veg",
            quantity=20,
            address="10 Green Way",
            area="Indiranagar",
            safe_until=now_utc + timedelta(hours=3),
            status="AVAILABLE"
        )
        d2_claimed = Donation(
            donor_id=donor1_id,
            title="Claimed Hot Pots",
            food_type="veg",
            quantity=30,
            address="10 Green Way",
            area="Indiranagar",
            safe_until=now_utc + timedelta(hours=3),
            status="CLAIMED",
            claimed_by_id=rec_id,
            claimed_at=now_utc
        )
        db.session.add_all([d1, d2_claimed])
        db.session.commit()
        d1_id = d1.id
        d2_id = d2_claimed.id

    # Non-owner donor trying to cancel d1 -> 403
    login(client, "other@donor.com")
    res_other_cancel = client.post(f'/donations/{d1_id}/cancel')
    assert res_other_cancel.status_code == 403

    client.get('/logout')

    # Owner donor cancels available donation -> Success
    login(client, "owner@donor.com")
    res_cancel_ok = client.post(f'/donations/{d1_id}/cancel', follow_redirects=True)
    assert res_cancel_ok.status_code == 200
    assert b"Your donation has been cancelled." in res_cancel_ok.data

    with app.app_context():
        d1_check = db.session.get(Donation, d1_id)
        assert d1_check.status == "CANCELLED"

    # Owner donor cannot cancel an already claimed donation
    res_cancel_claimed = client.post(f'/donations/{d2_id}/cancel', follow_redirects=True)
    assert b"Only available donations can be cancelled" in res_cancel_claimed.data

    with app.app_context():
        d2_check = db.session.get(Donation, d2_id)
        assert d2_check.status == "CLAIMED"

# 7. /api/stats returns correct numbers
def test_api_stats(app, client):
    donor_id = create_user(app, "Stats Donor", "stats@donor.com", "donor")
    rec_id = create_user(app, "Stats Rec", "stats@rec.com", "receiver")

    now_utc = datetime.now(timezone.utc)
    with app.app_context():
        d1 = Donation(
            donor_id=donor_id,
            title="Delivered Feast 1",
            food_type="veg",
            quantity=50,
            address="Address 1",
            area="HSR",
            safe_until=now_utc + timedelta(hours=2),
            status="DELIVERED",
            claimed_by_id=rec_id,
            claimed_at=now_utc,
            delivered_at=now_utc
        )
        d2 = Donation(
            donor_id=donor_id,
            title="Delivered Feast 2",
            food_type="nonveg",
            quantity=35,
            address="Address 2",
            area="HSR",
            safe_until=now_utc + timedelta(hours=2),
            status="DELIVERED",
            claimed_by_id=rec_id,
            claimed_at=now_utc,
            delivered_at=now_utc
        )
        d3 = Donation(
            donor_id=donor_id,
            title="Available Rice",
            food_type="veg",
            quantity=20,
            address="Address 3",
            area="HSR",
            safe_until=now_utc + timedelta(hours=3),
            status="AVAILABLE"
        )
        db.session.add_all([d1, d2, d3])
        db.session.commit()

    res = client.get('/api/stats')
    assert res.status_code == 200
    data = res.get_json()

    assert data['total_donations'] == 3
    assert data['total_delivered'] == 2
    assert data['total_meals_saved'] == 85  # 50 + 35
    assert data['active_donors'] == 1
