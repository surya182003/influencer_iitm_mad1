from flask import Flask, render_template, redirect, url_for, flash,request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, DateField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime

# Initialize Flask app and configure
app = Flask(__name__)
app.config['SECRET_KEY'] = '21f3001344Surya'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_sponsor = db.Column(db.Boolean, default=False)
    is_influencer = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # New admin field
    company_name = db.Column(db.String(150))  # For sponsors
    industry = db.Column(db.String(150))
    budget = db.Column(db.Integer)
    
    # Add a flagged column
    is_flagged = db.Column(db.Boolean, default=False)

    # Relationship to campaigns (if user is a sponsor)
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True)

    # Relationship to ad requests (if user is an influencer)
    ad_requests = db.relationship('AdRequest', backref='influencer', lazy=True)

class Sponsor(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    company_name = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    budget = db.Column(db.Float)

class Influencer(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    category = db.Column(db.String(100))
    niche = db.Column(db.String(100))
    followers = db.Column(db.Integer)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Integer)
    visibility = db.Column(db.String(50), default='public')  # 'public' or 'private'
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # Add a flagged column
    is_flagged = db.Column(db.Boolean, default=False)

    # Relationship to ad requests and notification
    ad_requests = db.relationship('AdRequest', backref='campaign',cascade="all, delete-orphan", lazy=True)
    notifications = db.relationship('Notification', backref='campaign', cascade='all, delete-orphan')

class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id', ondelete="CASCADE"), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    requirements = db.Column(db.Text)
    payment_amount = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'rejected'

class InfluencerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(150))
    niche = db.Column(db.String(150))
    reach = db.Column(db.Integer)  # e.g., calculated by followers

    # Define the relationship to User
    user = db.relationship('User', backref='influencer_profiles')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)  # To track if the notification has been read

    user = db.relationship('User', backref='notifications', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    campaigns = db.relationship('Campaign', backref='category', lazy=True)

# Flask-WTForms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('sponsor', 'Sponsor'), ('influencer', 'Influencer')], validators=[DataRequired()])
    submit = SubmitField('Register')

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    budget = FloatField('Budget', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])
    submit = SubmitField('Create/Update Campaign')

class EditCampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    budget = FloatField('Budget', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])

# Login Manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            
            # Check for user role using the boolean flags
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            elif user.is_sponsor:
                return redirect(url_for('sponsor_dashboard'))
            elif user.is_influencer:
                return redirect(url_for('influencer_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()  # This logs out the current user
    return redirect(url_for('login'))  # Redirect the user to the login page

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.role.data == 'admin':
            new_user = User(username=form.username.data, password=form.password.data, is_admin=True)
        elif form.role.data == 'sponsor':
            new_user = User(username=form.username.data, password=form.password.data, is_sponsor=True)
        elif form.role.data == 'influencer':
            new_user = User(username=form.username.data, password=form.password.data, is_influencer=True)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)  # Prevent non-admins from accessing the admin dashboard
    
    users = User.query.all()
    campaigns = Campaign.query.all()
    ad_requests = AdRequest.query.all()
    
    return render_template('admin_dashboard.html', users=users, campaigns=campaigns, ad_requests=ad_requests)

#flagging for admins
@app.route('/flag_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def flag_campaign(campaign_id):
    if not current_user.is_admin:
        abort(403)  # Only admin users can flag campaigns

    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = True  # Add a "flagged" column in the Campaign model
    db.session.commit()

    # Create notifications for both the sponsor and the influencer
    sponsor_notification = Notification(
        user_id=campaign.sponsor_id,
        campaign_id=campaign.id,
        message=f'Your campaign "{campaign.name}" has been flagged.'
    )
    db.session.add(sponsor_notification)

    # Notify all influencers associated with the campaign
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
    for ad_request in ad_requests:
        influencer_notification = Notification(
            user_id=ad_request.influencer.id,
            campaign_id=campaign.id,
            message=f'The campaign "{campaign.name}" you requested has been flagged.'
        )
        db.session.add(influencer_notification)

    db.session.commit()

    flash('Campaign has been flagged!')
    return redirect(url_for('admin_dashboard'))

@app.route('/flag_user/<int:user_id>', methods=['POST'])
@login_required
def flag_user(user_id):
    if not current_user.is_admin:
        abort(403)

    user = User.query.get_or_404(user_id)
    user.is_flagged = True  # Flag the user
    db.session.commit()

    # Create a notification for the flagged user
    notification_message = 'You have been flagged by an admin.'
    user_notification = Notification(user_id=user.id, campaign_id=0, message=notification_message)
    db.session.add(user_notification)

    db.session.commit()

    flash('User has been flagged!')
    return redirect(url_for('admin_dashboard'))

@app.route('/sponsor/dashboard')
@login_required
def sponsor_dashboard():
    if not current_user.is_sponsor:
        return redirect(url_for('home'))
    
    # Fetch the campaigns created by the sponsor
    campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
    
    # Preload the ad requests for each campaign
    for campaign in campaigns:
        campaign.ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
    
    return render_template('sponsor_dashboard.html', campaigns=campaigns)

@app.route('/sponsor_profile', methods=['GET', 'POST'])
@login_required
def sponsor_profile():
    if not current_user.is_sponsor:
        abort(403)  # Only sponsors can access this page

    sponsor = Sponsor.query.filter_by(id=current_user.id).first()
    
    if request.method == 'POST':
        # Get form data
        company_name = request.form['company_name']
        industry = request.form['industry']
        budget = request.form['budget']
        
        # Update sponsor profile
        if sponsor:
            sponsor.company_name = company_name
            sponsor.industry = industry
            sponsor.budget = budget
        else:
            # Create new sponsor profile if it doesn't exist
            new_sponsor = Sponsor(id=current_user.id, company_name=company_name, industry=industry, budget=budget)
            db.session.add(new_sponsor)
        
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('sponsor_profile'))

    return render_template('sponsor_profile.html', sponsor=sponsor)

@app.route('/sponsor_accept_ad_request/<int:ad_request_id>', methods=['GET'])
@login_required
def sponsor_accept_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if ad_request.campaign.sponsor_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('sponsor_dashboard'))
    
    ad_request.status = 'Accepted'
    db.session.commit()
    flash("Ad request accepted!", "success")
    return redirect(url_for('sponsor_dashboard'))

