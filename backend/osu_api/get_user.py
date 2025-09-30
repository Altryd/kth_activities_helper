from typing import List

from ossapi import OssapiAsync, User, UserCompact
from fastapi import HTTPException
from get_logger import logger

async def get_user(id_or_username: str | int, osu_api: OssapiAsync) -> User | None:
    """
    Asynchronously retrieves an osu! user by username or ID.

    Args:
        id_or_username (str | int): The username or ID of the osu! user.
        osu_api (OssapiAsync): The osu! API client.

    Returns:
        User | None: The User object if found, otherwise None.

    Raises:
        HTTPException: If the API request fails or the input is invalid.
    """
    if id_or_username is None or (isinstance(id_or_username, str) and not id_or_username.strip()):
        logger.error(f"Invalid input in get_user: {id_or_username}")
        raise HTTPException(status_code=400, detail="Username or ID cannot be None or empty")
    try:
        user = await osu_api.user(id_or_username)
        return user
    except ValueError as ex:
        logger.error(f"ValueError in get_user for {id_or_username}: {ex}")
        raise HTTPException(status_code=400, detail="Invalid username or ID")
    except Exception as ex:
        logger.error(f"Unexpected error in get_user for {id_or_username}: {ex}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_users(ids_or_usernames: List[int], osu_api: OssapiAsync) -> List[UserCompact] | None:
    """
    Asynchronously retrieves an osu! users by IDs.
    Primarily used in project to get PP of batch of users.

    Args:
        ids_or_usernames (List[int]): The IDs of the osu! users. The usernames cannot be used!
        osu_api (OssapiAsync): The osu! API client.

    Returns:
        List[UserCompact] | None: The List[UserCompact] object if found, otherwise None.

    Raises:
        HTTPException: If the API request fails or the input is invalid.
    """
    if not ids_or_usernames:
        logger.error("Empty list of IDs provided to get_users")
        raise HTTPException(status_code=400, detail="List of IDs cannot be empty")
    if not all(isinstance(id_, int) and id_ > 0 for id_ in ids_or_usernames):
        logger.error(f"Invalid IDs in get_users: {ids_or_usernames}")
        raise HTTPException(status_code=400, detail="All IDs must be positive integers")
    try:
        users = await osu_api.users(ids_or_usernames)
        return users
    except ValueError as ex:
        logger.error(f"ValueError in get_users for {ids_or_usernames}: {ex}")
        raise HTTPException(status_code=400, detail="Invalid username or ID")
    except Exception as ex:
        logger.error(f"Unexpected error in get_users for {ids_or_usernames}: {ex}")
        raise HTTPException(status_code=500, detail="Internal server error")
