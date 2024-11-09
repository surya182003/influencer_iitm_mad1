# Influencer-Sponsership collabration platform
by Surya Prakash V - 21f3001344
Welcome to the Influencer-Sponsership collabration platform! This project is a simple web application for connecting brands and influencers. Created for the submission of MAD - 1 project.

## Table of Contents
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

### Prerequisites
Before running the application, make sure you have the following tools and software installed:

- Python (3.6 or higher)
- Flask (and its dependencies)
- SQLite or another database system

### Installation
1. Clone this repository to your local machine:
git clone https://github.com/surya182003/influencer_iitm_mad1.git
cd influencer_iitm_mad1

2. Create a virtual environment (optional but recommended):
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install the required dependencies:
Flask==2.1.1
Flask-SQLAlchemy==3.0.1
Flask-Login==0.5.0
Flask-WTF==1.0.1
Werkzeug==2.0.1

4. Set up the database:
Open a terminal or command prompt.
Navigate to your project directory, where your app.py files are located.
Run a Python interactive shell or execute the following commands in your terminal:
    ```bash
    from app import db
    db.create_all()
    exit()

5. Run the application:
python app.py
The application should now be running locally at `http://localhost:5000`.

For admin login using this credentials:
URL - `http://localhost:5000/admin`
Username : surya
password: 123

## Usage
- Visit `http://localhost:5000` in your web browser to access the Influencer-Sponsership collabration platform.
- Explore different pages.

## Features
- User authentication and authorization (login and registration)
- Login as sponser to give out private and public campaigns and send ad reqest to influencers directly
- Login as influencer to view and accept public campaigns and accept or reject or regotitate ad reqest from influencers directly
- Login as admin to manage everything including flagging users

- ## Contributing
Contributions to this project are welcome! If you find any issues or have improvements to suggest, feel free to open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch for your feature: `git checkout -b feature-name`
3. Make your changes and commit them: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
