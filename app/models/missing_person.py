from app.extensions import db
from app.models.options import MissingPersonStatus
from datetime import datetime

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