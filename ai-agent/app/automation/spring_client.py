"""Fail-closed HTTP client for the proposed Spring automation contract.

Construction and validation never open a network connection.  The worker
creates this client only after two explicit live-delivery configuration
gates pass; the default worker path remains dry-run.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import RLock
from typing import Any
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr


logger = logging.getLogger(__name__)

TOKEN_PATH = "/api/v1/internal/auth/service-token"
ACTION_PATH = "/api/v1/internal/automation/actions"
REQUIRED_SCOPE = "automation:write"
EVENT_SCHEMA_VERSION = "1.0"

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
# ``backend`` is the fixed service alias on the private Docker Compose
# network. Public/non-local hosts still require HTTPS.
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "backend"}

EVENT_ID_PATTERN = re.compile(r"^evt_[0-9a-f]{32}$")
IDEMPOTENCY_KEY_PATTERN = re.compile(
    r"^hse-automation:v1:[0-9a-f]{64}$"
)
ERROR_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")

EVENT_BODY_FIELDS = {
    "schema_version",
    "event_id",
    "idempotency_key",
    "rule_id",
    "entity_type",
    "entity_id",
    "alert_code",
    "action",
    "evaluated_at_utc",
    "business_date",
    "payload",
}
LOCAL_ONLY_FIELDS = {"delivery_mode"}
SPRING_DELIVERY_MODE = "spring"
MAX_TEXT_LENGTH = 512
MAX_PAYLOAD_BYTES = 16_384


@dataclass(frozen=True, slots=True)
class RuleContract:
    """Expected immutable shape for one supported rule."""

    entity_type: str
    action: str
    entity_id_field: str
    required_payload_fields: frozenset[str]
    allowed_payload_fields: frozenset[str]


RULE_CONTRACTS = {
    "AUT-001": RuleContract(
        entity_type="PERMIT",
        action="FLAG_OVERDUE_PERMIT",
        entity_id_field="permit_id",
        required_payload_fields=frozenset(
            {"permit_id", "expiry_at", "status", "minutes_overdue"}
        ),
        allowed_payload_fields=frozenset(
            {
                "permit_id",
                "department_id",
                "zone_id",
                "requester_id",
                "issuer_id",
                "expiry_at",
                "risk_level",
                "status",
                "minutes_overdue",
            }
        ),
    ),
    "AUT-002": RuleContract(
        entity_type="CERTIFICATE",
        action="CREATE_TRAINING_REMINDER",
        entity_id_field="certificate_id",
        required_payload_fields=frozenset(
            {
                "certificate_id",
                "expiry_date",
                "status",
                "days_to_expiry",
            }
        ),
        allowed_payload_fields=frozenset(
            {
                "certificate_id",
                "employee_id",
                "manager_id",
                "course_id",
                "expiry_date",
                "status",
                "days_to_expiry",
            }
        ),
    ),
    "AUT-003": RuleContract(
        entity_type="CAPA",
        action="CREATE_CAPA_ESCALATION",
        entity_id_field="capa_id",
        required_payload_fields=frozenset(
            {
                "capa_id",
                "due_date",
                "status",
                "days_overdue",
                "escalation_day",
            }
        ),
        allowed_payload_fields=frozenset(
            {
                "capa_id",
                "incident_id",
                "finding_id",
                "assigned_to",
                "due_date",
                "priority",
                "status",
                "days_overdue",
                "escalation_day",
            }
        ),
    ),
    "AUT-004": RuleContract(
        entity_type="RISK",
        action="FLAG_RISK_FOR_REVIEW",
        entity_id_field="risk_id",
        required_payload_fields=frozenset(
            {"risk_id", "inherent_score", "status"}
        ),
        allowed_payload_fields=frozenset(
            {
                "risk_id",
                "department_id",
                "zone_id",
                "owner_id",
                "inherent_score",
                "risk_level",
                "residual_score",
                "status",
                "last_reviewed_at",
                "next_review_date",
                "days_since_review",
            }
        ),
    ),
}


class SpringClientError(RuntimeError):
    """Base error whose message never contains response bodies or secrets."""


class SpringClientConfigurationError(SpringClientError):
    """Raised when safe client configuration is incomplete or invalid."""


class SpringEventValidationError(SpringClientError):
    """Raised before network access when an event violates the contract."""


class SpringAuthenticationError(SpringClientError):
    """Raised when the service token cannot be obtained safely."""


class SpringTemporaryError(SpringClientError):
    """Raised after temporary failures exhaust the retry budget."""


class SpringActionRejectedError(SpringClientError):
    """Raised for a permanent Spring rejection."""

    def __init__(self, *, status_code: int, error_code: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        super().__init__("Spring permanently rejected the automation action")


@dataclass(frozen=True, slots=True)
class SpringClientConfig:
    """Explicit settings required for a future live Spring client."""

    base_url: str
    client_id: str
    client_secret: SecretStr
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 10.0
    max_attempts: int = 3
    token_refresh_leeway_seconds: int = 30

    def __post_init__(self) -> None:
        if not isinstance(self.base_url, str) or (
            self.base_url != self.base_url.strip()
        ):
            raise SpringClientConfigurationError(
                "Spring base URL is invalid"
            )

        try:
            parsed = urlsplit(self.base_url)
            parsed_port = parsed.port
        except (TypeError, ValueError):
            raise SpringClientConfigurationError(
                "Spring base URL is invalid"
            ) from None

        hostname = (parsed.hostname or "").lower()

        if parsed.scheme not in {"http", "https"} or not hostname:
            raise SpringClientConfigurationError(
                "Spring base URL must be an absolute HTTP URL"
            )
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise SpringClientConfigurationError(
                "Spring base URL cannot contain credentials, query, or fragment"
            )
        if parsed.path not in {"", "/"}:
            raise SpringClientConfigurationError(
                "Spring base URL cannot contain an API path"
            )
        if parsed.scheme != "https" and hostname not in LOCAL_HOSTS:
            raise SpringClientConfigurationError(
                "Non-local Spring endpoints require HTTPS"
            )
        if parsed_port is not None and not 1 <= parsed_port <= 65535:
            raise SpringClientConfigurationError(
                "Spring base URL port is invalid"
            )
        if (
            not isinstance(self.client_id, str)
            or not self.client_id.strip()
            or self.client_id != self.client_id.strip()
            or len(self.client_id) > 128
        ):
            raise SpringClientConfigurationError(
                "Spring automation client ID is required"
            )
        if not isinstance(self.client_secret, SecretStr):
            raise SpringClientConfigurationError(
                "Spring automation client secret is invalid"
            )
        secret_value = self.client_secret.get_secret_value()
        if (
            not secret_value.strip()
            or secret_value != secret_value.strip()
            or len(secret_value) > 4096
        ):
            raise SpringClientConfigurationError(
                "Spring automation client secret is required"
            )
        if (
            not isinstance(self.connect_timeout_seconds, (int, float))
            or isinstance(self.connect_timeout_seconds, bool)
            or not math.isfinite(self.connect_timeout_seconds)
            or self.connect_timeout_seconds <= 0
        ):
            raise SpringClientConfigurationError(
                "Spring connect timeout must be positive"
            )
        if (
            not isinstance(self.read_timeout_seconds, (int, float))
            or isinstance(self.read_timeout_seconds, bool)
            or not math.isfinite(self.read_timeout_seconds)
            or self.read_timeout_seconds <= 0
        ):
            raise SpringClientConfigurationError(
                "Spring read timeout must be positive"
            )
        if (
            not isinstance(self.max_attempts, int)
            or isinstance(self.max_attempts, bool)
            or not 1 <= self.max_attempts <= 5
        ):
            raise SpringClientConfigurationError(
                "Spring max attempts must be between 1 and 5"
            )
        if (
            not isinstance(self.token_refresh_leeway_seconds, int)
            or isinstance(self.token_refresh_leeway_seconds, bool)
            or self.token_refresh_leeway_seconds < 0
        ):
            raise SpringClientConfigurationError(
                "Token refresh leeway cannot be negative"
            )


@dataclass(frozen=True, slots=True)
class SpringActionResult:
    """Small structured outcome returned for one accepted request."""

    status: str
    event_id: str
    http_status: int
    action_record_id: str | None = None
    audit_id: str | None = None
    processed_at_utc: str | None = None
    error_code: str | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _CachedToken:
    access_token: SecretStr
    expires_at_monotonic: float


def _required_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise SpringEventValidationError(
            f"Automation event field must be text: {field_name}"
        )

    text_value = value.strip()
    if not text_value or len(text_value) > MAX_TEXT_LENGTH:
        raise SpringEventValidationError(
            f"Automation event is missing required field: {field_name}"
        )
    return text_value


def _utc_timestamp(value: Any, *, field_name: str) -> str:
    text_value = _required_text(value, field_name=field_name)
    try:
        parsed = datetime.fromisoformat(
            text_value.replace("Z", "+00:00")
        )
    except ValueError:
        raise SpringEventValidationError(
            f"Automation event timestamp is invalid: {field_name}"
        ) from None

    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(
        parsed
    ):
        raise SpringEventValidationError(
            f"Automation event timestamp must be UTC: {field_name}"
        )
    return text_value


def _calendar_date(value: Any, *, field_name: str) -> str:
    text_value = _required_text(value, field_name=field_name)
    try:
        datetime.strptime(text_value, "%Y-%m-%d")
    except ValueError:
        raise SpringEventValidationError(
            f"Automation event date is invalid: {field_name}"
        ) from None
    return text_value


def _calendar_date_or_utc_timestamp(value: Any, *, field_name: str) -> str:
    text_value = _required_text(value, field_name=field_name)
    try:
        datetime.strptime(text_value, "%Y-%m-%d")
        return text_value
    except ValueError:
        pass

    try:
        parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise SpringEventValidationError(
                f"Automation event timestamp must be UTC: {field_name}"
            )
        return text_value
    except (ValueError, TypeError):
        raise SpringEventValidationError(
            f"Automation event date/timestamp is invalid: {field_name}"
        ) from None


def _validate_payload_value(value: Any, *, field_name: str) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise SpringEventValidationError(
            f"Automation payload number is invalid: {field_name}"
        )
    if isinstance(value, str) and len(value) <= MAX_TEXT_LENGTH:
        return
    raise SpringEventValidationError(
        f"Automation payload value is invalid: {field_name}"
    )


def _response_required_text(
    payload: Mapping[str, Any],
    field_name: str,
) -> str:
    value = payload.get(field_name)
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > MAX_TEXT_LENGTH
    ):
        raise SpringClientError(
            "Spring action success response is invalid"
        )
    return value.strip()


def _response_utc_timestamp(
    payload: Mapping[str, Any],
    field_name: str,
) -> str:
    value = _response_required_text(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SpringClientError(
            "Spring action success response is invalid"
        ) from None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(
        parsed
    ):
        raise SpringClientError(
            "Spring action success response is invalid"
        )
    return value


def _safe_error_code(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return "UNKNOWN"
    value = str(payload.get("error_code") or "").strip()
    if ERROR_CODE_PATTERN.fullmatch(value):
        return value
    return "UNKNOWN"


def _response_json(response: httpx.Response) -> Mapping[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise SpringClientError(
            "Spring returned an invalid JSON response"
        ) from exc
    if not isinstance(payload, Mapping):
        raise SpringClientError(
            "Spring returned an invalid response object"
        )
    return payload


def _prepare_action(event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(event, Mapping):
        raise SpringEventValidationError(
            "Automation event must be an object"
        )

    unknown_fields = set(event) - EVENT_BODY_FIELDS - LOCAL_ONLY_FIELDS
    missing_fields = EVENT_BODY_FIELDS - set(event)
    if unknown_fields:
        raise SpringEventValidationError(
            "Automation event contains unknown top-level fields"
        )
    if missing_fields:
        raise SpringEventValidationError(
            "Automation event is missing required top-level fields"
        )

    schema_version = _required_text(
        event.get("schema_version"), field_name="schema_version"
    )
    delivery_mode = _required_text(
        event.get("delivery_mode"), field_name="delivery_mode"
    )
    event_id = _required_text(event.get("event_id"), field_name="event_id")
    idempotency_key = _required_text(
        event.get("idempotency_key"), field_name="idempotency_key"
    )
    rule_id = _required_text(event.get("rule_id"), field_name="rule_id")
    entity_type = _required_text(
        event.get("entity_type"), field_name="entity_type"
    )
    entity_id = _required_text(
        event.get("entity_id"), field_name="entity_id"
    )
    action = _required_text(event.get("action"), field_name="action")
    alert_code = _required_text(
        event.get("alert_code"), field_name="alert_code"
    )
    _utc_timestamp(
        event.get("evaluated_at_utc"), field_name="evaluated_at_utc"
    )
    _calendar_date(
        event.get("business_date"), field_name="business_date"
    )

    if schema_version != EVENT_SCHEMA_VERSION:
        raise SpringEventValidationError(
            "Unsupported automation event schema version"
        )
    if delivery_mode != SPRING_DELIVERY_MODE:
        raise SpringEventValidationError(
            "Spring delivery requires an explicitly spring-mode event"
        )
    if not EVENT_ID_PATTERN.fullmatch(event_id):
        raise SpringEventValidationError("Automation event ID is invalid")
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key):
        raise SpringEventValidationError(
            "Automation idempotency key is invalid"
        )
    if not ERROR_CODE_PATTERN.fullmatch(alert_code):
        raise SpringEventValidationError(
            "Automation alert code is invalid"
        )

    contract = RULE_CONTRACTS.get(rule_id)
    if contract is None:
        raise SpringEventValidationError("Unsupported automation rule ID")
    if entity_type != contract.entity_type or action != contract.action:
        raise SpringEventValidationError(
            "Automation event does not match its rule contract"
        )

    payload = event.get("payload")
    if not isinstance(payload, Mapping):
        raise SpringEventValidationError(
            "Automation event payload must be an object"
        )
    payload_fields = set(payload)
    if payload_fields - contract.allowed_payload_fields:
        raise SpringEventValidationError(
            "Automation payload contains forbidden fields"
        )
    if contract.required_payload_fields - payload_fields:
        raise SpringEventValidationError(
            "Automation payload is missing required fields"
        )
    for field_name, value in payload.items():
        _validate_payload_value(value, field_name=field_name)

    try:
        payload_size = len(
            json.dumps(
                payload,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
    except (TypeError, ValueError):
        raise SpringEventValidationError(
            "Automation payload is not JSON serializable"
        ) from None
    if payload_size > MAX_PAYLOAD_BYTES:
        raise SpringEventValidationError(
            "Automation payload is too large"
        )

    if str(payload.get(contract.entity_id_field)) != str(entity_id):
        raise SpringEventValidationError(
            "Automation payload entity ID does not match the event"
        )

    if rule_id == "AUT-001":
        _utc_timestamp(payload.get("expiry_at"), field_name="expiry_at")
    elif rule_id == "AUT-002":
        _calendar_date(
            payload.get("expiry_date"), field_name="expiry_date"
        )
    elif rule_id == "AUT-003":
        _calendar_date_or_utc_timestamp(
            payload.get("due_date"), field_name="due_date"
        )
    elif rule_id == "AUT-004":
        if payload.get("last_reviewed_at") is not None:
            _calendar_date_or_utc_timestamp(
                payload.get("last_reviewed_at"),
                field_name="last_reviewed_at",
            )
        if payload.get("next_review_date") is not None:
            _calendar_date_or_utc_timestamp(
                payload.get("next_review_date"),
                field_name="next_review_date",
            )

    # Detach the request from the caller and omit delivery_mode, which is
    # local dispatcher state and is forbidden by the Spring contract.
    return deepcopy(
        {field: event[field] for field in EVENT_BODY_FIELDS}
    )


class SpringAutomationClient:
    """Service-authenticated client for one-event-at-a-time delivery.

    Construction performs validation only.  No network operation happens
    until ``send_action`` is called.
    """

    def __init__(
        self,
        config: SpringClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic_clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = lambda: datetime.now(
            timezone.utc
        ),
    ) -> None:
        self._config = config
        self._sleeper = sleeper
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._cached_token: _CachedToken | None = None
        self._token_lock = RLock()
        self._closed = False
        self._client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            timeout=httpx.Timeout(
                config.read_timeout_seconds,
                connect=config.connect_timeout_seconds,
            ),
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "esca-hse-automation/1.0"},
        )

    def __enter__(self) -> SpringAutomationClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        with self._token_lock:
            if self._closed:
                return
            self._cached_token = None
            self._closed = True
            self._client.close()

    def _retry_delay(
        self,
        *,
        attempt: int,
        response: httpx.Response | None = None,
    ) -> float:
        if response is not None and response.status_code == 429:
            raw_value = response.headers.get("Retry-After", "")
            try:
                return min(max(float(raw_value), 0.0), 60.0)
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(raw_value)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    delay = (
                        retry_at.astimezone(timezone.utc)
                        - self._wall_clock().astimezone(timezone.utc)
                    ).total_seconds()
                    return min(max(delay, 0.0), 60.0)
                except (TypeError, ValueError, OverflowError):
                    pass
        return float(2 ** (attempt - 1))

    def _request_with_retry(
        self,
        *,
        stage: str,
        request: Callable[[], httpx.Response],
    ) -> httpx.Response:
        last_error_type = "UNKNOWN"

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                response = request()
            except httpx.TransportError as exc:
                last_error_type = type(exc).__name__
                if attempt == self._config.max_attempts:
                    break
                logger.warning(
                    "spring_request_retry stage=%s attempt=%d "
                    "reason=transport_error error_type=%s",
                    stage,
                    attempt,
                    last_error_type,
                )
                self._sleeper(self._retry_delay(attempt=attempt))
                continue

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                and attempt < self._config.max_attempts
            ):
                logger.warning(
                    "spring_request_retry stage=%s attempt=%d "
                    "reason=http_%dxx",
                    stage,
                    attempt,
                    response.status_code // 100,
                )
                self._sleeper(
                    self._retry_delay(attempt=attempt, response=response)
                )
                continue

            return response

        logger.error(
            "spring_request_failed stage=%s error_type=%s",
            stage,
            last_error_type,
        )
        raise SpringTemporaryError(
            f"Spring {stage} request failed after retries"
        ) from None

    def _request_token(self) -> _CachedToken:
        response = self._request_with_retry(
            stage="authentication",
            request=lambda: self._client.post(
                TOKEN_PATH,
                json={
                    "client_id": self._config.client_id,
                    "client_secret": (
                        self._config.client_secret.get_secret_value()
                    ),
                },
                headers={"Cache-Control": "no-store"},
            ),
        )

        if response.status_code in RETRYABLE_STATUS_CODES:
            raise SpringTemporaryError(
                "Spring authentication request failed after retries"
            )

        if response.status_code != 200:
            logger.error(
                "spring_authentication_failed status_class=%dxx",
                response.status_code // 100,
            )
            raise SpringAuthenticationError(
                "Spring service authentication failed"
            )

        payload = _response_json(response)
        raw_access_token = payload.get("access_token")
        raw_token_type = payload.get("token_type")
        if (
            not isinstance(raw_access_token, str)
            or not raw_access_token
            or raw_access_token != raw_access_token.strip()
            or len(raw_access_token) > 8192
            or not isinstance(raw_token_type, str)
        ):
            raise SpringAuthenticationError(
                "Spring authentication response is invalid"
            )
        access_token = raw_access_token
        token_type = raw_token_type
        raw_scope = payload.get("scope", "")
        if isinstance(raw_scope, str):
            scopes = set(raw_scope.split())
        elif (
            isinstance(raw_scope, list)
            and all(isinstance(value, str) for value in raw_scope)
        ):
            scopes = set(raw_scope)
        else:
            raise SpringAuthenticationError(
                "Spring authentication response is invalid"
            )

        expires_in = payload.get("expires_in")
        if not isinstance(expires_in, int) or isinstance(expires_in, bool):
            raise SpringAuthenticationError(
                "Spring authentication response is invalid"
            )

        if (
            not access_token
            or token_type.lower() != "bearer"
            or not 1 <= expires_in <= 86_400
            or REQUIRED_SCOPE not in scopes
        ):
            raise SpringAuthenticationError(
                "Spring authentication response is invalid"
            )

        return _CachedToken(
            access_token=SecretStr(access_token),
            expires_at_monotonic=(self._monotonic_clock() + expires_in),
        )

    def _access_token(self, *, force_refresh: bool = False) -> str:
        with self._token_lock:
            if self._closed:
                raise SpringClientError("Spring client is closed")
            if force_refresh:
                self._cached_token = None

            token = self._cached_token
            now = self._monotonic_clock()
            if (
                token is None
                or now
                >= (
                    token.expires_at_monotonic
                    - self._config.token_refresh_leeway_seconds
                )
            ):
                token = self._request_token()
                self._cached_token = token

            return token.access_token.get_secret_value()

    def validate_action(self, event: Mapping[str, Any]) -> None:
        """Validate one event without acquiring a token or using network."""

        _prepare_action(event)

    def send_action(
        self,
        event: Mapping[str, Any],
    ) -> SpringActionResult:
        """Validate and send one event using stable retry identifiers."""

        body = _prepare_action(event)
        event_id = str(body["event_id"])
        idempotency_key = str(body["idempotency_key"])
        schema_version = str(body["schema_version"])
        token = self._access_token()
        refreshed_after_401 = False

        while True:
            response = self._request_with_retry(
                stage="action",
                request=lambda: self._client.post(
                    ACTION_PATH,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": idempotency_key,
                        "X-Correlation-ID": event_id,
                        "X-Event-Schema-Version": schema_version,
                    },
                ),
            )

            if response.status_code == 401 and not refreshed_after_401:
                token = self._access_token(force_refresh=True)
                refreshed_after_401 = True
                continue
            break

        payload: Mapping[str, Any]
        if response.status_code in {200, 201, 409}:
            payload = _response_json(response)
        else:
            try:
                payload = _response_json(response)
            except SpringClientError:
                payload = {}

        if response.status_code in {200, 201}:
            expected_status = (
                "APPLIED" if response.status_code == 201 else "DUPLICATE"
            )
            if (
                payload.get("status") != expected_status
                or payload.get("event_id") != event_id
            ):
                raise SpringClientError(
                    "Spring action success response is invalid"
                )
            action_record_id = _response_required_text(
                payload,
                "action_record_id",
            )
            audit_id = _response_required_text(payload, "audit_id")
            processed_at_utc = _response_utc_timestamp(
                payload,
                "processed_at_utc",
            )
            result = SpringActionResult(
                status=expected_status,
                event_id=event_id,
                http_status=response.status_code,
                action_record_id=action_record_id,
                audit_id=audit_id,
                processed_at_utc=processed_at_utc,
            )
        elif (
            response.status_code == 409
            and payload.get("status") == "NOT_APPLICABLE"
            and payload.get("event_id") == event_id
        ):
            error_code = _safe_error_code(payload)
            if error_code == "UNKNOWN":
                raise SpringClientError(
                    "Spring not-applicable response is invalid"
                )
            result = SpringActionResult(
                status="NOT_APPLICABLE",
                event_id=event_id,
                http_status=409,
                error_code=error_code,
            )
        elif response.status_code in RETRYABLE_STATUS_CODES:
            raise SpringTemporaryError(
                "Spring action request failed after retries"
            )
        elif response.status_code == 401:
            raise SpringAuthenticationError(
                "Spring service authentication failed"
            )
        else:
            raise SpringActionRejectedError(
                status_code=response.status_code,
                error_code=_safe_error_code(payload),
            )

        logger.info(
            "spring_action_completed outcome=%s status_class=%dxx",
            result.status,
            result.http_status // 100,
        )
        return result
