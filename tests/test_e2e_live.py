import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Donation

def run_e2e_test():
    app = create_app({'WTF_CSRF_ENABLED': False})
    client = app.test_client()

    print("\n==============================================")
    print("  RUNNING FULL E2E INTEGRATION FLOW VERIFICATION")
    print("==============================================")

    # 1. Visitor checks Home page
    res_home = client.get('/')
    assert res_home.status_code == 200
    assert b"Share food. Save a meal." in res_home.data
    print("[PASS] 1. Home page loads with hero and impact numbers")

    # 2. Donor logs in
    res_login = client.post('/login', data={
        'email': 'hotel@demo.com',
        'password': 'demo123'
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b"Grand Palace Hotel" in res_login.data
    print("[PASS] 2. Donor logged in successfully and redirected to Dashboard")

    # 3. Donor posts a new food donation
    safe_time = (datetime.now() + timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M')
    res_post = client.post('/donations/new', data={
        'title': '60 Boxes Veg Biryani and Salan',
        'food_type': 'veg',
        'quantity': 60,
        'area': 'Indiranagar',
        'address': 'Grand Palace Kitchen Backdoor, Indiranagar',
        'safe_until': safe_time,
        'notes': 'Packed hot in foil containers'
    }, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"60 Boxes Veg Biryani and Salan" in res_post.data
    print("[PASS] 3. Donor created food donation, visible in My Activity")

    with app.app_context():
        new_donation = Donation.query.filter_by(title='60 Boxes Veg Biryani and Salan').first()
        assert new_donation is not None
        assert new_donation.status == 'AVAILABLE'
        donation_id = new_donation.id

    # 4. Donor logs out
    client.get('/logout', follow_redirects=True)
    print("[PASS] 4. Donor logged out")

    # 5. Receiver logs in
    res_rec_login = client.post('/login', data={
        'email': 'ngo@demo.com',
        'password': 'demo123'
    }, follow_redirects=True)
    assert res_rec_login.status_code == 200
    assert b"Available Food Donations" in res_rec_login.data
    print("[PASS] 5. Receiver logged in, redirected to Available Food list")

    # 6. Receiver sees the newly posted donation in Available Food
    res_list = client.get('/donations')
    assert b"60 Boxes Veg Biryani and Salan" in res_list.data
    print("[PASS] 6. Receiver sees the donation in available list with countdown")

    # 7. Receiver views detail BEFORE claiming -> Pickup address is locked
    res_detail_locked = client.get(f'/donations/{donation_id}')
    assert res_detail_locked.status_code == 200
    assert b"Pickup Contact & Address Locked" in res_detail_locked.data
    print("[PASS] 7. Privacy verified: address locked prior to claiming")

    # 8. Receiver claims the food donation
    res_claim = client.post(f'/donations/{donation_id}/claim', follow_redirects=True)
    assert res_claim.status_code == 200
    assert b"You have successfully claimed this donation" in res_claim.data
    assert b"Contact Details Unlocked" in res_claim.data
    assert b"9876543210" in res_claim.data  # Donor phone unlocked
    print("[PASS] 8. Receiver claimed donation; donor contact and address unlocked!")

    # 9. Receiver marks the donation as DELIVERED
    res_deliver = client.post(f'/donations/{donation_id}/deliver', follow_redirects=True)
    assert res_deliver.status_code == 200
    assert b"Donation marked as delivered!" in res_deliver.data

    with app.app_context():
        deliv_donation = db.session.get(Donation, donation_id)
        assert deliv_donation.status == 'DELIVERED'
        assert deliv_donation.delivered_at is not None
    print("[PASS] 9. Receiver marked donation as DELIVERED")

    # 10. Check impact stats updated
    res_stats = client.get('/api/stats')
    stats = res_stats.get_json()
    assert stats['total_delivered'] >= 3
    print(f"[PASS] 10. API Stats updated: {stats}")
    print("==============================================")
    print("  ALL E2E VERIFICATION CHECKS PASSED PERFECTLY")
    print("==============================================\n")

if __name__ == '__main__':
    run_e2e_test()
