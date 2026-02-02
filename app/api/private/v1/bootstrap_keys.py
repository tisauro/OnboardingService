from fastapi import APIRouter, HTTPException, status

from app.api.deps import PaginationDep, SessionDep
from app.core.crud.bootstrap_keys import (
    BootstrapKeyNotFoundError,
    create_key,
    delete_key,
    get_keys,
    update_key_status,
)
from app.core.schemas import schemas
from app.core.schemas.schemas import BootstrapKeyUpdateRequest

# ==============================================================================
# Private Endpoints: Admin Management
# ==============================================================================

boostrap_key_router = APIRouter()


@boostrap_key_router.post(
    "/admin/keys",
    response_model=schemas.BootstrapKeyCreateResponse,
    tags=["Admin"],
    summary="Admin: Create a new bootstrap key.",
)
async def create_bootstrap_key(
    key_data: schemas.BootstrapKeyCreateRequest,
    db: SessionDep,
):
    """
    Creates one or more new bootstrap keys.

    - `raw_key`: A new, secure key is generated automatically.
    - `key_hash`: A hash of the key is stored in the DB.
    - `key_hint`: The last 4 chars of the key are stored for identification.

    **The raw key is returned *only* at creation time.** It cannot be
    retrieved later.
    """
    try:
        db_key, raw_key = await create_key(db, key_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bootstrap key: {str(e)}",
        )

    return schemas.BootstrapKeyCreateResponse(
        id=db_key.id,
        raw_key=raw_key,  # Return the raw key this one time
        key_hint=db_key.key_hint,
        group=db_key.group,
        created_date=db_key.created_date,
        expiration_date=db_key.expiration_date,
    )


@boostrap_key_router.get(
    "/admin/keys",
    response_model=list[schemas.BootstrapKeyInfo],
    tags=["Admin"],
    summary="Admin: List all bootstrap keys.",
)
async def list_bootstrap_keys(
    pagination: PaginationDep,
    db: SessionDep,
):
    """
    Lists all bootstrap keys in the database.
    Does *not* return the raw key or hash.
    """
    try:
        keys = await get_keys(db, pagination)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list keys: {str(e)}",
        )

    return keys


@boostrap_key_router.delete(
    "/admin/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin"],
    summary="Admin: Delete a bootstrap key.",
)
async def delete_bootstrap_key(key_id: int, db: SessionDep):
    """
    Deletes a bootstrap key from the database by its ID.
    This permanently revokes the key.
    """
    try:
        await delete_key(key_id, db)
    except BootstrapKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete key: {str(e)}",
        )

    return None


@boostrap_key_router.put(
    "/admin/keys/{key_id}",
    response_model=schemas.BootstrapKeyInfo,
    tags=["Admin"],
    summary="Admin: Activate/Deactivate a bootstrap key.",
)
async def activate_bootstrap_key(
    key_id: int, key_status: BootstrapKeyUpdateRequest, db: SessionDep
):
    """
    Activates or deactivates a bootstrap key by its ID.

    > Temporarily deactivating a key will block any device using it from registering.
    """

    try:
        key = await update_key_status(key_id, key_status, db)
    except BootstrapKeyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update key: {str(e)}",
        )
    return key
