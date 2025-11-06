from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
from app.admin import bp as admin_bp
from app.extensions import db
from app.models.user import User
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.sighting import SightingReport, SightingPhoto
from app.models.audit import Notification, ActivityLog, Message, SystemSetting
from app.models.options import UserRole, MissingPersonStatus, ReportStatus


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def log_activity(action, entity_type=None, entity_id=None, description=None):
    try:
        log = ActivityLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")


@admin_bp.route('/')
@admin_required
def dashboard():
    try:
        total_users = User.query.count()
        total_missing = MissingPerson.query.filter_by(status=MissingPersonStatus.MISSING).count()
        total_found = MissingPerson.query.filter_by(status=MissingPersonStatus.FOUND).count()
        pending_reports = SightingReport.query.filter_by(status=ReportStatus.PENDING).count()

        recent_reports = SightingReport.query.order_by(SightingReport.created_at.desc()).limit(10).all()
        recent_missing = MissingPerson.query.order_by(MissingPerson.created_at.desc()).limit(5).all()

        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()

        stats = {
            'total_users': total_users,
            'total_missing': total_missing,
            'total_found': total_found,
            'pending_reports': pending_reports,
            'recent_users': recent_users,
            'recent_reports': recent_reports,
            'recent_missing': recent_missing
        }

        log_activity('VIEW_DASHBOARD', description='Accessed admin dashboard')

        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/dashboard.html', stats={})


@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    query = User.query

    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )

    if role_filter:
        query = query.filter_by(role=UserRole[role_filter.upper()])

    users_pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    log_activity('VIEW_USERS', description='Viewed users list')

    return render_template('admin/users.html', users=users_pagination, search=search, role_filter=role_filter)


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    missing_persons = user.missing_persons.all()
    sighting_reports = user.sighting_reports.all()

    log_activity('VIEW_USER', entity_type='User', entity_id=user_id)

    return render_template('admin/user_detail.html', user=user,
                         missing_persons=missing_persons,
                         sighting_reports=sighting_reports)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot modify your own status'}), 400

    user.is_active = not user.is_active
    db.session.commit()

    log_activity('TOGGLE_USER_STATUS', entity_type='User', entity_id=user_id,
                description=f'Set user status to {"active" if user.is_active else "inactive"}')

    return jsonify({
        'success': True,
        'is_active': user.is_active,
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
    })


@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')

    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot modify your own role'}), 400

    try:
        user.role = UserRole[new_role.upper()]
        db.session.commit()

        log_activity('CHANGE_USER_ROLE', entity_type='User', entity_id=user_id,
                    description=f'Changed user role to {new_role}')

        return jsonify({'success': True, 'message': f'User role changed to {new_role}'})
    except KeyError:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400


