"""Script to generate JWT_SECRET_KEY and SECRET_KEY."""
import secrets
import string

def generate_secret_key(length=64):
    """Generate a random secret key."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret_key(length=64):
    """Generate a random JWT secret key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print("=" * 60)
    print("Generated Secret Keys")
    print("=" * 60)
    print()
    print("JWT_SECRET_KEY=" + generate_jwt_secret_key())
    print()
    print("SECRET_KEY=" + generate_secret_key())
    print()
    print("=" * 60)
    print("Copy these keys to your .env file")
    print("=" * 60)

