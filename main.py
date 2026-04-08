from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid
import random

app = FastAPI(title="Student Finance App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Mock Databases ---
# In a real app, these would be a database (PostgreSQL, MongoDB, etc.)
users_db = {}  # email -> {"name": name, "password": password}
otp_db = {}  # email -> otp_code
token_db = {}  # token -> email


# --- Pydantic Models ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class OTPConfirm(BaseModel):
    email: str
    otp: str


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPassword(BaseModel):
    email: str


class ResetPassword(BaseModel):
    email: str
    new_password: str


class Transaction(BaseModel):
    category: str
    description: str
    amount: float
    time: str
    type: str  # "expense" or "income"


class HomeDataResponse(BaseModel):
    account_balance: float
    income: float
    expenses: float
    recent_transactions: List[Transaction]


# --- Auth Endpoints ---


@app.post("/register")
def register(user: UserRegister):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save user (storing plain text password for student demo; use hashing in production)
    users_db[user.email] = {"name": user.name, "password": user.password}

    # Generate mock OTP
    otp = str(random.randint(1000, 9999))
    otp_db[user.email] = otp

    return {
        "message": "User registered successfully. Check OTP.",
        "mock_otp_received": otp,
    }


@app.post("/confirm-otp")
def confirm_otp(data: OTPConfirm):
    if data.email not in otp_db:
        raise HTTPException(status_code=404, detail="No OTP requested for this email")

    if otp_db[data.email] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Clear OTP and generate token
    del otp_db[data.email]
    token = str(uuid.uuid4())
    token_db[token] = data.email

    return {"message": "OTP confirmed", "token": token}


@app.post("/login")
def login(user: UserLogin):
    db_user = users_db.get(user.email)
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate token
    token = str(uuid.uuid4())
    token_db[token] = user.email

    return {"message": "Login successful", "token": token}


@app.post("/forgot-password")
def forgot_password(data: ForgotPassword):
    if data.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # For this student demo, we skip email sending and go straight to allowing a reset
    return {"message": "Proceed to reset password step"}


@app.post("/reset-password")
def reset_password(data: ResetPassword):
    if data.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    users_db[data.email]["password"] = data.new_password
    return {"message": "Password reset successfully"}


# --- Data Endpoints ---


@app.get("/home", response_model=HomeDataResponse)
def get_home_data():
    """
    Returns the static data matching the provided UI mockup.
    For a real app, you would pass the token in headers to fetch specific user data.
    """
    return {
        "account_balance": 9400.00,
        "income": 5000.00,
        "expenses": 1200.00,
        "recent_transactions": [
            {
                "category": "Shopping",
                "description": "Buy some grocery",
                "amount": -120.00,
                "time": "10:00 AM",
                "type": "expense",
            },
            {
                "category": "Subscription",
                "description": "Disney+ Annual..",
                "amount": -80.00,
                "time": "03:30 PM",
                "type": "expense",
            },
            {
                "category": "Food",
                "description": "Buy a ramen",
                "amount": -32.00,
                "time": "07:30 PM",
                "type": "expense",
            },
        ],
    }