@admin_bp.route('/missing-persons')
@admin_required
def missing_persons():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    verified_filter = request.args.get('verified', '')

    query = MissingPerson.query

    if search:
        query = query.filter(
            or_(
                MissingPerson.full_name.ilike(f'%{search}%'),
                MissingPerson.case_number.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter_by(status=MissingPersonStatus[status_filter.upper()])

    if verified_filter:
        is_verified = verified_filter.lower() == 'true'
        query = query.filter_by(is_verified=is_verified)

    persons_pagination = query.order_by(MissingPerson.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    log_activity('VIEW_MISSING_PERSONS', description='Viewed missing persons list')

    return render_template('admin/missing_persons.html',
                         persons=persons_pagination,
                         search=search,
                         status_filter=status_filter,
                         verified_filter=verified_filter)


@admin_bp.route('/missing-persons/<int:person_id>')
@admin_required
def missing_person_detail(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    photos = person.photos.all()
    sightings = person.sighting_reports.order_by(SightingReport.created_at.desc()).all()

    log_activity('VIEW_MISSING_PERSON', entity_type='MissingPerson', entity_id=person_id)

    return render_template('admin/missing_person_detail.html',
                         person=person,
                         photos=photos,
                         sightings=sightings)


@admin_bp.route('/missing-persons/<int:person_id>/verify', methods=['POST'])
@admin_required
def verify_missing_person(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    person.is_verified = True
    db.session.commit()

    log_activity('VERIFY_MISSING_PERSON', entity_type='MissingPerson', entity_id=person_id)

    notification = Notification(
        user_id=person.reported_by,
        title='Report Verified',
        message=f'Your missing person report for {person.full_name} has been verified.',
        notification_type='verification'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Person verified successfully'})


@admin_bp.route('/missing-persons/<int:person_id>/update-status', methods=['POST'])
@admin_required
def update_person_status(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    new_status = request.json.get('status')

    try:
        person.status = MissingPersonStatus[new_status.upper()]
        if new_status.upper() == 'FOUND':
            person.found_date = datetime.now()
        db.session.commit()

        log_activity('UPDATE_PERSON_STATUS', entity_type='MissingPerson', entity_id=person_id,
                    description=f'Changed status to {new_status}')

        notification = Notification(
            user_id=person.reported_by,
            title='Status Updated',
            message=f'The status of {person.full_name} has been updated to {new_status}.',
            notification_type='status_update',
            related_person_id=person_id
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    except KeyError:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400


@admin_bp.route('/reports')
@admin_required
def reports():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')

    query = SightingReport.query

    if status_filter:
        query = query.filter_by(status=ReportStatus[status_filter.upper()])

    reports_pagination = query.order_by(SightingReport.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    log_activity('VIEW_REPORTS', description='Viewed sighting reports list')

    return render_template('admin/reports.html',
                         reports=reports_pagination,
                         status_filter=status_filter)


@admin_bp.route('/reports/<int:report_id>')
@admin_required
def report_detail(report_id):
    report = SightingReport.query.get_or_404(report_id)
    photos = report.photos.all()

    log_activity('VIEW_REPORT', entity_type='SightingReport', entity_id=report_id)

    return render_template('admin/report_detail.html', report=report, photos=photos)


@admin_bp.route('/reports/<int:report_id>/verify', methods=['POST'])
@admin_required
def verify_report(report_id):
    report = SightingReport.query.get_or_404(report_id)
    notes = request.json.get('notes', '')

    report.verify_report(current_user.id, notes)

    log_activity('VERIFY_REPORT', entity_type='SightingReport', entity_id=report_id)

    notification = Notification(
        user_id=report.reported_by,
        title='Sighting Report Verified',
        message=f'Your sighting report has been verified by our team.',
        notification_type='verification',
        related_report_id=report_id
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Report verified successfully'})


@admin_bp.route('/reports/<int:report_id>/reject', methods=['POST'])
@admin_required
def reject_report(report_id):
    report = SightingReport.query.get_or_404(report_id)
    notes = request.json.get('notes', '')

    report.reject_report(current_user.id, notes)

    log_activity('REJECT_REPORT', entity_type='SightingReport', entity_id=report_id)

    notification = Notification(
        user_id=report.reported_by,
        title='Sighting Report Reviewed',
        message=f'Your sighting report has been reviewed.',
        notification_type='verification',
        related_report_id=report_id
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Report rejected'})


@admin_bp.route('/activity-logs')
@admin_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')

    query = ActivityLog.query

    if action_filter:
        query = query.filter(ActivityLog.action.ilike(f'%{action_filter}%'))

    logs_pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    log_activity('VIEW_ACTIVITY_LOGS', description='Viewed activity logs')

    return render_template('admin/activity_logs.html',
                         logs=logs_pagination,
                         action_filter=action_filter)


@admin_bp.route('/settings')
@admin_required
def settings():
    settings_list = SystemSetting.query.all()

    log_activity('VIEW_SETTINGS', description='Viewed system settings')

    return render_template('admin/settings.html', settings=settings_list)


@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
def update_setting():
    key = request.json.get('key')
    value = request.json.get('value')

    setting = SystemSetting.query.filter_by(key=key).first()

    if setting:
        setting.value = value
        setting.updated_at = datetime.now()
    else:
        setting = SystemSetting(key=key, value=value)
        db.session.add(setting)

    db.session.commit()

    log_activity('UPDATE_SETTING', entity_type='SystemSetting',
                description=f'Updated setting: {key}')

    return jsonify({'success': True, 'message': 'Setting updated successfully'})


@admin_bp.route('/statistics')
@admin_required
def statistics():
    thirty_days_ago = datetime.now() - timedelta(days=30)

    daily_stats = db.session.query(
        func.date(MissingPerson.created_at).label('date'),
        func.count(MissingPerson.id).label('count')
    ).filter(
        MissingPerson.created_at >= thirty_days_ago
    ).group_by(
        func.date(MissingPerson.created_at)
    ).all()

    status_stats = db.session.query(
        MissingPerson.status,
        func.count(MissingPerson.id)
    ).group_by(MissingPerson.status).all()

    report_stats = db.session.query(
        SightingReport.status,
        func.count(SightingReport.id)
    ).group_by(SightingReport.status).all()

    log_activity('VIEW_STATISTICS', description='Viewed statistics')

    return render_template('admin/statistics.html',
                         daily_stats=daily_stats,
                         status_stats=status_stats,
                         report_stats=report_stats)
