# Phase 9: Polish, Error Handling & Production — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the CMA Automation System for production with global error handling, structured error shapes, skeleton loaders, error boundaries, AlertDialog confirmations, toast wire-up, production Docker builds, and a full E2E journey test.

**Architecture:** Backend exception middleware registered on `app` in `main.py` catches `RequestValidationError` and bare `Exception`; health check uses `get_service_client()` to probe DB. Frontend polish adds shadcn Skeleton + AlertDialog UI primitives, a React error boundary in the app layout, and replaces bare `window.confirm()` and `setError` patterns. Multi-stage Docker images separate build deps from runtime. Playwright E2E anchored to a local Docker stack.

**Tech Stack:** FastAPI exception handlers, Pydantic v2, shadcn Skeleton + AlertDialog, sonner toasts, React error boundary (class component), Playwright, Docker multi-stage builds + nginx

---

## Chunk 1: Backend Exception Handlers + Health Check

### Task 1: Global Exception Handlers

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_error_handling.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_error_handling.py
"""Tests for global exception handlers registered in main.py."""

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient


class TestValidationErrorHandler:
    """POST with a body that fails Pydantic validation → structured 422."""

    def test_returns_422_with_code_and_fields(self, admin_client):
        # ClientCreate requires name (min_length=1) and industry_type
        # Sending {} triggers RequestValidationError for both missing fields
        resp = admin_client.post("/api/clients/", json={})

        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert isinstance(body["fields"], list)
        assert len(body["fields"]) > 0
        # Each field entry must have "field" and "message" keys
        for f in body["fields"]:
            assert "field" in f
            assert "message" in f

    def test_detail_key_present(self, admin_client):
        resp = admin_client.post("/api/clients/", json={})
        assert resp.status_code == 422
        assert "detail" in resp.json()


class TestUnhandledExceptionHandler:
    """Unhandled exceptions → 500, no stack trace in body."""

    def test_returns_500_no_stack_trace(self):
        # Build an isolated mini-app that copies only the handlers from main.py
        # so we don't pollute the global app's route table.
        from app.main import validation_error_handler, unhandled_exception_handler

        mini = FastAPI()
        mini.add_exception_handler(RequestValidationError, validation_error_handler)
        mini.add_exception_handler(Exception, unhandled_exception_handler)

        @mini.get("/crash")
        async def crash():
            raise RuntimeError("intentional boom")

        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/crash")

        assert resp.status_code == 500
        body = resp.json()
        assert body == {"detail": "Internal server error"}
        # No stack trace, no exception class name leaked
        assert "traceback" not in resp.text.lower()
        assert "runtimeerror" not in resp.text.lower()
        assert "boom" not in resp.text.lower()

    def test_http_exception_passes_through(self, admin_client):
        # HTTPExceptions are NOT swallowed by the generic handler.
        # 404 from the framework should stay a 404.
        resp = admin_client.get("/api/clients/nonexistent-uuid-that-does-not-exist")
        # We expect 404 or 422 — NOT 500
        assert resp.status_code in (404, 422)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_error_handling.py -v
```

Expected: `ImportError: cannot import name 'validation_error_handler'` (handler not defined yet).

- [ ] **Step 3: Implement exception handlers in `main.py`**

Add imports and two named handler functions, then register them. Export the names so tests can import them.

```python
# backend/app/main.py  (full file — replace existing content)
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    auth,
    clients,
    classification,
    cma_reports,
    conversion,
    documents,
    extraction,
    rollover,
    tasks,
    users,
)

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="CMA Automation API",
    version="1.0.0",
    description="Automates CMA document preparation for CA firms",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ────────────────────────────────────────────────────────

