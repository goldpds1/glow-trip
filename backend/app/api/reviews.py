from flask import Blueprint, request, jsonify, g

from app import db
from app.models import Booking, Shop, Review, ReviewReport
from app.auth.decorators import login_required

reviews_bp = Blueprint("reviews", __name__, url_prefix="/api")


@reviews_bp.route("/reviews", methods=["POST"])
@login_required
def create_review():
    """리뷰 작성 — 완료된 예약만 가능, 예약당 1회."""
    data = request.get_json() or {}
    user = g.current_user

    booking_id = data.get("booking_id")
    rating = data.get("rating")
    comment = data.get("comment", "").strip()

    if not booking_id or rating is None:
        return jsonify(error="booking_id and rating are required"), 400

    rating = int(rating)
    if rating < 1 or rating > 5:
        return jsonify(error="Rating must be 1-5"), 400

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify(error="Booking not found"), 404
    if str(booking.user_id) != str(user.id):
        return jsonify(error="Not your booking"), 403
    if booking.status != "completed":
        return jsonify(error="Can only review completed bookings"), 400

    existing = Review.query.filter_by(booking_id=booking.id).first()
    if existing:
        return jsonify(error="Already reviewed this booking"), 400

    review = Review(
        user_id=user.id,
        shop_id=booking.shop_id,
        booking_id=booking.id,
        rating=rating,
        comment=comment or None,
    )
    db.session.add(review)
    db.session.commit()

    return jsonify(
        id=str(review.id),
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at.isoformat(),
    ), 201


@reviews_bp.route("/shops/<shop_id>/reviews", methods=["GET"])
def shop_reviews(shop_id):
    """샵의 리뷰 목록 + 평균 평점."""
    shop = Shop.query.get(shop_id)
    if not shop:
        return jsonify(error="Shop not found"), 404

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)

    q = Review.query.filter_by(shop_id=shop.id, is_hidden=False)

    # 평균 평점
    avg_result = db.session.query(db.func.avg(Review.rating)).filter_by(shop_id=shop.id).scalar()
    avg_rating = round(float(avg_result), 1) if avg_result else 0
    review_count = q.count()

    pagination = q.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    reviews = [
        {
            "id": str(r.id),
            "user_name": r.user.name or "Anonymous",
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        }
        for r in pagination.items
    ]

    return jsonify(
        avg_rating=avg_rating,
        review_count=review_count,
        reviews=reviews,
        total=pagination.total,
        page=pagination.page,
        pages=pagination.pages,
    ), 200


@reviews_bp.route("/reviews/<review_id>/report", methods=["POST"])
@login_required
def report_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify(error="Review not found"), 404

    data = request.get_json() or {}
    reason = (data.get("reason") or "").strip()
    if not reason:
        return jsonify(error="reason is required"), 400

    existing = ReviewReport.query.filter_by(
        review_id=review.id,
        reporter_id=g.current_user.id,
    ).first()
    if existing:
        return jsonify(error="Already reported"), 400

    rr = ReviewReport(
        review_id=review.id,
        reporter_id=g.current_user.id,
        reason=reason[:200],
        status="open",
    )
    db.session.add(rr)
    db.session.flush()

    count = ReviewReport.query.filter_by(review_id=review.id).count()
    if count >= 3:
        review.is_hidden = True

    db.session.commit()
    return jsonify(
        reported=True,
        review_id=str(review.id),
        report_count=count,
        review_hidden=review.is_hidden,
    ), 201
