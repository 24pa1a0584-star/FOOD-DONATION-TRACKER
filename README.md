# Food Donation Tracker 🍲

> **Community Service Project:** Connecting surplus cooked food from hotels, hostels, and caterers with local NGOs and volunteers before it spoils.

---

## 1. Project Overview

**Render deployment:** See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for the project assessment,
GitHub setup, Blueprint/manual deployment, PostgreSQL configuration, and verification steps.
The included `render.yaml` uses free demo plans; the free database expires after 30 days.

Food Donation Tracker is a responsive web application designed for fast, hyperlocal food recovery. Because prepared cooked food spoils within hours, this platform is optimized for immediate turnaround:
- **Donors** (restaurants, hostels, caterers, families) can publish surplus food donations in **under 1 minute**.
- **Receivers** (NGOs, shelters, community volunteers) can browse listings with **live expiry countdowns** and claim in **1 click**.
- **Double-Claim Protection:** Enforced via atomic database transactions ensuring no two receivers ever claim the same batch.
- **Privacy First:** Pickup address and phone number are hidden until a verified receiver claims the food.
- **Public Impact Metrics:** Live metrics displaying donations posted, deliveries completed, and total meals saved.

---

## 2. Tech Stack

- **Backend:** Python 3.11+ / Flask 3.0.3, Flask-SQLAlchemy 3.1.1, Flask-Login 0.6.3, Flask-WTF 1.2.1
- **Database:** SQLite (stored at `instance/app.db`)
- **Frontend:** Jinja2 server-rendered templates, Bootstrap 5.3 (CDN), Bootstrap Icons, Google Fonts (Inter)
- **Client Logic:** Vanilla JavaScript (live countdown timers, confirmation modals, auto-calculated date defaults)
- **Testing:** pytest 8.2.2 (in-memory SQLite test database)

---

## 3. Project Structure

```
food-donation-tracker/
├── app.py                  # App factory, Jinja filters, error handlers
├── models.py               # SQLAlchemy models (User, Donation)
├── forms.py                # Flask-WTF forms and validation
├── seed.py                 # Demo seed data script
├── requirements.txt        # Python dependencies
├── pytest.ini              # Test runner configuration
├── .env.example            # Environment variables template
├── .env                    # Local environment config
├── README.md               # Documentation and demo guide
├── routes/
│   ├── __init__.py
│   ├── auth.py             # Register, login, logout, role access controls
│   ├── donations.py        # Post, list, claim, deliver, cancel donations
│   ├── main.py             # Home impact stats, my activity dashboard
│   └── api.py              # Public JSON impact stats and donation API
├── templates/
│   ├── base.html           # Responsive layout, navbar, flash alerts
│   ├── home.html           # Hero section, impact statistics, 3-step guide
│   ├── register.html       # Role-based user registration
│   ├── login.html          # Authentication with demo login hints
│   ├── donation_new.html   # Food donation creation form
│   ├── donation_list.html  # Live receiver list with filters and countdowns
│   ├── donation_detail.html# Detail view with privacy-locked pickup address
│   ├── my_activity.html    # Role-aware donor/receiver dashboard
│   └── errors/
│       ├── 403.html        # Role permission denied page
│       ├── 404.html        # Not found page
│       └── 500.html        # Server error page
├── static/
│   ├── css/style.css       # Clean green & white theme, responsive cards
│   └── js/app.js           # Live countdown ticking, confirm dialogs
└── tests/
    └── test_app.py         # 7 automated test suites
```

---

## 4. Setup and Installation

### Windows (PowerShell)

```powershell
# 1. Clone/navigate to project directory
cd c:\Users\prane\OneDrive\Documents\csp

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Seed demo data
python seed.py

# 6. Run local server
flask --app app run --debug
```

### Mac / Linux (Terminal)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo data
python seed.py

# 4. Run local server
flask --app app run --debug
```

The application will be running at `http://127.0.0.1:5000`.

---

## 5. Demo Accounts

All demo accounts use password: `demo123`

| Role | Name | Email | Area |
|---|---|---|---|
| **Donor** | Grand Palace Hotel | `hotel@demo.com` | Indiranagar |
| **Donor** | Sunrise University Hostel | `hostel@demo.com` | Koramangala |
| **Donor** | Sharma Family Caterers | `family@demo.com` | Whitefield |
| **Receiver** | Hope For Hunger NGO | `ngo@demo.com` | Indiranagar |
| **Receiver** | Rahul Volunteer Corps | `volunteer@demo.com` | Koramangala |

---

## 6. How to Demo in 3 Minutes

Follow this quick walkthrough to showcase all key features:

1. **Impact Home Page (0:00 - 0:30)**
   - Open `http://127.0.0.1:5000`.
   - Point out the **Impact Numbers** (Donations Posted, Deliveries, Meals Saved, Active Donors).
   - Point out the clean green/white food-rescue theme and mobile responsiveness.

2. **Donor Posts Food (0:30 - 1:15)**
   - Click **Log In** and use `hotel@demo.com` / `demo123`.
   - Click **Post Donation** in the navbar.
   - Enter:
     - Title: `40 Packets Vegetable Biryani & Dal`
     - Food Type: `Vegetarian`
     - Quantity: `40`
     - Area: `Indiranagar`
     - Address: `12th Main Road, Indiranagar`
     - Safe Until: 4 hours from now (pre-filled automatically)
   - Click **Publish Donation**.
   - Show how it appears in the **Donor Dashboard (My Activity)** as `AVAILABLE`.

3. **Receiver Claims Food (1:15 - 2:15)**
   - Click user dropdown -> **Log Out**.
   - Log in as receiver: `ngo@demo.com` / `demo123`.
   - You are redirected directly to **Available Food**.
   - Note the **Live Countdown Timer** ticking down seconds in real-time.
   - Use the **Filter by Area** or **Food Type** controls.
   - Click **Details** on the donation: notice pickup address is locked for unclaiming viewers.
   - Click **Claim Food**.
   - Notice the success banner: the donor's name, phone number, and full pickup address are unlocked!

4. **Mark Delivered & Update Impact (2:15 - 3:00)**
   - Click **Mark Delivered** button (with browser confirmation dialog).
   - The status updates to `DELIVERED`.
   - Return to the **Home Page**: see the **Total Delivered** and **Meals Saved** numbers increase in real-time!

---

## 7. Running Automated Tests

Run the full pytest suite with:

```powershell
.\venv\Scripts\pytest -v
```

All 7 test suites will execute against an in-memory SQLite database:
1. `test_register_and_login_donor_and_receiver`: Role registration and login routing
2. `test_donor_can_create_donation_receiver_cannot`: Role permission enforcement
3. `test_claim_with_double_claim_protection`: Atomic update race-condition defense
4. `test_expired_donation_handling`: Lazy expiry and prevention of claiming expired items
5. `test_only_claiming_receiver_can_mark_delivered`: Authorization for delivery marking
6. `test_donor_cancel_donation`: Donor cancellation of available donations only
7. `test_api_stats`: Integrity of public impact metrics endpoint

---

## 8. JSON API Endpoints

- **`GET /api/stats`**: Public JSON endpoint returning impact numbers:
  ```json
  {
    "total_donations": 8,
    "total_delivered": 2,
    "total_meals_saved": 125,
    "active_donors": 3
  }
  ```
- **`GET /api/donations`**: Authenticated JSON endpoint returning all currently active and available donations.
