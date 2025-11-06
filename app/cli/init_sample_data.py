import click
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.user import User
from app.models.missing_person import MissingPerson, PersonPhoto
from app.models.sighting import SightingReport, SightingPhoto
from app.models.audit import Notification, ActivityLog, Message, SystemSetting
from app.models.options import UserRole, MissingPersonStatus, ReportStatus
from flask import current_app
from app.cli.data.pools import SYSTEM_SETTINGS
from app.cli.data import (
    create_users, create_missing_persons, create_sighting_reports, create_notifications, 
    create_messages, create_activity_logs, create_system_settings
    )


@click.command('load-sample-data')
@click.option('--users', default=20, help='Number of users to create')
@click.option('--persons', default=50, help='Number of missing persons to create')
@click.option('--sightings', default=100, help='Number of sightings to create')
@click.option('--notifications', default=150, help='Number of notifications to create')
@click.option('--messages', default=80, help='Number of messages to create')
@click.option('--logs', default=200, help='Number of activity logs to create')
@with_appcontext
def load_sample_data(users, persons, sightings, notifications, messages, logs):
    """Load comprehensive sample data into the database."""
    
    click.echo("\n" + "="*60)
    click.echo(click.style("🚀 SAMPLE DATA LOADER", fg='cyan', bold=True))
    click.echo("="*60)
    
    if not click.confirm('\n⚠️  This will create sample data. Continue?'):
        click.echo("Operation cancelled.")
        return
    
    try:
        # Get existing test users or create new ones
        existing_users = User.query.all()
        if len(existing_users) < 3:
            click.echo("⚠️  Not enough users. Creating sample users first...")
            user_objects = create_users(users)
        else:
            user_objects = existing_users
            click.echo(f"ℹ️  Using {len(existing_users)} existing users")
        
        # Create missing persons
        person_objects = create_missing_persons(user_objects, persons)
        
        # Create sighting reports
        sighting_objects = create_sighting_reports(user_objects, person_objects, sightings)
        
        # Create notifications
        notification_objects = create_notifications(user_objects, person_objects, sighting_objects, notifications)
        
        # Create messages
        message_objects = create_messages(user_objects, person_objects, messages)
        
        # Create activity logs
        log_objects = create_activity_logs(user_objects, person_objects, sighting_objects, logs)
        
        # Create system settings
        create_system_settings()
        
        # Print summary
        click.echo("\n" + "="*60)
        click.echo(click.style("📊 SUMMARY", fg='cyan', bold=True))
        click.echo("="*60)
        click.echo(f"✅ Users: {len(user_objects)}")
        click.echo(f"✅ Missing Persons: {len(person_objects)}")
        click.echo(f"✅ Sighting Reports: {len(sighting_objects)}")
        click.echo(f"✅ Notifications: {len(notification_objects)}")
        click.echo(f"✅ Messages: {len(message_objects)}")
        click.echo(f"✅ Activity Logs: {len(log_objects)}")
        click.echo(f"✅ System Settings: {len(SYSTEM_SETTINGS)}")
        
        click.echo("\n" + "="*60)
        click.echo(click.style("🎉 Sample data loaded successfully!", fg='green', bold=True))
        click.echo("="*60 + "\n")
        
        current_app.logger.info("Sample data loading completed successfully")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during sample data loading: {str(e)}")
        click.echo(click.style(f"\n❌ Error: {str(e)}", fg='red'))
        click.echo("Sample data loading failed. Changes rolled back.")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during sample data loading: {str(e)}")
        click.echo(click.style(f"\n❌ Unexpected error: {str(e)}", fg='red'))
        click.echo("Sample data loading failed. Changes rolled back.")


