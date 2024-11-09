from app import db, User

# Create an admin user
admin = User(username="admin", password=12345678, is_admin=True)
db.session.add(admin)
sponser = User(username="surya123", password=123, is_sponsor=True)
db.session.add(sponser)
influencer = User(username="surya", password=123, is_influencer=True)
db.session.add(influencer)
db.session.commit()