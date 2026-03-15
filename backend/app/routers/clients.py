"""Client CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_service_client, require_admin
from app.models.schemas import ClientCreate, ClientResponse, ClientUpdate, UserProfile

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
async def list_clients(
    search: str | None = None,
    industry: str | None = None,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ClientResponse]:
    """List all clients. Optionally filter by name (search) or industry type."""
    service = get_service_client()
    query = service.table("clients").select("*")

    if search:
        query = query.ilike("name", f"%{search}%")
    if industry:
        query = query.eq("industry_type", industry)

    result = query.order("created_at", desc=True).execute()
    return [ClientResponse(**r) for r in (result.data or [])]


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> ClientResponse:
    """Create a new client. Any authenticated user can create clients."""
    service = get_service_client()
    result = (
        service.table("clients")
        .insert({**data.model_dump(), "created_by": current_user.id})
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create client")

    return ClientResponse(**result.data[0])


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ClientResponse:
    """Get a single client by ID."""
    service = get_service_client()

    try:
        result = (
            service.table("clients")
            .select("*")
            .eq("id", client_id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Client not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse(**result.data)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> ClientResponse:
    """Update an existing client (partial update — only sent fields are changed)."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    service = get_service_client()
    result = (
        service.table("clients")
        .update(update_data)
        .eq("id", client_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")

    return ClientResponse(**result.data[0])


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: str,
    _: UserProfile = Depends(require_admin),
) -> None:
    """Delete a client and all associated data. Admin only."""
    service = get_service_client()
    service.table("clients").delete().eq("id", client_id).execute()
    return None