async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a structured 422 with per-field error details."""
    fields = []
    for error in exc.errors():
        loc = error.get("loc", ())
        # loc is a tuple like ("body", "name") — skip "body" prefix
        field_path = ".".join(str(p) for p in loc if p != "body")
        fields.append({"field": field_path, "message": error.get("msg", "Invalid value")})
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation failed",
            "code": "VALIDATION_ERROR",
            "fields": fields,
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for unexpected errors. Log internally, never expose stack traces."""
    logger.exception("Unhandled exception: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(documents.router)
app.include_router(extraction.router)
app.include_router(tasks.router)
app.include_router(classification.router)
app.include_router(cma_reports.router)
app.include_router(conversion.router)
app.include_router(rollover.router)
app.include_router(users.router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    from app.dependencies import get_service_client
    db_status = "ok"
    try:
        svc = get_service_client()
        svc.table("user_profiles").select("id").limit(1).execute()
    except Exception:
        logger.warning("Health check: Supabase connectivity failed")
        db_status = "error"
    status = "ok" if db_status == "ok" else "degraded"
    return {"status": status, "db": db_status}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_error_handling.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_error_handling.py
git commit -m "feat(phase-9): global exception handlers — structured 422 + 500 no-stack-trace"
```

---

### Task 2: Health Check Enhancement

**Files:**
- Modify: `backend/app/main.py` (already includes health logic from Task 1 above)
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_health.py
"""Tests for the /health endpoint."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    def test_health_check_returns_ok(self):
        """When Supabase is reachable, returns status=ok and db=ok."""
        mock_result = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_result
        mock_svc = MagicMock()
        mock_svc.table.return_value = mock_table

        with patch("app.main.get_service_client", return_value=mock_svc):
            client = TestClient(app)
            resp = client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"

    def test_health_check_db_failure_returns_degraded(self):
        """When Supabase raises, returns status=degraded and db=error."""
        mock_svc = MagicMock()
        mock_svc.table.return_value.select.return_value.limit.return_value.execute.side_effect = (
            Exception("connection refused")
        )

        with patch("app.main.get_service_client", return_value=mock_svc):
            client = TestClient(app)
            resp = client.get("/health")

        assert resp.status_code == 200  # health always returns 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "error"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_health.py -v
```

Expected: FAIL — health currently returns `{"status": "ok", "version": "1.0.0"}` without DB check.

- [ ] **Step 3: Verify that the health implementation written in Task 1 passes these tests**

The health implementation is already in `main.py` (Task 1, Step 3). Run:

```bash
cd backend && python -m pytest tests/test_health.py -v
```

Expected: both tests PASS.

- [ ] **Step 4: Run full backend test suite to verify no regressions**

```bash
cd backend && python -m pytest --tb=short -q
```

Expected: 360+ tests pass. If any existing test fails due to the new exception handler (e.g., tests that expected plain `{"detail": "..."}` 422 bodies), update those tests to match the new structured shape.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_health.py
git commit -m "test(phase-9): health check + DB connectivity tests"
```

---

## Chunk 2: Frontend — Skeleton, Error Boundary, Empty States

### Task 3: shadcn Skeleton Component

**Files:**
- Create: `frontend/src/components/ui/skeleton.tsx`
- Modify: `frontend/src/app/(app)/cma/[id]/page.tsx`
- Modify: `frontend/src/app/(app)/cma/[id]/review/page.tsx`
- Modify: `frontend/src/app/(app)/cma/[id]/doubts/page.tsx`

- [ ] **Step 1: Create `skeleton.tsx`**

```tsx
// frontend/src/components/ui/skeleton.tsx
import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }
```

- [ ] **Step 2: Replace `Loader2` spinner in CMA overview page**

Open `frontend/src/app/(app)/cma/[id]/page.tsx`. Replace the loading block (currently `<Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />`) with:

```tsx
// Add import at top:
import { Skeleton } from "@/components/ui/skeleton"

// Replace the loading return block:
if (loading) {
  return (
    <div className="space-y-6">
      <Skeleton className="h-5 w-32" />
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-28" />
          <Skeleton className="h-8 w-28" />
        </div>
      </div>
      <Skeleton className="h-48 w-full rounded-xl" />
    </div>
  )
}
```

- [ ] **Step 3: Replace `Loader2` spinner in review page**

Open `frontend/src/app/(app)/cma/[id]/review/page.tsx`. Replace:

```tsx
// Add import at top:
import { Skeleton } from "@/components/ui/skeleton"

// Replace the loading return block:
if (loading) {
  return (
    <div className="space-y-6">
      <Skeleton className="h-5 w-32" />
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-56" />
          <Skeleton className="h-4 w-44" />
        </div>
        <Skeleton className="h-8 w-48" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Replace `Loader2` spinner in doubts page + improve empty state**

Open `frontend/src/app/(app)/cma/[id]/doubts/page.tsx`. Replace loading block and add empty state:

```tsx
// Add imports at top:
import { CheckCircle2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

// Replace the loading return block:
if (loading) {
  return (
    <div className="space-y-6">
      <Skeleton className="h-5 w-32" />
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    </div>
  )
}

// After loading check, before render, add empty state — replace the DoubtReport render with:
return (
  <div className="space-y-6">
    <Link ...>...</Link>
    <div>
      <h1 ...>Resolve Doubts</h1>
      <p ...>...</p>
    </div>

    {doubts.length === 0 ? (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <CheckCircle2 className="mb-3 h-12 w-12 text-green-500/60" />
        <p className="font-medium text-muted-foreground">No doubt items</p>
        <p className="mt-1 text-sm text-muted-foreground">
          All classifications resolved
        </p>
      </div>
    ) : (
      <DoubtReport doubts={doubts} onResolved={handleResolved} />
    )}
  </div>
)
```

- [ ] **Step 5: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/skeleton.tsx \
        frontend/src/app/\(app\)/cma/\[id\]/page.tsx \
        frontend/src/app/\(app\)/cma/\[id\]/review/page.tsx \
        frontend/src/app/\(app\)/cma/\[id\]/doubts/page.tsx
git commit -m "feat(phase-9): skeleton loaders on CMA pages + doubts empty state"
```

---

### Task 4: React Error Boundary

**Files:**
- Create: `frontend/src/components/common/ErrorBoundary.tsx`
- Modify: `frontend/src/app/(app)/layout.tsx`

> **Why a class component?** React error boundaries must be class components — `componentDidCatch` cannot be implemented in a function component as of React 19.

- [ ] **Step 1: Create `ErrorBoundary.tsx`**

```tsx
// frontend/src/components/common/ErrorBoundary.tsx
"use client";

import { Component, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // In production, send to an error tracking service here
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
          <h2 className="text-xl font-semibold">Something went wrong</h2>
          <p className="max-w-sm text-sm text-muted-foreground">
            An unexpected error occurred. Please refresh the page or contact
            support if the problem persists.
          </p>
          <Button
            variant="outline"
            onClick={() => {
              this.setState({ hasError: false });
              window.location.reload();
            }}
          >
            Refresh page
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

- [ ] **Step 2: Wrap `main` in `(app)/layout.tsx` with the ErrorBoundary**

Open `frontend/src/app/(app)/layout.tsx`. Add the import and wrap `{children}` inside `<main>`:

```tsx
// Add import:
import { ErrorBoundary } from "@/components/common/ErrorBoundary";

// Replace:
<main className="flex-1 overflow-y-auto bg-muted/20 p-6">{children}</main>

// With:
<main className="flex-1 overflow-y-auto bg-muted/20 p-6">
  <ErrorBoundary>{children}</ErrorBoundary>
</main>
```

- [ ] **Step 3: Verify TypeScript**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/common/ErrorBoundary.tsx \
        frontend/src/app/\(app\)/layout.tsx
git commit -m "feat(phase-9): top-level error boundary in app layout"
```

---

## Chunk 3: Frontend — AlertDialog + Toast Wire-up

### Task 5: shadcn AlertDialog + Replace `window.confirm()`

**Files:**
- Create: `frontend/src/components/ui/alert-dialog.tsx`
- Modify: `frontend/src/app/(app)/clients/[id]/page.tsx`
- Modify: `frontend/src/app/(app)/settings/page.tsx`
- Modify: `frontend/src/app/(app)/cma/[id]/convert/page.tsx`

- [ ] **Step 1: Create `alert-dialog.tsx`**

This is the standard shadcn/ui AlertDialog — a thin wrapper over `@radix-ui/react-alert-dialog` (already available via `@base-ui/react` being in the project, but shadcn AlertDialog typically uses `@radix-ui`). Since the project uses shadcn and `@base-ui/react`, check if `@radix-ui/react-alert-dialog` is installed first:

```bash
cd frontend && ls node_modules/@radix-ui/react-alert-dialog 2>/dev/null && echo "exists" || echo "missing"
```

If missing, install it:
```bash
cd frontend && npm install @radix-ui/react-alert-dialog
```

Then create the component:

```tsx
// frontend/src/components/ui/alert-dialog.tsx
"use client"

import * as React from "react"
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

const AlertDialog = AlertDialogPrimitive.Root
const AlertDialogTrigger = AlertDialogPrimitive.Trigger
const AlertDialogPortal = AlertDialogPrimitive.Portal

const AlertDialogOverlay = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Overlay
    className={cn(
      "fixed inset-0 z-50 bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
    ref={ref}
  />
))
AlertDialogOverlay.displayName = AlertDialogPrimitive.Overlay.displayName

const AlertDialogContent = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Content>
>(({ className, ...props }, ref) => (
  <AlertDialogPortal>
    <AlertDialogOverlay />
    <AlertDialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      )}
      {...props}
    />
  </AlertDialogPortal>
))
AlertDialogContent.displayName = AlertDialogPrimitive.Content.displayName

const AlertDialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-2 text-center sm:text-left", className)} {...props} />
)
AlertDialogHeader.displayName = "AlertDialogHeader"

const AlertDialogFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)}
    {...props}
  />
)
AlertDialogFooter.displayName = "AlertDialogFooter"

