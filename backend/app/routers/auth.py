"""Auth endpoints: login, register (admin-only), logout, me."""

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_service_client, get_supabase_client, require_admin
from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserProfile

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest) -> AuthResponse:
    """Login with email and password. Returns JWT access token + user profile."""
    supabase = get_supabase_client()
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not result.session or not result.session.access_token:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Fetch profile from user_profiles
    service = get_service_client()
    profile_result = (
        service.table("user_profiles")
        .select("*")
        .eq("id", result.user.id)
        .single()
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(status_code=401, detail="User profile not found")

    return AuthResponse(
        access_token=result.session.access_token,
        user=UserProfile(**profile_result.data),
    )


@router.post("/register", response_model=UserProfile, status_code=201)
async def register(
    user_data: RegisterRequest,
    _: UserProfile = Depends(require_admin),
) -> UserProfile:
    """Create a new user (admin only). Creates Supabase auth user + profile row.

    V1 design: admins can create both employees and other admins (single-firm setup).
    """
    service = get_service_client()

    try:
        new_user = service.auth.admin.create_user(
            {
                "email": user_data.email,
                "password": user_data.password,
                "email_confirm": True,
            }
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Could not create user")

    # Insert profile row
    profile_result = (
        service.table("user_profiles")
        .insert(
            {
                "id": new_user.user.id,
                "full_name": user_data.full_name,
                "role": user_data.role,
            }
        )
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(status_code=500, detail="Failed to create user profile")

    return UserProfile(**profile_result.data[0])


@router.post("/logout", status_code=204)
async def logout(current_user: UserProfile = Depends(get_current_user)) -> None:
    """Logout current user (client should discard the JWT)."""
    # Supabase JWTs are stateless — client-side logout is sufficient.
    # For server-side revocation, Supabase handles token expiry automatically.
    return None


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Return the currently authenticated user's profile."""
    return current_user
