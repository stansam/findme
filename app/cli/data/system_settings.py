import click
from app.extensions import db
from app.cli.data.pools import SYSTEM_SETTINGS
from app.models.audit import SystemSetting



def create_system_settings():
    """Create system settings."""
    click.echo(f"\n⚙️ Creating system settings...")
    
    created = 0
    for setting_data in SYSTEM_SETTINGS:
        existing = SystemSetting.query.filter_by(key=setting_data['key']).first()
        if not existing:
            setting = SystemSetting(**setting_data)
            db.session.add(setting)
            created += 1
    
    db.session.commit()
    click.echo(f"✅ Created {created} system settings")