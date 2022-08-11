import jwt
from fastapi import Depends, HTTPException, status
from jwt import PyJWTError

from db.session import get_db
from db.models import users as models
from db.schemas import users as schemas
from db.schemas.token import TokenData
from db.crud.users import get_blacklisted_token, get_user_by_alias, create_user, get_user_by_wallet_address
from core import security


async def get_current_user(
    db=Depends(get_db), token: str = Depends(security.oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        alias: str = payload.get("sub")
        if alias is None:
            raise credentials_exception
        permissions: str = payload.get("permissions")
        token_data = TokenData(alias=alias, permissions=permissions)
    except PyJWTError:
        raise credentials_exception
    blacklisted = get_blacklisted_token(db, token)
    if blacklisted:
        raise credentials_exception
    user = get_user_by_alias(db, token_data.alias)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def authenticate_user(db, alias: str, password: str):
    user = get_user_by_alias(db, alias)
    if not user:
        return False
    if not security.verify_password(password, user.hashed_password):
        return False
    return user


def sign_up_new_user(db, alias: str, password: str, primary_wallet_address=None):
    # these checks are redundant as db already enforces unique constraints
    user = get_user_by_alias(db, alias)
    if user:
        return False  # User already exists
    if primary_wallet_address:
        user = get_user_by_wallet_address(db, primary_wallet_address)
        if user:
            return False  # Address is taken?

    new_user = create_user(
        db,
        schemas.UserCreate(
            alias=alias,
            password=password,
            primary_wallet_address=primary_wallet_address,
            is_active=True,
            is_superuser=False,
        ),
    )

    return new_user
