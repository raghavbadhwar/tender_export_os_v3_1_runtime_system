"""Source adapter registry."""

from __future__ import annotations

from typing import Any

from scripts.source_adapters.cppp_adapter import CPPPAdapter
from scripts.source_adapters.epublish_adapter import EPublishAdapter
from scripts.source_adapters.gem_adapter import GeMAdapter
from scripts.source_adapters.india_business_portal_adapter import IndiaBusinessPortalAdapter
from scripts.source_adapters.indian_trade_portal_adapter import IndianTradePortalAdapter
from scripts.source_adapters.mahatenders_adapter import MahaTendersAdapter
from scripts.source_adapters.mock_adapter import MockSourceAdapter
from scripts.source_adapters.punjab_etender_adapter import PunjabETenderAdapter
from scripts.source_adapters.supplier_directory_adapter import SupplierDirectoryAdapter
from scripts.source_adapters.ungm_adapter import UNGMAdapter

ADAPTERS = {
    "mock": MockSourceAdapter,
    "gem": GeMAdapter,
    "cppp": CPPPAdapter,
    "epublish": EPublishAdapter,
    "mahatenders": MahaTendersAdapter,
    "punjab": PunjabETenderAdapter,
    "indian_trade_portal": IndianTradePortalAdapter,
    "india_business_portal": IndiaBusinessPortalAdapter,
    "ungm": UNGMAdapter,
    "supplier_directory": SupplierDirectoryAdapter,
}


def get_adapter_class(name: str):
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown source adapter: {name}. Available: {', '.join(sorted(ADAPTERS))}") from exc


def create_adapter(name: str, **kwargs: Any):
    cls = get_adapter_class(name)
    if name == "mock":
        return cls()
    return cls(**kwargs)
