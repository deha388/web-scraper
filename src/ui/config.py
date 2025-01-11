import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Test kullanıcı bilgileri
TEST_USER = {
    "email": "admin@boattracker.com",
    "password": "admin123"
} 