"""Script to test JWT token."""
import requests
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.jwt import verify_token, create_access_token
from app.core.config import settings


def test_login():
    """Test login endpoint."""
    print("=" * 60)
    print("Test Login")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print(f"✅ Login successful!")
            print(f"Token: {token[:50]}...")
            print(f"User: {data['user']['username']} ({data['user']['role']})")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_token_verification(token: str):
    """Test token verification."""
    print("\n" + "=" * 60)
    print("Test Token Verification")
    print("=" * 60)
    
    try:
        payload = verify_token(token)
        if payload:
            print(f"✅ Token is valid!")
            print(f"User ID: {payload.get('sub')}")
            print(f"Role: {payload.get('role')}")
            print(f"Expiration: {payload.get('exp')}")
            return True
        else:
            print(f"❌ Token is invalid!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_current_user(token: str):
    """Test get current user endpoint."""
    print("\n" + "=" * 60)
    print("Test Get Current User")
    print("=" * 60)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get current user successful!")
            print(f"User: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Get current user failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_token_without_bearer(token: str):
    """Test token without Bearer prefix."""
    print("\n" + "=" * 60)
    print("Test Token Without Bearer Prefix")
    print("=" * 60)
    
    try:
        # Test with token only (without Bearer prefix)
        headers = {"Authorization": token}
        response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Token works without Bearer prefix!")
            return True
        else:
            print(f"❌ Token requires Bearer prefix: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_token_with_extra_spaces(token: str):
    """Test token with extra spaces."""
    print("\n" + "=" * 60)
    print("Test Token With Extra Spaces")
    print("=" * 60)
    
    try:
        # Test with extra spaces
        headers = {"Authorization": f"Bearer  {token}  "}
        response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Token works with extra spaces!")
            return True
        else:
            print(f"❌ Token fails with extra spaces: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_token():
    """Test with invalid token."""
    print("\n" + "=" * 60)
    print("Test Invalid Token")
    print("=" * 60)
    
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            "http://localhost:8000/api/auth/me",
            headers=headers
        )
        
        if response.status_code == 401:
            print(f"✅ Invalid token correctly rejected!")
            print(f"Error: {response.json().get('detail')}")
            return True
        else:
            print(f"❌ Invalid token not rejected: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_jwt_secret_key():
    """Test JWT_SECRET_KEY configuration."""
    print("\n" + "=" * 60)
    print("Test JWT_SECRET_KEY Configuration")
    print("=" * 60)
    
    if not settings.JWT_SECRET_KEY:
        print(f"❌ JWT_SECRET_KEY is not set!")
        return False
    else:
        print(f"✅ JWT_SECRET_KEY is set (length: {len(settings.JWT_SECRET_KEY)})")
        return True


def main():
    """Main function."""
    print("=" * 60)
    print("JWT Token Test Script")
    print("=" * 60)
    print()
    
    # Test JWT_SECRET_KEY
    if not test_jwt_secret_key():
        print("\n❌ Please set JWT_SECRET_KEY in .env file!")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Login failed! Please check your credentials and database connection.")
        return
    
    # Test token verification
    if not test_token_verification(token):
        print("\n❌ Token verification failed!")
        return
    
    # Test get current user
    if not test_get_current_user(token):
        print("\n❌ Get current user failed!")
        return
    
    # Test token without Bearer prefix
    test_token_without_bearer(token)
    
    # Test token with extra spaces
    test_token_with_extra_spaces(token)
    
    # Test invalid token
    test_invalid_token()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✅ All tests completed!")
    print(f"\nToken for API client: {token}")
    print(f"\nHeader format: Authorization: Bearer {token[:20]}...")


if __name__ == "__main__":
    main()

