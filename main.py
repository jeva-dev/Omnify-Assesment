from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List
from datetime import datetime
import sqlite3
import pytz
import logging

app = FastAPI()
DB_NAME = "fitness.db"

# Configure Logging
logging.basicConfig(level=logging.INFO)

# ---------- MODELS ----------

class ClassOut(BaseModel):
    id: int
    name: str
    date_time: str
    instructor: str
    available_slots: int

class BookingIn(BaseModel):
    class_id: int
    client_name: str = Field(..., min_length=1)
    client_email: EmailStr
    timezone: str = "Asia/Kolkata"  # default IST

class BookingOut(BaseModel):
    id: int
    class_id: int
    client_name: str
    client_email: EmailStr
    booked_at: str

# ---------- DB SETUP ----------

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date_time TEXT NOT NULL,
        instructor TEXT NOT NULL,
        available_slots INTEGER NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        client_name TEXT,
        client_email TEXT,
        booked_at TEXT,
        FOREIGN KEY (class_id) REFERENCES classes (id)
    )""")
    # Dummy class data (IST time zone)
    cur.execute("SELECT COUNT(*) FROM classes")
    if cur.fetchone()[0] == 0:
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)
        cur.executemany("""
        INSERT INTO classes (name, date_time, instructor, available_slots) VALUES (?, ?, ?, ?)
        """, [
            ("Yoga Morning", now.replace(hour=6, minute=30).isoformat(), "Anita", 5),
            ("Cardio Blast", now.replace(hour=9, minute=0).isoformat(), "Rahul", 3),
            ("Kung Fu", now.replace(hour=10, minute=0).isoformat(), "Jeva", 7),
            ("Evening Stretch", now.replace(hour=18, minute=0).isoformat(), "Meera", 4),
            ])
    conn.commit()
    conn.close()

init_db()

# ---------- HELPERS ----------

def get_db():
    return sqlite3.connect(DB_NAME)

def convert_time(dt_str, to_tz):
    ist = pytz.timezone("Asia/Kolkata")
    dt_obj = datetime.fromisoformat(dt_str)

    if dt_obj.tzinfo is None:
        dt_obj = ist.localize(dt_obj)
    else:
        dt_obj = dt_obj.astimezone(ist)

    utc_time = dt_obj.astimezone(pytz.utc)
    target = pytz.timezone(to_tz)
    return utc_time.astimezone(target).strftime("%Y-%m-%d %H:%M:%S %Z")
# ---------- ENDPOINTS ----------

@app.get("/classes", response_model=List[ClassOut])
def get_classes(timezone: str = Query(default="Asia/Kolkata")):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM classes")
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append(ClassOut(
            id=r[0],
            name=r[1],
            date_time=convert_time(r[2], timezone),
            instructor=r[3],
            available_slots=r[4]
        ))
    return result

@app.post("/book", response_model=BookingOut)
def book_class(booking: BookingIn):
    conn = get_db()
    cur = conn.cursor()

    # Validate class and slots
    cur.execute("SELECT * FROM classes WHERE id = ?", (booking.class_id,))
    cls = cur.fetchone()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls[4] <= 0:
        raise HTTPException(status_code=400, detail="No slots available")

    # Book
    booked_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
    cur.execute("INSERT INTO bookings (class_id, client_name, client_email, booked_at) VALUES (?, ?, ?, ?)",
                (booking.class_id, booking.client_name, booking.client_email, booked_at))
    cur.execute("UPDATE classes SET available_slots = available_slots - 1 WHERE id = ?", (booking.class_id,))
    conn.commit()
    booking_id = cur.lastrowid
    conn.close()

    logging.info(f"Booking successful: {booking.client_name} for class ID {booking.class_id}")

    return BookingOut(
        id=booking_id,
        class_id=booking.class_id,
        client_name=booking.client_name,
        client_email=booking.client_email,
        booked_at=convert_time(booked_at, booking.timezone)
    )

@app.get("/bookings", response_model=List[BookingOut])
def get_bookings(email: EmailStr, timezone: str = Query(default="Asia/Kolkata")):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE client_email = ?", (email,))
    rows = cur.fetchall()
    conn.close()
    return [
        BookingOut(
            id=r[0],
            class_id=r[1],
            client_name=r[2],
            client_email=r[3],
            booked_at=convert_time(r[4], timezone)
        ) for r in rows
    ]

