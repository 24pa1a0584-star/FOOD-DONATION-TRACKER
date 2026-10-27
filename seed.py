"""
Seed script to create demo users and donations for Food Donation Tracker.
Run: python seed.py
"""
import sys
import os
from datetime import datetime, timezone, timedelta
from app import create_app
from models import db, User, Donation

def seed_database():
    if os.environ.get('RENDER') == 'true':
        raise RuntimeError('Demo seeding deletes all data and is disabled on Render.')
    app = create_app()

    with app.app_context():
        # Drop existing tables and recreate cleanly
        db.drop_all()
        db.create_all()

        print("--- Seeding Database for Food Donation Tracker ---")

        # 1. Create Donors (3)
        donors = [
            User(
                name="Grand Palace Hotel & Banquets",
                email="hotel@demo.com",
                phone="9876543210",
                role="donor",
                area="Indiranagar"
            ),
            User(
                name="Sunrise University Hostel",
                email="hostel@demo.com",
                phone="9876543211",
                role="donor",
                area="Koramangala"
            ),
            User(
                name="Sharma Family Caterers",
                email="family@demo.com",
                phone="9876543212",
                role="donor",
                area="Whitefield"
            )
        ]

        # 2. Create Receivers (2)
        receivers = [
            User(
                name="Hope For Hunger NGO",
                email="ngo@demo.com",
                phone="9876543220",
                role="receiver",
                area="Indiranagar"
            ),
            User(
                name="Rahul Volunteer Corps",
                email="volunteer@demo.com",
                phone="9876543221",
                role="receiver",
                area="Koramangala"
            )
        ]

        # Set passwords
        for user in donors + receivers:
            user.set_password("demo123")
            db.session.add(user)

        db.session.commit()
        print("[OK] Created 3 donors and 2 receivers with password 'demo123'")

        now = datetime.now(timezone.utc)

        # 3. Create 8 Donations
        # - 4 AVAILABLE
        # - 2 CLAIMED
        # - 2 DELIVERED
        donations = [
            # Available 1 (Indiranagar, Veg, 35 meals, safe for 3 hours)
            Donation(
                donor_id=donors[0].id,
                title="35 Packets Paneer Butter Masala & Roti",
                food_type="veg",
                quantity=35,
                address="100 Feet Road, 12th Main, Indiranagar, Bengaluru",
                area="Indiranagar",
                notes="Freshly packed in disposable containers with cutlery.",
                ready_at=now - timedelta(minutes=45),
                safe_until=now + timedelta(hours=3),
                status="AVAILABLE"
            ),
            # Available 2 (Koramangala, Non-Veg, 50 meals, safe for 5 hours)
            Donation(
                donor_id=donors[1].id,
                title="50 Servings Chicken Biryani & Salan",
                food_type="nonveg",
                quantity=50,
                address="Block 4, 80 Feet Road, Koramangala, Bengaluru",
                area="Koramangala",
                notes="Hot in insulated vessels, please bring your own collection bins.",
                ready_at=now - timedelta(minutes=30),
                safe_until=now + timedelta(hours=5),
                status="AVAILABLE"
            ),
            # Available 3 (Whitefield, Veg, 25 meals, safe for 2 hours)
            Donation(
                donor_id=donors[2].id,
                title="25 Containers Mixed Veg Pulao & Raita",
                food_type="veg",
                quantity=25,
                address="ITPL Main Road, Near Hope Farm, Whitefield, Bengaluru",
                area="Whitefield",
                notes="Prepared at lunch event, kept chilled and covered.",
                ready_at=now - timedelta(minutes=20),
                safe_until=now + timedelta(hours=2),
                status="AVAILABLE"
            ),
            # Available 4 (Indiranagar, Non-Veg, 20 meals, safe for 7 hours)
            Donation(
                donor_id=donors[0].id,
                title="20 Portions Grilled Fish & Steamed Rice",
                food_type="nonveg",
                quantity=20,
                address="Kitchen Backdoor, Grand Palace, Indiranagar, Bengaluru",
                area="Indiranagar",
                notes="Packed individually in food-grade boxes.",
                ready_at=now - timedelta(minutes=15),
                safe_until=now + timedelta(hours=7),
                status="AVAILABLE"
            ),
            # Claimed 1 (Koramangala, Veg, 40 meals, safe for 4 hours)
            Donation(
                donor_id=donors[1].id,
                title="40 Plates Dal Tadka, Jeera Rice & Subzi",
                food_type="veg",
                quantity=40,
                address="Hostel Mess 2, Sunrise Campus, Koramangala",
                area="Koramangala",
                notes="Volunteers are on the way for pickup.",
                ready_at=now - timedelta(hours=1),
                safe_until=now + timedelta(hours=4),
                status="CLAIMED",
                claimed_by_id=receivers[0].id,
                claimed_at=now - timedelta(minutes=25)
            ),
            # Claimed 2 (Whitefield, Veg, 60 meals, safe for 6 hours)
            Donation(
                donor_id=donors[2].id,
                title="60 Meal Trays Idli, Vada & Sambar",
                food_type="veg",
                quantity=60,
                address="Gate 3, Sharma Caterers HQ, Whitefield",
                area="Whitefield",
                notes="Morning batch, verified hot and hygienic.",
                ready_at=now - timedelta(hours=1, minutes=30),
                safe_until=now + timedelta(hours=6),
                status="CLAIMED",
                claimed_by_id=receivers[1].id,
                claimed_at=now - timedelta(minutes=40)
            ),
            # Delivered 1 (Indiranagar, Non-Veg, 45 meals)
            Donation(
                donor_id=donors[0].id,
                title="45 Packets Mutton Curry & Ghee Rice",
                food_type="nonveg",
                quantity=45,
                address="100 Feet Road, Indiranagar, Bengaluru",
                area="Indiranagar",
                notes="Delivered to Shanti Shelter Home.",
                ready_at=now - timedelta(hours=5),
                safe_until=now + timedelta(hours=1),
                status="DELIVERED",
                claimed_by_id=receivers[0].id,
                claimed_at=now - timedelta(hours=4),
                delivered_at=now - timedelta(hours=2)
            ),
            # Delivered 2 (Koramangala, Veg, 80 meals)
            Donation(
                donor_id=donors[1].id,
                title="80 Boxes Khichdi & Achar (Comfort Food)",
                food_type="veg",
                quantity=80,
                address="Hostel Gate 1, Koramangala, Bengaluru",
                area="Koramangala",
                notes="Distributed at migrant worker colony.",
                ready_at=now - timedelta(hours=6),
                safe_until=now + timedelta(hours=2),
                status="DELIVERED",
                claimed_by_id=receivers[1].id,
                claimed_at=now - timedelta(hours=5),
                delivered_at=now - timedelta(hours=3)
            )
        ]

        for donation in donations:
            db.session.add(donation)

        db.session.commit()
        print("[OK] Created 8 donations (4 Available, 2 Claimed, 2 Delivered)")
        print("\n================ DEMO ACCOUNTS ================")
        print("Password for all accounts: demo123")
        print("\nDONORS:")
        for d in donors:
            print(f"  * {d.name} ({d.area}) -> {d.email}")
        print("\nRECEIVERS:")
        for r in receivers:
            print(f"  * {r.name} ({r.area}) -> {r.email}")
        print("===============================================\n")

if __name__ == '__main__':
    seed_database()
