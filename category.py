from app import db, Category

# Create an admin user
'''admin = Category(name="Tech")
db.session.add(admin)'''
admins = Category(name="Science")
db.session.add(admins)
adminss = Category(name="Business")
db.session.add(adminss)
db.session.commit()