from supabase import create_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def register_user(email: str, password: str, username: str) -> bool:
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username
                }

            }
        })
        if result and result.user:
            # Optionally store metadata like username
            # supabase.auth.update_user({"data": {"username": username}})
            return True
        return False
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise

def authenticate_user(email: str, password: str):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if result and result.user:
            return {
                "email": result.user.email,
                "username": result.user.user_metadata.get("username", "User"),
                "id": result.user.id
            }
        return None
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise


# import streamlit as st
# import bcrypt
# import pymongo

# # MongoDB connection
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client["resumatrix"]
# users_collection = db["users"]

# # Function to hash passwords
# def hash_password(password):
#     return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# # Function to verify passwords
# def verify_password(password, hashed_password):
#     return bcrypt.checkpw(password.encode(), hashed_password.encode())

# # Function to register a new user
# def register_user(email, password, username=None):
#     # Additional password strength validation
#     if len(password) < 5:
#         st.error("Password must be at least 5 characters long.")
#         return False

#     if users_collection.find_one({"email": email}):
#         st.error("Email already exists. Please choose another email.")  # User already exists
#         return False

#     hashed_password = hash_password(password)
#     users_collection.insert_one({"email": email, "password": hashed_password, "username": username})

#     return True

# # Function to authenticate user login
# def authenticate_user(email, password):
#     user = users_collection.find_one({"email": email})
#     if user and verify_password(password, user["password"]):
#         return user
#     return None