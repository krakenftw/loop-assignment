#How to Start the Project
##Prerequisites
 - Python 3.8+
 - PostgreSQL
 - Virtual environment (optional but recommended)
 - Setup Instructions
 - Clone the Repository:

```
git clone https://github.com/your-username/store-status-assignment.git
cd store-status-assignment
Set Up the Environment:
```

Create a virtual environment and activate it:

```
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install Dependencies:
```

```
pip install -r requirements.txt
```
Create a .env file in the root directory with your database URL:

```
DATABASE_URL=postgresql://username:password@localhost/dbname
Then, create the database tables:
```

Seed the Database:
Run the seeding script to populate the database with data from CSV files:

```
python seed.py
```

Run the backend

```
uvicorn app.main:app --reload
```
