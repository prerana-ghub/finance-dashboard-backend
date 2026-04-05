from flask import Blueprint, request, jsonify
from models.record import FinancialRecord
from models.db import db
from middleware.auth import login_required, role_required, get_current_user
from datetime import datetime, date

records_bp = Blueprint("records", __name__)

VALID_TYPES = ["income", "expense"]


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@records_bp.route("/", methods=["GET"])
@login_required
def get_records():
    query = FinancialRecord.query.filter_by(is_deleted=False)

    # Filters
    record_type = request.args.get("type")
    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    if record_type:
        if record_type not in VALID_TYPES:
            return jsonify({"error": "type must be 'income' or 'expense'"}), 400
        query = query.filter_by(type=record_type)

    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))

    if start_date:
        d = parse_date(start_date)
        if not d:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
        query = query.filter(FinancialRecord.date >= d)

    if end_date:
        d = parse_date(end_date)
        if not d:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
        query = query.filter(FinancialRecord.date <= d)

    query = query.order_by(FinancialRecord.date.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "records": [r.to_dict() for r in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages
    }), 200


@records_bp.route("/<int:record_id>", methods=["GET"])
@login_required
def get_record(record_id):
    record = FinancialRecord.query.filter_by(id=record_id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(record.to_dict()), 200


@records_bp.route("/", methods=["POST"])
@role_required("admin", "analyst")
def create_record():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    amount = data.get("amount")
    record_type = data.get("type", "").strip().lower()
    category = data.get("category", "").strip()
    date_str = data.get("date", "")
    notes = data.get("notes", "")

    # Validation
    if amount is None or not isinstance(amount, (int, float)):
        return jsonify({"error": "amount must be a number"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be greater than 0"}), 400
    if record_type not in VALID_TYPES:
        return jsonify({"error": "type must be 'income' or 'expense'"}), 400
    if not category:
        return jsonify({"error": "category is required"}), 400

    record_date = parse_date(date_str)
    if not record_date:
        return jsonify({"error": "date is required in YYYY-MM-DD format"}), 400

    current_user = get_current_user()
    record = FinancialRecord(
        amount=amount,
        type=record_type,
        category=category,
        date=record_date,
        notes=notes,
        created_by=current_user.id
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"message": "Record created", "record": record.to_dict()}), 201


@records_bp.route("/<int:record_id>", methods=["PUT"])
@role_required("admin", "analyst")
def update_record(record_id):
    record = FinancialRecord.query.filter_by(id=record_id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    if "amount" in data:
        if not isinstance(data["amount"], (int, float)) or data["amount"] <= 0:
            return jsonify({"error": "amount must be a positive number"}), 400
        record.amount = data["amount"]

    if "type" in data:
        if data["type"] not in VALID_TYPES:
            return jsonify({"error": "type must be 'income' or 'expense'"}), 400
        record.type = data["type"]

    if "category" in data:
        if not data["category"].strip():
            return jsonify({"error": "category cannot be empty"}), 400
        record.category = data["category"].strip()

    if "date" in data:
        d = parse_date(data["date"])
        if not d:
            return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400
        record.date = d

    if "notes" in data:
        record.notes = data["notes"]

    db.session.commit()
    return jsonify({"message": "Record updated", "record": record.to_dict()}), 200


@records_bp.route("/<int:record_id>", methods=["DELETE"])
@role_required("admin")
def delete_record(record_id):
    record = FinancialRecord.query.filter_by(id=record_id, is_deleted=False).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404

    # Soft delete
    record.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Record deleted"}), 200
