import uuid
from typing import Any

import httpx
import jwt
import structlog
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.config import settings

logger = structlog.get_logger(__name__)


class SupabaseAuthError(RuntimeError):
    """Raised when Supabase Auth rejects or cannot verify an auth operation."""


class SupabaseUser(BaseModel):
    """Subset of Supabase Auth user data needed by the application."""

    model_config = ConfigDict(extra="allow")

    id: uuid.UUID
    email: EmailStr
    user_metadata: dict[str, Any] = Field(default_factory=dict)


class SupabaseTokenClaims(BaseModel):
    """Validated Supabase access token claims used for app authorization."""

    model_config = ConfigDict(extra="allow")

    sub: uuid.UUID
    email: EmailStr
    user_metadata: dict[str, Any] = Field(default_factory=dict)


class SupabaseTokenVerifier:
    """Verify Supabase Auth access tokens from frontend requests."""

    def __init__(
        self,
        *,
        jwks_url: str = settings.supabase_jwks_url,
        jwt_secret: str | None = settings.SUPABASE_JWT_SECRET,
        audience: str = settings.SUPABASE_JWT_AUDIENCE,
        issuer: str | None = settings.SUPABASE_JWT_ISSUER,
    ) -> None:
        """Create a Supabase JWT verifier.

        Args:
            jwks_url: Supabase Auth JWKS endpoint for asymmetric tokens.
            jwt_secret: Optional HMAC secret for self-hosted or test tokens.
            audience: Expected JWT audience.
            issuer: Optional expected JWT issuer.
        """
        self.jwks_client = PyJWKClient(jwks_url)
        self.jwt_secret = jwt_secret
        self.audience = audience
        self.issuer = issuer

    def verify(self, token: str) -> SupabaseTokenClaims:
        """Verify a bearer token and return Supabase claims.

        Args:
            token: Raw bearer token from the Authorization header.

        Returns:
            Validated Supabase claims.

        Raises:
            SupabaseAuthError: Raised when token verification fails.
        """
        try:
            header = jwt.get_unverified_header(token)
            algorithm = str(header.get("alg", ""))
            key = self._get_signing_key(token=token, algorithm=algorithm)
            decode_kwargs: dict[str, Any] = {
                "algorithms": [algorithm],
                "audience": self.audience,
            }
            if self.issuer:
                decode_kwargs["issuer"] = self.issuer
            payload = jwt.decode(token, key, **decode_kwargs)
            return SupabaseTokenClaims.model_validate(payload)
        except (InvalidTokenError, PyJWKClientError, ValueError) as exc:
            logger.warning("supabase_token_verification_failed", error=str(exc))
            raise SupabaseAuthError("Could not validate credentials") from exc

    def _get_signing_key(self, *, token: str, algorithm: str) -> Any:
        """Resolve the signing key for the token algorithm.

        Args:
            token: JWT access token.
            algorithm: JWT signing algorithm from the token header.

        Returns:
            Signing key suitable for PyJWT decode.

        Raises:
            SupabaseAuthError: Raised when no compatible key is configured.
        """
        if algorithm.startswith("HS"):
            if not self.jwt_secret:
                raise SupabaseAuthError("SUPABASE_JWT_SECRET is required for HMAC JWTs")
            return self.jwt_secret
        return self.jwks_client.get_signing_key_from_jwt(token).key


class SupabaseAdminClient:
    """Small client for Supabase Auth admin operations used by the backend."""

    def __init__(
        self,
        *,
        base_url: str = settings.supabase_auth_base_url,
        secret_key: str = settings.SUPABASE_SECRET_KEY,
        timeout: float = 10.0,
    ) -> None:
        """Create a Supabase Auth admin API client.

        Args:
            base_url: Backend-reachable Supabase API URL.
            secret_key: Supabase secret or service-role key.
            timeout: HTTP timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.secret_key = secret_key
        self.timeout = timeout

    def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> SupabaseUser:
        """Create a confirmed Supabase Auth user.

        Args:
            email: User email.
            password: Initial user password.
            full_name: Optional display name stored in Supabase user metadata.

        Returns:
            Created Supabase user.
        """
        payload: dict[str, Any] = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name} if full_name else {},
        }
        return self._request("POST", "/auth/v1/admin/users", json=payload)

    def update_user(
        self,
        *,
        user_id: uuid.UUID,
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
    ) -> SupabaseUser:
        """Update a Supabase Auth user.

        Args:
            user_id: Supabase Auth user ID.
            email: Optional new email.
            password: Optional new password.
            full_name: Optional display name metadata.

        Returns:
            Updated Supabase user.
        """
        payload: dict[str, Any] = {}
        if email is not None:
            payload["email"] = email
            payload["email_confirm"] = True
        if password:
            payload["password"] = password
        if full_name is not None:
            payload["user_metadata"] = {"full_name": full_name}
        return self._request("PUT", f"/auth/v1/admin/users/{user_id}", json=payload)

    def delete_user(self, *, user_id: uuid.UUID) -> None:
        """Delete a Supabase Auth user.

        Args:
            user_id: Supabase Auth user ID.
        """
        self._raw_request("DELETE", f"/auth/v1/admin/users/{user_id}")

    def get_user_by_email(self, *, email: str) -> SupabaseUser | None:
        """Find a Supabase Auth user by email.

        Args:
            email: Email address to find.

        Returns:
            Supabase user when found, otherwise None.
        """
        page = 1
        while True:
            response = self._raw_request(
                "GET", "/auth/v1/admin/users", params={"page": page, "per_page": 100}
            )
            users = response.json().get("users", [])
            for user_data in users:
                if user_data.get("email") == email:
                    return SupabaseUser.model_validate(user_data)
            if len(users) < 100:
                return None
            page += 1

    def _request(self, method: str, path: str, **kwargs: Any) -> SupabaseUser:
        """Run an admin request expected to return a Supabase user.

        Args:
            method: HTTP method.
            path: Supabase Auth admin API path.
            kwargs: Additional request arguments.

        Returns:
            Supabase user from the response body.
        """
        response = self._raw_request(method, path, **kwargs)
        if response.content:
            return SupabaseUser.model_validate(response.json())
        raise SupabaseAuthError("Supabase Auth returned an empty response")

    def _raw_request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Run a Supabase Auth admin API request.

        Args:
            method: HTTP method.
            path: Supabase Auth admin API path.
            kwargs: Additional request arguments.

        Returns:
            Successful HTTP response.

        Raises:
            SupabaseAuthError: Raised when Supabase returns an error.
        """
        headers = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
        }
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )
        if response.is_success:
            return response
        raise SupabaseAuthError(
            f"Supabase Auth {method} {path} failed: {response.status_code} {response.text}"
        )


supabase_token_verifier = SupabaseTokenVerifier()
supabase_admin = SupabaseAdminClient()
