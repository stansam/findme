import click
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.extensions import db
from app.models.user import User
from app.models.options import UserRole
from flask import current_app
import os

@click.command('create-test-users')
@with_appcontext
def create_test_users():
    """Create three test users (admin, verified regular, and unverified regular)."""
    
    # Get passwords from environment variables
    admin_password = os.getenv('TEST_ADMIN_PASSWORD')
    user1_password = os.getenv('TEST_USER1_PASSWORD')
    user2_password = os.getenv('TEST_USER2_PASSWORD')
    
    # Validate that all passwords are set
    if not all([admin_password, user1_password, user2_password]):
        missing = []
        if not admin_password:
            missing.append('TEST_ADMIN_PASSWORD')
        if not user1_password:
            missing.append('TEST_USER1_PASSWORD')
        if not user2_password:
            missing.append('TEST_USER2_PASSWORD')
        
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        current_app.logger.error(error_msg)
        click.echo(click.style(f"❌ Error: {error_msg}", fg='red'))
        click.echo("Please set these variables in your .env file")
        return
    
    # Validate password strength
    min_password_length = 8
    for pwd_name, pwd_value in [
        ('TEST_ADMIN_PASSWORD', admin_password),
        ('TEST_USER1_PASSWORD', user1_password),
        ('TEST_USER2_PASSWORD', user2_password)
    ]:
        if len(pwd_value) < min_password_length:
            error_msg = f"{pwd_name} must be at least {min_password_length} characters long"
            current_app.logger.error(error_msg)
            click.echo(click.style(f"❌ Error: {error_msg}", fg='red'))
            return
    
    # Define test users
    test_users = [
        {
            'username': 'admin_user',
            'email': 'admin@findme.com',
            'password': admin_password,
            'full_name': 'Admin User',
            'role': UserRole.ADMIN,
            'phone_number': '+254700000001',
            'is_active': True,
            'is_verified': True,
            'location': 'Nairobi, Kenya'
        },
        {
            'username': 'verified_user',
            'email': 'verified@findme.com',
            'password': user1_password,
            'full_name': 'Verified Regular User',
            'role': UserRole.REGULAR,
            'phone_number': '+254700000002',
            'is_active': True,
            'is_verified': True,
            'location': 'Mombasa, Kenya'
        },
        {
            'username': 'unverified_user',
            'email': 'unverified@findme.com',
            'password': user2_password,
            'full_name': 'Unverified Regular User',
            'role': UserRole.REGULAR,
            'phone_number': '+254700000003',
            'is_active': True,
            'is_verified': False,
            'location': 'Kisumu, Kenya'
        }
    ]
    
    created_users = []
    skipped_users = []
    failed_users = []
    
    click.echo("\n🔄 Starting test user creation process...\n")
    
    for user_data in test_users:
        username = user_data['username']
        email = user_data['email']
        
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                current_app.logger.info(f"User '{username}' or email '{email}' already exists. Skipping.")
                skipped_users.append(username)
                click.echo(click.style(f"⏭️  Skipped: {username} (already exists)", fg='yellow'))
                continue
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                full_name=user_data['full_name'],
                role=user_data['role'],
                phone_number=user_data['phone_number'],
                is_active=user_data['is_active'],
                is_verified=user_data['is_verified'],
                location=user_data['location']
            )
            
            # Set password using the model's method
            new_user.set_password(user_data['password'])
            
            # Add to session and commit
            db.session.add(new_user)
            db.session.commit()
            
            created_users.append(username)
            role_display = "ADMIN" if new_user.is_admin() else "REGULAR"
            verified_display = "✓ Verified" if new_user.is_verified else "✗ Unverified"
            
            current_app.logger.info(f"Successfully created user: {username} ({role_display})")
            click.echo(click.style(
                f"✅ Created: {username} | {role_display} | {verified_display}",
                fg='green'
            ))
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error creating user '{username}': {str(e)}")
            failed_users.append(username)
            click.echo(click.style(
                f"❌ Failed: {username} (database integrity error)",
                fg='red'
            ))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating user '{username}': {str(e)}")
            failed_users.append(username)
            click.echo(click.style(
                f"❌ Failed: {username} (database error)",
                fg='red'
            ))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating user '{username}': {str(e)}")
            failed_users.append(username)
            click.echo(click.style(
                f"❌ Failed: {username} (unexpected error: {str(e)})",
                fg='red'
            ))
    
    # Print summary
    click.echo("\n" + "="*50)
    click.echo(click.style("📊 SUMMARY", fg='cyan', bold=True))
    click.echo("="*50)
    click.echo(f"✅ Created:  {len(created_users)} user(s)")
    click.echo(f"⏭️  Skipped:  {len(skipped_users)} user(s)")
    click.echo(f"❌ Failed:   {len(failed_users)} user(s)")
    
    if created_users:
        click.echo(f"\n🎉 Successfully created: {', '.join(created_users)}")
    
    if skipped_users:
        click.echo(f"\n⚠️  Skipped (already exist): {', '.join(skipped_users)}")
    
    if failed_users:
        click.echo(f"\n❗ Failed to create: {', '.join(failed_users)}")
        click.echo("Check the logs for more details.")
    
    click.echo("\n✨ Test user creation process completed!\n")
    current_app.logger.info(f"Test user creation completed. Created: {len(created_users)}, Skipped: {len(skipped_users)}, Failed: {len(failed_users)}")


@click.command('delete-test-users')
@with_appcontext
def delete_test_users():
    """Delete all test users created by create-test-users command."""
    
    test_usernames = ['admin_user', 'verified_user', 'unverified_user']
    
    click.echo("\n⚠️  WARNING: This will delete the following test users:")
    for username in test_usernames:
        click.echo(f"  - {username}")
    
    if not click.confirm('\nDo you want to continue?'):
        click.echo("Deletion cancelled.")
        return
    
    deleted_users = []
    not_found_users = []
    failed_users = []
    
    click.echo("\n🔄 Starting test user deletion process...\n")
    
    for username in test_usernames:
        try:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                current_app.logger.info(f"User '{username}' not found. Skipping.")
                not_found_users.append(username)
                click.echo(click.style(f"⏭️  Not found: {username}", fg='yellow'))
                continue
            
            db.session.delete(user)
            db.session.commit()
            
            deleted_users.append(username)
            current_app.logger.info(f"Successfully deleted user: {username}")
            click.echo(click.style(f"✅ Deleted: {username}", fg='green'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error deleting user '{username}': {str(e)}")
            failed_users.append(username)
            click.echo(click.style(
                f"❌ Failed: {username} (database error)",
                fg='red'
            ))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error deleting user '{username}': {str(e)}")
            failed_users.append(username)
            click.echo(click.style(
                f"❌ Failed: {username} (unexpected error: {str(e)})",
                fg='red'
            ))
    
    # Print summary
    click.echo("\n" + "="*50)
    click.echo(click.style("📊 SUMMARY", fg='cyan', bold=True))
    click.echo("="*50)
    click.echo(f"✅ Deleted:    {len(deleted_users)} user(s)")
    click.echo(f"⏭️  Not found:  {len(not_found_users)} user(s)")
    click.echo(f"❌ Failed:     {len(failed_users)} user(s)")
    
    if deleted_users:
        click.echo(f"\n🗑️  Successfully deleted: {', '.join(deleted_users)}")
    
    click.echo("\n✨ Test user deletion process completed!\n")
    current_app.logger.info(f"Test user deletion completed. Deleted: {len(deleted_users)}, Not found: {len(not_found_users)}, Failed: {len(failed_users)}")


def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(create_test_users)
    app.cli.add_command(delete_test_users)