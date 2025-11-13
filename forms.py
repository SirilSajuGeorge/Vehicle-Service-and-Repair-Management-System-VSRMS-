from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField, FloatField, DateField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, Email, EqualTo, Optional, NumberRange
from models import User,Admin


class CustomerRegisterForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Length(
        min=4, max=30)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})
    name = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Name"})
    phone = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Phone"})
    address = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Address"})

    submit = SubmitField("Register")

    def validate_email(self, email):
        existing_email = User.query.filter_by(email=email.data).first()
        if existing_email:
            raise ValidationError("Account already exists. Please Login")
    

class AdminRegisterForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Name"})
    email = StringField(validators=[InputRequired(), Length(
        min=4, max=30)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")

    
    def validate_email(self, email):
        existing_email = Admin.query.filter_by(email=email.data).first()
        if existing_email:
            raise ValidationError("Account already exists. Please Login")
    



class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    address = StringField('Address', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')

class VehicleForm(FlaskForm):
    model = StringField('Model', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    odo_reading = IntegerField('Odometer Reading', validators=[DataRequired()])
    license_plate = StringField('License Plate', validators=[DataRequired()])
    vin = StringField('VIN', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Add Vehicle')

class ServiceForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[
        ('regular', 'Regular Maintenance'),
        ('oil', 'Oil Change'),
        ('tire', 'Tire Rotation'),
        ('brake', 'Brake Service'),
        ('battery', 'Battery Check'),
        ('alignment', 'Wheel Alignment'),
        ('inspection', 'General Inspection')
    ], validators=[DataRequired()])
    scheduled_date = DateField('Scheduled Date', validators=[DataRequired()])
    odo_reading = IntegerField('Odometer Reading', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Schedule Service')

class ServiceUpdateForm(FlaskForm):
    status = SelectField('Status', 
                        choices=[
                            ('scheduled', 'Scheduled'),
                            ('in_progress', 'In Progress'),
                            ('completed', 'Completed'),
                            ('cancelled', 'Cancelled')
                        ],
                        validators=[DataRequired()])
    scheduled_date = DateField('Scheduled Date', validators=[Optional()])
    actual_date = DateField('Actual Date', validators=[Optional()])
    cost = FloatField('Cost', validators=[Optional(), NumberRange(min=0)])
    odometer_reading = IntegerField('Odometer Reading', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Update Service')

class PaymentForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    payment_method = SelectField('Payment Method', 
                               choices=[
                                   ('credit_card', 'Credit Card'),
                                   ('debit_card', 'Debit Card'),
                                   ('upi', 'UPI'),
                                   ('net_banking', 'Net Banking'),
                                   ('cash', 'Cash')
                               ],
                               validators=[DataRequired()])
    transaction_id = StringField('Transaction ID', validators=[DataRequired()])
    submit = SubmitField('Make Payment')

class ServiceFilterForm(FlaskForm):
    service_type = SelectField('Service Type', choices=[
        ('all', 'All Types'),
        ('regular', 'Regular Maintenance'),
        ('oil', 'Oil Change'),
        ('tire', 'Tire Rotation'),
        ('brake', 'Brake Service'),
        ('battery', 'Battery Check'),
        ('alignment', 'Wheel Alignment')
    ])
    status = SelectField('Status', choices=[
        ('all', 'All Status'),
        ('scheduled', 'Scheduled'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    submit = SubmitField('Apply Filters')
