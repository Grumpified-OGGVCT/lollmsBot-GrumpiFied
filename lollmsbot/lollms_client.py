from __future__ import annotations

from typing import Any

from lollms_client import LollmsClient  # from lollms-client package[web:21][web:41]

from .config import LollmsSettings


def build_lollms_client(settings: LollmsSettings | None = None) -> LollmsClient:
    """
    Build a LollmsClient either in 'LoLLMS server' mode or 'direct binding' mode
    depending on env settings.
    """
    if settings is None:
        settings = LollmsSettings.from_env()

    # Basic shared kwargs
    client_kwargs: dict[str, Any] = {}

    if settings.host_address:
        client_kwargs["host_address"] = settings.host_address

    # Some lollms_client versions support verify_ssl; if not, this can be removed
    if settings.verify_ssl is False:
        client_kwargs["verify_ssl"] = False

    # Direct binding mode
    return LollmsClient(
        llm_binding_name= settings.binding_name or "lollms",
        llm_binding_config={
            "host_address":settings.host_address,
            "model_name":settings.model_name,
            "service_key":settings.api_key,
            "ctx_size":settings.context_size,
        },
    )