@click.command('clear-sample-data')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def clear_sample_data(confirm):
    """Clear all sample data from the database (DANGEROUS!)."""
    
    click.echo("\n" + "="*60)
    click.echo(click.style("⚠️  CLEAR SAMPLE DATA", fg='red', bold=True))
    click.echo("="*60)
    
    click.echo("\n⚠️  WARNING: This will DELETE ALL data from:")
    click.echo("  - Activity Logs")
    click.echo("  - Notifications")
    click.echo("  - Messages")
    click.echo("  - Sighting Photos")
    click.echo("  - Sighting Reports")
    click.echo("  - Person Photos")
    click.echo("  - Missing Persons")
    click.echo("  - Users (except admin_user, verified_user, unverified_user)")
    click.echo("  - System Settings")
    
    if not confirm and not click.confirm('\n⚠️  Are you ABSOLUTELY sure? This cannot be undone!'):
        click.echo("Operation cancelled.")
        return
    
    if not confirm and not click.confirm('⚠️  Last chance. Really delete all data?'):
        click.echo("Operation cancelled.")
        return
    
    try:
        click.echo("\n🗑️  Clearing data...\n")
        
        # Delete in reverse order of dependencies
        activity_count = ActivityLog.query.delete()
        click.echo(f"✅ Deleted {activity_count} activity logs")
        
        notification_count = Notification.query.delete()
        click.echo(f"✅ Deleted {notification_count} notifications")
        
        message_count = Message.query.delete()
        click.echo(f"✅ Deleted {message_count} messages")
        
        sighting_photo_count = SightingPhoto.query.delete()
        click.echo(f"✅ Deleted {sighting_photo_count} sighting photos")
        
        sighting_count = SightingReport.query.delete()
        click.echo(f"✅ Deleted {sighting_count} sighting reports")
        
        person_photo_count = PersonPhoto.query.delete()
        click.echo(f"✅ Deleted {person_photo_count} person photos")
        
        person_count = MissingPerson.query.delete()
        click.echo(f"✅ Deleted {person_count} missing persons")
        
        # Delete users except test users
        test_usernames = ['admin_user', 'verified_user', 'unverified_user']
        user_count = User.query.filter(~User.username.in_(test_usernames)).delete(synchronize_session=False)
        click.echo(f"✅ Deleted {user_count} users (kept test users)")
        
        setting_count = SystemSetting.query.delete()
        click.echo(f"✅ Deleted {setting_count} system settings")
        
        db.session.commit()
        
        click.echo("\n" + "="*60)
        click.echo(click.style("🎉 All sample data cleared!", fg='green', bold=True))
        click.echo("="*60 + "\n")
        
        current_app.logger.info("Sample data cleared successfully")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during data clearing: {str(e)}")
        click.echo(click.style(f"\n❌ Error: {str(e)}", fg='red'))
        click.echo("Data clearing failed. Changes rolled back.")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during data clearing: {str(e)}")
        click.echo(click.style(f"\n❌ Unexpected error: {str(e)}", fg='red'))
        click.echo("Data clearing failed. Changes rolled back.")


@click.command('db-stats')
@with_appcontext
def show_db_stats():
    """Show current database statistics."""
    
    click.echo("\n" + "="*60)
    click.echo(click.style("📊 DATABASE STATISTICS", fg='cyan', bold=True))
    click.echo("="*60 + "\n")
    
    try:
        # Count records
        user_count = User.query.count()
        admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
        verified_user_count = User.query.filter_by(is_verified=True).count()
        
        person_count = MissingPerson.query.count()
        missing_count = MissingPerson.query.filter_by(status=MissingPersonStatus.MISSING).count()
        found_count = MissingPerson.query.filter_by(status=MissingPersonStatus.FOUND).count()
        
        sighting_count = SightingReport.query.count()
        pending_sighting = SightingReport.query.filter_by(status=ReportStatus.PENDING).count()
        verified_sighting = SightingReport.query.filter_by(status=ReportStatus.VERIFIED).count()
        
        notification_count = Notification.query.count()
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        message_count = Message.query.count()
        unread_messages = Message.query.filter_by(is_read=False).count()
        
        activity_count = ActivityLog.query.count()
        person_photo_count = PersonPhoto.query.count()
        sighting_photo_count = SightingPhoto.query.count()
        setting_count = SystemSetting.query.count()
        
        # Display statistics
        click.echo(click.style("👥 USERS", fg='yellow', bold=True))
        click.echo(f"  Total Users: {user_count}")
        click.echo(f"  Administrators: {admin_count}")
        click.echo(f"  Verified Users: {verified_user_count}")
        
        click.echo(f"\n{click.style('👤 MISSING PERSONS', fg='yellow', bold=True)}")
        click.echo(f"  Total Reports: {person_count}")
        click.echo(f"  Currently Missing: {missing_count}")
        click.echo(f"  Found: {found_count}")
        click.echo(f"  Photos: {person_photo_count}")
        
        click.echo(f"\n{click.style('👁️  SIGHTINGS', fg='yellow', bold=True)}")
        click.echo(f"  Total Reports: {sighting_count}")
        click.echo(f"  Pending Review: {pending_sighting}")
        click.echo(f"  Verified: {verified_sighting}")
        click.echo(f"  Photos: {sighting_photo_count}")
        
        click.echo(f"\n{click.style('🔔 NOTIFICATIONS', fg='yellow', bold=True)}")
        click.echo(f"  Total: {notification_count}")
        click.echo(f"  Unread: {unread_notifications}")
        
        click.echo(f"\n{click.style('💬 MESSAGES', fg='yellow', bold=True)}")
        click.echo(f"  Total: {message_count}")
        click.echo(f"  Unread: {unread_messages}")
        
        click.echo(f"\n{click.style('📊 OTHER', fg='yellow', bold=True)}")
        click.echo(f"  Activity Logs: {activity_count}")
        click.echo(f"  System Settings: {setting_count}")
        
        click.echo("\n" + "="*60 + "\n")
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving database stats: {str(e)}")
        click.echo(click.style(f"\n❌ Error: {str(e)}", fg='red'))


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(load_sample_data)
    app.cli.add_command(clear_sample_data)
    app.cli.add_command(show_db_stats)