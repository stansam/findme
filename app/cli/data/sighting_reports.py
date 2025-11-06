import click
from app.extensions import db
from app.models.sighting import SightingReport, SightingPhoto
from app.models.options import UserRole, ReportStatus
from datetime import timedelta
import random
from app.cli.data.utils import generate_random_date, generate_coordinates
from app.cli.data.pools import KENYAN_CITIES, NAIROBI_LOCATIONS

def create_sighting_reports(users, missing_persons, count=100):
    """Create sample sighting reports."""
    click.echo(f"\n👁️ Creating {count} sighting reports...")
    
    sightings = []
    photos = []
    
    for i in range(count):
        person = random.choice(missing_persons)
        reporter = random.choice(users)
        
        # Sighting should be after the person went missing
        sighting_date = person.last_seen_date + timedelta(days=random.randint(1, 90))
        
        city = random.choice(KENYAN_CITIES)
        location = random.choice(NAIROBI_LOCATIONS) if city == 'Nairobi' else f"{random.choice(['Near', 'At', 'Around'])} {random.choice(['market', 'bus stop', 'shopping center', 'park', 'street'])}, {city}"
        
        coords = generate_coordinates(city)
        
        is_anonymous = random.choice([True] * 20 + [False] * 80)
        
        descriptions = [
            f"I saw someone matching the description walking alone near {location}.",
            f"Spotted someone who looks like {person.full_name} at {location}. They were with another person.",
            f"Possible sighting at {location}. Person was wearing similar clothing.",
            f"I believe I saw this person at {location} around {sighting_date.strftime('%I:%M %p')}.",
            f"Definite match seen at {location}. Person seemed confused/disoriented.",
        ]
        
        conditions = [
            'Appeared healthy', 'Seemed distressed', 'Looked confused', 'Appeared well',
            'Seemed tired', 'Looked scared', 'Normal appearance', 'Appeared injured'
        ]
        
        accompanied = [
            'Alone', 'With one adult male', 'With one adult female', 'With a group of people',
            'With children', 'With an elderly person', None
        ]
        
        status_weights = [50, 30, 20]  # pending, verified, rejected
        status = random.choices(list(ReportStatus), weights=status_weights)[0]
        
        sighting = SightingReport(
            missing_person_id=person.id,
            reported_by=reporter.id,
            sighting_date=sighting_date,
            sighting_location=location,
            latitude=coords[0],
            longitude=coords[1],
            description=random.choice(descriptions),
            person_condition=random.choice(conditions) if random.random() > 0.2 else None,
            accompanied_by=random.choice(accompanied),
            reporter_contact=f"+2547{random.randint(10000000, 99999999)}" if not is_anonymous and random.random() > 0.3 else None,
            is_anonymous=is_anonymous,
            status=status,
            verified_by=random.choice([u for u in users if u.role == UserRole.ADMIN]).id if status != ReportStatus.PENDING else None,
            verification_notes=random.choice([
                'Verified with additional evidence',
                'Location confirmed by police',
                'Credible witness',
                'Video footage reviewed',
                'Insufficient evidence',
                'Duplicate report',
                'Not matching description'
            ]) if status != ReportStatus.PENDING else None,
            created_at=sighting_date + timedelta(hours=random.randint(1, 24)),
            updated_at=generate_random_date(30, 0) if status != ReportStatus.PENDING else None,
            verified_at=generate_random_date(25, 0) if status != ReportStatus.PENDING else None
        )
        
        sightings.append(sighting)
    
    db.session.bulk_save_objects(sightings)
    db.session.commit()
    
    # Reload to get IDs and add photos to some sightings
    all_sightings = SightingReport.query.all()
    
    click.echo("📸 Adding photos to sightings...")
    for sighting in random.sample(all_sightings, min(40, len(all_sightings))):
        num_photos = random.randint(1, 3)
        for j in range(num_photos):
            photo = SightingPhoto(
                sighting_id=sighting.id,
                filename=f"sighting_{sighting.id}_photo_{j+1}.jpg",
                file_path=f"/uploads/sightings/{sighting.id}/photo_{j+1}.jpg",
                file_size=random.randint(50000, 2000000),
                mime_type='image/jpeg',
                uploaded_at=sighting.created_at + timedelta(minutes=random.randint(1, 30))
            )
            photos.append(photo)
    
    db.session.bulk_save_objects(photos)
    db.session.commit()
    
    click.echo(f"✅ Created {len(sightings)} sighting reports with {len(photos)} photos")
    return sightings