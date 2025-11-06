from datetime import datetime, timedelta
import random

def generate_random_date(start_days_ago, end_days_ago=0):
    """Generate a random datetime between start_days_ago and end_days_ago."""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()


def generate_coordinates(city):
    """Generate realistic coordinates for Kenyan cities."""
    coordinates = {
        'Nairobi': (-1.2921, 36.8219),
        'Mombasa': (-4.0435, 39.6682),
        'Kisumu': (-0.0917, 34.7680),
        'Nakuru': (-0.3031, 36.0800),
        'Eldoret': (0.5143, 35.2698),
    }
    
    base_coords = coordinates.get(city, (-1.2921, 36.8219))
    # Add small random offset (within ~10km)
    lat_offset = random.uniform(-0.05, 0.05)
    lon_offset = random.uniform(-0.05, 0.05)
    
    return (base_coords[0] + lat_offset, base_coords[1] + lon_offset)