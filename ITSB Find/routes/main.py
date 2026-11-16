from flask import Blueprint, redirect, render_template, g, session, url_for

from config import team_members as T
from config.settings import FEEDBACK_CATEGORIES
from database.db import query
from services.security import login_required

bp = Blueprint("main", __name__)


def site_stats():
    r = query("""SELECT
        (SELECT COUNT(*) FROM found_items WHERE status IN ('stored','returned')) found,
        (SELECT COUNT(*) FROM lost_items) lost,
        (SELECT COUNT(*) FROM item_returns) returned,
        (SELECT COUNT(*) FROM users WHERE role!='security') users""", one=True)
    return dict(r)


@bp.route("/")
def landing():
    return render_template("landing.html", stats=site_stats(), team=T.TEAM_MEMBERS, project=T.PROJECT,
                           feedback_categories=FEEDBACK_CATEGORIES)


@bp.route("/about")
def about():
    return render_template("about.html", team=T.TEAM_MEMBERS, project=T.PROJECT)


@bp.route("/guest")
def guest():
    """Mode Tamu: hanya menandai sesi. Tidak ada akun yang dibuat di database."""
    if g.user is None:
        session["guest"] = True
    return redirect(url_for("user.found_items"))
