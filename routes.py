from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from models import db, Vehicle, User, Service, Admin, ServiceHistory, Payment, BookingSlot, SlotBooking, SlotSettings, NonWorkingDay
from datetime import datetime, timedelta, date
import json
from dateutil.relativedelta import relativedelta
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from forms import LoginForm, CustomerRegisterForm, AdminRegisterForm, VehicleForm, ServiceForm, ServiceUpdateForm, PaymentForm, ServiceFilterForm
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "select_user" 
# Add template filter
@app.template_filter('is_admin')
def is_admin(user):
    return isinstance(user, Admin)

@app.route('/',methods=['GET','POST'])
def landing_page():
    return send_from_directory('landing-page', 'index.html')

@app.route('/select_user',methods=['GET','POST'])
def select_user():
    return render_template('select_user.html')

@app.route('/login_customer', methods=['GET', 'POST'])
def login_customer():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('customer_dashboard'))
            else:
                flash("Invalid email or password", "danger")
        else:
            flash("No account found with this email", "danger")
    return render_template('login_customer.html', form=form)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    form = LoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('dashboard_admin'))
            else:
                flash("Invalid email or password", "danger")
        else:
            flash("No admin account found with this email", "danger")
    return render_template('login_admin.html', form=form)
@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if isinstance(current_user, Admin):
        return redirect(url_for('dashboard_admin'))
    vehicles = Vehicle.query.filter_by(user_id=current_user.real_id).all()
    upcoming_services = Service.query.filter_by(user_id=current_user.real_id).filter(Service.status.in_(['pending', 'in_progress'])).all()
    return render_template('customer/dashboard.html', vehicles=vehicles, upcoming_services=upcoming_services)

@app.route('/dashboard_admin', methods=['GET', 'POST'])
@login_required
def dashboard_admin():
    if not isinstance(current_user, Admin):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('select_user'))
    
    form = ServiceUpdateForm()
    services = Service.query.options(db.joinedload(Service.user), db.joinedload(Service.vehicle)).all()
    
    if form.validate_on_submit():
        service_id = request.form.get('service_id')
        service = Service.query.get_or_404(service_id)
        
        service.status = form.status.data
        service.actual_date = form.actual_date.data
        service.cost = form.cost.data
        service.odometer_reading = form.odometer_reading.data
        service.notes = form.notes.data
        
        if form.status.data == 'completed':
            service.vehicle.last_service_date = service.actual_date
            service.vehicle.next_service_date = service.actual_date + relativedelta(months=6)
        
        history = ServiceHistory(
            service_id=service.id,
            status=form.status.data,
            notes=f'Status updated to {form.status.data} by admin'
        )
        
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('dashboard_admin'))
    
    return render_template('admin/dashboard.html', services=services, form=form)

@app.route('/view_vehicles')
@login_required
def view_vehicles():
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to view vehicles.', 'warning')
            return redirect(url_for('select_user'))
        
        # Admin sees all vehicles
        if isinstance(current_user, Admin):
            vehicles = Vehicle.query.all()
            return render_template('admin/vehicles.html', vehicles=vehicles)
        
        # Customer sees only their vehicles
        # Get the real user ID (integer)
        user_id = current_user.real_id if hasattr(current_user, 'real_id') else current_user.id
        
        # Make sure we have an integer ID
        if isinstance(user_id, str):
            if user_id.startswith('user_'):
                user_id = int(user_id.replace('user_', ''))
            else:
                user_id = int(user_id)
        
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        return render_template('customer/view_vehicles.html', vehicles=vehicles)
        
    except Exception as e:
        # Return error details for debugging
        import traceback
        error_details = traceback.format_exc()
        return f"""
        <h1>500 Internal Server Error</h1>
        <h2>Error Details:</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <h3>Traceback:</h3>
        <pre>{error_details}</pre>
        <p><a href="/select_user">← Back to Login</a></p>
        """

