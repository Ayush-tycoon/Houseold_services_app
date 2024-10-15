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




@app.route('/')
def home():
    return render_template('home.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    return render_template('customer_dash.html')

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
        status = 'approved'

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


        elif user.role == 'service_professional':
            stat = ServiceProfessional.query.filter_by(user_id=user.id).first().status
            if stat == 'pending':
                flash('Your account is not approved yet')
                return redirect(url_for('Login'))
            elif stat == 'blacklisted':
                flash('Your account is blacklisted, Please contact admin')
                return redirect(url_for('Login'))

         
        else:
            if user.role =='customer':
                session['role'] = 'customer'
                session['user'] = user.username
                return redirect(url_for('customer_dashboard'))
            elif user.role =='service_professional':
                session['role'] = 'service_professional'
                session['user'] = user.username
                return redirect(url_for('service_professional_dashboard'))
            elif user.role =='admin':
                session['role'] = 'admin'
                session['user'] = user.username
                return redirect(url_for('admin_dashboard'))


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

        service_category = ServiceCategory(name=name, base_price=base_price, time_required=time_required, description=description)
        db.session.add(service_category)
        db.session.commit()
        flash('Category added successfully')
        return redirect(url_for('managecategories'))
    

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
    
@app.route('/decline/<int:id>')
def decline(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
        return redirect(url_for('manageusers'))
    
    service_professional = user.service_professional_det
    db.session.delete(service_professional)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted')
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