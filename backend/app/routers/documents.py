"""Document upload, listing, and deletion endpoints."""

import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from postgrest.exceptions import APIError

from app.dependencies import get_current_user, get_service_client
from app.models.schemas import (
    DetectNamesResponse,
    DocumentNature,
    DocumentResponse,
    DocumentType,
    FilterPagesRequest,
    FilterPagesResponse,
    PageCountResponse,
    RedactionApplyRequest,
    RedactionApplyResponse,
    RedactionPreviewRequest,
    RedactionPreviewResponse,
    SourceUnit,
    UserProfile,
)
from app.services.pdf.page_manager import (
    get_page_count,
    pages_to_keep,
    parse_page_ranges,
    remove_pages,
)
from app.services.pdf.redaction_service import (
    apply_redaction,
    detect_company_names,
    preview_redaction,
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
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

# MIME types for each file type (used when uploading to Supabase Storage)
MIME_TYPES: dict[str, str] = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
}


def _get_extension(filename: str) -> str:
    """Return lowercase extension from filename, or empty string if none."""
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def _check_magic_bytes(content: bytes, file_type: str) -> bool:
    """Return True if content starts with the expected magic bytes for file_type."""
    expected = MAGIC_BYTES.get(file_type, b"")
    return len(content) >= len(expected) and content[: len(expected)] == expected


def _get_owned_document(document_id: str, current_user: UserProfile) -> dict:
    """Fetch document and verify ownership. Admins can access all documents.

    Raises
    ------
    HTTPException 404  — document not found
    HTTPException 403  — user does not own this document (non-admin)
    """
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
    if current_user.role != "admin" and doc.get("uploaded_by") != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this document",
        )
    return doc


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
    source_unit: SourceUnit = Form("rupees"),
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

    # ── 4. File size guard (must check before storage upload) ────────────────
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum allowed size is 50 MB.",
        )

    # ── 5. Magic-byte validation (guards against renamed executables) ─────────
    if not _check_magic_bytes(content, file_type):
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match declared type .{ext}.",
        )

    service = get_service_client()

    # ── 6. Verify the client exists (CRITICAL: blocks cross-client uploads) ──
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

    # ── 7. Upload to Supabase Storage ────────────────────────────────────────
    # UUID path prevents collisions and path-traversal attacks
    safe_name = os.path.basename(file.filename or f"upload.{ext}")
    storage_path = f"{client_id}/{uuid4()}.{ext}"

    try:
        service.storage.from_(STORAGE_BUCKET).upload(
            storage_path,
            content,
            {"content-type": MIME_TYPES.get(file_type, "application/octet-stream")},
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Storage upload failed. Please try again.",
        )

    # ── 8. Create database record ────────────────────────────────────────────
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
                    "source_unit": source_unit,
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


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DocumentResponse:
    """Return a single document by ID."""
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

    return DocumentResponse(**result.data)


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


@router.get("/{document_id}/page-count", response_model=PageCountResponse)
async def get_document_page_count(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> PageCountResponse:
    """Return total page count for a PDF document."""
    # ── 1. Fetch document record + ownership check ────────────────────────────
    doc = _get_owned_document(document_id, current_user)
    service = get_service_client()

    # ── 2. Verify it's a PDF ──────────────────────────────────────────────────
    if doc.get("file_type") != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Page count is only supported for PDF documents.",
        )

    # ── 3. Download PDF from Supabase Storage ─────────────────────────────────
    file_path: str = doc["file_path"]
    try:
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to download document from storage.")

    # ── 4. Get page count ─────────────────────────────────────────────────────
    page_count = get_page_count(file_content)

    # ── 5. Update original_page_count in DB if not already set ───────────────
    if not doc.get("original_page_count"):
        service.table("documents").update(
            {"original_page_count": page_count}
        ).eq("id", document_id).execute()

    return PageCountResponse(document_id=document_id, page_count=page_count)


