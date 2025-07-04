# Omnify-Assesment

Fitness Class Booking API


A FastAPI application that allows users to:
- View available fitness classes
- Book a class by providing their name and email
- View their booking history

Features

- Timezone-aware class times (default: Asia/Kolkata)
- Validates email and client details
- SQLite database with auto-initialized sample data
- Clean REST endpoints using FastAPI
- Logging of successful bookings

Setup Instructions

1. Clone the Repository

```bash
git clone https://github.com/your-username/fitness-booking-app.git
cd fitness-booking-app

2. Create Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


3. Install Dependencies

bash
Copy
Edit
pip install fastapi uvicorn pydantic pytz

4. Run the App

bash
Copy
Edit
uvicorn main:app --reload

API Endpoints

1. View Available Classes

curl -X GET "http://localhost:8000/classes?timezone=Asia/Kolkata"

2. Book a Class

curl -X POST "http://localhost:8000/book" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": 1,
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "timezone": "Asia/Kolkata"
}'

3. View Bookings by Email

curl -X GET "http://localhost:8000/bookings?email=john@example.com&timezone=Asia/Kolkata"


Database

I have used local SQLite DB: fitness.db

Tables:

classes: Stores fitness class details

bookings: Stores client bookings with timestamps
