from datetime import datetime, timezone
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Donation, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # US-8: Impact numbers
    total_donations = Donation.query.count()
    total_delivered = Donation.query.filter_by(status='DELIVERED').count()
    total_meals_saved = db.session.query(db.func.sum(Donation.quantity)).filter(
        Donation.status == 'DELIVERED'
    ).scalar() or 0

    active_donors_count = db.session.query(db.func.count(db.distinct(Donation.donor_id))).scalar() or 0
    if active_donors_count == 0:
        active_donors_count = User.query.filter_by(role='donor').count()

    # Active available donations count for a live indicator
    now_utc = datetime.now(timezone.utc)
    active_available = Donation.query.filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until > now_utc
    ).count()

    stats = {
        'total_donations': total_donations,
        'total_delivered': total_delivered,
        'total_meals_saved': int(total_meals_saved),
        'active_donors': active_donors_count,
        'active_available': active_available
    }

    return render_template('home.html', stats=stats)

@main_bp.route('/my')
@login_required
def my_activity():
    now_utc = datetime.now(timezone.utc)

    # Lazily expire any old available donations
    db.session.query(Donation).filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until <= now_utc
    ).update({Donation.status: 'EXPIRED'}, synchronize_session=False)
    db.session.commit()

    if current_user.role == 'donor':
        donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.ready_at.desc()).all()
        total_posted = len(donations)
        active_count = sum(1 for d in donations if d.status == 'AVAILABLE')
        delivered_count = sum(1 for d in donations if d.status == 'DELIVERED')
        meals_fed = sum(d.quantity for d in donations if d.status == 'DELIVERED')

        stats = {
            'total_posted': total_posted,
            'active_count': active_count,
            'delivered_count': delivered_count,
            'meals_fed': meals_fed
        }
        return render_template('my_activity.html', donations=donations, stats=stats)

    else:
        # Receiver activity: claimed and delivered
        donations = Donation.query.filter_by(claimed_by_id=current_user.id).order_by(Donation.claimed_at.desc()).all()
        claimed_count = sum(1 for d in donations if d.status == 'CLAIMED')
        delivered_count = sum(1 for d in donations if d.status == 'DELIVERED')
        meals_distributed = sum(d.quantity for d in donations if d.status == 'DELIVERED')

        stats = {
            'total_claimed': len(donations),
            'pending_pickup': claimed_count,
            'delivered_count': delivered_count,
            'meals_distributed': meals_distributed
        }
        return render_template('my_activity.html', donations=donations, stats=stats)
