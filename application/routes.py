from main import app
from flask import render_template, session, redirect, url_for, request, flash
from application.model import *
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from flask import request, redirect, url_for, flash
from collections import defaultdict
import re
from flask_login import login_user, login_required, logout_user, current_user
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'Login'

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/Login', methods=['GET', 'POST'])
def Login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please enter username and password both')
            return redirect(url_for('Login'))

        user = User.query.filter_by(username=username).first() 

        if not user:
            flash('User not found, Register Please!')
            return redirect(url_for('Login'))

        elif user.password != password:
            flash('Password is incorrect')
            return redirect(url_for('Login'))
        
        login_user(user)

        # Check the user's role and status based on their role
        if user.role == 'customer':
            name = Customer.query.filter_by(user_id=user.id).first().name
            status = Customer.query.filter_by(user_id=user.id).first().status
            if status == 'inactive':
                flash('Your account is blocked, Please contact admin')
                return redirect(url_for('Login'))

            session['role'] = 'customer'
            session['user_id'] = user.id
            session['name'] = name
            return redirect(url_for('customer_dashboard'))

        elif user.role == 'service_professional':
            name = ServiceProfessional.query.filter_by(user_id=user.id).first().name
            stat = ServiceProfessional.query.filter_by(user_id=user.id).first().status
            if stat == 'pending':
                flash('Your account is not approved yet')
                return redirect(url_for('Login'))
            elif stat == 'blacklisted':
                flash('Your account is blacklisted, Please contact admin')
                return redirect(url_for('Login'))

            session['role'] = 'service_professional'
            session['user_id'] = user.id
            session['name'] = name
            
            service_prof = ServiceProfessional.query.filter_by(user_id=user.id).first() 
            review = Review.query.filter_by(service_professional_id=service_prof.id).all()
            if review:
                rating = sum([r.rating for r in review]) / len(review)
                service_professional = ServiceProfessional.query.filter_by(user_id=user.id).first()
                service_professional.rating = rating
                db.session.commit()
                
            category_status = ServiceCategory.query.filter_by(name=service_prof.service_category).first().status
            if category_status == 'inactive':
                flash('Your service category is inactive, Please contact admin')
                return redirect(url_for('Login'))
            return redirect(url_for('service_professional_dashboard'))

        elif user.role == 'admin':
            session['role'] = 'admin'
            session['user'] = user.username
            session['name'] = 'Admin Sir'
            return redirect(url_for('adminsummary'))

        
        flash('Unexpected role, please contact support.')
        return redirect(url_for('Login'))
    

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    user_id = session.get('user_id')  
    if not user_id:
        return redirect('/login')  
    customer = Customer.query.filter_by(user_id=user_id).first()  

    if not customer:
        return "Customer not found", 404

    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    categories = ServiceCategory.query.filter_by(status='active').all()

    return render_template('customer_dash.html', customer=customer, service_requests=service_requests, categories=categories)

 
@app.route('/customer/search_services', methods=['GET'])
@login_required
def search_services():
    # Retrieve and validate user input
    query = request.args.get('query', '').strip()
    city = request.args.get('city', '').strip()
    service_category = request.args.get('service_category', '').strip()

    # Validation
    errors = []
    if query and (len(query) > 50 or not query.replace(' ', '').isalpha()):
        errors.append("Query should be a maximum of 50 characters and contain only alphabets.")
    if city and (len(city) > 50 or not city.replace(' ', '').isalpha()):
        errors.append("City should be a maximum of 50 characters and contain only alphabets.")
    if service_category and len(service_category) > 50:
        errors.append("Invalid service category.")

    # If there are validation errors, flash messages and redirect
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('customer_dashboard'))  # Redirect to dashboard or a default page

    # Fetch user and related data
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to search services.", 'error')
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    customer = Customer.query.filter_by(user_id=user_id).first()
    if not customer:
        flash("Customer details not found.", 'error')
        return redirect(url_for('customer_dashboard'))

    categories = ServiceCategory.query.filter_by(status='active').all()

    # Construct query filters
    query_filters = [ServiceProfessional.status == 'approved']
    if query:
        query_filters.append(ServiceProfessional.name.like(f'%{query}%'))  # Case-insensitive match
    if city:
        query_filters.append(ServiceProfessional.city.like(f'%{city}%'))
    if service_category:
        query_filters.append(ServiceProfessional.service_category.like(f'%{service_category}%'))

    # Execute query with filters
    serviceprofessionals = ServiceProfessional.query.filter(*query_filters).all()

    # Render results in the customer dashboard
    return render_template(
        'customer_dash.html',
        services=serviceprofessionals,
        query=query,
        city=city,
        service_category=service_category,
        customer=customer,
        categories=categories
    )


