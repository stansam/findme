from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db
from app.models.options import UserRole
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    
    full_name = db.Column(db.String(150), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.REGULAR, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    location = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = db.Column(db.DateTime, nullable=True)
    
    missing_persons = db.relationship('MissingPerson', backref='reporter', lazy='dynamic', 
                                     foreign_keys='MissingPerson.reported_by')
    sighting_reports = db.relationship('SightingReport', foreign_keys='SightingReport.reported_by', backref='reporter', lazy='dynamic')
    verified_reports = db.relationship('SightingReport', foreign_keys='SightingReport.verified_by', backref='verifier', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def __repr__(self):
        return f'<User {self.username}>'
