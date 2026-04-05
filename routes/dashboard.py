from flask import Blueprint, request, jsonify
from models.record import FinancialRecord
from models.db import db
from middleware.auth import login_required
from sqlalchemy import func
from datetime import datetime, date, timedelta
import calendar

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
@login_required
def get_summary():
    """Returns total income, total expenses, and net balance."""
    base = FinancialRecord.query.filter_by(is_deleted=False)

    total_income = db.session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.is_deleted == False,
        FinancialRecord.type == "income"
    ).scalar() or 0

    total_expense = db.session.query(func.sum(FinancialRecord.amount)).filter(
        FinancialRecord.is_deleted == False,
        FinancialRecord.type == "expense"
    ).scalar() or 0

    return jsonify({
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(total_income - total_expense, 2)
    }), 200


@dashboard_bp.route("/by-category", methods=["GET"])
@login_required
def get_by_category():
    """Returns totals grouped by category."""
    results = db.session.query(
        FinancialRecord.category,
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label("total")
    ).filter(
        FinancialRecord.is_deleted == False
    ).group_by(
        FinancialRecord.category, FinancialRecord.type
    ).all()

    data = {}
    for row in results:
        key = row.category
        if key not in data:
            data[key] = {"category": key, "income": 0, "expense": 0}
        data[key][row.type] = round(row.total, 2)

    return jsonify(list(data.values())), 200


@dashboard_bp.route("/recent", methods=["GET"])
@login_required
def get_recent():
    """Returns last N records (default 5)."""
    limit = int(request.args.get("limit", 5))
    if limit > 50:
        limit = 50

    records = FinancialRecord.query.filter_by(is_deleted=False)\
        .order_by(FinancialRecord.date.desc())\
        .limit(limit).all()

    return jsonify([r.to_dict() for r in records]), 200


@dashboard_bp.route("/monthly", methods=["GET"])
@login_required
def get_monthly_trends():
    """Returns monthly income vs expense totals for a given year."""
    year = int(request.args.get("year", datetime.utcnow().year))

    results = db.session.query(
        func.strftime("%m", FinancialRecord.date).label("month"),
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label("total")
    ).filter(
        FinancialRecord.is_deleted == False,
        func.strftime("%Y", FinancialRecord.date) == str(year)
    ).group_by("month", FinancialRecord.type).all()

    monthly = {}
    for i in range(1, 13):
        m = f"{i:02d}"
        monthly[m] = {
            "month": calendar.month_abbr[i],
            "income": 0,
            "expense": 0
        }

    for row in results:
        if row.month in monthly:
            monthly[row.month][row.type] = round(row.total, 2)

    return jsonify({
        "year": year,
        "trends": list(monthly.values())
    }), 200


@dashboard_bp.route("/weekly", methods=["GET"])
@login_required
def get_weekly():
    """Returns income vs expense for the last 7 days."""
    today = date.today()
    week_ago = today - timedelta(days=6)

    results = db.session.query(
        func.strftime("%Y-%m-%d", FinancialRecord.date).label("day"),
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label("total")
    ).filter(
        FinancialRecord.is_deleted == False,
        FinancialRecord.date >= week_ago,
        FinancialRecord.date <= today
    ).group_by("day", FinancialRecord.type).all()

    daily = {}
    for i in range(7):
        d = (today - timedelta(days=6 - i)).isoformat()
        daily[d] = {"date": d, "income": 0, "expense": 0}

    for row in results:
        if row.day in daily:
            daily[row.day][row.type] = round(row.total, 2)

    return jsonify(list(daily.values())), 200
