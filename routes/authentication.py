import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

from utils.auth_helper import login, UniCredentials, BadCredentialsException

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Check if SECRET_KEY is set
# You can generate one with: openssl rand -hex 32
if SECRET_KEY is None:
    raise Exception("SECRET_KEY environment variable not set")


class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict):
    # Create a JWT token with the data
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/token", response_model=Token)
async def login_for_access_token(credentials: UniCredentials):
    try:
        # Login ang get cookies
        cookies = await login(credentials)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Create a JWT token with the username, expiration time and cookies
        access_token = create_access_token(
            data={
                "sub": credentials.username.lower(),
                "exp": datetime.utcnow() + access_token_expires,
                "cookies": cookies,
            },
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
    except BadCredentialsException:
        # throw 401 if the credentials are incorrect
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/session")
async def session(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        # Check if the jwt contains a username
        # Even though it's technically impossible
        # Due to the JWT signing
        if username is None:
            raise credentials_exception

        # Check if the token expired
        if payload.get("exp") < datetime.utcnow().timestamp():
            raise credentials_exception

        return {
            "valid": True,
            # We just check if it's < 5 minutes from expiring
            "needs_refresh": payload.get("exp") < (
                    datetime.utcnow() + timedelta(minutes=5)
            ).timestamp()
        }
    except JWTError:
        # Someone is tampering with the token
        raise credentials_exception
