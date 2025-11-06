import click
from app.extensions import db
from app.models.audit import Message
from datetime import timedelta
import random
from app.cli.data.utils import generate_random_date

def create_messages(users, missing_persons, count=80):
    """Create sample messages between users."""
    click.echo(f"\n💬 Creating {count} messages...")
    
    messages = []
    
    subjects = [
        'Question about missing person case',
        'Additional information',
        'Follow-up on sighting',
        'Request for clarification',
        'Update on case',
        'Thank you for your help',
        'Important information',
        'Case collaboration'
    ]
    
    bodies = [
        'Hello, I wanted to reach out regarding the case. I may have some additional information that could help.',
        'Thank you for submitting the report. Could you provide more details about what you saw?',
        'I noticed your sighting report and wanted to follow up. Are you available to discuss this further?',
        'I have some questions about the case. Can we arrange a time to talk?',
        'This is regarding the missing person case. I believe I have relevant information to share.',
        'Thank you for your cooperation. The information you provided has been very helpful.',
        'I wanted to update you on the progress of the investigation. Please let me know if you have questions.',
        'Could you please provide more details about the location and time? This would help significantly.'
    ]
    
    for i in range(count):
        sender = random.choice(users)
        receiver = random.choice([u for u in users if u.id != sender.id])
        
        person = random.choice(missing_persons) if random.random() > 0.4 else None
        
        is_read = random.choice([True] * 50 + [False] * 50)
        created = generate_random_date(90, 0)
        
        message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            subject=random.choice(subjects),
            body=random.choice(bodies),
            related_person_id=person.id if person else None,
            is_read=is_read,
            is_deleted_by_sender=random.choice([True] * 5 + [False] * 95),
            is_deleted_by_receiver=random.choice([True] * 5 + [False] * 95),
            created_at=created,
            read_at=created + timedelta(hours=random.randint(1, 72)) if is_read else None
        )
        
        messages.append(message)
    
    db.session.bulk_save_objects(messages)
    db.session.commit()
    
    click.echo(f"✅ Created {len(messages)} messages")
    return messages