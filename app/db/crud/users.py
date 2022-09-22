from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from starlette.responses import JSONResponse
import typing as t

from db.models import users as models
from db.schemas import users as schemas
from core.security import get_password_hash


#################################
### CRUD OPERATIONS FOR USERS ###
#################################


def get_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    return user


def get_user_by_alias(db: Session, alias: str) -> schemas.UserOut:
    return db.query(models.User).filter(models.User.alias == alias).first()


def get_user_by_wallet_address(db: Session, wallet_address: str):
    user = db.query(models.User, models.ErgoAddress).filter(
        models.ErgoAddress.address == wallet_address).first()
    if not user:
        return user
    return user[0]


def get_user_by_wallet_addresses(db: Session, addresses: t.List[str]):
    user = db.query(models.User, models.ErgoAddress).filter(
        models.User.id == models.ErgoAddress.user_id).filter(models.ErgoAddress.address.in_(addresses)).first()
    if not user:
        return user
    return user[0]


def get_primary_wallet_address_by_user_id(db: Session, user_id: int):
    return db.query(models.User, models.ErgoAddress).filter(
        models.User.id == user_id).filter(
            models.User.id == models.ErgoAddress.user_id).filter(
                models.User.primary_wallet_address_id == models.ErgoAddress.id).first()[1].address


def search_users(db: Session, search_string: str):
    raw_data = db.query(models.User, models.ErgoAddress, models.UserDetails).filter(
        models.User.id == models.ErgoAddress.user_id
    ).filter(
        models.User.id == models.UserDetails.user_id
    ).filter(
        or_(
            models.User.alias.ilike(f"%{search_string}%"),
            models.ErgoAddress.address.ilike(f"%{search_string}%"),
            models.UserDetails.name.ilike(f"%{search_string}%")
        )
    ).all()
    formatted_data = [
        {
            "id": row[0].id,
            "dao_id": row[2].dao_id,
            "alias": row[0].alias,
            "address": row[1].address,
            "name": row[2].name,
        }
        for row in raw_data
    ]
    return formatted_data


def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> t.List[schemas.UserOut]:
    return db.query(models.User).offset(skip).limit(limit).all()

def get_dao_users(db: Session, dao_id: int) -> t.List[schemas.UserDetails]:
    all_dao_users_raw = db.query(models.UserDetails).filter(models.UserDetails.dao_id==dao_id).all()
    all_dao_users = []
    for user in all_dao_users_raw:
        follower_data = get_followers_by_user_id(db, user.user_id)
        all_dao_users.append(schemas.UserDetails(
            id=user.id,
            user_id=user.user_id,
            dao_id=user.dao_id,
            name=user.name,
            profile_img_url=user.profile_img_url,
            bio=user.bio,
            level=user.level,
            xp=user.xp,
            followers=follower_data["followers"],
            following=follower_data["following"],
            social_links=user.social_links,
        ))
    return all_dao_users
    
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        alias=user.alias,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # insert primary wallet address
    if user.primary_wallet_address:
        addresses = set_ergo_addresses_by_user_id(
            db, db_user.id, [user.primary_wallet_address])
        setattr(db_user, "primary_wallet_address_id", addresses[0].id)
        db.add(db_user)
    db.commit()
    return db_user


def edit_user(
    db: Session, id: int, user: schemas.UserEdit
) -> schemas.User:

    db_user = get_user(db, id)
    if not db_user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    update_data = user.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(user.password)
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    db.delete(user)
    db.query(models.ErgoAddress).filter(
        models.ErgoAddress.user_id == user_id).delete()
    db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id).delete()
    db.query(models.UserProfileSettings).filter(
        models.UserProfileSettings.user_id == user_id).delete()
    db.query(models.UserFollower).filter(or_(models.UserFollower.followee_id ==
                                             user_id, models.UserFollower.follower_id == user_id)).delete()
    db.commit()
    return user


