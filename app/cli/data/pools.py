FIRST_NAMES_MALE = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph',
    'Thomas', 'Charles', 'Daniel', 'Matthew', 'Anthony', 'Donald', 'Mark', 'Paul',
    'Kevin', 'Brian', 'George', 'Edward', 'Samuel', 'Peter', 'Frank', 'Raymond'
]

FIRST_NAMES_FEMALE = [
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica',
    'Sarah', 'Karen', 'Nancy', 'Lisa', 'Betty', 'Margaret', 'Sandra', 'Ashley',
    'Dorothy', 'Kimberly', 'Emily', 'Donna', 'Michelle', 'Carol', 'Amanda', 'Melissa'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
    'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker'
]

KENYAN_CITIES = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Malindi',
    'Kitale', 'Garissa', 'Kakamega', 'Machakos', 'Meru', 'Nyeri', 'Kericho',
    'Naivasha', 'Kiambu', 'Bungoma', 'Kisii', 'Ruiru', 'Nanyuki'
]

NAIROBI_LOCATIONS = [
    'Westlands, Nairobi', 'Kilimani, Nairobi', 'Karen, Nairobi', 'Lavington, Nairobi',
    'Parklands, Nairobi', 'Eastleigh, Nairobi', 'South B, Nairobi', 'South C, Nairobi',
    'Kibera, Nairobi', 'Kasarani, Nairobi', 'Donholm, Nairobi', 'Embakasi, Nairobi',
    'Ngong Road, Nairobi', 'Kileleshwa, Nairobi', 'Upper Hill, Nairobi', 'CBD, Nairobi'
]

HAIR_COLORS = ['Black', 'Brown', 'Blonde', 'Red', 'Gray', 'White', 'Dark Brown', 'Light Brown']
EYE_COLORS = ['Brown', 'Blue', 'Green', 'Hazel', 'Gray', 'Amber', 'Dark Brown']
SKIN_TONES = ['Fair', 'Light', 'Medium', 'Olive', 'Tan', 'Brown', 'Dark Brown', 'Deep Brown']

DISTINGUISHING_FEATURES = [
    'Scar on left cheek', 'Tattoo on right arm', 'Birthmark on forehead',
    'Missing front tooth', 'Pierced ears', 'Scar above right eyebrow',
    'Tattoo on left shoulder', 'Mole on right cheek', 'Glasses wearer',
    'Birthmark on neck', 'Scar on chin', 'Dimples on both cheeks',
    'Crooked nose', 'Large forehead', 'Prominent chin'
]

CLOTHING_ITEMS = [
    'blue jeans and white t-shirt', 'red dress', 'black hoodie and gray pants',
    'green jacket and khaki pants', 'yellow shirt and blue jeans',
    'school uniform (white shirt, blue skirt)', 'brown jacket and black pants',
    'pink dress and white sandals', 'tracksuit (navy blue)', 'business suit (gray)',
    'traditional African attire', 'denim jacket and black jeans'
]

CIRCUMSTANCES = [
    'Left home in the morning and never returned',
    'Went to visit a friend and did not come back',
    'Disappeared after leaving school',
    'Last seen at a local market',
    'Went out for a walk and never returned',
    'Left home after an argument',
    'Disappeared while traveling to work',
    'Last seen at a bus stop',
    'Went missing during a family gathering',
    'Disappeared after leaving a shopping center'
]

NOTIFICATION_TYPES = [
    'new_sighting', 'report_verified', 'report_rejected', 'person_found',
    'message_received', 'status_update', 'system_alert'
]

ACTIVITY_ACTIONS = [
    'user_login', 'user_logout', 'report_created', 'report_updated',
    'sighting_submitted', 'sighting_verified', 'profile_updated',
    'photo_uploaded', 'search_performed', 'message_sent'
]

SYSTEM_SETTINGS = [
    {'key': 'site_name', 'value': 'FindMe Kenya', 'description': 'Name of the application'},
    {'key': 'admin_email', 'value': 'admin@findme.co.ke', 'description': 'Primary admin contact email'},
    {'key': 'max_photo_size', 'value': '5242880', 'description': 'Maximum photo size in bytes (5MB)'},
    {'key': 'photos_per_report', 'value': '5', 'description': 'Maximum photos per missing person report'},
    {'key': 'verification_required', 'value': 'true', 'description': 'Whether sightings require admin verification'},
    {'key': 'allow_anonymous_reports', 'value': 'true', 'description': 'Allow anonymous sighting reports'},
    {'key': 'search_radius_km', 'value': '50', 'description': 'Default search radius in kilometers'},
    {'key': 'notification_email_enabled', 'value': 'true', 'description': 'Enable email notifications'},
    {'key': 'maintenance_mode', 'value': 'false', 'description': 'Site maintenance mode status'},
    {'key': 'auto_archive_days', 'value': '365', 'description': 'Days before auto-archiving old cases'}
]