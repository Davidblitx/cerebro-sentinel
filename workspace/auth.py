```python
import hashlib
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def generate_salt():
    return os.urandom(16).hex()

def hash_password_with_salt(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

def verify_password_with_salt(provided_password, stored_password, salt):
    return stored_password == hash_password_with_salt(provided_password, salt)
```