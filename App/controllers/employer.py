from App import db
from App.models.employer import Employer
from App.models.user import User

def get_all_employers_info():
    """Returns a list of dictionaries with employer user_id and username."""
    employers = Employer.query.all()
    
    # We retrieve user_id and username via the relationship (assuming Employer model links to User model)
    # If Employer is the User, use .id and .username
    return [{
        'user_id': employer.user_id, # Assuming 'user_id' is the field linked to the main User table
        'username': employer.username,
        'employer_id': employer.id    # This is the ID in the specific Employer table
    } for employer in employers]