const AlertDialogTitle = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold", className)}
    {...props}
  />
))
AlertDialogTitle.displayName = AlertDialogPrimitive.Title.displayName

const AlertDialogDescription = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
AlertDialogDescription.displayName = AlertDialogPrimitive.Description.displayName

const AlertDialogAction = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Action>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Action>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Action
    ref={ref}
    className={cn(buttonVariants(), className)}
    {...props}
  />
))
AlertDialogAction.displayName = AlertDialogPrimitive.Action.displayName

const AlertDialogCancel = React.forwardRef<
  React.ElementRef<typeof AlertDialogPrimitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof AlertDialogPrimitive.Cancel>
>(({ className, ...props }, ref) => (
  <AlertDialogPrimitive.Cancel
    ref={ref}
    className={cn(buttonVariants({ variant: "outline" }), "mt-2 sm:mt-0", className)}
    {...props}
  />
))
AlertDialogCancel.displayName = AlertDialogPrimitive.Cancel.displayName

export {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogOverlay, AlertDialogPortal, AlertDialogTitle, AlertDialogTrigger,
}
```

- [ ] **Step 2: Replace `window.confirm()` in `clients/[id]/page.tsx`**

The `handleDelete` function at line 57 uses `window.confirm()`. Replace the entire delete flow with AlertDialog state management:

```tsx
// Add import:
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// Add state after existing state declarations:
const [showDeleteDialog, setShowDeleteDialog] = useState(false)