@app.route('/customer/search_services_admin', methods=['GET'])
@login_required
def search_services_admin():
    query = request.args.get('name', '')  # For name of the service professional
    city = request.args.get('city', '')    # For filtering by city
    service_category = request.args.get('category', '')  # For filtering by service category
    Customers = User.query.join(Customer).filter(User.role == 'customer').all()
    pending_requests = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status == 'pending')
    ).all()

    #user_id = session.get('user_id')  # Get user ID from session

    # Construct the query for service professionals
    query_filters = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status.in_(['approved', 'blacklisted']))
    )  # Filter only approved service professionals

    if query:
        query_filters = query_filters.filter(ServiceProfessional.name.like(f'%{query}%'))
    if city:
        query_filters = query_filters.filter(ServiceProfessional.city.like(f'%{city}%'))
    if service_category:
        query_filters = query_filters.filter(ServiceProfessional.service_category.like(f'%{service_category}%'))

    # Apply filters to the query
    serviceprofessionals = query_filters.all()

    return render_template('admin_users.html', pending_requests=pending_requests, ServiceProfessionals=serviceprofessionals, query=query, city=city, category=service_category, Customers=Customers)


@app.route('/customer/orders')
@login_required
def customer_orders():
    user_id = session.get('user_id')
    customer = Customer.query.filter_by(user_id=user_id).first()
    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    for request in service_requests:
        request.review = Review.query.filter_by(ServiceRequest_id=request.id).first()
    return render_template('customer_orders.html', service_requests=service_requests)


@app.route('/customer/profile')
@login_required
def customer_profile():
    Customer_id = session.get('user_id')
    customer = Customer.query.filter_by(user_id=Customer_id).first()
    return render_template('customer_profile.html', customer=customer)


# @app.route('/profile/edit', methods=['GET', 'POST'])
# def edit_customer():
#     customer = Customer.query.get(1)  # Assuming you're fetching the customer by ID, you can modify this based on your context.

#     if request.method == 'POST':
#         # Update customer details based on form data
#         customer.name = request.form['name']
#         customer.phone = request.form['phone']
#         customer.city = request.form['city']
#         customer.address = request.form['address']
#         customer.status = 'approved'

#         # Commit the changes to the database
#         db.session.commit()

#         # Redirect to the profile page after updating
#         return redirect(url_for('customer_profile'))

#     # Render the profile page with customer data for GET request
#     return render_template('profile.html', customer=customer)


@app.route('/submit_service_request', methods=['POST'])
@login_required
def submit_service_request():
    service_professional_id = request.form['service_professional_id']
    
    # Set date_request to the current date and time
    date_request = datetime.now()
    
    # Parse date_completion from the form, ensure it is a valid datetime object
    date_completion_str = request.form['date_completion']
    date_completion = datetime.strptime(date_completion_str, '%Y-%m-%dT%H:%M')  # Convert to datetime object
    
    status = 'requested'
    rating = None
    feedback = request.form['feedback']
    
    # Assuming you have the customer ID in the session
    customer = Customer.query.filter_by(user_id=session.get('user_id')).first()  # Get customer ID
    customer_id = customer.id  # Set to None if no customer is found
    
    # Get the service professional's service category to fetch the associated ServiceCategory
    service_professional = ServiceProfessional.query.get(service_professional_id)
    service_category_name = service_professional.service_category
    
    # Fetch the ServiceCategory using the service category name
    service_category_obj = ServiceCategory.query.filter_by(name=service_category_name).first()
    service_category_id = service_category_obj.id if service_category_obj else None  # Set to None if no category is found
    
    # Create the service request in the database
    new_request = ServiceRequest(
        customer_id=customer_id,
        service_professional_id=service_professional_id,
        service_category_id=service_category_id,
        service_category=service_category_name,
        date_request=date_request,
        date_completion=date_completion,
        status=status,
        rating=rating,
        feedback=feedback
    )
    
    db.session.add(new_request)
    db.session.commit()

    # Redirect or show a confirmation message
    flash('Service request submitted successfully!', 'success')
    return redirect(url_for('customer_orders'))


