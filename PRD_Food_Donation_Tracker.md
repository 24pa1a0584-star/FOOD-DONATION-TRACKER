# PRD: Food Donation Tracker

> **Instruction to the AI coding agent:** Read this whole document first. Then build the complete web project exactly as described, in the order given in Section 14 (Build Order). Run the app and fix any errors before finishing. Do not add features that are not listed here.

---

## 1. Overview

**Product name:** Food Donation Tracker
**Type:** Web application (server-rendered, mobile-friendly)
**Purpose:** Connect people who have extra cooked food (donors) with NGOs and volunteers (receivers) so the food is collected before it spoils.
**Context:** College community service project. Must be a working prototype that can be demoed in a few minutes.

### Problem
Good food is thrown away by hotels, hostels, function halls and homes, while people nearby are hungry. Donors do not know whom to call, and NGOs do not know where food is available. Cooked food is safe for only a few hours, so delay means waste.

### Solution
A simple website where donors post extra food in under one minute and receivers see a live list, claim a donation, collect it, and mark it delivered. A dashboard shows how many meals were saved.

### Goals
1. Post a donation in under 1 minute.
2. Receivers can find and claim food in under 3 clicks.
3. The same donation can never be claimed twice.
4. Expired food is never shown as available.
5. Show impact numbers (donations, meals saved).

### Non-Goals (do NOT build)
- Payment, chat, or real-time maps/GPS tracking
- Mobile native apps
- Email/SMS sending
- Admin approval workflows

---

## 2. Users and Roles

| Role | Who | What they can do |
|---|---|---|
| **Donor** | Hotel, hostel, caterer, family | Register, log in, post donations, view and cancel own donations |
| **Receiver** | NGO, volunteer | Register, log in, view available donations, claim, mark delivered |
| **Visitor** | Anyone not logged in | See home page and public impact numbers only |

Each user chooses ONE role at registration.

---

## 3. User Stories and Acceptance Criteria

**US-1 Register and log in**
As a user, I can create an account with a role and log in.
- Registration fields: name, email, phone, password, role (donor/receiver), area/city.
- Email must be unique. Password minimum 6 characters, stored hashed.
- After login, donors go to the Donor Dashboard and receivers go to the Donation List.

**US-2 Post a donation (Donor)**
As a donor, I can post extra food.
- Fields: food title, food type (Veg / Non-Veg), quantity (number of people it can feed), pickup address, area, ready time (auto = now), safe-until date and time, optional notes.
- Safe-until must be in the future and within 12 hours of now. Otherwise show an error.
- New donation starts with status `AVAILABLE`.

**US-3 View available donations (Receiver)**
As a receiver, I can see all `AVAILABLE` donations that are not expired.
- Shown as cards: title, type badge, quantity, area, time left until expiry.
- Filters: area (text/dropdown), food type, minimum quantity.
- Sorted by soonest expiry first.

**US-4 Claim a donation (Receiver)**
As a receiver, I can press **Claim**.
- Status changes `AVAILABLE` to `CLAIMED` and stores the receiver and claim time.
- This must be safe against double-claim: if two receivers press at the same time, only one succeeds and the other sees a friendly message.
- After claiming, the donor's name, phone and full pickup address are shown to that receiver only.

**US-5 Mark delivered (Receiver)**
As the receiver who claimed it, I can press **Mark Delivered**.
- Status changes `CLAIMED` to `DELIVERED` and stores the delivered time.

**US-6 Cancel a donation (Donor)**
As a donor, I can cancel my own donation while it is `AVAILABLE`.
- Status changes to `CANCELLED`. Claimed or delivered donations cannot be cancelled.

**US-7 Expiry**
- Any `AVAILABLE` donation past its safe-until time is treated as `EXPIRED` and hidden from receivers.
- Implement by checking the time when listing (and update status to `EXPIRED` lazily). No background scheduler needed.

**US-8 Impact dashboard (public)**
On the home page show: total donations posted, total delivered, total meals saved (sum of quantity of delivered donations), and number of active donors.

**US-9 My activity**
- Donor: list of my donations with status and who claimed them.
- Receiver: list of my claimed and delivered donations.

---

## 4. Functional Requirements Summary

