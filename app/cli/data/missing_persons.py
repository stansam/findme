import click
from app.extensions import db
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.options import MissingPersonStatus
from datetime import datetime, timedelta
import random
from app.cli.data.utils import generate_random_date, generate_coordinates
from app.cli.data.pools import FIRST_NAMES_FEMALE, FIRST_NAMES_MALE, LAST_NAMES, KENYAN_CITIES, NAIROBI_LOCATIONS, HAIR_COLORS, EYE_COLORS, SKIN_TONES, DISTINGUISHING_FEATURES, CLOTHING_ITEMS, CIRCUMSTANCES


def create_missing_persons(users, count=50):
    """Create sample missing persons reports."""
    click.echo(f"\n👤 Creating {count} missing persons reports...")
    
    missing_persons = []
    photos = []
    
    for i in range(count):
        gender = random.choice(['Male', 'Female', 'Non-binary'])
        age = random.randint(5, 85)
        
        if gender == 'Male':
            first_name = random.choice(FIRST_NAMES_MALE)
        elif gender == 'Female':
            first_name = random.choice(FIRST_NAMES_FEMALE)
        else:
            first_name = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
        
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        # Calculate date of birth
        dob = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))
        
        last_seen_date = generate_random_date(180, 1)
        city = random.choice(KENYAN_CITIES)
        location = random.choice(NAIROBI_LOCATIONS) if city == 'Nairobi' else f"{random.choice(['Downtown', 'Suburb', 'Market area', 'Bus station'])}, {city}"
        
        coords = generate_coordinates(city)
        
        status_weights = [60, 15, 20, 5]  # missing, found, investigating, closed
        status = random.choices(list(MissingPersonStatus), weights=status_weights)[0]
        
        person = MissingPerson(
            full_name=full_name,
            age=age,
            gender=gender,
            date_of_birth=dob.date(),
            height=f"{random.randint(140, 200)} cm",
            weight=f"{random.randint(40, 120)} kg",
            hair_color=random.choice(HAIR_COLORS),
            eye_color=random.choice(EYE_COLORS),
            skin_tone=random.choice(SKIN_TONES),
            distinguishing_features=random.choice(DISTINGUISHING_FEATURES) if random.random() > 0.3 else None,
            last_seen_location=location,
            last_seen_date=last_seen_date,
            last_seen_wearing=random.choice(CLOTHING_ITEMS),
            circumstances=random.choice(CIRCUMSTANCES),
            latitude=coords[0],
            longitude=coords[1],
            contact_name=f"{random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}",
            contact_phone=f"+2547{random.randint(10000000, 99999999)}",
            contact_email=f"contact{i}@example.com",
            contact_relationship=random.choice(['Parent', 'Sibling', 'Spouse', 'Friend', 'Relative', 'Guardian']),
            status=status,
            is_verified=random.choice([True] * 70 + [False] * 30),
            is_minor=age < 18,
            is_public=random.choice([True] * 90 + [False] * 10),
            case_number=f"MP-{datetime.now().year}-{str(i+1).zfill(5)}",
            police_report_number=f"OB-{random.randint(100, 999)}/{datetime.now().year}" if random.random() > 0.3 else None,
            reported_by=random.choice(users).id,
            created_at=last_seen_date + timedelta(hours=random.randint(2, 72)),
            updated_at=generate_random_date(30, 0),
            found_date=generate_random_date(30, 0) if status == MissingPersonStatus.FOUND else None,
            view_count=random.randint(0, 1000)
        )
        
        db.session.add(person)
        missing_persons.append(person)
    
    # db.session.bulk_save_objects(missing_persons)
    db.session.commit()
    
    # Reload to get IDs
    all_persons = MissingPerson.query.all()
    
    # Create photos for missing persons
    click.echo("📸 Adding photos to missing persons...")
    for person in all_persons:
        num_photos = random.randint(1, 4)
        for j in range(num_photos):
            photo = PersonPhoto(
                person_id=person.id,
                filename=f"person_{person.id}_photo_{j+1}.jpg",
                file_path=f"/uploads/persons/{person.id}/photo_{j+1}.jpg",
                file_size=random.randint(50000, 3000000),
                mime_type='image/jpeg',
                is_primary=(j == 0),
                caption=f"Photo {j+1} of {person.full_name}" if random.random() > 0.5 else None,
                uploaded_at=person.created_at + timedelta(minutes=random.randint(1, 60))
            )
            photos.append(photo)
    
    db.session.bulk_save_objects(photos)
    db.session.commit()
    
    click.echo(f"✅ Created {len(missing_persons)} missing persons with {len(photos)} photos")
    return missing_persons

