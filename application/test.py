from application.model import User, Customer
from application.database import db
from datetime import datetime

# Create a new Customer
c = Customer(name='John', phone='123', city='abc')

# Create a new User and associate the Customer
u = User(username='john', email='abc@gmail.com', role='customer', date_joined=datetime(2020, 1, 1), customer_det=c)

# Add both to the session and commit to the database
db.session.add(u)
db.session.commit()