@app.route('/view_services')
@login_required
def view_services():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.order_by(Service.scheduled_date).all()
        return render_template('admin/services.html', services=services)
    # For regular users, show their services using the real database ID
    user_id = current_user.real_id if hasattr(current_user, 'real_id') else current_user.id
    services = Service.query.filter_by(user_id=user_id).order_by(Service.scheduled_date).all()
    # Add debugging info
    print(f"Customer ID: {user_id}, Found {len(services)} services")
    for service in services:
        print(f"Service ID: {service.id}, Status: {service.status}, Type: {service.service_type}")
    return render_template('customer/services.html', services=services)

@app.route('/service_history')
@login_required
def service_history():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.order_by(Service.scheduled_date.desc()).all()
        return render_template('admin/history.html', services=services)
    # For regular users, show their service history
    services = Service.query.filter_by(user_id=current_user.real_id).order_by(Service.scheduled_date.desc()).all()
    return render_template('customer/history.html', services=services)

@app.route('/view_payments')
@login_required
def view_payments():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.filter(Service.cost.isnot(None)).order_by(Service.scheduled_date.desc()).all()
        return render_template('admin/payments.html', services=services)
    # For regular users, show their payments
    services = Service.query.filter_by(user_id=current_user.real_id).filter(Service.cost.isnot(None)).order_by(Service.scheduled_date.desc()).all()
    return render_template('customer/payments.html', services=services)

@app.route('/service_details/<int:service_id>', methods=['GET', 'POST'])
@login_required
def service_details(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check if user has permission to view the service
    if not isinstance(current_user, Admin) and service.user_id != current_user.real_id:
        flash('You do not have permission to view this service.', 'error')
        return redirect(url_for('view_services'))
    
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        # For customers, only allow updating notes
        if not isinstance(current_user, Admin):
            service.notes = form.notes.data
            history = ServiceHistory(
                service_id=service.id,
                status=service.status,
                notes=f'Customer updated notes: {form.notes.data}'
            )
        else:
            # Admin can update all fields
            service.status = form.status.data
            service.actual_date = form.actual_date.data
            service.cost = form.cost.data
            service.odometer_reading = form.odometer_reading.data
            service.notes = form.notes.data
            
            if form.status.data == 'completed':
                service.vehicle.last_service_date = service.actual_date
                service.vehicle.next_service_date = service.actual_date + relativedelta(months=6)
            
            history = ServiceHistory(
                service_id=service.id,
                status=form.status.data,
                notes=f'Status updated to {form.status.data}'
            )
        
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('service_details', service_id=service_id))
    
    # Use different templates for admin and customer
    template = 'admin/service_details.html' if isinstance(current_user, Admin) else 'customer/service_details.html'
    return render_template(template, service=service, form=form)

