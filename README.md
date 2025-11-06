# FindMe Flask Application - Setup Guide

## Quick Start
### 1. Clone the code from github repo
```bash

git clone https://github.com/stansam/findme.git

```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On (git) bash:
source venv/bin/activate

# On Windows CMD:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Environment Configuration
Rename env.example to .env and configure the following environment variables:
- `SECRET_KEY` - Flask secret key for sessions
- `JWT_SECRET_KEY` - Flask secret key for JWT auth
- `MAIL_USERNAME` 
- `MAIL_PASSWORD`
- `TEST_ADMIN_PASSWORD` - Admin user password
- `TEST_USER1_PASSWORD` - Test user 1 password
- `TEST_USER2_PASSWORD` - Test user 2 password

### 4. Run the Application

```bash
# Initialize flask migrate and commit changes
flask db init
flask db migrate
flask db upgrade 

# Create Admin and Test Users
flask create-test-users

# Load default amounts
flask load-sample-data

# Customize amounts
flask load-sample-data --users 30 --persons 100 --sightings 200

# Check statistics
flask db-stats

# Clear all sample data (with confirmation)
flask clear-sample-data

# Run Application
flask run --debug
```

The application will be available at `http://127.0.0.1:5000`