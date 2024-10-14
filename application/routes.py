from main import app
from flask import render_template, session, redirect, url_for, request, flash
from application.model import *
from datetime import datetime



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
            customer = Customer(name=name, phone=phone, city=city, address=address)
            user = User(username=username, password=password, email=email, role=role, date_joined=date_joined, customer_det=customer)

            db.session.add(user)
            db.session.commit()
            flash('User registered successfully')
            return redirect(url_for('Login'))



    
@app.route('/registerserviceprofessional', methods=['GET', 'POST'])
def registerserviceprofessional():
    if request.method == 'GET':
        return render_template('register_service_pro.html')
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
            if stat != 'approved':
                flash('Your account is not approved yet')
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
                return redirect(url_for('admin_dashboard'))
        
            
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('home'))