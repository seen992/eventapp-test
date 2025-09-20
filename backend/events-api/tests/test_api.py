"""
Test examples for Events API
"""
import requests
import json
from uuid import uuid4

# Base URL
BASE_URL = "http://localhost:8081"

# Test user UUID
TEST_USER_ID = str(uuid4())

def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health-check")
    print(f"Health Check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_create_user():
    """Test user creation"""
    user_data = {
        "email": f"test_{TEST_USER_ID}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+381123456789"
    }
    
    response = requests.post(
        f"{BASE_URL}/users",
        json=user_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Create User: {response.status_code} - {response.json()}")
    return response.status_code == 201

def test_get_user_profile():
    """Test getting user profile"""
    headers = {"Authorization": f"Bearer {TEST_USER_ID}"}
    response = requests.get(f"{BASE_URL}/users/profile", headers=headers)
    
    print(f"Get User Profile: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_create_event():
    """Test event creation"""
    event_data = {
        "name": "Test Wedding",
        "plan": "freemium",
        "location": "Belgrade, Serbia",
        "restaurant_name": "Test Restaurant",
        "date": "2024-06-15",
        "time": "18:00",
        "event_type": "wedding",
        "expected_guests": 100,
        "description": "Test wedding event"
    }
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_ID}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BASE_URL}/events", json=event_data, headers=headers)
    
    print(f"Create Event: {response.status_code} - {response.json()}")
    return response.status_code == 201

def test_get_events():
    """Test getting events"""
    headers = {"Authorization": f"Bearer {TEST_USER_ID}"}
    response = requests.get(f"{BASE_URL}/events", headers=headers)
    
    print(f"Get Events: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_update_user_profile():
    """Test updating user profile"""
    user_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+381987654321"
    }
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_ID}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(f"{BASE_URL}/users/profile", json=user_data, headers=headers)
    
    print(f"Update User Profile: {response.status_code} - {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing Events API...")
    print(f"Test User ID: {TEST_USER_ID}")
    print("-" * 50)
    
    # Note: These tests assume the API server is running
    # and that the user exists in the database
    
    # test_health_check()
    # test_create_user()
    # test_get_user_profile()
    # test_create_event()
    # test_get_events()
    # test_update_user_profile()
    
    print("To run tests, uncomment the test functions above and ensure the API server is running.")