// Replace handleDelete:
async function handleDelete() {
  if (!client) return
  setDeleting(true)
  try {
    await apiClient(`/api/clients/${client.id}`, { method: "DELETE" })
    toast.success(`"${client.name}" deleted`)
    router.replace("/clients")
  } catch (err) {
    toast.error(err instanceof Error ? err.message : "Failed to delete client")
    setDeleting(false)
  }
}

// Replace the Delete Button with AlertDialog-wrapped trigger:
<AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
  <Button
    variant="destructive"
    size="sm"
    onClick={() => setShowDeleteDialog(true)}
    disabled={deleting}
  >
    <Trash2 className="mr-1.5 h-3.5 w-3.5" />
    {deleting ? "Deleting…" : "Delete"}
  </Button>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete "{client.name}"?</AlertDialogTitle>
      <AlertDialogDescription>
        This will permanently delete the client and all associated data.
        This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
        onClick={handleDelete}
      >
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

> **Note:** `AlertDialog` wraps both the trigger button and the dialog content. The button itself is NOT `AlertDialogTrigger` here because we want to control open state manually (to avoid the trigger pattern causing layout issues with Radix).

- [ ] **Step 3: Replace `window.confirm()` in `settings/page.tsx`**

The `handleDeactivate` function at line 61 uses `window.confirm()`. Convert to AlertDialog + toast:

```tsx
// Add import:
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { toast } from "sonner"

// Add state:
const [deactivateTarget, setDeactivateTarget] = useState<string | null>(null)

// Replace handleDeactivate:
async function handleDeactivate(userId: string) {
  setUpdatingId(userId)
  setError(null)
  try {
    const updated = await apiClient<UserProfileFull>(`/api/users/${userId}/deactivate`, {
      method: "PUT",
    })
    setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)))
    toast.success("User deactivated")
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Deactivation failed"
    setError(msg)
    toast.error(msg)
  } finally {
    setUpdatingId(null)
    setDeactivateTarget(null)
  }
}

// Replace the deactivate Button with:
<Button
  variant="ghost"
  size="sm"
  onClick={() => setDeactivateTarget(user.id)}
  disabled={isUpdating}
  className="text-red-600 hover:text-red-700 hover:bg-red-50"
>
  {isUpdating ? (
    <Loader2 className="h-3 w-3 animate-spin" />
  ) : (
    <ShieldOff className="h-3 w-3" />
  )}
</Button>

// Add AlertDialog at the bottom of the return (after the Card, before closing </div>):
<AlertDialog
  open={deactivateTarget !== null}
  onOpenChange={(open) => { if (!open) setDeactivateTarget(null) }}
>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Deactivate this user?</AlertDialogTitle>
      <AlertDialogDescription>
        They will no longer be able to log in. This can be reversed by
        re-activating the account.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
        onClick={() => deactivateTarget && handleDeactivate(deactivateTarget)}
      >
        Deactivate
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

Also update `handleRoleChange` to use `toast.success()`:
```tsx
// In handleRoleChange, after successful update, add:
toast.success("Role updated")
// Remove setError(null) before try and replace setError in catch with:
toast.error(err instanceof Error ? err.message : "Update failed")
```

- [ ] **Step 4: Add confirmation dialog to convert page**

Open `frontend/src/app/(app)/cma/[id]/convert/page.tsx`. The "Confirm Conversion" button currently calls `handleConfirm()` directly. Wrap it with an AlertDialog, and add success/error toasts:

```tsx
// Add imports:
import { toast } from "sonner"
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// Add state:
const [showConfirmDialog, setShowConfirmDialog] = useState(false)