@router.post("/{document_id}/filter-pages", response_model=FilterPagesResponse)
async def filter_document_pages(
    document_id: str,
    body: FilterPagesRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> FilterPagesResponse:
    """Remove specified pages from PDF, save filtered version for OCR."""
    # ── 1. Fetch document + ownership check ───────────────────────────────────
    doc = _get_owned_document(document_id, current_user)
    service = get_service_client()

    if doc.get("file_type") != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Page filtering is only supported for PDF documents.",
        )

    # ── 2. Download original PDF ──────────────────────────────────────────────
    file_path: str = doc["file_path"]
    try:
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to download document from storage.")

    # ── 3. Get page count and validate pages_to_remove ───────────────────────
    page_count = get_page_count(file_content)

    # ── 4. Parse removal list ─────────────────────────────────────────────────
    removed_pages = parse_page_ranges(body.pages_to_remove, page_count)

    # ── 5. Guard: nothing to remove → 400 ────────────────────────────────────
    if not removed_pages:
        raise HTTPException(
            status_code=400,
            detail="No valid pages to remove. Check the pages_to_remove value.",
        )

    # ── 6. Build keep list and create filtered PDF ────────────────────────────
    keep_pages = pages_to_keep(body.pages_to_remove, page_count)
    if not keep_pages:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove all pages. At least one page must remain.",
        )
    filtered_bytes = remove_pages(file_content, keep_pages)

    # ── 7. Upload filtered PDF to Storage ────────────────────────────────────
    filtered_path = f"{file_path}_filtered.pdf"
    try:
        # Try remove first (idempotent re-filter support) — ignore errors
        try:
            service.storage.from_(STORAGE_BUCKET).remove([filtered_path])
        except Exception:
            pass
        service.storage.from_(STORAGE_BUCKET).upload(
            filtered_path,
            filtered_bytes,
            {"content-type": "application/pdf"},
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to upload filtered PDF to storage.")

    # ── 8. Update document record ─────────────────────────────────────────────
    service.table("documents").update(
        {
            "filtered_file_path": filtered_path,
            "removed_pages": removed_pages,
            "original_page_count": page_count,
        }
    ).eq("id", document_id).execute()

    # ── 9. Return response ────────────────────────────────────────────────────
    return FilterPagesResponse(
        document_id=document_id,
        original_page_count=page_count,
        removed_pages=removed_pages,
        filtered_page_count=page_count - len(removed_pages),
    )


@router.post("/{document_id}/detect-names", response_model=DetectNamesResponse)
async def detect_document_names(
    document_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DetectNamesResponse:
    """Auto-detect company names from PDF header (first page)."""
    doc = _get_owned_document(document_id, current_user)
    service = get_service_client()

    if doc.get("file_type") != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Name detection is only supported for PDF documents.",
        )

    file_path: str = doc["file_path"]
    try:
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to download document from storage.")

    detected = detect_company_names(file_content)
    return DetectNamesResponse(document_id=document_id, detected_names=detected)


@router.post("/{document_id}/preview-redaction", response_model=RedactionPreviewResponse)
async def preview_document_redaction(
    document_id: str,
    body: RedactionPreviewRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> RedactionPreviewResponse:
    """Count redaction instances across all pages without modifying the PDF."""
    doc = _get_owned_document(document_id, current_user)
    service = get_service_client()

    if doc.get("file_type") != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Redaction preview is only supported for PDF documents.",
        )

    if not body.terms:
        raise HTTPException(status_code=400, detail="At least one term is required.")

    file_path: str = doc["file_path"]
    try:
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to download document from storage.")

    term_counts = preview_redaction(file_content, body.terms)
    total = sum(term_counts.values())
    return RedactionPreviewResponse(
        document_id=document_id,
        term_counts=term_counts,
        total_instances=total,
    )


@router.post("/{document_id}/apply-redaction", response_model=RedactionApplyResponse)
async def apply_document_redaction(
    document_id: str,
    body: RedactionApplyRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> RedactionApplyResponse:
    """Apply true redaction to PDF. Creates redacted copy, preserves original."""
    doc = _get_owned_document(document_id, current_user)
    service = get_service_client()

    if doc.get("file_type") != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Redaction is only supported for PDF documents.",
        )

    if not body.terms:
        raise HTTPException(status_code=400, detail="At least one term is required.")

    # Prefer filtered PDF if it exists, else use original
    file_path: str = doc.get("filtered_file_path") or doc["file_path"]
    try:
        file_content: bytes = service.storage.from_(STORAGE_BUCKET).download(file_path)
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to download document from storage.")

    # Apply redaction
    redacted_bytes, stats = apply_redaction(file_content, body.terms)

    # Upload redacted PDF to Storage
    redacted_path = f"{doc['file_path']}_redacted.pdf"
    try:
        try:
            service.storage.from_(STORAGE_BUCKET).remove([redacted_path])
        except Exception:
            pass
        service.storage.from_(STORAGE_BUCKET).upload(
            redacted_path,
            redacted_bytes,
            {"content-type": "application/pdf"},
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Failed to upload redacted PDF to storage.")

    # Update document record
    service.table("documents").update(
        {
            "redacted_file_path": redacted_path,
            "redaction_terms": body.terms,
            "redaction_count": stats.total_redactions,
        }
    ).eq("id", document_id).execute()

    return RedactionApplyResponse(
        document_id=document_id,
        redacted_file_path=redacted_path,
        redaction_count=stats.total_redactions,
        per_term_counts=stats.per_term,
    )