@app.route('/edit_service_request/<int:request_id>', methods=['POST'])
@login_required
def edit_service_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Convert date_completion from form input to datetime object
    date_completion_str = request.form.get('date_completion')
    if date_completion_str:
        service_request.date_completion = datetime.strptime(date_completion_str, '%Y-%m-%dT%H:%M')
    
    # Update feedback
    service_request.feedback = request.form.get('feedback')
    
    db.session.commit()
    flash('Service request updated successfully', 'success')
    return redirect(url_for('customer_orders'))


@app.route('/close_service_request/<int:request_id>', methods=['GET'])
@login_required
def close_service_request(request_id):
    # Get the service request by its ID
    service_request = ServiceRequest.query.get(request_id)
    
    if service_request:
        try:
            # Delete the service request from the database
            db.session.delete(service_request)
            db.session.commit()
            flash('Service request closed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while closing the service request. Please try again.', 'danger')
    else:
        flash('Service request not found.', 'danger')
    
    # Redirect to the customer orders page
    return redirect(url_for('customer_orders'))


@app.route('/service_professional_dashboard')
@login_required
def service_professional_dashboard():
    user_id = session.get('user_id')
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    
    if not user_id:
        flash("Please log in to view your dashboard.", "danger")
        return redirect(url_for('Login'))  # Redirect to login if not authenticated

    # Get the service professional associated with the current user
    service_professional = ServiceProfessional.query.filter_by(user_id=user_id).first()
    if not service_professional:
        flash("Profile not found.", "danger")
        return redirect(url_for('Login'))  # Redirect if service professional is not found

    # Get the service requests assigned to the current service professional
    service_requests = ServiceRequest.query.filter_by(service_professional_id=service_professional.id).all()
    comsr= ServiceRequest.query.filter_by(service_professional_id=service_professional.id, status='completed').all()
    ids = [request.id for request in comsr]
    reviews = Review.query.filter(Review.ServiceRequest_id.in_(ids)).all()
    reviews_by_request_id = defaultdict(list)
    for review in reviews:
        reviews_by_request_id[review.ServiceRequest_id].append(review)

    return render_template('service_professional_dash.html', service_requests=service_requests, current_date=current_date, current_datetime=current_datetime, reviews_by_request_id=reviews_by_request_id)


@app.route('/service_professional/ratings', methods=['GET'])
@login_required
def service_professional_ratings():
    user_id = session.get('user_id')
    service_professional = ServiceProfessional.query.filter_by(user_id=user_id).first()
    reviews = Review.query.filter_by(service_professional_id=service_professional.id).all()
    if reviews:
        avg_rating = sum([r.rating for r in reviews]) / len(reviews)
        service_professional.rating = avg_rating 
        db.session.commit()
    
    # Get reviews along with the customer details
    reviews = db.session.query(Review, Customer).join(Customer, Customer.id == Review.customer_id).filter(Review.service_professional_id == service_professional.id).all()

    return render_template('service_professional_ratings.html', reviews=reviews, service_professional=service_professional)


