"""Document upload, listing, and deletion endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from postgrest.exceptions import APIError

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    DocumentNature,
    DocumentResponse,
    DocumentType,
    UserProfile,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Allowed file extensions (extension → FileType literal)
ALLOWED_EXTENSIONS: dict[str, str] = {
    "pdf": "pdf",
    "xlsx": "xlsx",
    "xls": "xls",
}

STORAGE_BUCKET = "documents"


def _get_extension(filename: str) -> str:
    """Return lowercase extension from filename, or empty string if none."""
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    client_id: str = Form(...),
    document_type: DocumentType = Form(...),
    financial_year: int = Form(...),
    nature: DocumentNature = Form(...),
    file: UploadFile = File(...),
    current_user: UserProfile = Depends(get_current_user),
) -> DocumentResponse:
    """Upload a financial document (PDF/Excel) and link it to a client."""
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Accepted: pdf, xlsx, xls.",
        )

    file_type = ALLOWED_EXTENSIONS[ext]

    # Read file content (whole file — large files handled by uvicorn streaming)
    content = await file.read()

    # Store in Supabase Storage using a UUID path to avoid collisions + path traversal
    storage_path = f"{client_id}/{uuid4()}.{ext}"
    service = get_service_client()
    service.storage.from_(STORAGE_BUCKET).upload(storage_path, content)

    # Create database record
    result = (
        service.table("documents")
        .insert(
            {
                "client_id": client_id,
                "file_name": file.filename,
                "file_path": storage_path,
                "file_type": file_type,
                "document_type": document_type,
                "financial_year": financial_year,
                "nature": nature,
                "extraction_status": "pending",
                "uploaded_by": current_user.id,
            }
        )
        .execute()
    )

    if not result.data:
        # Attempt to clean up the orphaned storage file
        service.storage.from_(STORAGE_BUCKET).remove([storage_path])
        raise HTTPException(status_code=500, detail="Failed to save document record")

    return DocumentResponse(**result.data[0])


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    client_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[DocumentResponse]:
    """List all documents for a client, newest first."""
    service = get_service_client()
    result = (
        service.table("documents")
        .select("*")
        .eq("client_id", client_id)
        .order("uploaded_at", desc=True)
        .execute()
    )
    return [DocumentResponse(**r) for r in (result.data or [])]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> None:
    """Delete a document: removes the file from storage and the DB record."""
    service = get_service_client()

    # Fetch the record first to get the storage path
    try:
        result = (
            service.table("documents")
            .select("*")
            .eq("id", document_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Document not found")

    if not result.data:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = result.data

    # Remove from Supabase Storage
    service.storage.from_(STORAGE_BUCKET).remove([doc["file_path"]])

    # Remove the DB record
    service.table("documents").delete().eq("id", document_id).execute()

    return None
