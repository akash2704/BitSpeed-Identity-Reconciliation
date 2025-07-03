import os
from datetime import datetime
from enum import Enum
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Configuration ---
# Use DATABASE_URL from .env, fallback to SQLite file
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///contacts.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Optionally set Flask debug from env
if os.getenv('FLASK_DEBUG') is not None:
    app.config['DEBUG'] = bool(int(os.getenv('FLASK_DEBUG')))

db = SQLAlchemy(app)

# --- Model ---
class LinkPrecedenceEnum(str, Enum):
    primary = "primary"
    secondary = "secondary"

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    phoneNumber = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    linkedId = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=True)
    linkPrecedence = db.Column(db.Enum(LinkPrecedenceEnum), nullable=False, default=LinkPrecedenceEnum.primary)
    createdAt = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())
    updatedAt = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    deletedAt = db.Column(db.DateTime, nullable=True)

    @validates('email')
    def validate_email(self, key, value):
        return value.lower() if value else value

# --- DB Creation & Seeding ---
@app.before_request
def create_tables_and_seed():
    db.create_all()
    # Seed only if table is empty
    if not Contact.query.first():
        example = Contact(
            email='seed@example.com',
            phoneNumber='+11111111111',
            linkPrecedence=LinkPrecedenceEnum.primary
        )
        db.session.add(example)
        db.session.commit()

# --- Helper Functions ---
def consolidate_contacts(email, phone):
    """
    Find all contacts matching email or phone, and all their linked contacts.
    Returns (primary_contact, all_contacts_set)
    """
    q = Contact.query.filter(
        (Contact.email == email) | (Contact.phoneNumber == phone)
    )
    matches = q.all()
    if not matches:
        return None, set()
    # Find all linked contacts (recursively)
    all_contacts = set(matches)
    ids_to_search = set(c.id for c in matches)
    while True:
        new_links = Contact.query.filter(Contact.linkedId.in_(ids_to_search)).all()
        new_set = set(new_links) - all_contacts
        if not new_set:
            break
        all_contacts.update(new_set)
        ids_to_search = set(c.id for c in new_set)
    # Find all primaries
    primaries = [c for c in all_contacts if c.linkPrecedence == LinkPrecedenceEnum.primary]
    primary = min(primaries, key=lambda c: c.createdAt) if primaries else min(all_contacts, key=lambda c: c.createdAt)
    return primary, all_contacts

# --- Endpoint ---
@app.route('/identify', methods=['POST'])
def identify():
    data = request.get_json(force=True)
    email = data.get('email')
    phone = data.get('phoneNumber')
    if not email and not phone:
        abort(400, description="At least one of email or phoneNumber must be provided.")
    # Normalize
    email_norm = email.lower() if email else None
    phone_norm = phone
    # Find/consolidate
    primary, all_contacts = consolidate_contacts(email_norm, phone_norm)
    if not all_contacts:
        # Create new primary
        now = datetime.utcnow()
        new_contact = Contact(
            email=email_norm,
            phoneNumber=phone_norm,
            linkPrecedence=LinkPrecedenceEnum.primary,
            createdAt=now,
            updatedAt=now
        )
        db.session.add(new_contact)
        db.session.commit()
        response = {
            "contact": {
                "primaryContatctId": new_contact.id,
                "emails": [email_norm] if email_norm else [],
                "phoneNumbers": [phone_norm] if phone_norm else [],
                "secondaryContactIds": []
            }
        }
        return jsonify(response)
    # There are matches: consolidate
    # Gather all emails and phones
    all_contacts_list = list(all_contacts)
    all_contacts_list.sort(key=lambda c: (c.linkPrecedence != LinkPrecedenceEnum.primary, c.createdAt))
    emails = []
    phones = []
    secondary_ids = []
    seen_emails = set()
    seen_phones = set()
    for c in all_contacts_list:
        if c.email and c.email not in seen_emails:
            emails.append(c.email)
            seen_emails.add(c.email)
        if c.phoneNumber and c.phoneNumber not in seen_phones:
            phones.append(c.phoneNumber)
            seen_phones.add(c.phoneNumber)
        if c.linkPrecedence == LinkPrecedenceEnum.secondary:
            secondary_ids.append(c.id)
    # If new info, add as secondary
    known_emails = set(e for e in emails)
    known_phones = set(p for p in phones)
    new_secondary = None
    now = datetime.utcnow()
    if (email_norm and email_norm not in known_emails) or (phone_norm and phone_norm not in known_phones):
        new_secondary = Contact(
            email=email_norm if email_norm not in known_emails else None,
            phoneNumber=phone_norm if phone_norm not in known_phones else None,
            linkPrecedence=LinkPrecedenceEnum.secondary,
            linkedId=primary.id,
            createdAt=now,
            updatedAt=now
        )
        db.session.add(new_secondary)
        db.session.commit()
        if new_secondary.email:
            emails.append(new_secondary.email)
        if new_secondary.phoneNumber:
            phones.append(new_secondary.phoneNumber)
        secondary_ids.append(new_secondary.id)
    # Ensure only oldest is primary
    primaries = [c for c in all_contacts if c.linkPrecedence == LinkPrecedenceEnum.primary]
    if len(primaries) > 1:
        oldest = min(primaries, key=lambda c: c.createdAt)
        for c in primaries:
            if c != oldest:
                c.linkPrecedence = LinkPrecedenceEnum.secondary
                c.linkedId = oldest.id
                c.updatedAt = now
        db.session.commit()
        secondary_ids.extend([c.id for c in primaries if c != oldest])
    # Prepare response
    response = {
        "contact": {
            "primaryContatctId": primary.id,
            "emails": emails,
            "phoneNumbers": phones,
            "secondaryContactIds": secondary_ids
        }
    }
    return jsonify(response)

# --- Main Entrypoint ---
if __name__ == '__main__':
    app.run(debug=True)
