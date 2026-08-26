from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from genomeai_api.ratelimit.providers import AIProvider

router = APIRouter(prefix="/admin/limits", tags=["admin", "limits"])


class LimitToggleRequest(BaseModel):
    enabled: bool


class ConfigUpdateRequest(BaseModel):
    global_requests_per_minute: int | None = Field(default=None, ge=0)
    global_requests_per_hour: int | None = Field(default=None, ge=0)
    global_requests_per_day: int | None = Field(default=None, ge=0)
    per_endpoint_requests_per_minute: int | None = Field(default=None, ge=0)
    per_endpoint_requests_per_hour: int | None = Field(default=None, ge=0)
    ai_tokens_per_minute: int | None = Field(default=None, ge=0)
    ai_tokens_per_hour: int | None = Field(default=None, ge=0)
    ai_tokens_per_day: int | None = Field(default=None, ge=0)
    ai_requests_per_minute: int | None = Field(default=None, ge=0)
    ai_requests_per_hour: int | None = Field(default=None, ge=0)
    ai_requests_per_day: int | None = Field(default=None, ge=0)


class ProviderQuotaRequest(BaseModel):
    requests_per_minute: int | None = Field(default=None, ge=0)
    requests_per_day: int | None = Field(default=None, ge=0)
    tokens_per_minute: int | None = Field(default=None, ge=0)
    tokens_per_day: int | None = Field(default=None, ge=0)
    enabled: bool | None = None


def _get_controller(request: Request) -> Any:
    state = request.app.state.app_state
    if not hasattr(state, "limit_controller") or state.limit_controller is None:
        raise HTTPException(status_code=503, detail="Rate limit controller not initialized")
    return state.limit_controller


@router.get("/status")
async def get_status(request: Request) -> dict[str, Any]:
    controller = _get_controller(request)
    status = controller.get_status()
    usage = await controller.get_all_provider_usage()
    status["usage"] = {
        p.value: {
            "requests_minute": u.requests_minute,
            "requests_day": u.requests_day,
            "tokens_minute": u.tokens_minute,
            "tokens_day": u.tokens_day,
        }
        for p, u in usage.items()
    }
    return status


@router.post("/api/toggle")
async def toggle_api_limits(
    body: LimitToggleRequest,
    request: Request,
) -> dict[str, str]:
    controller = _get_controller(request)
    if body.enabled:
        controller.enable_api_limits()
    else:
        controller.disable_api_limits()
    return {"status": "ok", "api_rate_limiting": "enabled" if body.enabled else "disabled"}


@router.post("/ai/toggle")
async def toggle_ai_limits(
    body: LimitToggleRequest,
    request: Request,
) -> dict[str, str]:
    controller = _get_controller(request)
    if body.enabled:
        controller.enable_ai_limits()
    else:
        controller.disable_ai_limits()
    return {"status": "ok", "ai_rate_limiting": "enabled" if body.enabled else "disabled"}


@router.post("/all/toggle")
async def toggle_all_limits(
    body: LimitToggleRequest,
    request: Request,
) -> dict[str, str]:
    controller = _get_controller(request)
    if body.enabled:
        controller.enable_all()
    else:
        controller.disable_all()
    return {"status": "ok", "all_limits": "enabled" if body.enabled else "disabled"}


@router.patch("/config")
async def update_config(
    body: ConfigUpdateRequest,
    request: Request,
) -> dict[str, Any]:
    controller = _get_controller(request)
    kwargs = body.model_dump(exclude_none=True)
    new_config = controller.update_config(**kwargs)
    return {"status": "ok", "config": new_config.__dict__}


@router.get("/config")
async def get_config(request: Request) -> dict[str, Any]:
    controller = _get_controller(request)
    return controller.get_config().__dict__


@router.get("/providers")
async def get_all_providers(request: Request) -> dict[str, Any]:
    controller = _get_controller(request)
    quotas = controller.get_all_provider_quotas()
    return {
        p.value: {
            "enabled": q.enabled,
            "requests_per_minute": q.requests_per_minute,
            "requests_per_day": q.requests_per_day,
            "tokens_per_minute": q.tokens_per_minute,
            "tokens_per_day": q.tokens_per_day,
            "priority": q.priority,
        }
        for p, q in quotas.items()
    }


@router.get("/providers/{provider}")
async def get_provider(
    provider: AIProvider,
    request: Request,
) -> dict[str, Any]:
    controller = _get_controller(request)
    try:
        quota = controller.get_provider_quota(provider)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Provider {provider.value} not found")
    usage = await controller.get_provider_usage(provider)
    return {
        "provider": provider.value,
        "quota": {
            "enabled": quota.enabled,
            "requests_per_minute": quota.requests_per_minute,
            "requests_per_day": quota.requests_per_day,
            "tokens_per_minute": quota.tokens_per_minute,
            "tokens_per_day": quota.tokens_per_day,
            "priority": quota.priority,
        },
        "usage": {
            "requests_minute": usage.requests_minute,
            "requests_day": usage.requests_day,
            "tokens_minute": usage.tokens_minute,
            "tokens_day": usage.tokens_day,
        },
    }


@router.patch("/providers/{provider}")
async def update_provider(
    provider: AIProvider,
    body: ProviderQuotaRequest,
    request: Request,
) -> dict[str, Any]:
    controller = _get_controller(request)
    kwargs = body.model_dump(exclude_none=True)
    new_quota = controller.update_provider_quota(provider, **kwargs)
    return {
        "status": "ok",
        "provider": provider.value,
        "quota": {
            "enabled": new_quota.enabled,
            "requests_per_minute": new_quota.requests_per_minute,
            "requests_per_day": new_quota.requests_per_day,
            "tokens_per_minute": new_quota.tokens_per_minute,
            "tokens_per_day": new_quota.tokens_per_day,
        },
    }


@router.post("/providers/{provider}/enable")
async def enable_provider(
    provider: AIProvider,
    request: Request,
) -> dict[str, str]:
    controller = _get_controller(request)
    controller.enable_provider(provider)
    return {"status": "ok", "provider": provider.value, "enabled": "true"}


@router.post("/providers/{provider}/disable")
async def disable_provider(
    provider: AIProvider,
    request: Request,
) -> dict[str, str]:
    controller = _get_controller(request)
    controller.disable_provider(provider)
    return {"status": "ok", "provider": provider.value, "enabled": "false"}


@router.post("/providers/{provider}/reset")
async def reset_provider(
    provider: AIProvider,
    request: Request,
) -> dict[str, Any]:
    controller = _get_controller(request)
    deleted = await controller.reset_provider(provider)
    return {"status": "ok", "provider": provider.value, "keys_deleted": deleted}


@router.post("/reset-all")
async def reset_all(request: Request) -> dict[str, Any]:
    controller = _get_controller(request)
    deleted = await controller.reset_all()
    return {"status": "ok", "total_keys_deleted": deleted}


@router.get("/audit")
async def get_audit_log(
    request: Request,
    limit: int = 100,
) -> dict[str, Any]:
    controller = _get_controller(request)
    return {"log": controller.get_audit_log(limit)}
