import click
from app.extensions import db
from app.models.user import User
from app.models.options import UserRole
import random
from app.cli.data.utils import generate_random_date
from app.cli.data.pools import FIRST_NAMES_FEMALE, FIRST_NAMES_MALE, LAST_NAMES, KENYAN_CITIES, NAIROBI_LOCATIONS

def create_users(count=20):
    """Create sample users."""
    users = []
    click.echo(f"\n📝 Creating {count} sample users...")
    
    for i in range(count):
        gender = random.choice(['male', 'female'])
        first_name = random.choice(FIRST_NAMES_MALE if gender == 'male' else FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES)
        
        username = f"{first_name.lower()}_{last_name.lower()}_{i}"
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
        
        # Check if user exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            continue
        
        user = User(
            username=username,
            email=email,
            full_name=f"{first_name} {last_name}",
            role=random.choices(
                [UserRole.REGULAR, UserRole.VERIFIED, UserRole.ADMIN],
                weights=[70, 25, 5]
            )[0],
            phone_number=f"+2547{random.randint(10000000, 99999999)}",
            is_active=random.choice([True] * 95 + [False] * 5),
            is_verified=random.choice([True] * 60 + [False] * 40),
            location=random.choice(KENYAN_CITIES + NAIROBI_LOCATIONS),
            created_at=generate_random_date(365, 30),
            last_login=generate_random_date(30, 0) if random.random() > 0.2 else None
        )
        user.set_password('TestPass123!')
        
        users.append(user)
    
    db.session.bulk_save_objects(users)
    db.session.commit()
    click.echo(f"✅ Created {len(users)} users")
    return users