@app.route('/delete_vehicle/<int:vehicle_id>')
@login_required
def delete_vehicle(vehicle_id):
    vehicle_to_delete = Vehicle.query.get_or_404(vehicle_id)
    # Ensure the vehicle belongs to the current user
    if vehicle_to_delete.user_id != current_user.real_id:
        flash('You do not have permission to delete this vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))
    try:
        db.session.delete(vehicle_to_delete)
        db.session.commit()
        flash('Vehicle deleted successfully!', 'success')
        return redirect(url_for('view_vehicles'))
    except:
        flash('There was an error deleting the vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))

@app.route('/update_vehicle/<int:vehicle_id>', methods=["GET", "POST"])
@login_required
def update_vehicle(vehicle_id):
    vehicle_to_update = Vehicle.query.get_or_404(vehicle_id)
    # Ensure the vehicle belongs to the current user
    if vehicle_to_update.user_id != current_user.real_id:
        flash('You do not have permission to update this vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))
    
    form = VehicleForm(obj=vehicle_to_update)
    
    if form.validate_on_submit():
        try:
            vehicle_to_update.model = form.model.data
            vehicle_to_update.year = form.year.data
            vehicle_to_update.odo_reading = form.odo_reading.data
            vehicle_to_update.license_plate = form.license_plate.data
            vehicle_to_update.vin = form.vin.data
            if form.notes.data:  # Only update notes if provided
                vehicle_to_update.notes = form.notes.data

            db.session.commit()
            flash('Vehicle updated successfully!', 'success')
            return redirect(url_for('view_vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error updating the vehicle: {str(e)}', 'danger')
            return redirect(url_for('update_vehicle', vehicle_id=vehicle_id))
    
    return render_template('customer/update_vehicle.html', vehicle=vehicle_to_update, form=form)

@app.route('/update_customer', methods=["GET", "POST"])
@login_required
def update_user_details():
    if not isinstance(current_user, User):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    user = User.query.get_or_404(current_user.real_id)

    if request.method == "POST":
        try:
            user.name = request.form['name']
            user.phone = request.form['phone']
            user.address = request.form['address']
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('update_user_details'))

    return render_template('customer/update_customer.html', user=user)

@app.route('/book_service/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_service(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Check if vehicle belongs to current user
    user_id = current_user.real_id if hasattr(current_user, 'real_id') else current_user.id
    if vehicle.user_id != user_id:
        flash('You can only book services for your own vehicles.', 'danger')
        return redirect(url_for('view_vehicles'))
    
    # Use the new calendar-based booking template
    return render_template('customer/book_service_calendar.html', vehicle=vehicle)

def api_login_required(f):
    """Custom login_required decorator for API endpoints that returns JSON instead of redirect"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Check if this is an API request
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            else:
                flash('You need to be logged in to access this page.', 'danger')
                return redirect(url_for('select_user'))
        
        if not isinstance(current_user, Admin):
            # Check if this is an API request
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin privileges required'}), 403
            else:
                flash('You need to be an admin to access this page.', 'danger')
                return redirect(url_for('select_user'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_vehicles = Vehicle.query.count()
    total_services = Service.query.count()
    pending_services = Service.query.filter_by(status='scheduled').count()
    completed_services = Service.query.filter_by(status='completed').count()
    
    return render_template('admin/dashboard.html',
                         total_vehicles=total_vehicles,
                         total_services=total_services,
                         pending_services=pending_services,
                         completed_services=completed_services)

@app.route('/admin/vehicles')
@login_required
@admin_required
def admin_vehicles():
    form = ServiceFilterForm()
    vehicles = Vehicle.query.all()
    return render_template('admin/vehicles.html', vehicles=vehicles, form=form)

@app.route('/admin/services')
@login_required
@admin_required
def admin_services():
    form = ServiceFilterForm()
    services = Service.query.order_by(Service.scheduled_date).all()
    return render_template('admin/services.html', services=services, form=form)

@app.route('/admin/service/<int:service_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_service_details(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        service.status = form.status.data
        service.actual_date = form.actual_date.data
        service.cost = form.cost.data
        service.odometer_reading = form.odometer_reading.data
        service.notes = form.notes.data
        
        if form.status.data == 'completed':
            service.vehicle.last_service_date = service.actual_date
            service.vehicle.next_service_date = service.actual_date + relativedelta(months=6)
        
        history = ServiceHistory(
            service_id=service.id,
            status=form.status.data,
            notes=f'Status updated to {form.status.data}'
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('main.admin_service_details', service_id=service_id))
    
    return render_template('admin/service_details.html', service=service, form=form)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    form = ServiceFilterForm()
    services = Service.query.order_by(Service.scheduled_date).all()
    return render_template('admin/reports.html', services=services, form=form)

@login_manager.user_loader
def load_user(user_id):
    try:
        print(f"DEBUG: Loading user with ID: {user_id}")
        # Check if the ID has a prefix to identify the user type
        if user_id.startswith('admin_'):
            admin_id = int(user_id.replace('admin_', ''))
            admin = Admin.query.get(admin_id)
            print(f"DEBUG: Loaded admin: {admin}")
            return admin
        elif user_id.startswith('user_'):
            user_real_id = int(user_id.replace('user_', ''))
            user = User.query.get(user_real_id)
            print(f"DEBUG: Loaded user: {user}")
            return user
        else:
            # For backward compatibility, try both (but this shouldn't happen with the new system)
            print(f"DEBUG: Trying backward compatibility for ID: {user_id}")
            user = User.query.get(int(user_id))
            if user:
                print(f"DEBUG: Found user via backward compatibility: {user}")
                return user
            admin = Admin.query.get(int(user_id))
            if admin:
                print(f"DEBUG: Found admin via backward compatibility: {admin}")
                return admin
    except Exception as e:
        print(f"ERROR in user_loader: {str(e)}")
        import traceback
        traceback.print_exc()
    return None

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('select_user'))

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    form = CustomerRegisterForm()

    if form.validate_on_submit():
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash("This email is already registered.", "danger")
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, password=hashed_password,
                        name=form.name.data, phone=form.phone.data,
                        address=form.address.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for('login_customer'))

    
    return render_template('register.html', form=form)

@app.route('/register_admin',methods=['GET','POST'])
def register_admin():
    form = AdminRegisterForm()
    if form.validate_on_submit():
        existing_email = Admin.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash("This email is already registered.", "danger")
            return redirect(url_for('admin_register'))
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_admin = Admin(email=form.email.data, password=hashed_password,
                        name=form.name.data)
        db.session.add(new_admin)
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for('login_admin'))

    return render_template('register_admin.html', form=form)

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        model = form.model.data
        year = form.year.data
        odo_reading = form.odo_reading.data
        license_plate = form.license_plate.data
        vin = form.vin.data

        existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()

        if existing_vehicle:
            flash("Error: License plate already exists!", "danger")
            return redirect(url_for('add_vehicle'))
        
        vehicle = Vehicle(user_id=current_user.real_id,
                        model=model,
                        year=year,  
                        odo_reading=odo_reading,
                        license_plate=license_plate,
                        vin=vin)   
        db.session.add(vehicle)
        db.session.commit()
        flash("Vehicle Added Successfully", "success")
        return redirect(url_for('view_vehicles'))

    return render_template('add_vehicle.html', form=form)

@app.route('/cancel_service/<int:service_id>', methods=['POST'])
@login_required
def cancel_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Ensure the service belongs to the current user
    if service.user_id != current_user.real_id:
        flash('You do not have permission to cancel this service.', 'danger')
        return redirect(url_for('view_services'))
    
    # Only allow cancellation of scheduled services
    if service.status != 'scheduled':
        flash('Only scheduled services can be cancelled.', 'danger')
        return redirect(url_for('view_services'))
    
    # Update service status
    service.status = 'cancelled'
    
    # Create service history entry
    history = ServiceHistory(
        service_id=service.id,
        status='cancelled',
        notes='Service cancelled by customer'
    )
    
    db.session.add(history)
    db.session.commit()
    
    flash('Service cancelled successfully!', 'success')
    return redirect(url_for('view_services'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if not isinstance(current_user, User):
        flash('Only customers can delete their accounts.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    try:
        # Delete all vehicles associated with the user
        vehicles = Vehicle.query.filter_by(user_id=current_user.real_id).all()
        for vehicle in vehicles:
            db.session.delete(vehicle)
        
        # Delete all services associated with the user
        services = Service.query.filter_by(user_id=current_user.real_id).all()
        for service in services:
            db.session.delete(service)
        
        # Delete the user account
        db.session.delete(current_user)
        db.session.commit()
        
        logout_user()
        flash('Your account has been successfully deleted.', 'success')
        return redirect(url_for('select_user'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account. Please try again.', 'danger')
        return redirect(url_for('customer_dashboard'))

@app.route('/modify_service/<int:service_id>', methods=['GET', 'POST'])
@login_required
def modify_service(service_id):
    if not isinstance(current_user, Admin):
        flash('You do not have permission to modify services.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    service = Service.query.get_or_404(service_id)
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        try:
            # Update service details
            service.status = form.status.data
            service.scheduled_date = form.scheduled_date.data
            service.actual_date = form.actual_date.data
            service.cost = form.cost.data
            service.odometer_reading = form.odometer_reading.data
            service.notes = form.notes.data
            
            # If service is completed, update vehicle's last service date
            if form.status.data == 'completed' and form.actual_date.data:
                service.vehicle.last_service_date = form.actual_date.data
                service.vehicle.next_service_date = form.actual_date.data + relativedelta(months=6)
            
            # Create service history entry
            history = ServiceHistory(
                service_id=service.id,
                status=form.status.data,
                notes=f'Service modified by admin: {form.notes.data}'
            )
            
            db.session.add(history)
            db.session.commit()
            
            flash('Service updated successfully!', 'success')
            return redirect(url_for('view_services'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating service: {str(e)}', 'danger')
            return redirect(url_for('modify_service', service_id=service_id))
    
    return render_template('admin/modify_service.html', service=service, form=form)

@app.route('/make_payment/<int:service_id>', methods=['GET', 'POST'])
@login_required
def make_payment(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check if user has permission to make payment
    if not isinstance(current_user, Admin) and service.user_id != current_user.real_id:
        flash('You do not have permission to make this payment.', 'danger')
        return redirect(url_for('view_services'))
    
    # Check if service is completed and has a cost
    if service.status != 'completed' or not service.cost:
        flash('Service is not ready for payment.', 'danger')
        return redirect(url_for('service_details', service_id=service_id))
    
    # Check if payment already exists
    if service.payment and service.payment.status == 'completed':
        flash('Payment has already been made for this service.', 'info')
        return redirect(url_for('service_details', service_id=service_id))
    
    form = PaymentForm()
    form.amount.data = service.cost  # Pre-fill the amount
    
    if form.validate_on_submit():
        try:
            # Create or update payment
            if service.payment:
                payment = service.payment
            else:
                payment = Payment(service_id=service_id)
            
            payment.amount = form.amount.data
            payment.payment_method = form.payment_method.data
            payment.transaction_id = form.transaction_id.data
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            if not service.payment:
                db.session.add(payment)
            
            db.session.commit()
            flash('Payment processed successfully!', 'success')
            return redirect(url_for('service_details', service_id=service_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}', 'danger')
    
    return render_template('customer/make_payment.html', service=service, form=form)

@app.route('/admin/payments')
@login_required
@admin_required
def admin_payments():
    services = Service.query.filter(Service.status == 'completed').all()
    return render_template('admin/payments.html', services=services)

@app.route('/admin/payment_details/<int:service_id>')
@login_required
@admin_required
def admin_payment_details(service_id):
    service = Service.query.get_or_404(service_id)
    if service.status != 'completed':
        flash('Service is not completed.', 'danger')
        return redirect(url_for('admin_payments'))
    return render_template('admin/payment_details.html', service=service)

# Routes to serve static files from landing-page directory
@app.route('/css/<path:filename>')
def landing_css(filename):
    return send_from_directory('landing-page/css', filename)

@app.route('/js/<path:filename>')
def landing_js(filename):
    return send_from_directory('landing-page/js', filename)

@app.route('/images/<path:filename>')
def landing_images(filename):
    return send_from_directory('landing-page/images', filename)

# ==================== CALENDAR SLOT BOOKING SYSTEM ====================

# API endpoint to get available slots for a specific date
@app.route('/api/slots/<string:date_str>')
@api_login_required
def get_available_slots(date_str):
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if it's a weekend
        if target_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
            return jsonify({'available': False, 'reason': 'Weekend - No bookings available'}), 200
        
        # Check if it's a non-working day
        non_working = NonWorkingDay.query.filter_by(date=target_date).first()
        if non_working:
            return jsonify({'available': False, 'reason': non_working.reason or 'Non-working day'}), 200
        
        # Get slot settings, create defaults if not found
        settings = SlotSettings.query.first()
        if not settings:
            # Create default settings
            default_times = ['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM']
            settings = SlotSettings(
                default_slots_per_day=5,
                slot_times=json.dumps(default_times),
                max_bookings_per_slot=1,
                booking_advance_days=30,
                updated_at=datetime.utcnow()
            )
            db.session.add(settings)
            db.session.commit()
        
        # Parse slot times safely
        try:
            slot_times = json.loads(settings.slot_times) if settings.slot_times else ['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM']
        except json.JSONDecodeError:
            slot_times = ['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM']
        
        # Get or create slots for this date
        slots_data = []
        for time_slot in slot_times:
            slot = BookingSlot.query.filter_by(date=target_date, time=time_slot).first()
            
            if not slot:
                # Create slot if it doesn't exist
                slot = BookingSlot(
                    date=target_date,
                    time=time_slot,
                    max_bookings=settings.max_bookings_per_slot or 1,
                    current_bookings=0,
                    is_available=True
                )
                db.session.add(slot)
                
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            
            slots_data.append({
                'id': slot.id,
                'time': slot.time or time_slot,
                'available': (slot.is_available if hasattr(slot, 'is_available') else True) and not slot.is_fully_booked(),
                'current_bookings': slot.current_bookings or 0,
                'max_bookings': slot.max_bookings or 1
            })
        
        return jsonify({
            'available': True,
            'date': date_str,
            'slots': slots_data
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Server error: {str(e)}',
            'available': False,
            'reason': 'Service temporarily unavailable'
        }), 500

# Book a slot
@app.route('/api/book_slot', methods=['POST'])
@api_login_required
def book_slot():
    try:
        data = request.json
        slot_id = data.get('slot_id')
        vehicle_id = data.get('vehicle_id')
        service_type = data.get('service_type')
        notes = data.get('notes', '')
        
        # Validate slot
        slot = BookingSlot.query.get(slot_id)
        if not slot:
            return jsonify({'error': 'Invalid slot'}), 400
        
        if slot.is_fully_booked():
            return jsonify({'error': 'Slot is fully booked'}), 400
        
        # Create booking
        booking = SlotBooking(
            slot_id=slot_id,
            user_id=current_user.real_id if hasattr(current_user, 'real_id') else current_user.id,
            vehicle_id=vehicle_id,
            service_type=service_type,
            notes=notes
        )
        
        # Update slot bookings count
        slot.current_bookings += 1
        
        db.session.add(booking)
        db.session.commit()
        
        # Create service record
        service = Service(
            service_type=service_type,
            scheduled_date=datetime.combine(slot.date, datetime.strptime(slot.time, '%I:%M %p').time()),
            status='scheduled',
            vehicle_id=vehicle_id,
            user_id=current_user.real_id if hasattr(current_user, 'real_id') else current_user.id,
            notes=notes
        )
        db.session.add(service)
        db.session.commit()
        
        # Link service to booking
        booking.service_id = service.id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'service_id': service.id,
            'message': 'Slot booked successfully!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Get all bookings for admin
@app.route('/api/admin/bookings')
@api_login_required
@admin_required
def get_all_bookings():
    try:
        # Get date range from query params
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        query = SlotBooking.query.join(BookingSlot).join(User).join(Vehicle)
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(BookingSlot.date >= start)
        
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(BookingSlot.date <= end)
        
        bookings = query.all()
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'date': booking.slot.date.strftime('%Y-%m-%d'),
                'time': booking.slot.time,
                'user': booking.user.name if booking.user else 'Unknown',
                'vehicle': f"{booking.vehicle.model} ({booking.vehicle.license_plate})" if booking.vehicle else 'Unknown',
                'service_type': booking.service_type,
                'status': booking.status,
                'notes': booking.notes
            })
        
        return jsonify({'bookings': bookings_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: Update slot settings
@app.route('/api/admin/slot_settings', methods=['GET', 'POST'])
@api_login_required
@admin_required
def manage_slot_settings():
    try:
        if request.method == 'GET':
            settings = SlotSettings.query.first()
            if settings:
                slot_times_list = []
                if settings.slot_times:
                    try:
                        slot_times_list = json.loads(settings.slot_times)
                    except json.JSONDecodeError:
                        slot_times_list = ['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM']
                
                return jsonify({
                    'default_slots_per_day': settings.default_slots_per_day or 5,
                    'slot_times': slot_times_list,
                    'max_bookings_per_slot': settings.max_bookings_per_slot or 1,
                    'booking_advance_days': settings.booking_advance_days or 30
                }), 200
            return jsonify({'error': 'Settings not found'}), 404
        
        elif request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            settings = SlotSettings.query.first()
            
            if not settings:
                # Create new settings with defaults
                settings = SlotSettings(
                    default_slots_per_day=5,
                    slot_times=json.dumps(['09:00 AM', '11:00 AM', '01:00 PM', '03:00 PM', '05:00 PM']),
                    max_bookings_per_slot=1,
                    booking_advance_days=30,
                    updated_at=datetime.utcnow()
                )
                db.session.add(settings)
            
            # Update fields if provided
            if 'slot_times' in data and data['slot_times']:
                settings.slot_times = json.dumps(data['slot_times'])
                settings.default_slots_per_day = len(data['slot_times'])
            
            if 'max_bookings_per_slot' in data:
                settings.max_bookings_per_slot = max(1, int(data['max_bookings_per_slot']))
            
            if 'booking_advance_days' in data:
                settings.booking_advance_days = max(1, int(data['booking_advance_days']))
            
            settings.updated_at = datetime.utcnow()
            
            try:
                db.session.commit()
                return jsonify({'success': True, 'message': 'Settings updated successfully'}), 200
            except Exception as commit_error:
                db.session.rollback()
                return jsonify({'error': f'Database error: {str(commit_error)}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Admin: Mark day as non-working
@app.route('/api/admin/non_working_days', methods=['GET', 'POST', 'DELETE'])
@api_login_required
@admin_required
def manage_non_working_days():
    try:
        if request.method == 'GET':
            non_working_days = NonWorkingDay.query.all()
            days_data = [{
                'id': day.id,
                'date': day.date.strftime('%Y-%m-%d'),
                'reason': day.reason,
                'is_recurring': day.is_recurring
            } for day in non_working_days]
            
            return jsonify({'non_working_days': days_data}), 200
        
        elif request.method == 'POST':
            data = request.json
            target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Check if already exists
            existing = NonWorkingDay.query.filter_by(date=target_date).first()
            if existing:
                return jsonify({'error': 'This date is already marked as non-working'}), 400
            
            non_working = NonWorkingDay(
                date=target_date,
                reason=data.get('reason', 'Holiday'),
                is_recurring=data.get('is_recurring', False),
                created_by=current_user.real_id if hasattr(current_user, 'real_id') else current_user.id
            )
            
            db.session.add(non_working)
            db.session.commit()
            
            # Cancel all bookings for this date
            slots = BookingSlot.query.filter_by(date=target_date).all()
            for slot in slots:
                slot.is_available = False
                bookings = SlotBooking.query.filter_by(slot_id=slot.id, status='confirmed').all()
                for booking in bookings:
                    booking.status = 'cancelled'
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Non-working day added successfully'}), 200
        
        elif request.method == 'DELETE':
            day_id = request.args.get('id')
            non_working = NonWorkingDay.query.get(day_id)
            
            if not non_working:
                return jsonify({'error': 'Non-working day not found'}), 404
            
            # Re-enable slots for this date
            slots = BookingSlot.query.filter_by(date=non_working.date).all()
            for slot in slots:
                slot.is_available = True
            
            db.session.delete(non_working)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Non-working day removed successfully'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get user's bookings
@app.route('/api/my_bookings')
@api_login_required
def get_my_bookings():
    try:
        user_id = current_user.real_id if hasattr(current_user, 'real_id') else current_user.id
        bookings = SlotBooking.query.filter_by(user_id=user_id).join(BookingSlot).all()
        
        bookings_data = []
        for booking in bookings:
            bookings_data.append({
                'id': booking.id,
                'date': booking.slot.date.strftime('%Y-%m-%d'),
                'time': booking.slot.time,
                'vehicle': f"{booking.vehicle.model} ({booking.vehicle.license_plate})" if booking.vehicle else 'Unknown',
                'service_type': booking.service_type,
                'status': booking.status
            })
        
        return jsonify({'bookings': bookings_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin page for slot management
@app.route('/admin/slot_management')
@login_required
@admin_required
def admin_slot_management():
    return render_template('admin/slot_management.html')

# Debug endpoint to check database status
@app.route('/api/debug/db_status')
def debug_db_status():
    try:
        # Test basic database connection
        total_users = User.query.count()
        total_admins = Admin.query.count()
        
        # Test SlotSettings model
        settings_count = SlotSettings.query.count()
        
        return jsonify({
            'success': True,
            'users': total_users,
            'admins': total_admins,
            'slot_settings_count': settings_count,
            'database_url': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500