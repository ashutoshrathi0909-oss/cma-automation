"""Document upload, listing, and deletion endpoints."""

import os
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

ALLOWED_EXTENSIONS: dict[str, str] = {
    "pdf": "pdf",
    "xlsx": "xlsx",
    "xls": "xls",
}

# Magic bytes (file signatures) for each allowed type
MAGIC_BYTES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "xlsx": b"PK\x03\x04",      # ZIP-based (OOXML)
    "xls": b"\xd0\xcf\x11\xe0", # OLE2 compound document
}

STORAGE_BUCKET = "documents"


def _get_extension(filename: str) -> str:
    """Return lowercase extension from filename, or empty string if none."""
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def _check_magic_bytes(content: bytes, file_type: str) -> bool:
    """Return True if content starts with the expected magic bytes for file_type."""
    expected = MAGIC_BYTES.get(file_type, b"")
    return len(content) >= len(expected) and content[: len(expected)] == expected


def _cleanup_storage(service, path: str) -> None:
    """Best-effort removal of a storage file; errors are silently ignored."""
    try:
        service.storage.from_(STORAGE_BUCKET).remove([path])
    except Exception:
        pass


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
    # ── 1. Validate extension ────────────────────────────────────────────────
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Accepted: pdf, xlsx, xls.",
        )

    # ── 2. Validate financial year range ─────────────────────────────────────
    if not (1990 <= financial_year <= 2100):
        raise HTTPException(
            status_code=400,
            detail="financial_year must be between 1990 and 2100.",
        )

    file_type = ALLOWED_EXTENSIONS[ext]

    # ── 3. Read file content ─────────────────────────────────────────────────
    content = await file.read()

    # ── 4. Magic-byte validation (guards against renamed executables) ─────────
    if not _check_magic_bytes(content, file_type):
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match declared type .{ext}.",
        )

    service = get_service_client()

    # ── 5. Verify the client exists (CRITICAL: blocks cross-client uploads) ──
    try:
        client_result = (
            service.table("clients")
            .select("id")
            .eq("id", client_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client_result.data:
        raise HTTPException(status_code=404, detail="Client not found")

    # ── 6. Upload to Supabase Storage ────────────────────────────────────────
    # UUID path prevents collisions and path-traversal attacks
    safe_name = os.path.basename(file.filename or f"upload.{ext}")
    storage_path = f"{client_id}/{uuid4()}.{ext}"

    try:
        service.storage.from_(STORAGE_BUCKET).upload(storage_path, content)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Storage upload failed. Please try again.",
        )

    # ── 7. Create database record ────────────────────────────────────────────
    try:
        result = (
            service.table("documents")
            .insert(
                {
                    "client_id": client_id,
                    "file_name": safe_name,
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
    except Exception:
        _cleanup_storage(service, storage_path)
        raise HTTPException(status_code=500, detail="Failed to save document record")

    if not result.data:
        _cleanup_storage(service, storage_path)
        raise HTTPException(status_code=500, detail="Failed to save document record")

    return DocumentResponse(**result.data[0])


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    client_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[DocumentResponse]:
    """List all documents for a client, newest first."""
    service = get_service_client()

    # Verify the client exists before listing (CRITICAL: blocks cross-client reads)
    try:
        client_result = (
            service.table("clients")
            .select("id")
            .eq("id", client_id)
            .single()
            .execute()
        )
    except APIError:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client_result.data:
        raise HTTPException(status_code=404, detail="Client not found")

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
    service.storage.from_(STORAGE_BUCKET).remove([doc["file_path"]])
    service.table("documents").delete().eq("id", document_id).execute()
    return None
