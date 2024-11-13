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



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/customer/dashboard')
def customer_dashboard():
    user_id = session.get('user_id')  
    if not user_id:
        return redirect('/login')  
    customer = Customer.query.filter_by(user_id=user_id).first()  

    if not customer:
        return "Customer not found", 404

    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()

    return render_template('customer_dash.html', customer=customer, service_requests=service_requests)
 
@app.route('/customer/search_services', methods=['GET'])
def search_services():
    query = request.args.get('query', '')  # For name of the service professional
    city = request.args.get('city', '')    # For filtering by city
    service_category = request.args.get('service_category', '')  # For filtering by service category

    user_id = session.get('user_id')  # Get user ID from session
    customer = Customer.query.filter_by(user_id=user_id).first()  # Get customer details

    # Construct the query for service professionals
    query_filters = [ServiceProfessional.status == 'approved']  # Filter only approved service professionals

    if query:
        query_filters.append(ServiceProfessional.name.like(f'%{query}%'))
    if city:
        query_filters.append(ServiceProfessional.city.like(f'%{city}%'))
    if service_category:
        query_filters.append(ServiceProfessional.service_category.like(f'%{service_category}%'))

    # Apply filters to the query
    serviceprofessionals = ServiceProfessional.query.filter(*query_filters).all()

    return render_template('customer_dash.html', services=serviceprofessionals, query=query, city=city, service_category=service_category, customer=customer)

@app.route('/customer/orders')
def customer_orders():
    user_id = session.get('user_id')
    customer = Customer.query.filter_by(user_id=user_id).first()
    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    for request in service_requests:
        request.review = Review.query.filter_by(ServiceRequest_id=request.id).first()
    return render_template('customer_orders.html', service_requests=service_requests)

@app.route('/customer/profile')
def customer_profile():
    Customer_id = session.get('user_id')
    customer = Customer.query.filter_by(user_id=Customer_id).first()
    return render_template('customer_profile.html', customer=customer)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_customer():
    customer = Customer.query.get(1)  # Assuming you're fetching the customer by ID, you can modify this based on your context.

    if request.method == 'POST':
        # Update customer details based on form data
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.city = request.form['city']
        customer.address = request.form['address']
        customer.status = 'approved'

        # Commit the changes to the database
        db.session.commit()

        # Redirect to the profile page after updating
        return redirect(url_for('customer_profile'))

    # Render the profile page with customer data for GET request
    return render_template('profile.html', customer=customer)

@app.route('/submit_service_request', methods=['POST'])
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
    customer_id = session.get('user_id')  # Get customer ID
    
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

@app.route('/close_service_request/<int:request_id>', methods=['GET'])
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

@app.route('/edit_service_request/<int:request_id>', methods=['POST'])
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



@app.route('/submit_review/<int:request_id>', methods=['POST'])
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
            date_review=datetime.utcnow()
        )
        db.session.add(review)

    # Update rating in ServiceRequest for convenience
    #service_request.rating = rating
    db.session.commit()

    flash('Review has been successfully submitted!' if not review else 'Review has been updated!')
    return redirect(url_for('customer_orders'))


@app.route('/service_professional_dashboard')
def service_professional_dashboard():
    return render_template('service_professional_dash.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/registercustomer', methods=['GET', 'POST'])
def registercustomer():
    if request.method == 'GET':
        return render_template('register_customer.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
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
        
        elif not phone:
            flash('Please enter phone number')
            return redirect(url_for('registercustomer'))    
        
        elif not city:
            flash('Please enter city')
            return redirect(url_for('registercustomer'))    
        
        elif not name:
            flash('Please enter name')
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
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        email = request.form.get('email')
        role = 'service_professional'
        phone = request.form.get('phone')
        city = request.form.get('city')
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
    
        elif not email:
            flash('Please enter email')
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
        
        elif not phone:
            flash('Please enter phone number')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not city:
            flash('Please enter city')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not name:
            flash('Please enter name')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not service_category:
            flash('Please enter service category')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not experience:
            flash('Please enter experience')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not company_name:
            flash('Please enter company name')
            return redirect(url_for('registerserviceprofessional'))
        
        elif not price_per_hour:
            flash('Please enter price per hour')
            return redirect(url_for('registerserviceprofessional'))
        
        else:
            service_professional = ServiceProfessional(name=name, phone=phone, city=city, service_category=service_category, rating=rating, experience=experience, company_name=company_name, status=status, price_per_hour=price_per_hour, expenses_per_hour=expenses_per_hour)
            user = User(username=username, password=password, email=email, role=role, date_joined=date_joined, service_professional_det=service_professional)

            db.session.add(user)
            db.session.commit()
            flash('User registered successfully! Please wait for approval')
            return redirect(url_for('Login'))
        

@app.route('/manageusers')
def manageusers():
    service_categories = ServiceCategory.query.all()
    Customers = User.query.join(Customer).filter(User.role == 'customer').all()
    ServiceProfessionals = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status.in_(['approved', 'blacklisted']))
    ).all()
    
    pending_requests = User.query.join(ServiceProfessional).filter(
        (User.role == 'service_professional') & 
        (ServiceProfessional.status == 'pending')
    ).all()
    
    return render_template('admin_users.html', Customers=Customers, ServiceProfessionals=ServiceProfessionals, pending_requests=pending_requests, service_categories=service_categories)

