import jwt
from fastapi import HTTPException, Security, Cookie, status, Depends
from fastapi.requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class HTTPCookieBearer(HTTPBearer):
    # Override
    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        authorization: str = request.cookies.get("token")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        if scheme.lower() != "bearer":
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)

class UserAuthHandler():
    security = HTTPCookieBearer(auto_error=False)
    bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = "SECRET"

    def hash(self, password: str):
        return self.bcrypt.hash(password)

    def verify(self, password: str, hashed: str):
        return self.bcrypt.verify(password, hashed)

    def encode_token(self, user: str):
        payload = {
            "exp": datetime.utcnow() + timedelta(days=0, minutes=30),
            "iat": datetime.utcnow(),
            "sub": user
        }

        return jwt.encode(payload, self.secret, algorithm="HS256")

    def decode_token(self, token: bytes):
        try:
            payload: Dict[str, Any] = jwt.decode(token, self.secret, algorithms=["HS256"])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, details="Invalid token")

    def login_optional(self, auth: HTTPAuthorizationCredentials = Security(security)):
        if isinstance(auth, HTTPException):
            return None

        return self.decode_token(auth.credentials)

    def login_required(self, auth: HTTPAuthorizationCredentials = Security(security)):
        if isinstance(auth, HTTPException):
            raise auth

        return self.decode_token(auth.credentials)

    def admin_required(self, auth: HTTPAuthorizationCredentials = Security(security)):
        if isinstance(auth, HTTPException):
            raise auth

        user = self.decode_token(auth.credentials)

        if not user["admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        return self.decode_token(auth.credentials)