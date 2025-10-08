from flask import jsonify, request, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.api import bp
from app.models.missing_person import MissingPerson
from app.models.sighting import SightingReport
from app.extensions import db
from app.models.options import MissingPersonStatus, ReportStatus
from sqlalchemy import and_, desc
from datetime import datetime

@bp.route('/missing-persons', methods=['POST'])
@login_required
def create_missing_person():
    data = request.get_json()

    try:
        person = MissingPerson(
            full_name=data['full_name'],
            age=data.get('age'),
            gender=data.get('gender'),
            last_seen_location=data['last_seen_location'],
            last_seen_date=datetime.fromisoformat(data['last_seen_date']),
            last_seen_wearing=data.get('last_seen_wearing'),
            circumstances=data.get('circumstances'),
            height=data.get('height'),
            weight=data.get('weight'),
            hair_color=data.get('hair_color'),
            eye_color=data.get('eye_color'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            reported_by=current_user.id
        )

        db.session.add(person)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Missing person report created successfully',
            'person_id': person.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/sightings', methods=['POST'])
def create_sighting():
    data = request.get_json()

    try:
        sighting = SightingReport(
            missing_person_id=data['missing_person_id'],
            reported_by=current_user.id if current_user.is_authenticated else None,
            sighting_date=datetime.fromisoformat(data['sighting_date']),
            sighting_location=data['sighting_location'],
            description=data['description'],
            person_condition=data.get('person_condition'),
            is_anonymous=data.get('is_anonymous', False),
            reporter_contact=data.get('reporter_contact')
        )

        db.session.add(sighting)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Sighting report submitted successfully',
            'sighting_id': sighting.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/search', methods=['GET'])
def search_api():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)

    results = MissingPerson.query.filter(
        MissingPerson.is_public == True,
        (MissingPerson.full_name.ilike(f'%{query}%') |
         MissingPerson.last_seen_location.ilike(f'%{query}%'))
    ).limit(limit).all()

    return jsonify([{
        'id': person.id,
        'full_name': person.full_name,
        'age': person.age,
        'last_seen_location': person.last_seen_location,
        'status': person.status.value
    } for person in results])

@bp.route('/recent-cases')
def api_recent_cases():
    limit = request.args.get('limit', 6, type=int)
    cases = MissingPerson.query.filter_by(
        is_public=True,
        status=MissingPersonStatus.MISSING
    ).order_by(desc(MissingPerson.created_at)).limit(limit).all()

    return jsonify([{
        'id': case.id,
        'full_name': case.full_name,
        'age': case.age,
        'last_seen_location': case.last_seen_location,
        'last_seen_date': case.last_seen_date.isoformat() if case.last_seen_date else None,
        'photo_url': url_for('static', filename=f'uploads/{case.photos.first().filename}')
        if case.photos.first() else None
    } for case in cases])


@bp.route('/map-data')
def api_map_data():
    cases = MissingPerson.query.filter(
        and_(
            MissingPerson.is_public == True,
            MissingPerson.status == MissingPersonStatus.MISSING,
            MissingPerson.latitude.isnot(None),
            MissingPerson.longitude.isnot(None)
        )
    ).all()

    return jsonify([{
        'id': case.id,
        'name': case.full_name,
        'lat': case.latitude,
        'lng': case.longitude,
        'location': case.last_seen_location,
        'date': case.last_seen_date.isoformat() if case.last_seen_date else None
    } for case in cases])