// Update handleConfirm to add toast.success and toast.error:
async function handleConfirm() {
  if (!diff || !reportId) return
  setConfirmLoading(true)
  setError(null)
  try {
    const data = await apiClient<ConversionConfirmResponse>("/api/conversion/confirm", {
      method: "POST",
      body: JSON.stringify({
        provisional_doc_id: provisionalDocId,
        audited_doc_id: auditedDocId,
        cma_report_id: reportId,
      }),
    })
    setConfirmResult(data)
    setConfirmed(true)
    toast.success(`Conversion complete — ${data.updated_count} items updated`)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Conversion failed"
    setError(msg)
    toast.error(msg)
  } finally {
    setConfirmLoading(false)
    setShowConfirmDialog(false)
  }
}

// Replace the Confirm Conversion Button with:
<AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
  <Button onClick={() => setShowConfirmDialog(true)} disabled={confirmLoading}>
    {confirmLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
    Confirm Conversion
  </Button>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Confirm conversion?</AlertDialogTitle>
      <AlertDialogDescription>
        This will update {diff?.differences?.length ?? 0} provisional amount(s) to
        audited values and flag affected classifications for re-review.
        This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleConfirm}>
        Confirm
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

- [ ] **Step 5: Verify TypeScript**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors. Fix any import or type issues before committing.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/alert-dialog.tsx \
        frontend/src/app/\(app\)/clients/\[id\]/page.tsx \
        frontend/src/app/\(app\)/settings/page.tsx \
        frontend/src/app/\(app\)/cma/\[id\]/convert/page.tsx
git commit -m "feat(phase-9): AlertDialog replaces window.confirm() on 3 pages"
```

---

### Task 6: Wire Toast Notifications for Remaining Pages

**Files:**
- Modify: `frontend/src/app/(app)/clients/[id]/rollover/page.tsx`

> **What's already done:** `review/page.tsx`, `clients/[id]/page.tsx`, and `DocumentList.tsx` already use `toast`. Settings and convert pages were updated in Task 5. The rollover page still uses `setError` for all errors.

- [ ] **Step 1: Update rollover page to use `toast.error`**

Open `frontend/src/app/(app)/clients/[id]/rollover/page.tsx`. Add `toast` import and replace the `setError(...)` call:

```tsx
// Add import:
import { toast } from "sonner"

// Replace .catch callback:
.catch(() => {
  const msg = "Failed to load client data"
  setError(msg)
  toast.error(msg)
})
```

Keep the inline error banner (`{error && <div ...>}`) as a fallback for the initial load failure — toast alone isn't enough if the page is blank.

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/\(app\)/clients/\[id\]/rollover/page.tsx
git commit -m "feat(phase-9): toast error on rollover page load failure"
```

---

## Chunk 4: Docker Production Builds

### Task 7: Multi-Stage Production Docker Images

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.prod.yml`
- Create: `frontend/nginx.conf`

- [ ] **Step 1: Create `backend/Dockerfile` (multi-stage)**

```dockerfile
# backend/Dockerfile
# Stage 1: builder — installs all deps including build tools
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime — slim image, no build tools
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

- [ ] **Step 2: Create `frontend/nginx.conf`**

```nginx
# frontend/nginx.conf
server {
    listen 3000;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Next.js static export
    location /_next/static/ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

> **Important:** Next.js App Router does NOT support `next export` (static HTML export) by default — it requires a Node.js server for RSC, server actions, etc. The production frontend image must run `next start` (not nginx), since this project uses Next.js 16 with server-side features (Supabase SSR, `createClient` in server components, `redirect()`).

- [ ] **Step 3: Create `frontend/Dockerfile` (multi-stage, Node runtime)**

```dockerfile
# frontend/Dockerfile
# Stage 1: builder — installs deps and builds Next.js
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

COPY . .

# Build Next.js for production
RUN npm run build

# Stage 2: runtime — minimal Node image, only production deps
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production

# Copy only what's needed to run `next start`
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

> **Note on standalone output:** For the `COPY .next/standalone` pattern to work, `next.config.ts` must have `output: 'standalone'`. Add that if not present.

- [ ] **Step 4: Check/update `frontend/next.config.ts` for standalone output**

```bash
cat frontend/next.config.ts
```

If `output: 'standalone'` is not there, open the file and add it:

```ts
// frontend/next.config.ts
import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  output: "standalone",
}

export default nextConfig
```

- [ ] **Step 5: Create `docker-compose.prod.yml`**

