from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, Donation, User
from forms import DonationForm, IST
from routes.auth import donor_required, receiver_required

donations_bp = Blueprint('donations', __name__)

def check_and_expire_donations():
    """Lazily update status of any past safe-until AVAILABLE donations to EXPIRED."""
    now_utc = datetime.now(timezone.utc)
    db.session.query(Donation).filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until <= now_utc
    ).update({Donation.status: 'EXPIRED'}, synchronize_session=False)
    db.session.commit()

@donations_bp.route('/donations/new', methods=['GET', 'POST'])
@donor_required
def create_donation():
    form = DonationForm()
    if form.validate_on_submit():
        # safe_until is submitted in local time (IST). Convert to UTC.
        local_dt = form.safe_until.data.replace(tzinfo=IST)
        safe_until_utc = local_dt.astimezone(timezone.utc)

        donation = Donation(
            donor_id=current_user.id,
            title=form.title.data.strip(),
            food_type=form.food_type.data,
            quantity=form.quantity.data,
            address=form.address.data.strip(),
            area=form.area.data.strip(),
            notes=form.notes.data.strip() if form.notes.data else None,
            ready_at=datetime.now(timezone.utc),
            safe_until=safe_until_utc,
            status='AVAILABLE'
        )
        db.session.add(donation)
        db.session.commit()

        flash('Food donation posted successfully! It is now visible to nearby receivers.', 'success')
        return redirect(url_for('main.my_activity'))

    return render_template('donation_new.html', form=form)

@donations_bp.route('/donations')
@receiver_required
def list_donations():
    # Update expired donations first
    check_and_expire_donations()

    now_utc = datetime.now(timezone.utc)
    query = Donation.query.filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until > now_utc
    )

    # Filter by Area
    selected_area = request.args.get('area', '').strip()
    if selected_area:
        query = query.filter(Donation.area.ilike(f'%{selected_area}%'))

    # Filter by Food Type
    selected_type = request.args.get('food_type', '').strip()
    if selected_type in ['veg', 'nonveg']:
        query = query.filter(Donation.food_type == selected_type)

    # Filter by Min Quantity
    min_qty = request.args.get('min_quantity', '').strip()
    if min_qty and min_qty.isdigit():
        query = query.filter(Donation.quantity >= int(min_qty))

    # US-3: Sorted by soonest expiry first
    donations = query.order_by(Donation.safe_until.asc()).all()

    # Get unique available areas for filter dropdown
    available_areas = [r[0] for r in db.session.query(Donation.area).filter(
        Donation.status == 'AVAILABLE',
        Donation.safe_until > now_utc
    ).distinct().order_by(Donation.area.asc()).all()]

    return render_template(
        'donation_list.html',
        donations=donations,
        selected_area=selected_area,
        selected_type=selected_type,
        min_qty=min_qty,
        available_areas=available_areas
    )

@donations_bp.route('/donations/<int:id>')
@login_required
def donation_detail(id):
    check_and_expire_donations()
    donation = db.session.get(Donation, id)
    if not donation:
        abort(404)

    # Check authorization to see contact info:
    # Shown only to donor and the receiver who claimed it
    can_view_contact = (
        current_user.id == donation.donor_id or
        (donation.claimed_by_id and current_user.id == donation.claimed_by_id)
    )

    return render_template(
        'donation_detail.html',
        donation=donation,
        can_view_contact=can_view_contact
    )

@donations_bp.route('/donations/<int:id>/claim', methods=['POST'])
@receiver_required
def claim_donation(id):
    check_and_expire_donations()
    now_utc = datetime.now(timezone.utc)

    # Atomic update to protect against double claim
    rows_updated = db.session.query(Donation).filter(
        Donation.id == id,
        Donation.status == 'AVAILABLE',
        Donation.safe_until > now_utc
    ).update({
        Donation.status: 'CLAIMED',
        Donation.claimed_by_id: current_user.id,
        Donation.claimed_at: now_utc
    }, synchronize_session=False)

    db.session.commit()

    if rows_updated == 0:
        flash("Sorry, this donation was just claimed or has expired.", "danger")
        return redirect(url_for('donations.list_donations'))

    flash("You have successfully claimed this donation! Pickup contact details are now unlocked below.", "success")
    return redirect(url_for('donations.donation_detail', id=id))

@donations_bp.route('/donations/<int:id>/deliver', methods=['POST'])
@receiver_required
def deliver_donation(id):
    donation = db.session.get(Donation, id)
    if not donation:
        abort(404)

    # Rule 3: Only the receiver who claimed it can mark delivered
    if donation.claimed_by_id != current_user.id:
        abort(403)

    if donation.status != 'CLAIMED':
        flash("Only claimed donations can be marked as delivered.", "warning")
        return redirect(url_for('donations.donation_detail', id=id))

    donation.status = 'DELIVERED'
    donation.delivered_at = datetime.now(timezone.utc)
    db.session.commit()

    flash(f"Donation marked as delivered! {donation.quantity} meals successfully saved and distributed.", "success")
    return redirect(url_for('donations.donation_detail', id=id))

@donations_bp.route('/donations/<int:id>/cancel', methods=['POST'])
@donor_required
def cancel_donation(id):
    donation = db.session.get(Donation, id)
    if not donation:
        abort(404)

    # Rule: Donor can cancel only their own donation while AVAILABLE
    if donation.donor_id != current_user.id:
        abort(403)

    if donation.status != 'AVAILABLE':
        flash("Only available donations can be cancelled. Claimed or delivered donations cannot be cancelled.", "warning")
        return redirect(url_for('donations.donation_detail', id=id))

    donation.status = 'CANCELLED'
    db.session.commit()

    flash("Your donation has been cancelled.", "info")
    return redirect(url_for('main.my_activity'))