@app.route('/accept_request/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    if service_request and (service_request.status == 'requested' or service_request.status == 'denied'):
        service_request.status = 'accepted'
        db.session.commit()
        flash('Service request accepted!', 'success')
    else:
        flash('Invalid request or already processed.', 'danger')
    return redirect(url_for('service_professional_dashboard'))


@app.route('/decline_request/<int:request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    service_request = ServiceRequest.query.get(request_id)
    if service_request and (service_request.status == 'requested' or service_request.status == 'accepted'):
        service_request.status = 'denied'
        db.session.commit()
        flash('Service request declined!', 'danger')
    else:
        flash('Invalid request or already processed.', 'danger')
    return redirect(url_for('service_professional_dashboard'))


@app.route('/start_work/<int:request_id>', methods=['POST'])
@login_required
def start_work(request_id):
    service_request = ServiceRequest.query.get(request_id)
    if service_request and service_request.status == 'accepted' and service_request.date_completion <= datetime.now():
        service_request.status = 'in_progress'
        service_request.date_request = datetime.now()
        db.session.commit()
        flash('Work started on the service request!', 'success')
    else:
        flash('Invalid request or cannot start work yet.', 'danger')
    return redirect(url_for('service_professional_dashboard'))


@app.route('/complete_service_request/<int:request_id>', methods=['GET', 'POST'])
@login_required
def complete_service_request(request_id):
    # Fetch the service request from the database using the request_id
    service_request = ServiceRequest.query.get(request_id)
    
    # Check if the service request exists and is in 'in_progress' status
    if service_request and service_request.status == 'payed':
        # Update the status to 'completed'
        service_request.status = 'completed'
        db.session.commit()  # Save the change to the database
        
        flash('Service request has been marked as completed!', 'success')
    else:
        flash('Invalid request or the service request is not in progress.', 'danger')
    
    return redirect(url_for('customer_orders'))  # Redirect to the customer orders page


@app.route('/submit_review/<int:request_id>', methods=['POST'])
@login_required
def submit_review(request_id):
    # Get form data
    rating = request.form.get('rating')
    feedback = request.form.get('feedback')
    
    # Fetch the service request
    service_request = ServiceRequest.query.get_or_404(request_id)

    # Check if a review already exists for this request
    review = Review.query.filter_by(ServiceRequest_id=request_id).first()
    
    if review:
        # Update existing review
        review.rating = rating
        review.feedback = feedback
        review.date_review = datetime.utcnow()
    else:
        # Create new review
        review = Review(
            customer_id=service_request.customer_id,
            service_professional_id=service_request.service_professional_id,
            ServiceRequest_id=request_id,
            rating=rating,
            feedback=feedback,
            date_review=datetime.now()
        )
        db.session.add(review)

    # Update rating in ServiceRequest for convenience
    #service_request.rating = rating
    db.session.commit()

    flash('Review has been successfully submitted!' if not review else 'Review has been updated!')
    return redirect(url_for('customer_orders'))


@app.route('/service_professional/profile')
@login_required
def service_professional_profile():
    user_id = session.get('user_id')
    service_professional = ServiceProfessional.query.filter_by(user_id=user_id).first()
    return render_template('service_professional_profile.html', service_professional=service_professional)


@app.route('/edit_servicepro_profile', methods=['POST'])
@login_required
def edit_servicepro_profile():
    # Get the current user's ID from the session
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to edit your profile.", "danger")
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    # Get the service professional associated with the current user
    service_professional = ServiceProfessional.query.filter_by(user_id=user_id).first()
    if not service_professional:
        flash("Profile not found.", "danger")
        return redirect(url_for('profile'))  # Replace 'profile' with the correct profile route name

    # Update service professional details from form data
    service_professional.name = request.form.get('name')
    service_professional.status = 'edited'
    service_professional.rating = service_professional.rating
    service_professional.phone = request.form.get('phone')
    service_professional.city = request.form.get('city')
    service_professional.service_category = request.form.get('category')
    service_professional.experience = request.form.get('experience')
    service_professional.company_name = request.form.get('company_name')
    service_professional.price_per_hour = float(request.form.get('price_per_hour', 0))
    service_professional.expenses_per_hour = float(request.form.get('expenses_per_hour', 0))

    # Save changes to the database
    try:
        db.session.commit()
        flash("After Admin approves the changes, you can start using the app again", "info")
        return redirect(url_for('logout'))  # Log out the user after updating the profile
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the profile.", "danger")
        print(e)  # For debugging purposes
        return redirect(url_for('service_professional_profile'))
    # Redirect back to the profile page
     

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/admin/search_customer', methods=['GET'])
@login_required
def search_customer():
    # Retrieve search parameters
    name = request.args.get('name1', '').strip()
    city = request.args.get('city1', '').strip()
    phone = request.args.get('phone1', '').strip()
    #flash("hi")
    # Validate inputs
    if name and (not name.isalpha()):
        flash("Name should only contain letters and spaces.", "light")
        return redirect(url_for('search_customer'))
    if city and not city.isalpha():
        flash("City should only contain letters and spaces.", "light")
        return redirect(url_for('search_customer'))
    if phone and (not phone.isdigit() or len(phone) != 10):
        flash("Phone number should be exactly 10 digits.", "light")
        return redirect(url_for('search_customer'))

    # Query service professionals for pending and approved statuses
    ServiceProfessionals = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status.in_(['approved', 'blacklisted']))
    ).all()
    pending_requests = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status == 'pending')
    ).all()

    # Base query for customers
    query = User.query.join(Customer).filter(User.role == 'customer')

    # Add filters based on validated search criteria
    if name:
        query = query.filter(Customer.name.like(f"%{name}%"))
    if city:
        query = query.filter(Customer.city.like(f"%{city}%"))
    if phone:
        query = query.filter(Customer.phone.like(f"%{phone}%"))

    # Execute the query to get filtered results
    filtered_customers = query.all()

    # Provide appropriate feedback
    if not filtered_customers:
        flash("No customers found matching the search criteria.", "light")
    else:
        flash(f"Found {len(filtered_customers)} customers.", "light")

    # Render the template with the filtered results
    return render_template(
        'admin_users.html',
        Customers=filtered_customers,
        name1=name,
        city1=city,
        phone1=phone,
        pending_requests=pending_requests,
        ServiceProfessionals=ServiceProfessionals
    )
    

