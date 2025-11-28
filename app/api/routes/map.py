from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.sighting import SightingReport, SightingPhoto
from app.models.options import MissingPersonStatus, ReportStatus
# from app.models.system import ActivityLog, Notification
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import requests
from functools import lru_cache

from app.api import bp as maps_bp 

# Configuration
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
NOMINATIM_HEADERS = {
    'User-Agent': 'FindMe-MissingPersons/1.0'
}

# ========== HELPER FUNCTIONS ==========

@lru_cache(maxsize=100)
def geocode_address(address):
    """
    Geocode an address to lat/lng using Nominatim
    Cached to avoid repeated API calls
    """
    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/search",
            params={
                'q': address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'ke'  # Restrict to Kenya
            },
            headers=NOMINATIM_HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lng': float(data[0]['lon']),
                    'display_name': data[0]['display_name']
                }
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
    
    return None


def reverse_geocode(lat, lng):
    """
    Reverse geocode lat/lng to address
    """
    try:
        response = requests.get(
            f"{NOMINATIM_BASE_URL}/reverse",
            params={
                'lat': lat,
                'lon': lng,
                'format': 'json'
            },
            headers=NOMINATIM_HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', 'Unknown Location')
    except Exception as e:
        print(f"Reverse geocoding error: {str(e)}")
    
    return None


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


# def log_activity(action, entity_type=None, entity_id=None, description=None):
#     """Helper to log user activities"""
#     try:
#         log = ActivityLog(
#             user_id=current_user.id if current_user.is_authenticated else None,
#             action=action,
#             entity_type=entity_type,
#             entity_id=entity_id,
#             description=description,
#             ip_address=request.remote_addr,
#             user_agent=request.headers.get('User-Agent', '')[:255]
#         )
#         db.session.add(log)
#         db.session.commit()
#     except Exception as e:
#         print(f"Activity logging error: {str(e)}")




@maps_bp.route('/maps/markers', methods=['GET'])
def get_map_markers():
    """
    Get all missing persons and sightings as map markers
    Supports filtering by status, date range, and location
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status', 'all')
        days_filter = request.args.get('days', 'all')
        bounds = request.args.get('bounds')  # "sw_lat,sw_lng,ne_lat,ne_lng"
        search_query = request.args.get('q', '').strip()
        
        # Base query for missing persons
        query = MissingPerson.query.filter_by(is_public=True)
        
        # Apply status filter
        if status_filter != 'all':
            try:
                status_enum = MissingPersonStatus[status_filter.upper()]
                query = query.filter_by(status=status_enum)
            except KeyError:
                pass
        
        # Apply date filter
        if days_filter != 'all':
            try:
                days = int(days_filter)
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(MissingPerson.last_seen_date >= cutoff_date)
            except ValueError:
                pass
        
        # Apply bounds filter (viewport)
        if bounds:
            try:
                sw_lat, sw_lng, ne_lat, ne_lng = map(float, bounds.split(','))
                query = query.filter(
                    and_(
                        MissingPerson.latitude >= sw_lat,
                        MissingPerson.latitude <= ne_lat,
                        MissingPerson.longitude >= sw_lng,
                        MissingPerson.longitude <= ne_lng
                    )
                )
            except (ValueError, AttributeError):
                pass
        
        # Apply search query
        if search_query:
            query = query.filter(
                or_(
                    MissingPerson.full_name.ilike(f'%{search_query}%'),
                    MissingPerson.last_seen_location.ilike(f'%{search_query}%'),
                    MissingPerson.case_number.ilike(f'%{search_query}%')
                )
            )
        
        # Execute query
        missing_persons = query.filter(
            and_(
                MissingPerson.latitude.isnot(None),
                MissingPerson.longitude.isnot(None)
            )
        ).all()
        
        # Build markers array
        markers = []
        
        for person in missing_persons:
            # Get primary photo
            primary_photo = person.photos.filter_by(is_primary=True).first()
            if not primary_photo:
                primary_photo = person.photos.first()
            
            # Get sighting count
            sighting_count = person.sighting_reports.filter_by(
                status=ReportStatus.VERIFIED
            ).count()
            
            # Calculate days missing
            days_missing = (datetime.now() - person.last_seen_date).days
            
            marker_data = {
                'id': person.id,
                'type': 'missing_person',
                'lat': person.latitude,
                'lng': person.longitude,
                'name': person.full_name,
                'age': person.age,
                'gender': person.gender,
                'status': person.status.value,
                'case_number': person.case_number,
                'last_seen_location': person.last_seen_location,
                'last_seen_date': person.last_seen_date.isoformat(),
                'days_missing': days_missing,
                'is_minor': person.is_minor,
                'is_verified': person.is_verified,
                'photo_url': person.display_image_url,
                'sighting_count': sighting_count,
                'view_count': person.view_count,
                'description': person.circumstances[:200] if person.circumstances else None
            }
            
            markers.append(marker_data)
        
        # Get verified sightings if requested
        include_sightings = request.args.get('include_sightings', 'true').lower() == 'true'
        
        if include_sightings:
            sightings_query = SightingReport.query.filter_by(
                status=ReportStatus.VERIFIED
            ).filter(
                and_(
                    SightingReport.latitude.isnot(None),
                    SightingReport.longitude.isnot(None)
                )
            )
            
            # Apply bounds filter to sightings
            if bounds:
                try:
                    sw_lat, sw_lng, ne_lat, ne_lng = map(float, bounds.split(','))
                    sightings_query = sightings_query.filter(
                        and_(
                            SightingReport.latitude >= sw_lat,
                            SightingReport.latitude <= ne_lat,
                            SightingReport.longitude >= sw_lng,
                            SightingReport.longitude <= ne_lng
                        )
                    )
                except (ValueError, AttributeError):
                    pass
            
            sightings = sightings_query.all()
            
            for sighting in sightings:
                marker_data = {
                    'id': sighting.id,
                    'type': 'sighting',
                    'lat': sighting.latitude,
                    'lng': sighting.longitude,
                    'missing_person_id': sighting.missing_person_id,
                    'missing_person_name': sighting.missing_person.full_name,
                    'sighting_location': sighting.sighting_location,
                    'sighting_date': sighting.sighting_date.isoformat(),
                    'description': sighting.description[:200],
                    'person_condition': sighting.person_condition,
                    'reported_by': 'Anonymous' if sighting.is_anonymous else None
                }
                
                markers.append(marker_data)
        
        # Log activity
        current_app.logger.info('Viewed map with {len(markers)} markers')
        
        return jsonify({
            'success': True,
            'markers': markers,
            'total': len(markers),
            'filters': {
                'status': status_filter,
                'days': days_filter,
                'search': search_query
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching markers: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch map markers',
            'message': str(e)
        }), 500


@maps_bp.route('/maps/person/<int:person_id>', methods=['GET'])
def get_person_details(person_id):
    """Get detailed information about a missing person"""
    try:
        person = MissingPerson.query.get_or_404(person_id)
        
        if not person.is_public and not (current_user.is_authenticated and current_user.is_admin()):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        # Get all photos
        photos = [{
            'url': photo.file_path,
            'is_primary': photo.is_primary,
            'caption': photo.caption
        } for photo in person.photos.all()]
        
        # Get verified sightings
        sightings = []
        for sighting in person.sighting_reports.filter_by(status=ReportStatus.VERIFIED).order_by(SightingReport.sighting_date.desc()).all():
            sightings.append({
                'id': sighting.id,
                'location': sighting.sighting_location,
                'lat': sighting.latitude,
                'lng': sighting.longitude,
                'date': sighting.sighting_date.isoformat(),
                'description': sighting.description,
                'condition': sighting.person_condition
            })
        
        # Increment view count
        person.increment_views()
        
        return jsonify({
            'success': True,
            'person': {
                'id': person.id,
                'full_name': person.full_name,
                'age': person.age,
                'gender': person.gender,
                'date_of_birth': person.date_of_birth.isoformat() if person.date_of_birth else None,
                'height': person.height,
                'weight': person.weight,
                'hair_color': person.hair_color,
                'eye_color': person.eye_color,
                'skin_tone': person.skin_tone,
                'distinguishing_features': person.distinguishing_features,
                'last_seen_location': person.last_seen_location,
                'last_seen_date': person.last_seen_date.isoformat(),
                'last_seen_wearing': person.last_seen_wearing,
                'circumstances': person.circumstances,
                'latitude': person.latitude,
                'longitude': person.longitude,
                'status': person.status.value,
                'case_number': person.case_number,
                'is_minor': person.is_minor,
                'is_verified': person.is_verified,
                'contact_name': person.contact_name,
                'contact_phone': person.contact_phone,
                'contact_email': person.contact_email,
                'photos': photos,
                'sightings': sightings,
                'view_count': person.view_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch person details',
            'message': str(e)
        }), 500


@maps_bp.route('/maps/search-location', methods=['POST'])
def search_location():
    """Geocode a location search query"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        result = geocode_address(query)
        
        if result:
            return jsonify({
                'success': True,
                'location': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Location not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500


@maps_bp.route('/maps/nearby', methods=['POST'])
def get_nearby_cases():
    """Get missing persons within a radius of a location"""
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        radius = float(data.get('radius', 10))  # Default 10km
        
        # Get all persons with coordinates
        all_persons = MissingPerson.query.filter(
            and_(
                MissingPerson.is_public == True,
                MissingPerson.latitude.isnot(None),
                MissingPerson.longitude.isnot(None)
            )
        ).all()
        
        # Filter by distance
        nearby = []
        for person in all_persons:
            distance = calculate_distance(lat, lng, person.latitude, person.longitude)
            if distance <= radius:
                nearby.append({
                    'id': person.id,
                    'name': person.full_name,
                    'distance': round(distance, 2),
                    'lat': person.latitude,
                    'lng': person.longitude,
                    'status': person.status.value,
                    'last_seen_location': person.last_seen_location
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'success': True,
            'results': nearby,
            'count': len(nearby)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to search nearby',
            'message': str(e)
        }), 500


@maps_bp.route('/maps/statistics', methods=['GET'])
def get_map_statistics():
    """Get overall statistics for the map"""
    try:
        # Overall stats
        total_missing = MissingPerson.query.filter_by(is_public=True).count()
        total_found = MissingPerson.query.filter_by(
            is_public=True,
            status=MissingPersonStatus.FOUND
        ).count()
        total_investigating = MissingPerson.query.filter_by(
            is_public=True,
            status=MissingPersonStatus.INVESTIGATING
        ).count()
        
        # Recent cases (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_cases = MissingPerson.query.filter(
            and_(
                MissingPerson.is_public == True,
                MissingPerson.created_at >= thirty_days_ago
            )
        ).count()
        
        # Minors count
        minors = MissingPerson.query.filter_by(
            is_public=True,
            is_minor=True,
            status=MissingPersonStatus.MISSING
        ).count()
        
        # Hotspot regions (top 5 locations)
        hotspots = db.session.query(
            MissingPerson.last_seen_location,
            func.count(MissingPerson.id).label('count')
        ).filter_by(is_public=True).group_by(
            MissingPerson.last_seen_location
        ).order_by(func.count(MissingPerson.id).desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_missing': total_missing,
                'total_found': total_found,
                'total_investigating': total_investigating,
                'active_cases': total_missing - total_found,
                'recent_cases': recent_cases,
                'minors': minors,
                'hotspots': [{'location': h[0], 'count': h[1]} for h in hotspots]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch statistics',
            'message': str(e)
        }), 500


@maps_bp.route('/maps/update-coordinates/<int:person_id>', methods=['PUT'])
@login_required
def update_coordinates(person_id):
    """Update coordinates for a missing person (admin only)"""
    try:
        if not current_user.is_admin():
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        person = MissingPerson.query.get_or_404(person_id)
        data = request.get_json()
        
        person.latitude = float(data.get('lat'))
        person.longitude = float(data.get('lng'))
        
        db.session.commit()
        
        # log_activity(
        #     'update_coordinates',
        #     'missing_person',
        #     person_id,
        #     f'Updated coordinates for {person.full_name}'
        # )
        
        return jsonify({
            'success': True,
            'message': 'Coordinates updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update coordinates',
            'message': str(e)
        }), 500