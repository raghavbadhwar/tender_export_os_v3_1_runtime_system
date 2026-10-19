"""Supplier directory safe adapter."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class SupplierDirectoryAdapter(GeMAdapter):
    name = "supplier_directory"
    source_name = "Supplier Directory"
    source_type = "supplier"
    workflow_type = "SUPPLIER"
    base_url = "https://www.indiamart.com"