@app.route('/registercustomer', methods=['GET', 'POST'])
def registercustomer():
    if request.method == 'GET':
        return render_template('register_customer.html')
    elif request.method == 'POST':
        username = request.form.get('username').strip()
        name = request.form.get('name').strip()
        password = request.form.get('password').strip()
        cpassword = request.form.get('cpassword').strip()
        email = request.form.get('email')
        role = 'customer'
        phone = request.form.get('phone')
        city = request.form.get('city')
        address = request.form.get('address')
        date_joined = datetime.now()
        status = 'active'

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('registercustomer'))
        
        elif " " in username:
            flash('Username should not contain spaces')
            return redirect(url_for('registercustomer'))
    
        elif not email:
            flash('Please enter email')
            return redirect(url_for('registercustomer'))
    
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('registercustomer'))
        
        elif not password or not cpassword:
            flash('Please enter password')
            return redirect(url_for('registercustomer'))

        elif password != cpassword:
            flash('Passwords do not match')
            return redirect(url_for('registercustomer'))
        
        elif not phone or len(phone) != 10:
            flash('Please enter valid phone number')
            return redirect(url_for('registercustomer'))    
        
        elif not city:
            flash('Please enter city')
            return redirect(url_for('registercustomer'))    
        
        elif not name or not name.replace(' ', '').isalpha():
            flash('Please enter a valid name')
            return redirect(url_for('registercustomer'))
        
        elif not address:
            flash('Please enter address')
            return redirect(url_for('registercustomer'))
        
        else:
            customer = Customer(name=name, phone=phone, city=city, address=address, status=status)
            user = User(username=username, password=password, email=email, role=role, date_joined=date_joined, customer_det=customer)

            db.session.add(user)
            db.session.commit()
            flash('User registered successfully')
            return redirect(url_for('Login'))

    