@app.route('/sponsor_reject_ad_request/<int:ad_request_id>', methods=['GET'])
@login_required
def sponsor_reject_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if ad_request.campaign.sponsor_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('sponsor_dashboard'))
    
    ad_request.status = 'Rejected'
    db.session.commit()
    flash("Ad request rejected.", "danger")
    return redirect(url_for('sponsor_dashboard'))

@app.route('/accept_negotiated_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def accept_negotiated_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if not current_user.is_sponsor or ad_request.campaign.sponsor_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for('sponsor_dashboard'))
    
    if ad_request.status == 'Negotiating':
        ad_request.status = 'Accepted'
        db.session.commit()
        flash("Ad request accepted with new terms", "success")
    
    return redirect(url_for('sponsor_dashboard'))


@app.route('/reject_negotiated_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def reject_negotiated_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if not current_user.is_sponsor or ad_request.campaign.sponsor_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for('sponsor_dashboard'))
    
    if ad_request.status == 'Negotiating':
        ad_request.status = 'Rejected'
        db.session.commit()
        flash("Ad request rejected", "success")
    
    return redirect(url_for('sponsor_dashboard'))

@app.route('/create_campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        # Fetch form data
        name = request.form['name']
        description = request.form['description']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        budget = float(request.form['budget'])
        visibility = request.form['visibility']
        sponsor_id = current_user.id
        
        # Create a new campaign
        campaign = Campaign(name=name, description=description,start_date=start_date, end_date=end_date,budget=budget, visibility=visibility, sponsor_id=sponsor_id)
        db.session.add(campaign)
        db.session.commit()

        # Handle influencer selection if private
        if visibility == 'private':
            influencer_id = request.form['influencer_id']
            requirements = request.form['requirements']
            payment_amount = float(request.form['payment_amount'])
            
            # Create ad request for a private campaign
            ad_request = AdRequest(campaign_id=campaign.id, influencer_id=influencer_id,requirements=requirements, payment_amount=payment_amount)
            db.session.add(ad_request)
            db.session.commit()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))

    # For GET request, render the campaign creation form
    influencers = User.query.filter_by(is_influencer=True).all()  # Get list of influencers for private campaigns
    return render_template('create_campaign.html', influencers=influencers)

@app.route('/campaign/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    # Check if current user is the owner of the campaign
    if campaign.sponsor_id != current_user.id:
        flash('You do not have permission to edit this campaign.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    form = EditCampaignForm(obj=campaign)

    if form.validate_on_submit():
        campaign.name = form.name.data
        campaign.description = form.description.data
        campaign.start_date = form.start_date.data
        campaign.end_date = form.end_date.data
        campaign.budget = form.budget.data
        campaign.visibility = form.visibility.data
        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))

    return render_template('edit_campaign.html', form=form, campaign=campaign)

@app.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    # Check if current user is the owner of the campaign
    if campaign.sponsor_id != current_user.id:
        flash('You do not have permission to delete this campaign.', 'danger')
        return redirect(url_for('sponsor_dashboard'))

    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully.', 'success')
    return redirect(url_for('sponsor_dashboard'))

@app.route('/categorize_campaign/<int:campaign_id>', methods=['GET', 'POST'])
def categorize_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        selected_category_id = request.form.get('category')
        campaign.category_id = selected_category_id  # Assuming category_id is a foreign key in Campaign
        db.session.commit()
        flash('Campaign categorized successfully!', 'success')
        return redirect(url_for('sponsor_dashboard'))  # Redirect to the dashboard or campaign list

    return render_template('categorize_campaign.html', campaign=campaign, categories=categories)

@app.route('/send_ad_request/<int:campaign_id>', methods=['POST'])
@login_required
def send_ad_request(campaign_id):
    # Ensure the user is an influencer
    if not current_user.is_influencer:
        flash("Only influencers can send ad requests.", "danger")
        return redirect(url_for('public_campaigns'))

    # Fetch the campaign
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get the proposed payment amount and requirements from the form
    requirements = request.form['requirements']
    payment_amount = float(request.form['payment_amount'])

    # Create a new ad request for this campaign with the provided data
    ad_request = AdRequest(
        campaign_id=campaign.id,
        influencer_id=current_user.id,
        requirements=requirements,
        payment_amount=payment_amount,
        status='pending'
    )
    
    db.session.add(ad_request)
    db.session.commit()
    
    flash("Ad request sent successfully!", "success")
    return redirect(url_for('public_campaigns'))


@app.route('/sponsor_campaigns')
@login_required
def sponsor_campaigns():
    if not current_user.is_sponsor:
        return redirect(url_for('login'))
    
    campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
    return render_template('sponsor_campaigns.html', campaigns=campaigns)

@app.route('/influencer/dashboard')
@login_required
def influencer_dashboard():
    if not current_user.is_influencer:
        return redirect(url_for('home'))
    ad_requests = AdRequest.query.filter_by(influencer_id=current_user.id).all()
    return render_template('influencer_dashboard.html', ad_requests=ad_requests)

@app.route('/view_influencers', methods=['GET'])
def view_influencers():
    influencers = InfluencerProfile.query.all()  # Fetch all influencer profiles
    return render_template('view_influencers.html', influencers=influencers)

@app.route('/influencer/profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    # Ensure the user is an influencer
    if not current_user.is_influencer:
        flash("Only influencers can update their profiles.", "danger")
        return redirect(url_for('home'))
    
    # Fetch the existing profile
    profile = InfluencerProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        category = request.form['category']
        niche = request.form['niche']
        reach = request.form['reach']
        
        # Update the profile
        if profile:
            profile.category = category
            profile.niche = niche
            profile.reach = reach
        else:
            # Create a new profile if it doesn't exist
            profile = InfluencerProfile(user_id=current_user.id, category=category, niche=niche, reach=reach)
            db.session.add(profile)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('view_profile', user_id=current_user.id))

    return render_template('update_profile.html', profile=profile)

@app.route('/influencer/profile/<int:user_id>')
def view_profile(user_id):
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    user = User.query.get_or_404(user_id)
    return render_template('view_profile.html', profile=profile, user=user)

@app.route('/public_campaigns')
@login_required
def public_campaigns():
    if not current_user.is_influencer:
        return redirect(url_for('login'))

    # Filter public campaigns by budget, category, etc.
    category_id = request.args.get('category_id')
    
    # Fetch categories for the dropdown
    categories = Category.query.all()

    # Fetch public campaigns, optionally filtered by category
    if category_id:
        campaigns = Campaign.query.filter_by(visibility='public', category_id=category_id).all()
    else:
        campaigns = Campaign.query.filter_by(visibility='public').all()
    
    return render_template('public_campaigns.html', campaigns=campaigns, categories=categories)

@app.route('/manage_ad_requests', methods=['GET', 'POST'])
@login_required
def manage_ad_requests():
    if not current_user.is_admin:
        return redirect(url_for('login'))

    if request.method == 'POST':
        ad_request_id = request.form['ad_request_id']
        status = request.form['status']  # 'accepted', 'rejected'
        payment_amount = request.form['payment_amount']

        ad_request = AdRequest.query.get(ad_request_id)
        ad_request.status = status
        ad_request.payment_amount = payment_amount
        db.session.commit()
        flash('Ad request updated!')

    ad_requests = AdRequest.query.all()
    return render_template('manage_ad_requests.html', ad_requests=ad_requests)

@app.route('/accept_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def accept_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if not current_user.is_influencer or ad_request.influencer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('influencer_dashboard'))

    ad_request.status = 'Accepted'
    db.session.commit()
    flash('Ad request accepted.', 'success')
    return redirect(url_for('influencer_dashboard'))

@app.route('/reject_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def reject_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if not current_user.is_influencer or ad_request.influencer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('influencer_dashboard'))

    ad_request.status = 'Rejected'
    db.session.commit()
    flash('Ad request rejected.', 'info')
    return redirect(url_for('influencer_dashboard'))

@app.route('/negotiate_ad_request/<int:ad_request_id>', methods=['GET', 'POST'])
@login_required
def negotiate_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    
    if not current_user.is_influencer or ad_request.influencer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('influencer_dashboard'))

    if request.method == 'POST':
        new_payment_amount = request.form.get('payment_amount')
        if new_payment_amount:
            ad_request.payment_amount = new_payment_amount
            ad_request.status = 'Negotiating'
            db.session.commit()
            flash('Ad request terms renegotiated.', 'success')
        return redirect(url_for('influencer_dashboard'))
    
    return render_template('negotiate_ad_request.html', ad_request=ad_request)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
