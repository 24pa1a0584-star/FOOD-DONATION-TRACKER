from datetime import datetime, timezone
from flask import Blueprint, jsonify
from flask_login import login_required
from models import db, Donation, User

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Return public impact statistics in JSON format."""
    total_donations = Donation.query.count()
    total_delivered = Donation.query.filter_by(status='DELIVERED').count()
    total_meals_saved = db.session.query(db.func.sum(Donation.quantity)).filter(
        Donation.status == 'DELIVERED'
    ).scalar() or 0

    active_donors_count = db.session.query(db.func.count(db.distinct(Donation.donor_id))).scalar() or 0
    if active_donors_count == 0:
        active_donors_count = User.query.filter_by(role='donor').count()

    return jsonify({
        'total_donations': total_donations,
        'total_delivered': total_delivered,
        'total_meals_saved': int(total_meals_saved),
        'active_donors': active_donors_count
    }), 200

@api_bp.route('/donations', methods=['GET'])
@login_required
def get_donations():
    """Return JSON list of currently available and non-expired donations."""
    now_utc = datetime.now(timezone.utc)

    # Lazy expiry update
    db.session.query(Donation).filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until <= now_utc
    ).update({Donation.status: 'EXPIRED'}, synchronize_session=False)
    db.session.commit()

    donations = Donation.query.filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until > now_utc
    ).order_by(Donation.safe_until.asc()).all()

    return jsonify([d.to_dict() for d in donations]), 200