@app.route('/registerserviceprofessional', methods=['GET', 'POST'])
def registerserviceprofessional():
    service_categories = ServiceCategory.query.all()
    if request.method == 'GET':
        return render_template('register_service_pro.html', service_categories=service_categories)
    elif request.method == 'POST':
        username = request.form.get('username').strip()
        name = request.form.get('name').strip()
        password = request.form.get('password').strip()
        cpassword = request.form.get('cpassword').strip()
        email = request.form.get('email')
        role = 'service_professional'
        phone = request.form.get('phone')
        city = request.form.get('city').strip()
        service_category = request.form.get('service_category')
        rating = request.form.get('rating')
        date_joined = datetime.now()
        experience = request.form.get('experience')
        company_name = request.form.get('company_name')
        status = 'pending'
        price_per_hour = float(request.form.get('price_per_hour'))
        expenses_per_hour = float(request.form.get('expenses_per_hour') if request.form.get('expenses_per_hour') else 0)

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('registerserviceprofessional'))
        
        if " " in username:
            flash('Username should not contain spaces')
            return redirect(url_for('registerserviceprofessional'))
    
        elif not email or not "@" in email:
            flash('Please enter a valid email')
            return redirect(url_for('registerserviceprofessional'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not password or not cpassword:
            flash('Please enter password')
            return redirect(url_for('registerserviceprofessional'))
        
        elif password != cpassword: 
            flash('Passwords do not match')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not phone or len(phone) != 10:
            flash('Please enter a valid phone number')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not city:
            flash('Please enter city')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not name or not name.replace(' ', '').isalpha():
            flash('Please enter name')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not service_category or service_category=='Service Category':
            flash('Please enter a valid service category')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not experience or not experience.isnumeric():
            flash('Please enter experience in numbers')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not company_name:
            flash('Please enter company name')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not price_per_hour:
            flash('Please enter price per hour in rupees')
            return redirect(url_for('registerserviceprofessional'))
        
        else:
            service_professional = ServiceProfessional(name=name, phone=phone, city=city, service_category=service_category, rating=rating, experience=experience, company_name=company_name, status=status, price_per_hour=price_per_hour, expenses_per_hour=expenses_per_hour)
            user = User(username=username, password=password, email=email, role=role, date_joined=date_joined, service_professional_det=service_professional)

            db.session.add(user)
            db.session.commit()
            flash('User registered successfully! Please wait for approval')
            return redirect(url_for('Login'))
        

@app.route('/manageusers')
@login_required
def manageusers():
    service_categories = ServiceCategory.query.all()
    Customers = User.query.join(Customer).filter(User.role == 'customer').all()
    ServiceProfessionals = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status.in_(['approved', 'blacklisted']))
    ).all()
    
    pending_requests = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status == 'pending') | (ServiceProfessional.status == 'edited')
    ).all()
    
    return render_template('admin_users.html', Customers=Customers, ServiceProfessionals=ServiceProfessionals, pending_requests=pending_requests, service_categories=service_categories)


@app.route('/baseprice')
def baseprice():
    service_categories = ServiceCategory.query.all()
    return render_template('baseprices.html', service_categories=service_categories)


@app.route('/managecategories')
@login_required
def managecategories():
    service_categories = ServiceCategory.query.all()
    return render_template('admin_categories.html', service_categories=service_categories)


@app.route('/addcategory', methods=['GET', 'POST'])
@login_required
def addcategory():
    if request.method == 'GET':
        return render_template('add_category.html')
    elif request.method == 'POST':
        name = request.form.get('name', '').strip()
        base_price = request.form.get('base_price', '').strip()
        time_required = request.form.get('time_required', '').strip()
        description = request.form.get('description', '').strip()

        # Server-side validation
        errors = []
        if not name or not (3 <= len(name) <= 50) or not name.replace(' ', '').isalpha():
            errors.append("Category name must be 3-50 letters long and contain letters only.")
        if not base_price or not base_price.isnumeric() or not (1 <= float(base_price) <= 100000):
            errors.append("Base price must be a number between 1 and 100,000.")
        if not time_required or not time_required.isnumeric() or not (1 <= int(time_required) <= 1440):
            errors.append("Time required must be a number between 1 and 1440 minutes.")
        if not description or not (10 <= len(description) <= 500):
            errors.append("Description must be between 10 and 500 characters.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('addcategory'))

        # Add to database
        service_category = ServiceCategory(
            name=name, 
            base_price=float(base_price), 
            time_required=int(time_required), 
            description=description, 
            status='active'
        )
        db.session.add(service_category)
        db.session.commit()
        flash('Category added successfully', 'success')
        return redirect(url_for('managecategories'))


@app.route('/delcategory/<int:id>')
@login_required
def deletecategory(id):
    service_category = ServiceCategory.query.get(id)
    if not service_category:
        flash('Category not found')
    else:
        update = service_category.status = 'inactive'
        db.session.commit()
        flash('Category deleted')
        return redirect(url_for('managecategories'))

    
@app.route('/actcategory/<int:id>')
@login_required
def activecategory(id):
    service_category = ServiceCategory.query.get(id)
    if not service_category:
        flash('Category not found')
    else:
        update = service_category.status = 'active'
        db.session.commit()
        flash('Category Activated')
        return redirect(url_for('managecategories'))   

    
@app.route('/editcategory/<int:id>', methods=['POST'])
@login_required
def editcategory(id):
    category = ServiceCategory.query.get_or_404(id)

    if category.status != 'active':
        flash('Category must be active to edit.', 'danger')
        return redirect(url_for('managecategories'))

    # Get form data
    name = request.form.get('name', '').strip()
    base_price = request.form.get('base_price', '').strip()
    time_required = request.form.get('time_required', '').strip()
    description = request.form.get('description', '').strip()

    # Validate inputs
    errors = []
    if not name or not (3 <= len(name) <= 50) or not name.replace(' ', '').isalpha():
        errors.append("Category name must be 3-50 letters long and contain only letters.")
    if not base_price or not base_price.isnumeric() or not (1 <= float(base_price) <= 100000):
        errors.append("Base price must be a number between 1 and 100,000.")
    if not time_required or not time_required.isnumeric() or not (1 <= int(time_required) <= 1440):
        errors.append("Time required must be a number between 1 and 1440 minutes.")
    if not description or not (10 <= len(description) <= 500):
        errors.append("Description must be between 10 and 500 characters.")

    # Handle errors
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('managecategories'))

    # Update category
    try:
        category.name = name
        category.base_price = float(base_price)
        category.time_required = int(time_required)
        category.description = description
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating category. Please try again.', 'danger')

    return redirect(url_for('managecategories'))

   
