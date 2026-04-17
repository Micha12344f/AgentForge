"""
apollo_api.py — Apollo.io REST API wrapper for CONTENT agent (prospecting).

Usage:
    from Business.CONTENT.executions.apollo_api import ApolloAPI
    api = ApolloAPI()                                # loads key from .env
    org = api.enrich_organization("apollo.io")       # company data
    api.create_contact(first_name="Tim", last_name="Zheng", title="CEO",
                       organization_name="Apollo.io", email="tim@apollo.io")
    contacts = api.search_contacts(per_page=25)
    accounts = api.search_accounts(per_page=25)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve .env
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def _load_env(path: Path = _ENV_PATH) -> dict[str, str]:
    """Read key=value pairs from a .env file."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# ---------------------------------------------------------------------------
# ApolloAPI class
# ---------------------------------------------------------------------------

class ApolloAPI:
    """Thin wrapper around the Apollo.io REST API (Free-plan compatible)."""

    BASE = "https://api.apollo.io/api/v1"

    def __init__(self, api_key: str | None = None):
        env = _load_env()
        self.api_key = api_key or env.get("APOLLO_API_KEY", "") or os.environ.get("APOLLO_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("APOLLO_API_KEY not set in .env and not passed explicitly.")

    # -- internal helpers -------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "x-api-key": self.api_key,
            "User-Agent": "AgentForge/1.0",
        }

    def _request(self, method: str, path: str, body: dict | None = None,
                 query: dict | None = None) -> dict[str, Any]:
        url = f"{self.BASE}{path}"
        if query:
            qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in query.items())
            url = f"{url}?{qs}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode(errors="replace") if exc.fp else ""
            raise RuntimeError(
                f"Apollo API {method} {url} -> {exc.code}: {err_body}"
            ) from exc

    # =====================================================================
    # TIER 1 — Free, no credits
    # =====================================================================

    def search_contacts(self, per_page: int = 25, page: int = 1,
                        **filters) -> dict[str, Any]:
        """Search contacts in your Apollo CRM.

        Optional filters: q_keywords, contact_stage_ids[], etc.
        Returns: {contacts: [...], pagination: {total_entries, ...}}
        """
        body = {"per_page": per_page, "page": page, **filters}
        return self._request("POST", "/contacts/search", body=body)

    def search_accounts(self, per_page: int = 25, page: int = 1,
                        **filters) -> dict[str, Any]:
        """Search accounts in your Apollo CRM.

        Returns: {accounts: [...], pagination: {total_entries, ...}}
        """
        body = {"per_page": per_page, "page": page, **filters}
        return self._request("POST", "/accounts/search", body=body)

    def create_contact(self, first_name: str, last_name: str,
                       title: str = "", organization_name: str = "",
                       email: str = "", **extra) -> dict[str, Any]:
        """Create a contact in your Apollo CRM.

        Returns: {contact: {id, first_name, last_name, ...}}
        """
        body = {
            "first_name": first_name,
            "last_name": last_name,
        }
        if title:
            body["title"] = title
        if organization_name:
            body["organization_name"] = organization_name
        if email:
            body["email"] = email
        body.update(extra)
        return self._request("POST", "/contacts", body=body)

    def update_contact(self, contact_id: str, **fields) -> dict[str, Any]:
        """Update an existing contact by ID.

        Pass any updatable fields as kwargs (first_name, last_name, title, email, etc.).
        Returns: {contact: {id, ...}}
        """
        return self._request("PATCH", f"/contacts/{contact_id}", body=fields)

    # =====================================================================
    # TIER 2 — Consumes credits (1 per call)
    # =====================================================================

    def enrich_organization(self, domain: str) -> dict[str, Any]:
        """Enrich a company by domain. Returns full firmographic profile.

        Returns: {organization: {name, industry, estimated_num_employees, ...}}
        Costs: 1 credit per unique domain.
        """
        return self._request("GET", "/organizations/enrich", query={"domain": domain})

    # =====================================================================
    # TIER 3 — Requires paid plan (will raise 403 on Free)
    # =====================================================================

    def search_people(self, person_titles: list[str] | None = None,
                      person_locations: list[str] | None = None,
                      person_seniorities: list[str] | None = None,
                      organization_locations: list[str] | None = None,
                      organization_num_employees_ranges: list[str] | None = None,
                      per_page: int = 25, page: int = 1,
                      **filters) -> dict[str, Any]:
        """Search Apollo's 210M+ contact database for net-new prospects.

        REQUIRES: Paid plan + master API key. Does NOT consume credits.
        Returns: {people: [...], pagination: {...}}
        """
        body: dict[str, Any] = {"per_page": per_page, "page": page}
        if person_titles:
            body["person_titles"] = person_titles
        if person_locations:
            body["person_locations"] = person_locations
        if person_seniorities:
            body["person_seniorities"] = person_seniorities
        if organization_locations:
            body["organization_locations"] = organization_locations
        if organization_num_employees_ranges:
            body["organization_num_employees_ranges"] = organization_num_employees_ranges
        body.update(filters)
        return self._request("POST", "/mixed_people/api_search", body=body)

    def enrich_person(self, first_name: str = "", last_name: str = "",
                      email: str = "", domain: str = "",
                      linkedin_url: str = "", **extra) -> dict[str, Any]:
        """Enrich a person's data (email, phone, firmographic).

        REQUIRES: Paid plan. Costs credits.
        Returns: {person: {name, title, email, phone_numbers, ...}}
        """
        body: dict[str, Any] = {}
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if email:
            body["email"] = email
        if domain:
            body["domain"] = domain
        if linkedin_url:
            body["linkedin_url"] = linkedin_url
        body.update(extra)
        return self._request("POST", "/people/match", body=body)

    def search_organizations(self, q_organization_name: str = "",
                             organization_locations: list[str] | None = None,
                             organization_num_employees_ranges: list[str] | None = None,
                             per_page: int = 25, page: int = 1,
                             **filters) -> dict[str, Any]:
        """Search Apollo's company database.

        REQUIRES: Paid plan. Costs credits.
        Returns: {organizations: [...], pagination: {...}}
        """
        body: dict[str, Any] = {"per_page": per_page, "page": page}
        if q_organization_name:
            body["q_organization_name"] = q_organization_name
        if organization_locations:
            body["organization_locations"] = organization_locations
        if organization_num_employees_ranges:
            body["organization_num_employees_ranges"] = organization_num_employees_ranges
        body.update(filters)
        return self._request("POST", "/mixed_companies/search", body=body)


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    api = ApolloAPI()
    if len(sys.argv) > 1:
        domain = sys.argv[1]
        print(f"Enriching: {domain}")
        result = api.enrich_organization(domain)
        org = result.get("organization", {})
        print(f"  Name:      {org.get('name')}")
        print(f"  Industry:  {org.get('industry')}")
        print(f"  Employees: {org.get('estimated_num_employees')}")
        print(f"  LinkedIn:  {org.get('linkedin_url')}")
        print(f"  Keywords:  {', '.join((org.get('keywords') or [])[:5])}")
    else:
        print("Usage: python apollo_api.py <domain>")
        print("Example: python apollo_api.py apollo.io")
        print()
        # Default: show contact count
        contacts = api.search_contacts(per_page=1)
        total = contacts.get("pagination", {}).get("total_entries", 0)
        print(f"Contacts in CRM: {total}")
        accounts = api.search_accounts(per_page=1)
        total_acc = accounts.get("pagination", {}).get("total_entries", 0)
        print(f"Accounts in CRM: {total_acc}")
