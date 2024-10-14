from application.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(80), nullable=False)
    date_joined = db.Column(db.DateTime, nullable=False)
    password = db.Column(db.String(80), nullable=False)

    # One-to-One relationship with Customer and ServiceProfessional
    customer_det = db.relationship('Customer', backref='user', lazy=True, uselist=False)
    service_professional_det = db.relationship('ServiceProfessional', backref='user', lazy=True, uselist=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to ServiceRequest (One-to-Many relationship)
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True)

class ServiceProfessional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    service_category = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    experience = db.Column(db.Integer, nullable=False)
    company_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(80), nullable=False)  # ('blacklisted', 'approved', 'pending')
    price_per_hour = db.Column(db.Float, nullable=False)
    expenses_per_hour = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to ServiceRequest (One-to-Many relationship)
    service_requests = db.relationship('ServiceRequest', backref='service_professional', lazy=True)

class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(80), nullable=False)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    service_professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)
    service_category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    date_request = db.Column(db.DateTime, nullable=False)
    date_completion = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(80), nullable=False)  # ('completed', 'requested', 'denied', 'in_progress')
    rating = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.String(400), nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    service_professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)
    ServiceRequest_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.String(400), nullable=True)
    date_review = db.Column(db.DateTime, nullable=False)

class AdminActions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_professional_id = db.Column(db.Integer, db.ForeignKey('service_professional.id'), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    date_action = db.Column(db.DateTime, nullable=False)
    remarks = db.Column(db.String(400), nullable=True)