# @app.route('/logout')
# def logout():
#     session.pop('user', None)
#     session.pop('role', None)
#     return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    session.pop('role', None)
    session.pop('name', None)
    session.pop('user_id', None)
    logout_user()
    return redirect(url_for('Login'))


@app.route('/admin_summary')
@login_required
def adminsummary():

    users = User.query.all()
    service_pros = ServiceProfessional.query.all()

    roles = [user.role for user in users]
    ratings = [sp.rating for sp in service_pros if sp.rating is not None]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), dpi=80)

    sns.countplot(x=roles, ax=ax1)
    ax1.set_title("User Roles Distribution")

    sns.histplot(ratings, bins=10, kde=True, ax=ax2)
    ax2.set_title("Service Professionals' Ratings Distribution")

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    plot_url1 = base64.b64encode(img.getvalue()).decode()

    plt.close(fig) 

    return render_template('admin_summary.html', plot_url=plot_url1)


@app.route('/approve/<int:id>')
@login_required
def approve(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
    else:
        user.service_professional_det.status = 'approved'
        db.session.commit()
        flash('User approved')
        return redirect(url_for('manageusers'))

    
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    
    service_professional = user.service_professional_det
    if user.role == 'service_professional' and user.service_professional_det.status == 'pending':
        
        db.session.delete(service_professional)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted')
        return redirect(url_for('manageusers'))
    elif user.role == 'service_professional' and user.service_professional_det.status == 'edited':

        service_professional.status = 'approved'
        db.session.commit()
        flash('User deleted')
        return redirect(url_for('manageusers'))

    
@app.route('/activate/<int:id>')
@login_required
def active(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    user.customer_det.status = 'active'
    db.session.commit()
    flash('User activated')
    return redirect(url_for('manageusers'))

    
@app.route('/inactive/<int:id>')
@login_required
def inactive(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    user.customer_det.status = 'inactive'
    db.session.commit()
    flash('User inactivated')
    return redirect(url_for('manageusers'))


@app.route('/blacklist/<int:id>')
@login_required
def blacklist(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    
    service_professional = user.service_professional_det
    service_professional.status = 'blacklisted'
    db.session.commit()
    flash('User blacklisted')
    return redirect(url_for('manageusers'))


@app.route('/edit_service_pro/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service_pro(id):
    # Retrieve the user by ID
    user = User.query.get(id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('manageusers'))

    service_pro = user.service_professional_det
    if not service_pro:
        flash('Service Professional details not found', 'error')
        return redirect(url_for('manageusers'))

    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        service_category = request.form.get('service_category')
        experience = request.form.get('experience')
        company_name = request.form.get('company_name')
        price_per_hour = request.form.get('price_per_hour')
        expenses_per_hour = request.form.get('expenses_per_hour')

        # Validate input fields
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not name or len(name) < 2 and not name.isalpha():
            errors.append('Name must be at least 2 characters long and contain only letters.')
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append('Invalid email address.')
        if not phone or not re.match(r"^\d{10}$", phone):
            errors.append('Phone number must be exactly 10 digits.')
        if not city or len(city) < 2:
            errors.append('City name must be at least 2 characters long.')
        if not service_category:
            errors.append('Service category is required.')
        if not experience or not experience.isdigit() or int(experience) < 0:
            errors.append('Experience must be a positive integer.')
        if not company_name or len(company_name) < 2:
            errors.append('Company name must be at least 2 characters long.')
        try:
            if not price_per_hour or float(price_per_hour) <= 0:
                errors.append('Price per hour must be a positive number.')
        except ValueError:
            errors.append('Price per hour must be a valid number.')
        try:
            if expenses_per_hour and float(expenses_per_hour) < 0:
                errors.append('Expenses per hour must not be negative.')
        except ValueError:
            errors.append('Expenses per hour must be a valid number.')

        # If there are errors, flash them and redirect to the edit page
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('edit_service_pro', id=id))

        # Update user and service professional details
        user.username = username
        user.email = email
        service_pro.name = name
        service_pro.phone = phone
        service_pro.city = city
        service_pro.service_category = service_category
        service_pro.experience = int(experience)
        service_pro.company_name = company_name
        service_pro.price_per_hour = float(price_per_hour)
        service_pro.expenses_per_hour = float(expenses_per_hour) if expenses_per_hour else 0

        # Save changes to the database
        try:
            db.session.commit()
            flash('Service Professional updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating Service Professional: {str(e)}', 'error')

        return redirect(url_for('manageusers'))

    # Render the edit form with current user and service professional details
    return redirect(url_for('manageusers'))


@app.route('/editcust/<int:id>', methods=['GET', 'POST'])
@login_required
def editcustomer(id):
    # Retrieve the user by ID
    user = User.query.get(id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('manageusers'))

    customer = user.customer_det
    if not customer:
        flash('Customer details not found', 'error')
        return redirect(url_for('manageusers'))

    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        address = request.form.get('address')
        
        use = User.query.filter_by(username=username).first()
        if use and session['role']=='customer':
            flash('Username already exists')
            Customer_id = session.get('user_id')
            customer = Customer.query.filter_by(user_id=Customer_id).first()
            return render_template('customer_profile.html', customer=customer)
        elif use and session['role']=='admin':
            flash('Username already exists')
            return redirect(url_for('manageusers', id=id))

        # Validation
        errors = []
        if not username or len(username) < 3 and not name.isalpha():
            errors.append('Username must be at least 3 characters long.')
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters long.')
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append('Invalid email address.')
        if not phone or not re.match(r"^\d{10}$", phone):
            errors.append('Phone number must be exactly 10 digits.')
        if not city or len(city) < 2:
            errors.append('City name must be at least 2 characters long.')
        if not address or len(address) < 5:
            errors.append('Address must be at least 5 characters long.')

        # If errors exist, flash them and redirect back to the form
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('editcustomer', id=id))

        # Update user and customer details
        user.username = username
        user.email = email
        customer.name = name
        customer.phone = phone
        customer.city = city
        customer.address = address

        # Commit changes to the database
        try:
            db.session.commit()
            flash('Customer updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'error')
            
        if session['role'] == 'admin':
            return redirect(url_for('manageusers'))
        elif session['role'] == 'customer':
            Customer_id = session.get('user_id')
            customer = Customer.query.filter_by(user_id=Customer_id).first()
            use = User.query.get(customer.user_id).username
            return render_template('customer_profile.html', customer=customer, username=use)
    
    # Render the edit form with current user details
    if session['role'] == 'admin':
        return redirect(url_for('manageusers'))
    elif session['role'] == 'customer':
        Customer_id = session.get('user_id')
        customer = Customer.query.filter_by(user_id=Customer_id).first()
        return render_template('customer_profile.html', customer=customer)


@app.route('/payment/<int:service_request_id>', methods=['GET', 'POST'])
@login_required
def payment(service_request_id):
    # Get the service request data based on ID
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    customer = Customer.query.get(service_request.customer_id)
    service_professional = ServiceProfessional.query.get(service_request.service_professional_id)
    category = ServiceCategory.query.get(service_request.service_category_id) if service_request.service_category_id else None

    return render_template('payment.html', service_request=service_request, customer=customer, 
                           service_professional=service_professional, category=category)
    
@app.route('/payment_success/<int:service_request_id>', methods=['POST'])
@login_required
def payment_success(service_request_id):
    # Get the service request data based on ID
    service_request = ServiceRequest.query.get_or_404(service_request_id)
    # Update the service request status to 'paid'
    service_request.status = 'payed'
    db.session.commit()

    flash('Payment successful!', 'success')
    return redirect(url_for('customer_orders'))