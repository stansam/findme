from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.sighting import SightingReport, SightingPhoto
from flask_login import login_required, current_user
import os
import uuid
from PIL import Image
from datetime import datetime

from app.api import bp as photo_bp

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES_PER_UPLOAD = 10
IMAGE_MAX_DIMENSION = 2048  # Max width/height for optimization


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file):
    """Validate file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE


def optimize_image(file_path, max_dimension=IMAGE_MAX_DIMENSION):
    """Optimize image size and quality"""
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_dimension or img.height > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(file_path, optimize=True, quality=85)
            return True
    except Exception as e:
        current_app.logger.error(f"Image optimization error: {str(e)}")
        return False


def save_uploaded_file(file, upload_folder):
    """Save uploaded file with unique name"""
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Optimize image
        optimize_image(file_path)
        
        return {
            'success': True,
            'filename': unique_filename,
            'file_path': file_path,
            'file_size': file_size,
            'mime_type': file.content_type
        }
    except Exception as e:
        current_app.logger.error(f"File save error: {str(e)}")
        return {'success': False, 'error': str(e)}


@photo_bp.route('/photos/missing-person/<int:person_id>', methods=['POST'])
@login_required
def upload_missing_person_photos(person_id):
    """
    Upload multiple photos for a missing person
    
    Expected form data:
    - files[]: Multiple image files
    - is_primary: (optional) Index of primary photo
    - captions[]: (optional) Captions for each photo
    """
    try:
        # Verify missing person exists and user has permission
        missing_person = MissingPerson.query.get_or_404(person_id)
        
        # Check if user is authorized (reporter or admin)
        if missing_person.reported_by != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access'
            }), 403
        
        # Check if files are present
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400
        
        files = request.files.getlist('files[]')
        
        # Validate number of files
        if len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        if len(files) > MAX_FILES_PER_UPLOAD:
            return jsonify({
                'success': False,
                'error': f'Maximum {MAX_FILES_PER_UPLOAD} files allowed per upload'
            }), 400
        
        # Get optional parameters
        primary_index = request.form.get('is_primary', type=int, default=0)
        captions = request.form.getlist('captions[]')
        
        # Upload folder setup
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        
        uploaded_photos = []
        errors = []
        
        # Process each file
        for idx, file in enumerate(files):
            if file.filename == '':
                errors.append(f"File {idx + 1}: No filename")
                continue
            
            # Validate file type
            if not allowed_file(file.filename):
                errors.append(f"File {idx + 1}: Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
                continue
            
            # Validate file size
            if not validate_file_size(file):
                errors.append(f"File {idx + 1}: File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")
                continue
            
            # Save file
            result = save_uploaded_file(file, upload_folder)
            
            if not result['success']:
                errors.append(f"File {idx + 1}: {result.get('error', 'Upload failed')}")
                continue
            
            # Create database record
            try:
                photo = PersonPhoto(
                    person_id=person_id,
                    filename=result['filename'],
                    file_path=result['file_path'],
                    file_size=result['file_size'],
                    mime_type=result['mime_type'],
                    is_primary=(idx == primary_index),
                    caption=captions[idx] if idx < len(captions) else None
                )
                
                db.session.add(photo)
                uploaded_photos.append({
                    'filename': result['filename'],
                    'url': f"/static/uploads/{result['filename']}",
                    'is_primary': idx == primary_index,
                    'caption': photo.caption
                })
            except Exception as e:
                errors.append(f"File {idx + 1}: Database error - {str(e)}")
                # Clean up uploaded file
                try:
                    os.remove(result['file_path'])
                except:
                    pass
                continue
        
        # Commit all successful uploads
        if uploaded_photos:
            try:
                # Update missing person timestamp
                missing_person.updated_at = datetime.now()
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully uploaded {len(uploaded_photos)} photo(s)',
                    'photos': uploaded_photos,
                    'errors': errors if errors else None,
                    'total_uploaded': len(uploaded_photos),
                    'total_errors': len(errors)
                }), 201
            except Exception as e:
                db.session.rollback()
                # Clean up uploaded files
                for photo_data in uploaded_photos:
                    try:
                        file_path = os.path.join(upload_folder, photo_data['filename'])
                        os.remove(file_path)
                    except:
                        pass
                
                return jsonify({
                    'success': False,
                    'error': f'Database commit failed: {str(e)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'No files were successfully uploaded',
                'errors': errors
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


@photo_bp.route('/photos/sighting/<int:sighting_id>', methods=['POST'])
@login_required
def upload_sighting_photos(sighting_id):
    """
    Upload multiple photos for a sighting report
    
    Expected form data:
    - files[]: Multiple image files
    """
    try:
        # Verify sighting report exists and user has permission
        sighting = SightingReport.query.get_or_404(sighting_id)
        
        # Check if user is authorized (reporter or admin)
        if sighting.reported_by != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access'
            }), 403
        
        # Check if files are present
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400
        
        files = request.files.getlist('files[]')
        
        # Validate number of files
        if len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        if len(files) > MAX_FILES_PER_UPLOAD:
            return jsonify({
                'success': False,
                'error': f'Maximum {MAX_FILES_PER_UPLOAD} files allowed per upload'
            }), 400
        
        # Upload folder setup
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'sightings')
        
        uploaded_photos = []
        errors = []
        
        # Process each file
        for idx, file in enumerate(files):
            if file.filename == '':
                errors.append(f"File {idx + 1}: No filename")
                continue
            
            # Validate file type
            if not allowed_file(file.filename):
                errors.append(f"File {idx + 1}: Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
                continue
            
            # Validate file size
            if not validate_file_size(file):
                errors.append(f"File {idx + 1}: File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")
                continue
            
            # Save file
            result = save_uploaded_file(file, upload_folder)
            
            if not result['success']:
                errors.append(f"File {idx + 1}: {result.get('error', 'Upload failed')}")
                continue
            
            # Create database record
            try:
                photo = SightingPhoto(
                    sighting_id=sighting_id,
                    filename=result['filename'],
                    file_path=result['file_path'],
                    file_size=result['file_size'],
                    mime_type=result['mime_type']
                )
                
                db.session.add(photo)
                uploaded_photos.append({
                    'filename': result['filename'],
                    'url': f"/static/uploads/sightings/{result['filename']}",
                })
            except Exception as e:
                errors.append(f"File {idx + 1}: Database error - {str(e)}")
                # Clean up uploaded file
                try:
                    os.remove(result['file_path'])
                except:
                    pass
                continue
        
        # Commit all successful uploads
        if uploaded_photos:
            try:
                # Update sighting timestamp
                sighting.updated_at = datetime.now()
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully uploaded {len(uploaded_photos)} photo(s)',
                    'photos': uploaded_photos,
                    'errors': errors if errors else None,
                    'total_uploaded': len(uploaded_photos),
                    'total_errors': len(errors)
                }), 201
            except Exception as e:
                db.session.rollback()
                # Clean up uploaded files
                for photo_data in uploaded_photos:
                    try:
                        file_path = os.path.join(upload_folder, photo_data['filename'])
                        os.remove(file_path)
                    except:
                        pass
                
                return jsonify({
                    'success': False,
                    'error': f'Database commit failed: {str(e)}'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'No files were successfully uploaded',
                'errors': errors
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Sighting upload error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


@photo_bp.route('/photos/missing-person/<int:person_id>/<int:photo_id>', methods=['DELETE'])
@login_required
def delete_missing_person_photo(person_id, photo_id):
    """Delete a photo from a missing person"""
    try:
        photo = PersonPhoto.query.filter_by(id=photo_id, person_id=person_id).first_or_404()
        missing_person = MissingPerson.query.get_or_404(person_id)
        
        # Check authorization
        if missing_person.reported_by != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete file from filesystem
        try:
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
        except Exception as e:
            current_app.logger.warning(f"Could not delete file {photo.file_path}: {str(e)}")
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Photo deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@photo_bp.route('/photos/sighting/<int:sighting_id>/<int:photo_id>', methods=['DELETE'])
@login_required
def delete_sighting_photo(sighting_id, photo_id):
    """Delete a photo from a sighting report"""
    try:
        photo = SightingPhoto.query.filter_by(id=photo_id, sighting_id=sighting_id).first_or_404()
        sighting = SightingReport.query.get_or_404(sighting_id)
        
        # Check authorization
        if sighting.reported_by != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete file from filesystem
        try:
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
        except Exception as e:
            current_app.logger.warning(f"Could not delete file {photo.file_path}: {str(e)}")
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Photo deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500