```yaml
# docker-compose.prod.yml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env.prod
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    env_file: .env.prod
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

> **Note:** No code-mount volumes in prod. No `--reload`. Env vars from `.env.prod` (create from `.env.example` on the server).

- [ ] **Step 6: Create `.env.prod.example` template**

```bash
# .env.prod.example — copy to .env.prod and fill in values on the server
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=
REDIS_URL=redis://redis:6379
BACKEND_URL=https://your-domain.com
FRONTEND_URL=https://your-domain.com
ENVIRONMENT=production
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=https://your-domain.com
```

- [ ] **Step 7: Verify build succeeds (backend)**

```bash
cd "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2"
docker build -t cma-backend-prod ./backend -f ./backend/Dockerfile
```

Expected: build completes with no errors, final image uses `runtime` stage.

- [ ] **Step 8: Verify build succeeds (frontend)**

```bash
docker build -t cma-frontend-prod ./frontend -f ./frontend/Dockerfile
```

Expected: build completes. If `next build` fails due to missing env vars, set them as build args or use `.env.local` in the build context with placeholder values.

- [ ] **Step 9: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf \
        docker-compose.prod.yml .env.prod.example frontend/next.config.ts
git commit -m "feat(phase-9): multi-stage production Docker builds"
```

---

## Chunk 5: E2E Full Journey Test

### Task 8: Playwright Setup + Full V1 Journey

**Files:**
- Create: `e2e/package.json`
- Create: `e2e/playwright.config.ts`
- Create: `e2e/full-journey.spec.ts`
- Create: `e2e/fixtures/sample.xlsx` (tiny fixture file)

> **Setup strategy:** Playwright lives in a dedicated `e2e/` workspace to avoid polluting the frontend's `package.json`. Tests target the running Docker dev stack at `http://localhost:3002`.

- [ ] **Step 1: Initialise the `e2e/` workspace**

```bash
mkdir e2e && cd e2e
npm init -y
npm install --save-dev @playwright/test
npx playwright install chromium
```

- [ ] **Step 2: Create `e2e/playwright.config.ts`**

```ts
// e2e/playwright.config.ts
import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: ".",
  testMatch: "**/*.spec.ts",
  timeout: 60_000,
  retries: 1,
  use: {
    baseURL: "http://localhost:3002",
    headless: true,
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
})
```

- [ ] **Step 3: Create a minimal `sample.xlsx` fixture**

