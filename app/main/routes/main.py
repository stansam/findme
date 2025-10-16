from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc
from datetime import datetime, timedelta
from app.main import bp
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.sighting import SightingReport
from app.models.user import User
from app.models.options import MissingPersonStatus, ReportStatus
from app.extensions import db


@bp.route('/')
@bp.route('/index')
def index():
    recent_cases = MissingPerson.query.filter_by(
        is_public=True,
        status=MissingPersonStatus.MISSING
    ).order_by(desc(MissingPerson.created_at)).limit(6).all()

    stats = {
        'total_missing': MissingPerson.query.filter_by(status=MissingPersonStatus.MISSING).count(),
        'total_found': MissingPerson.query.filter_by(status=MissingPersonStatus.FOUND).count(),
        'active_reports': SightingReport.query.filter_by(status=ReportStatus.PENDING).count(),
        'total_users': User.query.count()
    }

    return render_template('main/index.html', recent_cases=recent_cases, stats=stats)


@bp.route('/browse')
def browse():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    gender_filter = request.args.get('gender', '')
    sort_by = request.args.get('sort', 'recent')

    query = MissingPerson.query.filter_by(is_public=True)

    if search_query:
        query = query.filter(
            or_(
                MissingPerson.full_name.ilike(f'%{search_query}%'),
                MissingPerson.last_seen_location.ilike(f'%{search_query}%')
            )
        )

    if status_filter:
        try:
            status_enum = MissingPersonStatus[status_filter.upper()]
            query = query.filter_by(status=status_enum)
        except KeyError:
            pass

    if gender_filter:
        query = query.filter_by(gender=gender_filter)

    if sort_by == 'recent':
        query = query.order_by(desc(MissingPerson.created_at))
    elif sort_by == 'oldest':
        query = query.order_by(MissingPerson.created_at)
    elif sort_by == 'last_seen':
        query = query.order_by(desc(MissingPerson.last_seen_date))

    pagination = query.paginate(
        page=page,
        per_page=12,
        error_out=False
    )

    return render_template('main/browse.html',
                         missing_persons=pagination.items,
                         pagination=pagination,
                         search_query=search_query,
                         status_filter=status_filter,
                         gender_filter=gender_filter,
                         sort_by=sort_by)


@bp.route('/person/<int:person_id>')
def person_detail(person_id):
    person = MissingPerson.query.get_or_404(person_id)

    if not person.is_public and (not current_user.is_authenticated or
                                 (current_user.id != person.reported_by and not current_user.is_admin())):
        flash('This case is not publicly accessible.', 'error')
        return redirect(url_for('main.browse'))

    person.increment_views()

    sightings = SightingReport.query.filter_by(
        missing_person_id=person_id,
        status=ReportStatus.VERIFIED
    ).order_by(desc(SightingReport.sighting_date)).all()

    photos = PersonPhoto.query.filter_by(person_id=person_id).all()
    current_time = datetime.now()
    return render_template('main/person_detail.html',
                         person=person,
                         sightings=sightings,
                         current_time=current_time,
                         photos=photos)


@bp.route('/report-missing')
@login_required
def report_missing():
    return render_template('main/report/missing.html')


@bp.route('/report-sighting/<int:person_id>')
def report_sighting(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    return render_template('main/report/sighting.html', person=person)


@bp.route('/about')
def about():
    return render_template('main/about.html')


@bp.route('/contact')
def contact():
    return render_template('main/contact.html')


@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.browse'))

    results = MissingPerson.query.filter(
        and_(
            MissingPerson.is_public == True,
            or_(
                MissingPerson.full_name.ilike(f'%{query}%'),
                MissingPerson.last_seen_location.ilike(f'%{query}%'),
                MissingPerson.case_number.ilike(f'%{query}%')
            )
        )
    ).order_by(desc(MissingPerson.created_at)).limit(20).all()

    return render_template('main/search_results.html', results=results, query=query)


@bp.route('/dashboard')
@login_required
def dashboard():
    user_reports = MissingPerson.query.filter_by(reported_by=current_user.id).order_by(
        desc(MissingPerson.created_at)
    ).all()

    user_sightings = SightingReport.query.filter_by(reported_by=current_user.id).order_by(
        desc(SightingReport.created_at)
    ).all()

    return render_template('main/dashboard.html',
                         user_reports=user_reports,
                         user_sightings=user_sightings)


@bp.route('/map')
def map_view():
    return render_template('main/map.html')


@bp.route('/statistics')
def statistics():
    total_cases = MissingPerson.query.count()
    missing_count = MissingPerson.query.filter_by(status=MissingPersonStatus.MISSING).count()
    found_count = MissingPerson.query.filter_by(status=MissingPersonStatus.FOUND).count()
    investigating_count = MissingPerson.query.filter_by(status=MissingPersonStatus.INVESTIGATING).count()

    recent_found = MissingPerson.query.filter_by(
        status=MissingPersonStatus.FOUND
    ).order_by(desc(MissingPerson.found_date)).limit(10).all()

    stats_data = {
        'total_cases': total_cases,
        'missing_count': missing_count,
        'found_count': found_count,
        'investigating_count': investigating_count,
        'success_rate': round((found_count / total_cases * 100) if total_cases > 0 else 0, 2),
        'recent_found': recent_found
    }

    return render_template('main/statistics.html', stats=stats_data)

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@bp.route('/privacy')
def privacy():
    return render_template('main/resources/privacy.html')

@bp.route('/safety-tips')
def safety():
    return render_template('main/resources/safety_tips.html')

@bp.route('/terms-of-service')
def terms():
    return render_template('main/resources/terms.html')

@bp.route('/faq')
def faq():
    return render_template('main/resources/faqs.html')