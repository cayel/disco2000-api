import os
from jwt_utils import create_access_token

def get_test_jwt_contributeur():
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@user.com",
        "identifier": "testuser",
        "roles": ["contributeur"]
    }
    return create_access_token(data)