| ID | Requirement | Priority |
|---|---|---|
| F1 | Register / login / logout with roles | Must |
| F2 | Post donation with validation | Must |
| F3 | List and filter available donations | Must |
| F4 | Claim with double-claim protection | Must |
| F5 | Mark delivered | Must |
| F6 | Cancel donation | Should |
| F7 | Expiry handling | Must |
| F8 | Impact dashboard on home page | Must |
| F9 | My activity pages | Should |
| F10 | JSON API endpoints (read) | Could |
| F11 | Seed script with demo data | Must |
| F12 | Basic automated tests | Should |

---

## 5. Tech Stack and Environment

### Languages
- **Python 3.11+** (backend)
- **HTML5, CSS3, JavaScript (vanilla)** (frontend)
- **SQL** via SQLAlchemy ORM (SQLite database)

### Libraries (put in `requirements.txt`)
```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
python-dotenv==1.0.1
pytest==8.2.2
```
(Password hashing uses `werkzeug.security`, which comes with Flask.)

### Frontend
- Jinja2 templates (server-rendered)
- Bootstrap 5 via CDN for layout and cards (no build step, no npm)
- Small vanilla JS file for countdown timers and confirm dialogs

### Database
- SQLite file at `instance/app.db`. No external database server.

### Environment setup commands
**Windows (PowerShell):**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
flask --app app run --debug
```
**Mac/Linux:**
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
flask --app app run --debug
```
App runs at `http://127.0.0.1:5000`.

### Environment variables (`.env` file, with `.env.example` committed)
```
SECRET_KEY=change-this-to-a-long-random-string
DATABASE_URL=sqlite:///app.db
```

---

## 6. Project Structure

```
food-donation-tracker/
├── app.py                  # app factory, config, blueprint registration
├── models.py               # SQLAlchemy models
├── forms.py                # Flask-WTF forms with validation
├── seed.py                 # creates demo users and donations
├── requirements.txt
├── .env.example
├── README.md               # setup + demo steps
├── routes/
│   ├── __init__.py
│   ├── auth.py             # register, login, logout
│   ├── donations.py        # create, list, claim, deliver, cancel
│   ├── main.py             # home, dashboard stats, my activity
│   └── api.py              # read-only JSON endpoints
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── donation_new.html
│   ├── donation_list.html
│   ├── donation_detail.html
│   └── my_activity.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── tests/
    └── test_app.py
```

---

## 7. Data Model

### User
| Field | Type | Notes |
|---|---|---|
| id | Integer, PK | |
| name | String(80) | required |
| email | String(120) | unique, required |
| phone | String(15) | required |
| password_hash | String(255) | required |
| role | String(10) | `donor` or `receiver` |
| area | String(80) | required |
| created_at | DateTime | default now (UTC) |

### Donation
| Field | Type | Notes |
|---|---|---|
| id | Integer, PK | |
| donor_id | FK to User | required |
| title | String(100) | required |
| food_type | String(10) | `veg` or `nonveg` |
| quantity | Integer | people it can feed, 1 to 500 |
| address | String(200) | full pickup address |
| area | String(80) | used for filtering |
| notes | String(300) | optional |
| ready_at | DateTime | default now (UTC) |
| safe_until | DateTime | required, must be in the future, max 12 hours ahead |
| status | String(12) | `AVAILABLE`, `CLAIMED`, `DELIVERED`, `CANCELLED`, `EXPIRED` |
| claimed_by_id | FK to User | nullable |
| claimed_at | DateTime | nullable |
| delivered_at | DateTime | nullable |

### Status flow
```
AVAILABLE --claim--> CLAIMED --deliver--> DELIVERED
AVAILABLE --cancel--> CANCELLED
AVAILABLE --time passes--> EXPIRED
```

---

## 8. Routes and Pages

| Method | URL | Who | Description |
|---|---|---|---|
| GET | `/` | Anyone | Home page with impact numbers |
| GET/POST | `/register` | Visitor | Create account |
| GET/POST | `/login` | Visitor | Log in |
| GET | `/logout` | Logged in | Log out |
| GET/POST | `/donations/new` | Donor | Post donation |
| GET | `/donations` | Receiver | List and filter available donations |
| GET | `/donations/<id>` | Logged in | Donation details (contact shown only to donor and claiming receiver) |
| POST | `/donations/<id>/claim` | Receiver | Claim |
| POST | `/donations/<id>/deliver` | Claiming receiver | Mark delivered |
| POST | `/donations/<id>/cancel` | Owning donor | Cancel |
| GET | `/my` | Logged in | My activity |
| GET | `/api/stats` | Anyone | JSON impact numbers |
| GET | `/api/donations` | Logged in | JSON list of available donations |

