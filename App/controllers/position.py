from sqlalchemy import or_
from App.models import Position, Employer
from App.database import db

def _resolve_employer(identifier):
    """ Helper to resolve an employer by user_id (FK) or id (PK) """
    if identifier is None:
        return None
    return db.session.query(Employer).filter(or_(Employer.user_id==identifier,Employer.id==identifier)).first()

def open_position(title,user_id, number_of_positions=1):
    employer = _resolve_employer(user_id)
    if not employer:
        return False

    new_position = Position(title=title, number=number_of_positions, employer_id=employer.id)
    db.session.add(new_position)
    try:
        db.session.commit()
        return new_position
    except Exception as e:
        db.session.rollback()
        return False


def get_positions_by_employer(user_id):
    employer = _resolve_employer(user_id)
    if not employer:
        return []
    return db.session.query(Position).filter_by(employer_id=employer.id).all()

def get_all_positions_json():
    positions = Position.query.all()
    if positions:
        return [position.toJSON() for position in positions]
    return []

def get_positions_by_employer_json(user_id):
    employer = _resolve_employer(user_id)
    if not employer:
        return []
    positions = db.session.query(Position).filter_by(employer_id=employer.id).all()
    if positions:
        return [position.toJSON() for position in positions]
    return []