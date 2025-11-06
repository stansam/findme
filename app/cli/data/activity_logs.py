import click
from app.extensions import db
from app.models.audit import  ActivityLog
import random
from app.cli.data.utils import generate_random_date
from app.cli.data.pools import ACTIVITY_ACTIONS

def create_activity_logs(users, missing_persons, sightings, count=200):
    """Create sample activity logs."""
    click.echo(f"\n📊 Creating {count} activity logs...")
    
    logs = []
    
    entity_types = ['missing_person', 'sighting_report', 'user', 'notification', 'message']
    
    ip_addresses = [
        f"41.90.{random.randint(1, 255)}.{random.randint(1, 255)}",  # Kenyan IPs
        f"197.248.{random.randint(1, 255)}.{random.randint(1, 255)}",
        f"105.163.{random.randint(1, 255)}.{random.randint(1, 255)}"
    ]
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
        'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    descriptions_map = {
        'user_login': 'User logged into the system',
        'user_logout': 'User logged out',
        'report_created': 'New missing person report created',
        'report_updated': 'Missing person report updated',
        'sighting_submitted': 'New sighting report submitted',
        'sighting_verified': 'Sighting report verified by admin',
        'profile_updated': 'User profile information updated',
        'photo_uploaded': 'Photo uploaded to report',
        'search_performed': 'Search query executed',
        'message_sent': 'Message sent to another user'
    }
    
    for i in range(count):
        user = random.choice(users) if random.random() > 0.1 else None
        action = random.choice(ACTIVITY_ACTIONS)
        entity_type = random.choice(entity_types)
        
        if entity_type == 'missing_person':
            entity_id = random.choice(missing_persons).id if missing_persons else None
        elif entity_type == 'sighting_report':
            entity_id = random.choice(sightings).id if sightings else None
        else:
            entity_id = random.choice(users).id if random.random() > 0.5 else None
        
        log = ActivityLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=descriptions_map.get(action, 'System action performed'),
            ip_address=random.choice(ip_addresses),
            user_agent=random.choice(user_agents),
            created_at=generate_random_date(90, 0)
        )
        
        logs.append(log)
    
    db.session.bulk_save_objects(logs)
    db.session.commit()
    
    click.echo(f"✅ Created {len(logs)} activity logs")
    return logs