All POST forms must include a CSRF token (Flask-WTF).

---

## 9. Business Rules and Edge Cases

1. **Double-claim protection:** Claim with a single atomic database update, for example `UPDATE donation SET status='CLAIMED', claimed_by_id=:uid, claimed_at=:now WHERE id=:id AND status='AVAILABLE' AND safe_until > :now`. If zero rows are updated, show "Sorry, this donation was just claimed or has expired."
2. A donor cannot claim their own donation (a user has only one role, so this is enforced by role checks).
3. Only the receiver who claimed a donation can mark it delivered.
4. Donor contact details and exact address are hidden from other receivers until claimed.
5. Safe-until must be after now and at most 12 hours ahead.
6. Quantity must be a whole number from 1 to 500.
7. Role checks on every protected route. Return 403 with a friendly page for wrong role.
8. Escape all user input in templates (Jinja2 autoescape stays on).
9. Use UTC for storage and show times in local time in the UI (India, IST).

---

## 10. UI Requirements

- Clean, simple, mobile-first (works well on a phone screen).
- Colour theme: green and white (food and care feeling). Primary green `#2E7D32`, light background `#F6FAF6`.
- Navbar: logo/name, links change by role, login/logout.
- **Home page:** hero text ("Share food. Save a meal."), two buttons (Donate Food, Find Food), and four impact number cards.
- **Donation card:** title, Veg (green) or Non-Veg (red) badge, "Feeds N people", area, live countdown ("2h 15m left"), Claim button.
- Status badges with colours: Available (green), Claimed (orange), Delivered (blue), Cancelled/Expired (grey).
- Flash messages for success and error.
- Empty states, for example "No food available right now. Check back soon."
- Confirm dialog before Cancel.
- Basic accessibility: labels on all inputs, sufficient colour contrast.

---

## 11. Demo Seed Data (`seed.py`)

Create:
- 3 donors (e.g. a hotel, a hostel, a family) and 2 receivers (e.g. an NGO, a volunteer), with the password `demo123` for all.
- 8 donations: mix of veg and non-veg, different areas, safe-until times between 1 and 8 hours ahead, 2 already `CLAIMED`, 2 already `DELIVERED`.
- Print the demo login emails in the console when done.

---

## 12. Testing (`tests/test_app.py`, pytest)

Write tests for:
1. Register and login works for both roles.
2. Donor can create a donation; receiver cannot.
3. Receiver can claim; a second claim on the same donation fails.
4. Expired donation cannot be claimed and does not appear in the list.
5. Only the claiming receiver can mark delivered.
6. Donor can cancel only `AVAILABLE` donations.
7. `/api/stats` returns correct numbers.

Use an in-memory SQLite database for tests.

---

## 13. Non-Functional Requirements

- Runs locally with the commands in Section 5, with no paid services.
- Page loads in under 2 seconds locally.
- Code is clean, commented in simple English, and follows PEP 8.
- README includes: what the project is, setup steps, demo login details, screenshots list, and a short "how to demo in 3 minutes" script.

---

## 14. Build Order for the Agent

1. Create the project folder, virtual environment, `requirements.txt`, `.env.example`.
2. Write `app.py` (app factory, config, extensions) and `models.py`.
3. Build authentication (register, login, logout) with role handling.
4. Build donation creation with validation.
5. Build the donation list with filters and the countdown timer.
6. Build claim (atomic), deliver, and cancel.
7. Build the home page impact numbers and the My Activity page.
8. Add the JSON API endpoints.
9. Style with Bootstrap and `style.css`.
10. Write `seed.py` and run it.
11. Write the pytest tests and make them pass.
12. Write `README.md`.
13. Run the app, test the full flow in the browser (donor posts, receiver claims, receiver delivers), and fix any bugs.

---

## 15. Definition of Done

- [ ] App starts with `flask --app app run --debug` with no errors.
- [ ] Full flow works: donor posts, receiver claims, receiver delivers, numbers update on home page.
- [ ] Double-claim and expiry rules work.
- [ ] All pytest tests pass.
- [ ] Demo data loads with `python seed.py`.
- [ ] README is complete.
- [ ] No secrets are committed; `.env.example` is provided.

---

## 16. Future Scope (do NOT build now)

Map view with GPS, SMS/WhatsApp alerts, donor and NGO verification badges, ratings, PostgreSQL, a mobile app, and an admin panel.
