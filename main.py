from flask import Flask, render_template
from application.database import db
from application.config import config
from application.model import *
from datetime import datetime


def create_app():
    app = Flask(__name__, template_folder='templates')
    
    app.config.from_object(config)
    app.config['DEBUG'] = True

    db.init_app(app)


    with app.app_context():
        db.create_all()  # This ensures the tables are created
        
        # Make sure to check the roles within the application context
        cust_role = User.query.filter_by(role='customer').first()
        if not cust_role:
            c = Customer(name='John', phone='123', city='abc', address='asgkjdchgkjh',)
            u = User(username='john', email='abc@gmail.com', role='customer', date_joined=datetime(2020, 1, 1), password = 'a', customer_det=c)
            db.session.add(u)
            
        sp_role = User.query.filter_by(role='service_professional').first()
        if not sp_role:
            sp = ServiceProfessional(name='John', phone='123', city='abc', service_category='Electrician', rating=4.5, experience=2, company_name='abc', status='approved', price_per_hour=100, user_id=1)
            u = User(username='shon', email='def@gmail.com', role='service_professional', date_joined=datetime(2020, 1, 1), password = 'b', service_professional_det=sp)
            db.session.add(u)

        sr = ServiceRequest.query.first()
        if not sr:
            sr = ServiceRequest(customer_id=1, service_professional_id=1, service_category_id=1, date_request=datetime(2020, 1, 1), date_completion=datetime(2020, 1, 2), status='completed', rating=4.5, feedback='good')
            db.session.add(sr)
        
        sc = ServiceCategory.query.first()
        if not sc:
            sc = ServiceCategory(name='Electrician', base_price=100, time_required=2, description='Electrician')
            db.session.add(sc)

        r = Review.query.first()
        if not r:
            r = Review(service_professional_id=1, customer_id=1, rating=4.5, feedback='good', date_review=datetime(2020, 1, 2), ServiceRequest_id=1)
            db.session.add(r)

        db.session.commit()
    return app

app = create_app()
from application.routes import *


if __name__ == '__main__':
    app.run(debug=True)
