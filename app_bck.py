"""app.py — Streamlit Marketplace POC (Anywhere-style)

Implements (as requested):
1) Hardcoded multi-user login (broker/analyst/datasci).
2) Token generation is a separate tab. Token is generated based on the selected subscription product.
3) API Explorer uses ONLY the provided APIs:
   - GET /v1/listings
   - GET /v1/listings/{listing_id}
   - GET /v1/listings/export

Behavior:
- Login establishes the persona (Broker / Market Analyst / Data Scientist).
- Subscription (chosen in Token tab) establishes the access tier (Free / Paid / Enterprise).
- Generated token is shown and automatically used for API calls (Authorization: Bearer <token>).
- Tier gating:
    Free -> List endpoint
    Paid -> List + Detail
    Enterprise -> List + Detail + Export
- RBAC simulation (field visibility) is based on persona.

Run:
  pip install streamlit requests pandas
  streamlit run app.py
"""

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import streamlit as st

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import requests
except Exception:
    requests = None

# -----------------------------
# Config
# -----------------------------
APP_TITLE = os.getenv("MARKETPLACE_TITLE", "MOVE | API Products")
APP_SUBTITLE = os.getenv(
    "MARKETPLACE_SUBTITLE",
    "Private marketplace experience for real estate APIs — browse, filter, subscribe, and try endpoints live.",
)

API_GATEWAY_BASE = os.getenv(
    "API_GATEWAY_BASE", "https://7fsd5a0ox6.execute-api.us-east-2.amazonaws.com"
).rstrip("/")
API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "/v1")

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏠")

