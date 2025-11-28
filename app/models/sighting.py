from app.extensions import db
from app.models.options import ReportStatus
from datetime import datetime

class SightingReport(db.Model):
    __tablename__ = 'sighting_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_persons.id'), 
                                 nullable=False, index=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    sighting_date = db.Column(db.DateTime, nullable=False)
    sighting_location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    description = db.Column(db.Text, nullable=False)
    person_condition = db.Column(db.String(255), nullable=True)
    accompanied_by = db.Column(db.String(255), nullable=True)
    
    # Reporter Contact (optional for anonymous tips)
    reporter_contact = db.Column(db.String(100), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING, 
                      nullable=False, index=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    photos = db.relationship('SightingPhoto', backref='sighting', lazy='dynamic',
                           cascade='all, delete-orphan')
    
    def verify_report(self, admin_id, notes=None):
        self.status = ReportStatus.VERIFIED
        self.verified_by = admin_id
        self.verification_notes = notes
        self.verified_at = datetime.now()
        db.session.commit()
    
    def reject_report(self, admin_id, notes=None):
        self.status = ReportStatus.REJECTED
        self.verified_by = admin_id
        self.verification_notes = notes
        self.verified_at = datetime.now()
        db.session.commit()
    
    def __repr__(self):
        return f'<SightingReport {self.id}>'


class SightingPhoto(db.Model):
    __tablename__ = 'sighting_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    sighting_id = db.Column(db.Integer, db.ForeignKey('sighting_reports.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(50), nullable=True)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def get_display_url(self):
        """
        Returns the local static URL if the file exists on the server.
        Otherwise, returns a fallback image from an external API.
        """
        from flask import url_for
        import os
        try:
            # 1. Construct the absolute file system path to check existence
            # Assuming 'static' is your static folder and file_path is relative to it
            full_path = os.path.join('static', self.file_path)

            # 2. Check if file exists locally
            if os.path.exists(full_path):
                return url_for('static', filename=self.file_path)
            
        except Exception:
            # Fallback if contexts aren't set up or pathing fails
            pass

        # 3. Return API Fallback Image if local file is missing
        # We use the photo ID as a 'seed' so the image is consistent for this specific record
        return f"https://picsum.photos/seed/{self.id}/800/600"
    
    def __repr__(self):
        return f'<SightingPhoto {self.filename}>'