@app.route('/baseprice')
def baseprice():
    service_categories = ServiceCategory.query.all()
    return render_template('baseprices.html', service_categories=service_categories)

@app.route('/managecategories')
def managecategories():
    service_categories = ServiceCategory.query.all()
    return render_template('admin_categories.html', service_categories=service_categories)


@app.route('/addcategory', methods=['GET', 'POST'])
def addcategory():
    if request.method == 'GET':
        return render_template('add_category.html')
    elif request.method == 'POST':
        name = request.form.get('name')
        base_price = float(request.form.get('base_price'))
        time_required = int(request.form.get('time_required'))
        description = request.form.get('description')
        status = 'active'

        service_category = ServiceCategory(name=name, base_price=base_price, time_required=time_required, description=description, status=status)
        db.session.add(service_category)
        db.session.commit()
        flash('Category added successfully')
        return redirect(url_for('managecategories'))

@app.route('/delcategory/<int:id>')
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
def editcategory(id):
    category = ServiceCategory.query.get_or_404(id)
    if request.method == 'POST' and category.status == 'active':
        category.name = request.form['name']
        category.base_price = request.form['base_price']
        category.time_required = request.form['time_required']
        category.description = request.form['description']
        category.status = 'active'
        
        try:
            db.session.commit()
            flash('Category updated successfully!', 'success')
        except:
            db.session.rollback()
            flash('Error updating category. Please try again.', 'danger')
        
    return redirect(url_for('managecategories')) 


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

        # Check the user's role and status based on their role
        if user.role == 'customer':
            status = Customer.query.filter_by(user_id=user.id).first().status
            if status == 'inactive':
                flash('Your account is blocked, Please contact admin')
                return redirect(url_for('Login'))

            session['role'] = 'customer'
            session['user_id'] = user.id
            return redirect(url_for('customer_dashboard'))

        elif user.role == 'service_professional':
            stat = ServiceProfessional.query.filter_by(user_id=user.id).first().status
            if stat == 'pending':
                flash('Your account is not approved yet')
                return redirect(url_for('Login'))
            elif stat == 'blacklisted':
                flash('Your account is blacklisted, Please contact admin')
                return redirect(url_for('Login'))

            session['role'] = 'service_professional'
            session['user_id'] = user.id
            return redirect(url_for('service_professional_dashboard'))

        elif user.role == 'admin':
            session['role'] = 'admin'
            session['user'] = user.username
            return redirect(url_for('admin_dashboard'))

        
        flash('Unexpected role, please contact support.')
        return redirect(url_for('Login'))
   

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('home'))


@app.route('/admin_summary')
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
def delete(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    
    if user.role == 'service_professional':
        service_professional = user.service_professional_det
        db.session.delete(service_professional)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted')
        return redirect(url_for('manageusers'))
    
@app.route('/activate/<int:id>')
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
def edit_service_pro(id):
    
    user = User.query.get(id)
    if not user:
        flash('User not found')
    service_pro = user.service_professional_det

    if request.method == 'POST':
        
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

        if not username or not name or not email or not phone or not city or not service_category or not experience or not company_name or not price_per_hour:
            flash('Please fill all the fields')
            return redirect(url_for('manageusers', id=id))
        
        user.username = username
        user.email = email

        
        service_pro.name = name
        service_pro.phone = phone
        service_pro.city = city
        service_pro.service_category = service_category
        service_pro.experience = int(experience)
        service_pro.company_name = company_name
        service_pro.price_per_hour = float(price_per_hour)
        service_pro.expenses_per_hour = int(float(expenses_per_hour)) if expenses_per_hour else 0

        
        db.session.commit()
        flash('Service Professional updated successfully!', 'success')

        return redirect(url_for('manageusers'))  

@app.route('/editcust/<int:id>', methods=['GET', 'POST'])
def editcustomer(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')

    customer = user.customer_det
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        city = request.form.get('city')
        address = request.form.get('address')

        if not username or not name or not email or not phone or not city or not address:
            flash('Please fill all the fields')
            return redirect(url_for('manageusers', id=id))
        
        user.username = username
        user.email = email

        customer.name = name
        customer.phone = phone
        customer.city = city
        customer.address = address

        db.session.commit()
        flash('Customer updated successfully!')

        return redirect(url_for('manageusers'))

    