# -----------------------------
# Styling
# -----------------------------
CSS = """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
h1, h2, h3 { letter-spacing: -0.015em; }
[data-testid="stSidebar"] { border-right: 1px solid rgba(49,51,63,0.12); }

.mkt-card {
  border: 1px solid rgba(49, 51, 63, 0.14);
  border-radius: 16px;
  padding: 16px 16px 14px 16px;
  background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.92));
  box-shadow: 0 1px 10px rgba(0,0,0,0.05);
  height: 100%;
}
.mkt-title { font-weight: 750; font-size: 1.03rem; margin-bottom: 6px; }
.mkt-desc { color: rgba(49,51,63,0.78); font-size: 0.92rem; line-height: 1.25rem; margin-bottom: 10px; }
.mkt-meta { margin-top: 6px; margin-bottom: 8px; }
.badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 650;
  margin-right: 6px;
  border: 1px solid rgba(49, 51, 63, 0.18);
  background: rgba(49, 51, 63, 0.04);
}
.badge-free { background: rgba(46, 204, 113, 0.12); border-color: rgba(46, 204, 113, 0.35); }
.badge-paid { background: rgba(52, 152, 219, 0.12); border-color: rgba(52, 152, 219, 0.35); }
.badge-ent  { background: rgba(155, 89, 182, 0.12); border-color: rgba(155, 89, 182, 0.35); }

.badge-public  { background: rgba(39, 174, 96, 0.12); border-color: rgba(39, 174, 96, 0.35); }
.badge-partner { background: rgba(52, 152, 219, 0.12); border-color: rgba(52, 152, 219, 0.35); }
.badge-private { background: rgba(231, 76, 60, 0.12); border-color: rgba(231, 76, 60, 0.35); }

.price { font-weight: 850; font-size: 1.05rem; margin-top: 6px; }
.small { font-size: 0.82rem; color: rgba(49, 51, 63, 0.72); }

code { font-size: 0.82rem; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------
# Data models
# -----------------------------

@dataclass
class Product:
    id: str
    name: str
    description: str
    domain: str
    tier: str  # Free / Paid / Enterprise
    access: str  # Public / Partner / Private
    price_monthly: Optional[float]
    features: List[str]
    tags: List[str]
    endpoints: List[Dict[str, str]]


# -----------------------------
# Embedded product catalog
# -----------------------------

CATALOG: List[Product] = [
    Product(
        id="re-listings-free",
        name="Real Estate Listings API - Free",
        description="Starter access to active listings for evaluation and quick prototypes.",
        domain="Listings",
        tier="Free",
        access="Public",
        price_monthly=0.0,
        features=[
            "Up to 1,000 API calls per month",
            "Active listings only",
            "Basic filters: status, limit",
            "Community support",
        ],
        tags=["Listings", "Starter", "REST", "Quality"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
        ],
    ),
    Product(
        id="re-listings-basic",
        name="Real Estate Listings API - Basic",
        description="Access to active listings with basic filtering. Ideal for small integrations.",
        domain="Listings",
        tier="Paid",
        access="Public",
        price_monthly=300.0,
        features=[
            "Up to 10,000 API calls per month",
            "Active listings (standard payload)",
            "Filters: status, limit, offset",
            "Standard support",
        ],
        tags=["Listings", "Active", "REST"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
            {"name": "Get listing by id", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}"},
        ],
    ),
    Product(
        id="re-listings-premium",
        name="Real Estate Listings API - Premium",
        description="Higher throughput + richer filters for analytics and internal dashboards.",
        domain="Listings",
        tier="Paid",
        access="Partner",
        price_monthly=1500.0,
        features=[
            "Up to 100,000 API calls per month",
            "Advanced filters: state, city, price, beds",
            "Priority support",
            "Ideal for analyst workflows",
        ],
        tags=["Listings", "Analytics", "REST"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
            {"name": "Export listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/export"},
        ],
    ),
    Product(
        id="re-listings-enterprise",
        name="Real Estate Listings API - Enterprise",
        description="Bulk export + partner access for large-scale integrations and pipelines.",
        domain="Listings",
        tier="Enterprise",
        access="Private",
        price_monthly=5000.0,
        features=[
            "Unlimited or negotiated API usage",
            "Bulk exports to S3 with pre-signed download URLs",
            "Best for external data delivery and resellers",
            "Dedicated support / SLA (demo placeholder)",
        ],
        tags=["Bulk Export","REST", "S3", "Enterprise"],
        endpoints=[
            {"name": "Export listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/export"},
            {"name": "Get listing by id", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}"},
        ],
    ),
   
    Product(
        id="re-listings-enterprise",
        name="Real Estate Listings API - Enterprise",
        description="Snowflake Bulk export + partner access for large-scale integrations and pipelines.",
        domain="Listings",
        tier="Enterprise",
        access="Private",
        price_monthly=5000.0,
        features=[
            "No-Copy access using snowflake",
            "Bulk exports using shared snowflake schema",
            "Best for external data delivery and resellers",
            "Dedicated support / SLA (demo placeholder)",
        ],
        tags=["Bulk Export", "snowflake", "Enterprise"],
        endpoints=[
            {"name": "Access listings in Snowflake", "method": "Shared Snowflake Schema", "path": f"https://app.snowflake.com/lpgjexw/qu57033/#/data/shared/listing/private/GZT1ZHLC55?originTab=shared"},
        ],
    ),
]

CATALOG_BY_ID = {p.id: p for p in CATALOG}

# -----------------------------
# Hardcoded users (as before)
# -----------------------------

SAMPLE_USERS = {
    "broker": {"password": "broker123", "display": "Broker"},
    "analyst": {"password": "analyst123", "display": "Market Analyst"},
    "datasci": {"password": "datasci123", "display": "Data Scientist"},
}

# -----------------------------
# Session state
# -----------------------------

if "auth" not in st.session_state:
    st.session_state.auth = {
        "logged_in": False,
        "username": None,
        "persona": None,
    }

if "subscription" not in st.session_state:
    st.session_state.subscription = {
        "product_id": "re-listings-free",
        "tier": "Free",
        "token": None,
        "issued_at": None,
    }

# -----------------------------
# Helpers
# -----------------------------

def badge_class_for_tier(tier: str) -> str:
    t = (tier or "").lower()
    if t == "free":
        return "badge-free"
    if t == "paid":
        return "badge-paid"
    return "badge-ent"


def badge_class_for_access(access: str) -> str:
    a = (access or "").lower()
    if a == "public":
        return "badge-public"
    if a == "partner":
        return "badge-partner"
    return "badge-private"


def money(v: Optional[float]) -> str:
    if v is None:
        return "$ Custom"
    try:
        v = float(v)
    except Exception:
        return str(v)
    if v <= 0:
        return "$0"
    if v.is_integer():
        return f"${int(v):,}"
    return f"${v:,.2f}"


def build_url(path: str) -> str:
    return f"{API_GATEWAY_BASE}{path}"


def tier_allows(required_tier: str, token_tier: Optional[str]) -> bool:
    """Free < Paid < Enterprise"""
    order = {"Free": 0, "Paid": 1, "Enterprise": 2}
    if token_tier is None:
        return required_tier == "Free"
    return order.get(token_tier, 0) >= order.get(required_tier, 0)


def generate_demo_token(username: str, persona: str, product: Product) -> str:
    """Simulated token: base64(payload).signature (NOT a real JWT)."""
    payload = {
        "sub": username,
        "persona": persona,
        "subscription": {
            "product_id": product.id,
            "product_name": product.name,
            "tier": product.tier,
        },
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("=")
    return f"{b64}.{sig}"


def auth_header() -> Dict[str, str]:
    tok = st.session_state.subscription.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


def build_curl(url: str, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> str:
    qs = ""
    if params:
        qs = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    curl = f"curl --location '{url}{'?' + qs if qs else ''}'"
    if token:
        curl += f" \\\n  -H 'Authorization: Bearer {token}'"
    return curl


def apply_rbac_to_listings(rows: List[Dict[str, Any]], persona: Optional[str]) -> List[Dict[str, Any]]:
    """Simulate per-persona field visibility."""
    if not rows:
        return rows
    p = (persona or "").lower()

    # Broker: minimal fields
    if "broker" in p:
        keep = {"LISTING_ID", "CITY", "STATE", "LIST_PRICE", "POSTAL_CODE"}
        return [{k: v for k, v in row.items() if k in keep} for row in rows]

    # Analyst: more analytic fields
    if "analyst" in p or "market" in p:
        keep = {
            "LISTING_ID",
            "CITY",
            "STATE",
            "POSTAL_CODE",
            "LIST_PRICE",
            "PRICE_PER_SQFT",
            "BED_COUNT",
            "BATH_COUNT",
            "BUILDING_SQFT",
            "YEAR_BUILT",
            "DATA_SOURCE",
        }
        return [{k: v for k, v in row.items() if k in keep} for row in rows]

    # Data Scientist: full
    return rows


def require_requests():
    if requests is None:
        st.error("The 'requests' package is required. Install it with: pip install requests")
        st.stop()


# -----------------------------
# Sidebar: Login + Filters + Current Token
# -----------------------------

with st.sidebar:
    st.header("🔐 Login")

    if not st.session_state.auth["logged_in"]:
        st.caption("Hardcoded demo users")
        username = st.text_input("Username", placeholder="broker / analyst / datasci")
        password = st.text_input("Password", type="password", placeholder="e.g., broker123")

        if st.button("Login", type="primary"):
            u = (username or "").strip().lower()
            p = password or ""
            user = SAMPLE_USERS.get(u)
            if user and p == user["password"]:
                st.session_state.auth.update({"logged_in": True, "username": u, "persona": user["display"]})
                st.success(f"Logged in as {user['display']}")
            else:
                st.error("Invalid credentials (broker/broker123, analyst/analyst123, datasci/datasci123)")
    else:
        st.success(f"{st.session_state.auth['persona']}")
        st.caption(f"User: {st.session_state.auth['username']}")
        if st.button("Logout"):
            st.session_state.auth = {"logged_in": False, "username": None, "persona": None}
            st.session_state.subscription["token"] = None
            st.session_state.subscription["issued_at"] = None
            st.rerun()

    st.divider()
    st.header("🔑 Active Token")

    active_pid = st.session_state.subscription.get("product_id")
    active_prod = CATALOG_BY_ID.get(active_pid)
    active_tier = st.session_state.subscription.get("tier")
    active_tok = st.session_state.subscription.get("token")

    if active_prod:
        st.caption("Subscription")
        st.write(f"**{active_prod.name}**")
        st.write(f"Tier: **{active_tier}**")

    if active_tok:
        st.caption("Authorization")
        st.code(f"Bearer {active_tok}")
        st.caption(f"Issued at: {st.session_state.subscription.get('issued_at')}")
    else:
        st.info("No token generated yet. Go to **Token** tab to generate.")

    st.divider()
    st.header("Filters")
    search = st.text_input("Search", placeholder="Search products…")
    domains = sorted({p.domain for p in CATALOG})
    tiers = ["Free", "Paid", "Enterprise"]
    domain_filter = st.multiselect("Domain", domains, default=[])
    tier_filter = st.multiselect("Tier", tiers, default=[])
    st.caption("Tip: Leave a filter empty to include all values.")


# -----------------------------
# Header
# -----------------------------

left, right = st.columns([0.72, 0.28])
with left:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
with right:
    st.caption("API Base")
    st.code(API_GATEWAY_BASE)

st.divider()

# -----------------------------
# Catalog filter logic
# -----------------------------

def matches(prod: Product) -> bool:
    if search:
        s = search.strip().lower()
        hay = " ".join([prod.name, prod.description, prod.domain, prod.tier, " ".join(prod.tags)]).lower()
        if s not in hay:
            return False
    if domain_filter and prod.domain not in domain_filter:
        return False
    if tier_filter and prod.tier not in tier_filter:
        return False
    return True


filtered_catalog = [p for p in CATALOG if matches(p)]

# -----------------------------
# Tabs
# -----------------------------

tab_products, tab_token, tab_explorer, tab_docs = st.tabs([
    "API Products",
    "Token",
    "API Explorer",
    "Docs",
])

# -----------------------------
# API Products tab
# -----------------------------

with tab_products:
    st.subheader("API Products")
    st.caption(f"Showing {len(filtered_catalog)} product(s)")

    if not filtered_catalog:
        st.info("No products match your filters.")
    else:
        cols_per_row = 3
        rows = (len(filtered_catalog) + cols_per_row - 1) // cols_per_row
        idx = 0
        for _ in range(rows):
            cols = st.columns(cols_per_row)
            for col in cols:
                if idx >= len(filtered_catalog):
                    break
                p = filtered_catalog[idx]
                idx += 1

                tier_cls = badge_class_for_tier(p.tier)
                access_cls = badge_class_for_access(p.access)

                price = money(p.price_monthly)
                period = " / month" if (p.price_monthly is not None and p.price_monthly > 0) else ""

                card_html = f"""
                <div class='mkt-card'>
                    <div class='mkt-title'>{p.name}</div>
                    <div class='mkt-meta'>
                        <span class='badge {access_cls}'>{p.access}</span>
                        <span class='badge'>{p.domain}</span>
                        <span class='badge {tier_cls}'>{p.tier}</span>
                    </div>
                    <div class='mkt-desc'>{p.description}</div>
                    <div class='price'>{price}<span class='small'>{period}</span></div>
                    <div style='margin-top: 10px;'>
                        {"".join([f"<span class='badge'>{t}</span>" for t in p.tags[:6]])}
                    </div>
                </div>
                """

                with col:
                    st.markdown(card_html, unsafe_allow_html=True)
                    with st.expander("Details"):
                        st.write("**Features**")
                        for f in p.features:
                            st.write(f"- {f}")
                        st.write("**Endpoints (demo)**")
                        for e in p.endpoints:
                            st.code(f"{e['method']} {build_url(e['path'])}")

# -----------------------------
# Token tab (subscription -> token)
# -----------------------------

with tab_token:
    st.subheader("Token Generation")
    st.caption("Select a subscription product and generate a token for API access.")

    if not st.session_state.auth["logged_in"]:
        st.warning("Please login first using the sidebar (broker/analyst/datasci).")
    else:
        prod_options = {p.name: p.id for p in CATALOG}
        default_name = CATALOG_BY_ID[st.session_state.subscription["product_id"]].name
        selected_name = st.selectbox(
            "Choose subscription product",
            list(prod_options.keys()),
            index=list(prod_options.keys()).index(default_name),
        )
        selected_pid = prod_options[selected_name]
        selected_prod = CATALOG_BY_ID[selected_pid]

        st.write("**Selected subscription**")
        st.write(f"Product: **{selected_prod.name}**")
        st.write(f"Tier: **{selected_prod.tier}**")

        st.write("**What this tier unlocks (in this demo):**")
        if selected_prod.tier == "Free":
            st.write("- ✅ List listings")
            st.write("- ❌ Listing detail")
            st.write("- ❌ Export")
        elif selected_prod.tier == "Paid":
            st.write("- ✅ List listings")
            st.write("- ✅ Listing detail")
            st.write("- ❌ Export")
        else:
            st.write("- ✅ List listings")
            st.write("- ✅ Listing detail")
            st.write("- ✅ Export (S3 presigned URL)")

        col1, col2 = st.columns([0.28, 0.72])
        with col1:
            if st.button("Generate Token", type="primary"):
                tok = generate_demo_token(
                    st.session_state.auth["username"],
                    st.session_state.auth["persona"],
                    selected_prod,
                )
                st.session_state.subscription.update(
                    {
                        "product_id": selected_pid,
                        "tier": selected_prod.tier,
                        "token": tok,
                        "issued_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
                st.success("Token generated and activated")

        with col2:
            tok = st.session_state.subscription.get("token")
            if tok:
                st.caption("Active token")
                st.code(f"Bearer {tok}")

        with st.expander("Token payload (decoded)", expanded=False):
            tok = st.session_state.subscription.get("token")
            if not tok:
                st.info("Generate a token first.")
            else:
                try:
                    part = tok.split(".")[0]
                    pad = "=" * (-len(part) % 4)
                    raw = base64.urlsafe_b64decode(part + pad).decode("utf-8")
                    st.json(json.loads(raw))
                except Exception:
                    st.write("Unable to decode token payload.")

# -----------------------------
# API Explorer tab (ONLY your APIs)
# -----------------------------

with tab_explorer:
    st.subheader("API Explorer")
    st.caption("Run your demo APIs and auto-generate cURL (uses only your 3 endpoints).")

    require_requests()

    token_tier = st.session_state.subscription.get("tier") if st.session_state.subscription.get("token") else None

    endpoints = {
        "List listings": {
            "method": "GET",
            "path": f"{API_VERSION_PREFIX}/listings",
            "params": [("limit", "10"), ("offset", "0"), ("status", "ACTIVE")],
            "min_tier": "Free",
        },
        "Get listing by id": {
            "method": "GET",
            "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}",
            "params": [("listing_id", "c03a9346f9")],
            "min_tier": "Paid",
        },
        "Export listings (CSV → S3 presigned URL)": {
            "method": "GET",
            "path": f"{API_VERSION_PREFIX}/listings/export",
            "params": [
                ("limit", "100"),
                ("status", "ACTIVE"),
                ("state", ""),
                ("city", ""),
                ("postal_code", ""),
                ("min_price", ""),
                ("max_price", ""),
                ("min_beds", ""),
                ("max_beds", ""),
            ],
            "min_tier": "Enterprise",
        },
    }

    choice = st.selectbox("Choose an API", list(endpoints.keys()))
    ep = endpoints[choice]
    allowed = tier_allows(ep["min_tier"], token_tier)

    st.write(f"**Required tier:** {ep['min_tier']} · **Token tier:** {token_tier or 'No token'}")

    params: Dict[str, str] = {}
    cols = st.columns(2)
    for i, (k, default) in enumerate(ep["params"]):
        with cols[i % 2]:
            params[k] = st.text_input(k, value=default)

    path = ep["path"]
    if "{listing_id}" in path:
        listing_id = params.pop("listing_id", "").strip()
        path = path.replace("{listing_id}", listing_id)

    url = build_url(path)

    st.write("**Generated cURL**")
    st.code(build_curl(url, params, st.session_state.subscription.get("token")), language="bash")

    col_a, col_b = st.columns([0.25, 0.75])
    with col_a:
        run = st.button("Run", type="primary", disabled=not allowed)
        show_raw = st.checkbox("Show raw JSON", value=False)

    if not allowed:
        st.info("Generate a token with the required subscription tier in the **Token** tab.")

    if run:
        try:
            headers = auth_header()
            qparams = {k: v for k, v in params.items() if v != ""}
            resp = requests.get(url, params=qparams, headers=headers, timeout=30)
            st.write(f"Status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict) and data.get("success") is True:
                payload = data.get("data")

                if isinstance(payload, list):
                    trimmed = apply_rbac_to_listings(payload, st.session_state.auth.get("persona"))
                    if pd is not None:
                        st.dataframe(pd.DataFrame(trimmed), use_container_width=True)
                    else:
                        st.json(trimmed)

                    if "pagination" in data:
                        st.caption("Pagination")
                        st.json(data.get("pagination"))

                elif isinstance(payload, dict):
                    if "LISTING_ID" in payload:
                        trimmed = apply_rbac_to_listings([payload], st.session_state.auth.get("persona"))
                        st.json(trimmed[0] if trimmed else payload)
                    else:
                        st.json(payload)

                    dl = payload.get("download") if isinstance(payload, dict) else None
                    if isinstance(dl, dict) and dl.get("presigned_url"):
                        st.success("Export ready")
                        st.markdown(f"[Download CSV]({dl['presigned_url']})")

            else:
                st.json(data)

            if show_raw:
                st.code(json.dumps(data, indent=2), language="json")

        except Exception as e:
            st.error(f"Request failed: {e}")

# -----------------------------
# Docs tab
# -----------------------------

with tab_docs:
    st.subheader("Docs")
    st.markdown(
        """
This POC demonstrates:

- **Marketplace UI**: browse products, filter by domain and tier
- **Multi-user demo login**: broker/analyst/datasci (hardcoded)
- **Subscription-based token generation**: choose a product → generate a token
- **Tier gating (based on subscription)**:
  - **Free**: list endpoint
  - **Paid**: list + detail endpoint
  - **Enterprise**: export endpoint with S3 pre-signed URL
- **RBAC simulation (based on persona)**:
  - Broker sees fewer fields
  - Analyst sees more analytic fields
  - Data Scientist sees full payload

Endpoints used in this demo (only):
- GET /v1/listings
- GET /v1/listings/{listing_id}
- GET /v1/listings/export
"""
    )

    st.write("**API Base**")
    st.code(API_GATEWAY_BASE)

    st.write("**Sample users**")
    st.json({k: {"password": v["password"], "persona": v["display"]} for k, v in SAMPLE_USERS.items()})
