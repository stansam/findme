from app.extensions import db
from app.models.options import MissingPersonStatus
from datetime import datetime
import os, random
from flask import current_app, url_for


class MissingPerson(db.Model):
    __tablename__ = 'missing_persons'
    
    id = db.Column(db.Integer, primary_key=True)
    
    full_name = db.Column(db.String(150), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    height = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.String(20), nullable=True)
    hair_color = db.Column(db.String(50), nullable=True)
    eye_color = db.Column(db.String(50), nullable=True)
    skin_tone = db.Column(db.String(50), nullable=True)
    distinguishing_features = db.Column(db.Text, nullable=True)
    
    last_seen_location = db.Column(db.String(255), nullable=False)
    last_seen_date = db.Column(db.DateTime, nullable=False, index=True)
    last_seen_wearing = db.Column(db.Text, nullable=True)
    circumstances = db.Column(db.Text, nullable=True)
    
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    contact_name = db.Column(db.String(150), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_relationship = db.Column(db.String(100), nullable=True)
    
    status = db.Column(db.Enum(MissingPersonStatus), 
                      default=MissingPersonStatus.MISSING, 
                      nullable=False, 
                      index=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_minor = db.Column(db.Boolean, default=False, nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    
    case_number = db.Column(db.String(50), unique=True, nullable=True, index=True)
    police_report_number = db.Column(db.String(100), nullable=True)
    
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    found_date = db.Column(db.DateTime, nullable=True)
    
    view_count = db.Column(db.Integer, default=0, nullable=False)
    
    photos = db.relationship('PersonPhoto', backref='person', lazy='dynamic', 
                           cascade='all, delete-orphan')
    sighting_reports = db.relationship('SightingReport', backref='missing_person', 
                                      lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def display_image_url(self):
        """
        Returns a usable photo URL or a fallback avatar.
        - Checks both DB record and actual file existence.
        - Gracefully handles missing files and OS errors.
        - Uses gender-based random avatar as fallback.
        """
        try:
            # Use Flask's configured static folder (portable across environments)
            static_folder = current_app.static_folder
            upload_dir = os.path.join(static_folder, 'uploads')

            # 1️⃣ Check if the person has an uploaded photo record
            first_photo = self.photos.first()
            if first_photo:
                photo_path = os.path.join(upload_dir, first_photo.filename)
                if os.path.isfile(photo_path):  # safer and faster than os.path.exists
                    return url_for('static', filename=f'uploads/{first_photo.filename}')

                # Log the missing file for admin awareness
                current_app.logger.warning(
                    f"Photo file missing for MissingPerson ID {self.id}: {photo_path}"
                )

            # 2️⃣ Build a robust fallback (always succeeds)
            gender = (self.gender or 'unknown').strip().lower()
            name_seed = (self.full_name or 'User').split()[0]

            fallback_sources = {
                'male': [
                    f"https://api.dicebear.com/9.x/adventurer/png?seed={name_seed}",
                    f"https://randomuser.me/api/portraits/men/{random.randint(1, 99)}.jpg",
                ],
                'female': [
                    f"https://api.dicebear.com/9.x/adventurer/png?seed={name_seed}",
                    f"https://randomuser.me/api/portraits/women/{random.randint(1, 99)}.jpg",
                ],
                'unknown': [
                    f"https://api.dicebear.com/9.x/identicon/png?seed={name_seed}",
                ]
            }

            # 3️⃣ Pick a random fallback based on gender, or default to unknown
            url = random.choice(fallback_sources.get(gender, fallback_sources['unknown']))

            # Optional: add a static local fallback if external APIs fail
            if not url:
                if gender == 'male':
                    url = url_for('static', filename='assets/male_placeholder.png')

                elif gender == 'female':
                    url = url_for('static', filename='assets/missing_placeholder.png')
                else:
                    url = url_for('static', filename='assets/blank_face.png')
            return url

        except Exception as e:
            # 4️⃣ Catch-all safeguard (should never propagate to Jinja)
            current_app.logger.error(
                f"Error resolving display_image_url for MissingPerson ID {self.id}: {e}",
                exc_info=True
            )
            # Always provide a working final fallback
            return url_for('static', filename='images/default_unknown.png')
        
    @property
    def display_photos(self):
        """Return up to 4 valid photo URLs or random fallbacks."""
        upload_dir = os.path.join('app', 'static', 'uploads')

        photos = []
        if hasattr(self, 'photos') and self.photos:
            for photo in self.photos:
                photo_path = os.path.join(upload_dir, photo.filename)
                if os.path.exists(photo_path):
                    photos.append(url_for('static', filename=f'uploads/{photo.filename}'))

        # If none exist, generate random placeholders
        if not photos:
            base_name = self.full_name.split()[0] if self.full_name else "user"
            gender = getattr(self, 'gender', 'neutral').lower()

            if gender in ['male', 'm']:
                api_base = "https://randomuser.me/api/portraits/men/"
                alt_sources = [
                    f"https://api.dicebear.com/7.x/adventurer/png?seed={base_name}{i}"
                    for i in range(1, 5)
                ]
            elif gender in ['female', 'f']:
                api_base = "https://randomuser.me/api/portraits/women/"
                alt_sources = [
                    f"https://api.dicebear.com/7.x/adventurer-neutral/png?seed={base_name}{i}"
                    for i in range(1, 5)
                ]
            else:
                api_base = "https://randomuser.me/api/portraits/lego/"
                alt_sources = [
                    f"https://api.dicebear.com/7.x/bottts/png?seed={base_name}{i}"
                    for i in range(1, 5)
                ]

            # choose up to 4 images — random user fallback
            photos = random.sample(alt_sources, min(4, len(alt_sources)))

        return photos

    
    def increment_views(self):
        """Increment view counter"""
        self.view_count += 1
        db.session.commit()
    
    def mark_as_found(self):
        """Mark person as found"""
        self.status = MissingPersonStatus.FOUND
        self.found_date = datetime.now()
        db.session.commit()
    
    def __repr__(self):
        return f'<MissingPerson {self.full_name}>'


class PersonPhoto(db.Model):
    __tablename__ = 'person_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('missing_persons.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(50), nullable=True)
    
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    def __repr__(self):
        return f'<PersonPhoto {self.filename}>'