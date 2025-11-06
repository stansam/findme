import click
from app.extensions import db
from app.models.audit import Notification
from datetime import timedelta
import random
from app.cli.data.utils import generate_random_date
from app.cli.data.pools import NOTIFICATION_TYPES

def create_notifications(users, missing_persons, sightings, count=150):
    """Create sample notifications."""
    click.echo(f"\n🔔 Creating {count} notifications...")
    
    notifications = []
    
    notification_templates = {
        'new_sighting': 'New sighting reported for {person_name}',
        'report_verified': 'Your sighting report has been verified',
        'report_rejected': 'Your sighting report needs review',
        'person_found': '{person_name} has been found!',
        'message_received': 'You have a new message from {sender}',
        'status_update': 'Status update for {person_name}',
        'system_alert': 'System notification'
    }
    
    for i in range(count):
        user = random.choice(users)
        notif_type = random.choice(NOTIFICATION_TYPES)
        
        person = random.choice(missing_persons) if random.random() > 0.3 else None
        sighting = random.choice(sightings) if random.random() > 0.3 else None
        
        title_template = notification_templates.get(notif_type, 'Notification')
        
        if person:
            title = title_template.format(person_name=person.full_name, sender='Admin')
        else:
            title = title_template.format(person_name='Missing Person', sender='User')
        
        messages_content = [
            f"A new sighting has been reported. Please review the details.",
            f"Your report has been reviewed and verified by our team.",
            f"Thank you for your contribution. The information has been forwarded.",
            f"Important update regarding this case. Please check the details.",
            f"Your account has been updated. Please review the changes."
        ]
        
        is_read = random.choice([True] * 40 + [False] * 60)
        created = generate_random_date(60, 0)
        
        notification = Notification(
            user_id=user.id,
            title=title[:200],
            message=random.choice(messages_content),
            notification_type=notif_type,
            related_person_id=person.id if person else None,
            related_report_id=sighting.id if sighting else None,
            is_read=is_read,
            created_at=created,
            read_at=created + timedelta(hours=random.randint(1, 48)) if is_read else None
        )
        
        notifications.append(notification)
    
    db.session.bulk_save_objects(notifications)
    db.session.commit()
    
    click.echo(f"✅ Created {len(notifications)} notifications")
    return notifications