The fixture must be a real, valid `.xlsx` file (even if it's empty). Generate it with a tiny script:

```bash
cd e2e && node -e "
const { execSync } = require('child_process');
// Create a minimal xlsx using Node Buffer magic isn't easy —
// instead, copy DOCS/CMA classification.xls as test fixture
// OR create a trivial xlsx using a python one-liner (if python available)
"
```

Simpler: copy the existing `DOCS/CMA.xlsm` to `e2e/fixtures/sample.xlsx` as a test fixture (rename extension — the upload endpoint accepts .xlsx):

```bash
mkdir -p e2e/fixtures
cp "DOCS/CMA.xlsm" e2e/fixtures/sample.xlsx
```

- [ ] **Step 4: Create `e2e/full-journey.spec.ts`**

```ts
// e2e/full-journey.spec.ts
/**
 * CMA V1 Full Journey E2E Test
 * Covers all 13 steps from login to logout.
 *
 * Pre-conditions:
 * - Docker dev stack running: docker compose up
 * - A seeded admin user exists with credentials in env vars:
 *   E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD
 */

import { test, expect, type Page } from "@playwright/test"
import path from "path"

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@test.local"
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "testpassword"
const CLIENT_NAME = `E2E Test Co ${Date.now()}`  // unique per run
const FIXTURE_PATH = path.join(__dirname, "fixtures", "sample.xlsx")

async function login(page: Page) {
  await page.goto("/login")
  await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
  await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
  await page.getByRole("button", { name: /sign in|log in/i }).click()
  await page.waitForURL("**/dashboard", { timeout: 15_000 })
}

test.describe("CMA V1 Full Journey", () => {
  test("complete workflow from login to Excel download", async ({ page }) => {
    // ── Step 1: Login ──────────────────────────────────────────────────────
    await login(page)
    await expect(page).toHaveURL(/dashboard/)

    // ── Step 2: Create a new client ────────────────────────────────────────
    await page.goto("/clients/new")
    await page.getByLabel(/client name/i).fill(CLIENT_NAME)
    // Select industry — shadcn Select or native select
    await page.getByRole("combobox", { name: /industry/i }).click()
    await page.getByRole("option", { name: /manufacturing/i }).click()
    await page.getByRole("button", { name: /create|save/i }).click()
    // After creation, redirected to client detail page
    await page.waitForURL("**/clients/**", { timeout: 15_000 })

    // ── Step 3: Verify client appears on detail page ───────────────────────
    await expect(page.getByText(CLIENT_NAME)).toBeVisible()
    const clientUrl = page.url()  // save for later navigation

    // ── Step 4: Upload a document ──────────────────────────────────────────
    await page.getByRole("link", { name: /upload/i }).click()
    await page.waitForURL("**/upload")
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(FIXTURE_PATH)
    // Select document type and year if required
    await page.getByRole("combobox", { name: /document type/i }).click()
    await page.getByRole("option", { name: /balance sheet|combined/i }).first().click()
    await page.getByRole("button", { name: /upload/i }).click()
    await expect(page.getByText(/uploaded|success/i)).toBeVisible({ timeout: 20_000 })

    // ── Step 5: Create a new CMA report ───────────────────────────────────
    await page.goto(clientUrl)
    await page.getByRole("link", { name: /new report/i }).click()
    await page.waitForURL("**/cma/new")
    // Select the uploaded document
    await page.getByRole("button", { name: /create report|create/i }).click()
    await page.waitForURL("**/cma/**", { timeout: 15_000 })
    const reportUrl = page.url()

    // ── Step 6: Trigger extraction ─────────────────────────────────────────
    // Navigate to verify page (extraction is triggered there)
    await page.goto(reportUrl.replace(/\/$/, "") + "/verify")
    // Wait for "extracted" status — extraction happens async
    await expect(
      page.getByText(/extracted|extraction complete/i)
    ).toBeVisible({ timeout: 60_000 })

    // ── Step 7: Verify all items and confirm ──────────────────────────────
    // Mark all items as verified
    const verifyAllBtn = page.getByRole("button", { name: /verify all|confirm all/i })
    if (await verifyAllBtn.isVisible()) {
      await verifyAllBtn.click()
    }
    await page.getByRole("button", { name: /confirm verification/i }).click()
    await expect(page.getByText(/verified/i)).toBeVisible({ timeout: 15_000 })

    // ── Step 8: Trigger classification ────────────────────────────────────
    await page.goto(reportUrl)
    await page.getByRole("button", { name: /classify/i }).click()
    await expect(
      page.getByText(/classified|classification complete/i)
    ).toBeVisible({ timeout: 60_000 })

    // ── Step 9: Bulk approve high-confidence items ─────────────────────────
    await page.goto(reportUrl.replace(/\/$/, "") + "/review")
    const bulkApproveBtn = page.getByRole("button", { name: /approve all high confidence/i })
    if (await bulkApproveBtn.isVisible()) {
      await bulkApproveBtn.click()
      await expect(page.getByText(/approved \d+/i)).toBeVisible({ timeout: 10_000 })
    }

    // ── Step 10: Resolve doubts if any ────────────────────────────────────
    await page.goto(reportUrl.replace(/\/$/, "") + "/doubts")
    const doubtItems = page.locator("[data-testid='doubt-item']")
    const doubtCount = await doubtItems.count()
    for (let i = 0; i < doubtCount; i++) {
      // Select a CMA field for each doubt
      await doubtItems.nth(0).getByRole("combobox").selectOption({ index: 1 })
      await doubtItems.nth(0).getByRole("button", { name: /resolve|save/i }).click()
    }

    // ── Step 11: Generate Excel ────────────────────────────────────────────
    await page.goto(reportUrl.replace(/\/$/, "") + "/generate")
    // Generation starts automatically on page load; wait for complete state
    await expect(page.getByText(/cma excel is ready|complete/i)).toBeVisible({
      timeout: 60_000,
    })

    // ── Step 12: Download Excel ────────────────────────────────────────────
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: /download/i }).click(),
    ])
    // Alternatively, if download is a signed URL opened in new tab:
    // Just verify the download button is present and clickable — signed URL
    // verification is covered by backend tests.
    expect(download.suggestedFilename()).toMatch(/\.xlsm?$/)

    // ── Step 13: Logout ────────────────────────────────────────────────────
    // Find logout button in header or sidebar
    await page.getByRole("button", { name: /logout|sign out/i }).click()
    await page.waitForURL("**/login", { timeout: 10_000 })
    await expect(page).toHaveURL(/login/)
  })
})
```

> **Note on adaptability:** Selectors use `getByRole` + `getByLabel` which are semantic and resilient to CSS changes. If the UI uses a custom Select (not a native `<select>`), update the option-picking to match shadcn's `Select` component (click trigger → click option). When a step's UI is not yet built (e.g., classify button on overview page), the test handles this gracefully by checking visibility first.

- [ ] **Step 5: Add npm script to root `package.json` (or create one)**

```bash
# From project root:
cat package.json 2>/dev/null || echo "no root package.json"
```

If no root `package.json`, create `e2e/README.md` with run instructions:

```markdown
# E2E Tests

## Run

```bash
# Start the dev stack first
docker compose up -d

# Run tests
cd e2e
E2E_ADMIN_EMAIL=admin@test.local E2E_ADMIN_PASSWORD=password npx playwright test

# Open test report
npx playwright show-report
```
```

- [ ] **Step 6: Commit**

```bash
git add e2e/
git commit -m "feat(phase-9): Playwright E2E full V1 journey test (13 steps)"
```

---

## Chunk 6: Final Gate

### Task 9: Verification + Checkpoint

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend && python -m pytest --tb=short -q
```

Expected: all tests pass, 80%+ coverage maintained.

- [ ] **Step 2: Run backend coverage report**

```bash
cd backend && python -m pytest --cov=app --cov-report=term-missing -q
```

Expected: overall coverage ≥ 80%; `test_error_handling.py` and `test_health.py` both report 100%.

- [ ] **Step 3: TypeScript check for frontend**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 4: Verify Docker prod builds**

```bash
# From project root:
docker build -t cma-backend-prod ./backend -f ./backend/Dockerfile
docker build -t cma-frontend-prod ./frontend -f ./frontend/Dockerfile
```

Expected: both builds succeed. Frontend build runs `npm run build` cleanly.

- [ ] **Step 5: Check no `window.confirm()` remains in frontend source**

```bash
grep -r "window.confirm" frontend/src/
```

Expected: no matches (all replaced with AlertDialog).

- [ ] **Step 6: Check no stack traces in 500 responses**

Already covered by `test_unhandled_exception_returns_500_no_stack_trace`.

- [ ] **Step 7: Create git tag for Phase 9 checkpoint**

```bash
git tag phase-9-production-ready
```

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "feat(phase-9): production-ready — error handling, polish, Docker, E2E"
```

---

## File Map Summary

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/main.py` | Modify | Add exception handlers + enhanced health check |
| `backend/tests/test_error_handling.py` | Create | Tests for 422 + 500 handlers |
| `backend/tests/test_health.py` | Create | Tests for health check (ok + degraded) |
| `frontend/src/components/ui/skeleton.tsx` | Create | shadcn Skeleton primitive |
| `frontend/src/components/ui/alert-dialog.tsx` | Create | shadcn AlertDialog primitive |
| `frontend/src/components/common/ErrorBoundary.tsx` | Create | React class error boundary |
| `frontend/src/app/(app)/layout.tsx` | Modify | Wrap main content with ErrorBoundary |
| `frontend/src/app/(app)/cma/[id]/page.tsx` | Modify | Skeleton loader |
| `frontend/src/app/(app)/cma/[id]/review/page.tsx` | Modify | Skeleton loader |
| `frontend/src/app/(app)/cma/[id]/doubts/page.tsx` | Modify | Skeleton loader + empty state |
| `frontend/src/app/(app)/clients/[id]/page.tsx` | Modify | AlertDialog for delete |
| `frontend/src/app/(app)/settings/page.tsx` | Modify | AlertDialog for deactivate + toasts |
| `frontend/src/app/(app)/cma/[id]/convert/page.tsx` | Modify | AlertDialog for confirm + toasts |
| `frontend/src/app/(app)/clients/[id]/rollover/page.tsx` | Modify | toast.error on load failure |
| `frontend/next.config.ts` | Modify | Add `output: 'standalone'` |
| `backend/Dockerfile` | Create | Multi-stage prod backend image |
| `frontend/Dockerfile` | Create | Multi-stage prod frontend image |
| `frontend/nginx.conf` | Create | nginx config (kept as reference, not used) |
| `docker-compose.prod.yml` | Create | Production Compose file |
| `.env.prod.example` | Create | Env var template for production |
| `e2e/playwright.config.ts` | Create | Playwright configuration |
| `e2e/full-journey.spec.ts` | Create | 13-step V1 journey test |
| `e2e/fixtures/sample.xlsx` | Create | Upload fixture file |

---

## Critical Constraints (from spec)

1. No stack traces in production error responses — enforced by `unhandled_exception_handler`
2. `keep_vba=True` and all Phase 7 Excel constraints remain — this phase does NOT touch `excel_generator.py`
3. Sonner toasts replace ALL bare `alert()` and `window.confirm()` patterns
4. Docker prod build must succeed: `docker compose -f docker-compose.prod.yml build`
5. E2E must cover the full V1 journey (steps 1–13)
6. 80%+ backend test coverage maintained
