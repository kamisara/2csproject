import jwt
from datetime import datetime, timedelta
from django.conf import settings

JWT_ALGO = "HS256"
JWT_EXP_DAYS = 7  # token validity

def create_jwt_for_user(user):
    payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXP_DAYS),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGO)
    # PyJWT>=2 returns str, older returns bytes — ensure string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except Exception:
        raise