def get_user_address_config(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")

    addresses = get_ergo_addresses_by_user_id(db, user_id)
    return schemas.UserAddressConfig(
        id=user_id,
        alias=user.alias,
        registered_addresses=list(map(lambda x: x.address, addresses)),
    )


def get_followers_by_user_id(db: Session, user_id: int):
    followers = list(map(lambda x: x.follower_id, db.query(
        models.UserFollower).filter(models.UserFollower.followee_id == user_id).all()))
    following = list(map(lambda x: x.followee_id, db.query(
        models.UserFollower).filter(models.UserFollower.follower_id == user_id).all()))
    return {
        "followers": followers,
        "following": following
    }


def get_user_profile(db: Session, user_id: int, dao_id: int):
    db_profile = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id
    ).filter(
        models.UserDetails.dao_id == dao_id
    ).first()
    if not db_profile:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    follower_data = get_followers_by_user_id(db, user_id)
    return schemas.UserDetails(
        id=db_profile.id,
        user_id=db_profile.user_id,
        dao_id=db_profile.dao_id,
        name=db_profile.name,
        profile_img_url=db_profile.profile_img_url,
        bio=db_profile.bio,
        level=db_profile.level,
        xp=db_profile.xp,
        followers=follower_data["followers"],
        following=follower_data["following"],
        social_links=db_profile.social_links,
    )


def get_user_profile_settings(db: Session, user_id: int, dao_id: int):
    db_settings = db.query(models.UserProfileSettings).filter(
        models.UserProfileSettings.user_id == user_id
    ).filter(
        models.UserProfileSettings.dao_id == dao_id
    ).first()
    if not db_settings:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    return db_settings


def create_user_dao_profile(db: Session, user_id: int, dao_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    # create empty configs for new user
    db_user_details = models.UserDetails(
        user_id=db_user.id,
        dao_id=dao_id,
        name=db_user.alias,
        social_links=[]
    )
    db_user_profile_settings = models.UserProfileSettings(
        user_id=db_user.id,
        dao_id=dao_id,
    )
    db.add(db_user_details)
    db.add(db_user_profile_settings)
    db.commit()
    return get_user_profile(db, user_id, dao_id)


def edit_user_profile(db: Session, user_id: int, dao_id: int, user_details: schemas.UpdateUserDetails):
    db_profile = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id
    ).filter(
        models.UserDetails.dao_id == dao_id
    ).first()
    if not db_profile:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")

    update_data = user_details.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return get_user_profile(db, user_id, dao_id)


def edit_user_profile_settings(db: Session, user_id: int, dao_id: int, user_settings: schemas.UpdateUserProfileSettings):
    db_settings = get_user_profile_settings(db, user_id, dao_id)
    if not db_settings:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="User not found")
    update_data = user_settings.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_settings, key, value)

    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings


def update_user_follower(db: Session, user_id: int, follow_request: schemas.FollowUserRequest):
    if follow_request.type not in ("follow", "unfollow"):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Type must by in (follow, unfollow)")
    # delete older entry if exists
    db.query(models.UserFollower).filter(models.UserFollower.followee_id ==
                                         follow_request.user_id).filter(models.UserFollower.follower_id == user_id).delete()
    if follow_request.type == "follow":
        db_follow = models.UserFollower(
            followee_id=follow_request.user_id,
            follower_id=user_id,
        )
        db.add(db_follow)
    db.commit()
    return get_followers_by_user_id(db, user_id)


def get_ergo_addresses_by_user_id(db: Session, user_id: int):
    return db.query(models.ErgoAddress).filter(models.ErgoAddress.user_id == user_id).all()


def set_ergo_addresses_by_user_id(db: Session, user_id: int, addresses: t.List[str]):
    # get older entries if they exist
    old_addresses = list(
        map(lambda x: x.address, get_ergo_addresses_by_user_id(db, user_id))
    )
    # add new addresses
    for address in addresses:
        if address not in old_addresses:
            db_ergo_address = models.ErgoAddress(
                user_id=user_id,
                address=address,
                is_smart_contract=False,
            )
            db.add(db_ergo_address)
    db.commit()
    return get_ergo_addresses_by_user_id(db, user_id)


def update_primary_address_for_user(db: Session, user_id: int, new_address: str):
    db_user = get_user(db, user_id)
    db_addresses = get_ergo_addresses_by_user_id(db, user_id)
    addresses = list(map(lambda x: x.address, db_addresses))
    addresses.append(new_address)
    addresses = list(set(addresses))
    # update ergo_addresses table
    addresses = set_ergo_addresses_by_user_id(db, user_id, addresses)
    # get primary address id
    for address in addresses:
        if address.address == new_address:
            setattr(db_user, "alias", new_address)
            setattr(db_user, "primary_wallet_address_id", address.id)
            break
    db.add(db_user)
    db.commit()
    # uwu
    return get_user_address_config(db, user_id)


def blacklist_token(db: Session, token: str):
    db_token = models.JWTBlackList(token=token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_blacklisted_token(db: Session, token: str):
    return db.query(models.JWTBlackList).filter(models.JWTBlackList.token == token).first()
