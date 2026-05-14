"""
app.py — Streamlit Marketplace POC (Business-first + Developer view)

Implements requested changes from [Move PoC Discussion](https://teams.microsoft.com/l/meeting/details?eventId=AAMkAGJkMDE4MGRkLTNlYmQtNDlkYi1iOWViLWEzNDM2N2ZlMzc4OQBGAAAAAAB0GfvTcX2qSbSz4fdUGQArBwCZFTtxVRffRphNi9W_2RzVAAAAAAENAACZFTtxVRffRphNi9W_2RzVAAG5ictiAAA%3d&EntityRepresentationId=13862581-7e7f-491d-a669-32c6af491dec) tasks:
- Business-focused landing page with domain/category menu and tiles per data product
- Personas updated to real-world roles: Provider / Agent / Consumer
- Data products expanded to include APIs + Analytics + Dashboards + Datasets
- Technical aspects (token + API explorer) moved to a separate Developer View
- Provider + Consumer flows demo-able using two browsers (shared state via JSON file)

Still preserves original demo behavior:
- Only these APIs are used in API Explorer:
    - GET /v1/listings
    - GET /v1/listings/{listing_id}
    - GET /v1/listings/export
- Tier gating:
    Free -> List
    Paid -> List + Detail
    Enterprise -> List + Detail + Export
- RBAC simulation based on persona (fields visible in listings response)

Refs:
- Original app behavior described in uploaded [app.py](https://brillioonline-my.sharepoint.com/personal/anil_kumar6_brillio_com/Documents/Microsoft%20Copilot%20Chat%20Files/app.py?EntityRepresentationId=4b741a79-d2d4-4e6f-8b43-532a98b896d4) and meeting transcript. [3](https://brillioonline-my.sharepoint.com/personal/anil_kumar6_brillio_com/Documents/Microsoft%20Copilot%20Chat%20Files/app.py)[4](https://brillioonline-my.sharepoint.com/personal/sandeep_kumar4_brillio_com/Documents/Recordings/Move%20PoC%20Discussion-20260514_202303-Meeting%20Recording.mp4?web=1)
- Anywhere-style API Products browsing experience (category filters + tiles). [1](https://developers.anywhere.re/api-products)
"""

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
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
APP_TITLE = os.getenv("MARKETPLACE_TITLE", "MOVE Data Product Marketplace")
APP_SUBTITLE = os.getenv(
    "MARKETPLACE_SUBTITLE",
    "Discover and access real estate data products (APIs, analytics, dashboards, datasets) through a business-first marketplace experience.",
)

API_GATEWAY_BASE = os.getenv(
    "API_GATEWAY_BASE",
    "https://7fsd5a0ox6.execute-api.us-east-2.amazonaws.com",
).rstrip("/")
API_VERSION_PREFIX = os.getenv("API_VERSION_PREFIX", "/v1")

STATE_FILE = os.getenv("MARKETPLACE_STATE_FILE", "marketplace_state.json")

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🏠")


# -----------------------------
# Styling (simple, clean cards)
# -----------------------------
CSS = """
<style>
    .subtle { color: rgba(0,0,0,0.65); font-size: 0.95rem; }
    .pill { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.75rem; margin-right: 0.35rem; margin-top: 0.25rem; border: 1px solid rgba(0,0,0,0.08);}
    .pill-public { background: #ECFDF3; color: #067647; border-color: #A6F4C5; }
    .pill-partner { background: #EFF8FF; color: #175CD3; border-color: #B2DDFF; }
    .pill-private { background: #FEF3F2; color: #B42318; border-color: #FECDCA; }

    .pill-api { background: #F9F5FF; color: #5925DC; border-color: #D6BBFB; }
    .pill-analytics { background: #FFFAEB; color: #B54708; border-color: #FEDF89; }
    .pill-dashboard { background: #F0F9FF; color: #026AA2; border-color: #B9E6FE; }
    .pill-dataset { background: #F8FAFC; color: #0F172A; border-color: #E2E8F0; }

    .pill-free { background: #F8FAFC; color: #0F172A; border-color: #E2E8F0; }
    .pill-paid { background: #EEF2FF; color: #3730A3; border-color: #C7D2FE; }
    .pill-ent { background: #FFF7ED; color: #9A3412; border-color: #FED7AA; }

    .card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 16px;
        padding: 14px 14px 10px 14px;
        background: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        height: 100%;
    }
    .card h4 { margin: 0 0 6px 0; font-size: 1.05rem; }
    .card p { margin: 0 0 10px 0; }
    .card .meta { margin-top: 8px; }
    .divider-soft { height: 1px; background: rgba(0,0,0,0.06); margin: 10px 0; }
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
    category: str               # business domain/category (Listings, Consumer, Transactions, etc.)
    product_type: str           # API / Analytics / Dashboard / Dataset
    tier: str                   # Free / Paid / Enterprise
    access: str                 # Public / Partner / Private
    provider: str               # org/provider label
    business_owner: str         # role/owner label
    features: List[str]
    tags: List[str]
    endpoints: List[Dict[str, str]]  # only used for API type products


# -----------------------------
# Embedded base catalog (expanded beyond APIs)
# -----------------------------
BASE_CATALOG: List[Product] = [
    Product(
        id="listings-api-free",
        name="Listings API (Starter)",
        description="Starter access to active listings for evaluation and quick prototypes.",
        category="Listings",
        product_type="API",
        tier="Free",
        access="Public",
        provider="MOVE / RDC",
        business_owner="Data Products",
        features=[
            "Up to 1,000 API calls / month (demo)",
            "Active listings only",
            "Basic filters: status, limit",
        ],
        tags=["Listings", "REST", "Starter"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
        ],
    ),
    Product(
        id="listings-api-paid",
        name="Listings API (Basic)",
        description="Access to active listings with detail lookup for small integrations.",
        category="Listings",
        product_type="API",
        tier="Paid",
        access="Public",
        provider="MOVE / RDC",
        business_owner="Data Products",
        features=[
            "Up to 10,000 API calls / month (demo)",
            "List + Detail lookup",
            "Standard support (demo)",
        ],
        tags=["Listings", "REST", "Integration"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
            {"name": "Get listing by id", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}"},
        ],
    ),
    Product(
        id="listings-api-enterprise",
        name="Listings API (Enterprise)",
        description="Enterprise access with bulk export (S3 presigned URL) for large-scale delivery.",
        category="Listings",
        product_type="API",
        tier="Enterprise",
        access="Partner",
        provider="MOVE / RDC",
        business_owner="Data Products",
        features=[
            "Negotiated API usage (demo)",
            "Bulk export to S3 with presigned download URL",
            "Best for external delivery/resellers",
        ],
        tags=["Listings", "Bulk Export", "S3"],
        endpoints=[
            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
            {"name": "Get listing by id", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}"},
            {"name": "Export listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/export"},
        ],
    ),
    Product(
        id="market-trends-analytics",
        name="Market Trends Analytics",
        description="Neighborhood-level trends for pricing and inventory movement (visualization product).",
        category="Analytics",
        product_type="Analytics",
        tier="Paid",
        access="Public",
        provider="MOVE / RDC",
        business_owner="Analytics",
        features=[
            "Trend summaries by city/state",
            "Designed for business users (demo)",
            "Can be extended to dashboards/BI",
        ],
        tags=["Analytics", "Trends"],
        endpoints=[],
    ),
    Product(
        id="consumer-journey-dashboard",
        name="Consumer Journey Dashboard",
        description="A business dashboard view to track consumer funnel and transaction journey (visualization product).",
        category="Consumer",
        product_type="Dashboard",
        tier="Paid",
        access="Partner",
        provider="MOVE / RDC",
        business_owner="Consumer Apps",
        features=[
            "Journey stages and drop-offs (demo)",
            "Persona-based insights",
            "Designed for executive review",
        ],
        tags=["Dashboard", "Consumer"],
        endpoints=[],
    ),
    Product(
        id="agents-dataset",
        name="Agent & Office Reference Dataset",
        description="Reference dataset for agent/office enrichment (dataset product).",
        category="Brokerage",
        product_type="Dataset",
        tier="Enterprise",
        access="Private",
        provider="MOVE / RDC",
        business_owner="Brokerage Ops",
        features=[
            "Agent & office canonical attributes (demo)",
            "Governance-ready data product type",
            "Can be delivered via Snowflake share / files / APIs",
        ],
        tags=["Dataset", "Reference"],
        endpoints=[],
    ),
]

BASE_CATALOG_BY_ID = {p.id: p for p in BASE_CATALOG}


# -----------------------------
# Personas (hardcoded demo users)
# -----------------------------
SAMPLE_USERS = {
    "provider": {"password": "provider123", "display": "Data Provider"},
    "agent": {"password": "agent123", "display": "Real Estate Agent"},
    "consumer": {"password": "consumer123", "display": "Home Buyer"},
}


# -----------------------------
# Shared state across sessions (two browsers) via JSON file
# -----------------------------
def _init_state_file():
    if not os.path.exists(STATE_FILE):
        payload = {"custom_products": [], "access_requests": []}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


def load_shared_state() -> Dict[str, Any]:
    _init_state_file()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"custom_products": [], "access_requests": []}


def save_shared_state(state: Dict[str, Any]) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        # fail silently for demo robustness
        pass


def custom_products_from_state(state: Dict[str, Any]) -> List[Product]:
    out: List[Product] = []
    for raw in state.get("custom_products", []):
        try:
            out.append(Product(**raw))
        except Exception:
            continue
    return out


def access_requests_from_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return state.get("access_requests", [])


# -----------------------------
# Session state (per user/browser session)
# -----------------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": None, "persona": None}

if "ui" not in st.session_state:
    st.session_state.ui = {
        "selected_category": None,
        "search": "",
        "product_type_filter": [],
        "access_filter": [],
        "tier_filter": [],
        "selected_product_id": None,
    }

if "subscription" not in st.session_state:
    st.session_state.subscription = {
        "product_id": None,
        "tier": None,
        "token": None,
        "issued_at": None,
    }


# -----------------------------
# Helpers
# -----------------------------
def require_requests():
    if requests is None:
        st.error("The 'requests' package is required. Install it with: pip install requests")
        st.stop()


def pill(label: str, cls: str) -> str:
    return f"<span class='pill {cls}'>{label}</span>"


def pill_access(access: str) -> str:
    a = (access or "").lower()
    if a == "public":
        return pill("Public", "pill-public")
    if a == "partner":
        return pill("Partner", "pill-partner")
    return pill("Private", "pill-private")


def pill_type(t: str) -> str:
    tt = (t or "").lower()
    if tt == "api":
        return pill("API", "pill-api")
    if tt == "analytics":
        return pill("Analytics", "pill-analytics")
    if tt == "dashboard":
        return pill("Dashboard", "pill-dashboard")
    return pill("Dataset", "pill-dataset")


def pill_tier(tier: str) -> str:
    tt = (tier or "").lower()
    if tt == "free":
        return pill("Free", "pill-free")
    if tt == "paid":
        return pill("Paid", "pill-paid")
    return pill("Enterprise", "pill-ent")


def build_url(path: str) -> str:
    return f"{API_GATEWAY_BASE}{path}"


def build_curl(url: str, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> str:
    qs = ""
    if params:
        qs = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    curl = f"curl --location '{url}{'?' + qs if qs else ''}'"
    if token:
        curl += f" \\\n  -H 'Authorization: Bearer {token}'"
    return curl


def tier_allows(required_tier: str, token_tier: Optional[str]) -> bool:
    """Free < Paid < Enterprise"""
    order = {"Free": 0, "Paid": 1, "Enterprise": 2}
    if token_tier is None:
        return required_tier == "Free"
    return order.get(token_tier, 0) >= order.get(required_tier, 0)


def generate_demo_token(username: str, persona: str, product: Product) -> str:
    """
    Simulated token: base64(payload).signature (NOT a real JWT).
    Matches the original POC concept: token tied to subscription tier/product.
    """
    payload = {
        "sub": username,
        "persona": persona,
        "subscription": {"product_id": product.id, "product_name": product.name, "tier": product.tier},
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = base64.urlsafe_b64encode(os.urandom(12)).decode("utf-8").rstrip("=")
    return f"{b64}.{sig}"


def decode_token_payload(tok: str) -> Optional[Dict[str, Any]]:
    try:
        part = tok.split(".")[0]
        pad = "=" * (-len(part) % 4)
        raw = base64.urlsafe_b64decode(part + pad).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return None


def auth_header() -> Dict[str, str]:
    tok = st.session_state.subscription.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


def apply_rbac_to_listings(rows: List[Dict[str, Any]], persona: Optional[str]) -> List[Dict[str, Any]]:
    """Simulate field visibility based on persona."""
    if not rows:
        return rows
    p = (persona or "").lower()

    # Home Buyer (consumer): very limited
    if "home buyer" in p or "consumer" in p:
        keep = {"LISTING_ID", "CITY", "STATE", "LIST_PRICE", "BED_COUNT", "BATH_COUNT"}
        return [{k: v for k, v in r.items() if k in keep} for r in rows]

    # Agent: more fields useful for their work
    if "agent" in p:
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
        }
        return [{k: v for k, v in r.items() if k in keep} for r in rows]

    # Provider: full payload
    return rows


def merged_catalog() -> List[Product]:
    shared = load_shared_state()
    custom = custom_products_from_state(shared)
    return BASE_CATALOG + custom


def categories_from_catalog(catalog: List[Product]) -> List[str]:
    return sorted({p.category for p in catalog})


def matches_filters(prod: Product) -> bool:
    ui = st.session_state.ui
    s = (ui.get("search") or "").strip().lower()
    if s:
        hay = " ".join([prod.name, prod.description, prod.category, prod.product_type, prod.tier, prod.access, " ".join(prod.tags)]).lower()
        if s not in hay:
            return False

    cat = ui.get("selected_category")
    if cat and prod.category != cat:
        return False

    pt = ui.get("product_type_filter") or []
    if pt and prod.product_type not in pt:
        return False

    af = ui.get("access_filter") or []
    if af and prod.access not in af:
        return False

    tf = ui.get("tier_filter") or []
    if tf and prod.tier not in tf:
        return False

    return True


def is_api_product(prod: Product) -> bool:
    return (prod.product_type or "").lower() == "api"


def user_has_access(prod: Product, username: Optional[str]) -> bool:
    """
    Access rules for demo:
    - Public: always visible/accessible
    - Partner/Private: requires approval entry in shared state for the user
    """
    if (prod.access or "").lower() == "public":
        return True
    if not username:
        return False

    state = load_shared_state()
    reqs = access_requests_from_state(state)
    for r in reqs:
        if (
            r.get("product_id") == prod.id
            and r.get("requester") == username
            and r.get("status") == "APPROVED"
        ):
            return True
    return False


def create_access_request(product_id: str, requester: str, requester_persona: str):
    state = load_shared_state()
    reqs = access_requests_from_state(state)

    # avoid duplicate pending requests
    for r in reqs:
        if r.get("product_id") == product_id and r.get("requester") == requester and r.get("status") in ("PENDING", "APPROVED"):
            return

    reqs.append(
        {
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "requester": requester,
            "requester_persona": requester_persona,
            "status": "PENDING",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": None,
        }
    )
    state["access_requests"] = reqs
    save_shared_state(state)


def approve_request(req_id: str):
    state = load_shared_state()
    reqs = access_requests_from_state(state)
    for r in reqs:
        if r.get("id") == req_id:
            r["status"] = "APPROVED"
            r["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    state["access_requests"] = reqs
    save_shared_state(state)


def reject_request(req_id: str):
    state = load_shared_state()
    reqs = access_requests_from_state(state)
    for r in reqs:
        if r.get("id") == req_id:
            r["status"] = "REJECTED"
            r["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            break
    state["access_requests"] = reqs
    save_shared_state(state)


def publish_custom_product(prod: Product):
    state = load_shared_state()
    items = state.get("custom_products", [])
    items.append(asdict(prod))
    state["custom_products"] = items
    save_shared_state(state)


# -----------------------------
# Sidebar: Login + Global Filters + Token Summary
# -----------------------------
with st.sidebar:
    st.header("🔐 Login")

    if not st.session_state.auth["logged_in"]:
        st.caption("Demo users (real-world personas)")
        u = st.text_input("Username", placeholder="provider / agent / consumer")
        p = st.text_input("Password", type="password", placeholder="provider123 / agent123 / consumer123")
        if st.button("Login", type="primary"):
            uu = (u or "").strip().lower()
            user = SAMPLE_USERS.get(uu)
            if user and p == user["password"]:
                st.session_state.auth.update({"logged_in": True, "username": uu, "persona": user["display"]})
                st.success(f"Logged in as {user['display']}")
            else:
                st.error("Invalid credentials. Try provider/provider123, agent/agent123, consumer/consumer123.")
    else:
        st.success(st.session_state.auth["persona"])
        st.caption(f"User: {st.session_state.auth['username']}")
        if st.button("Logout"):
            st.session_state.auth = {"logged_in": False, "username": None, "persona": None}
            st.session_state.subscription = {"product_id": None, "tier": None, "token": None, "issued_at": None}
            st.session_state.ui["selected_product_id"] = None
            st.rerun()

    st.divider()
    st.header("🔎 Browse Filters")
    st.session_state.ui["search"] = st.text_input("Search", value=st.session_state.ui.get("search", ""), placeholder="Search products…")

    catalog_for_filters = merged_catalog()
    cats = categories_from_catalog(catalog_for_filters)
    # Show category as a quick-select in sidebar too
    selected = st.selectbox("Category", ["(All)"] + cats, index=0 if not st.session_state.ui.get("selected_category") else (cats.index(st.session_state.ui["selected_category"]) + 1))
    st.session_state.ui["selected_category"] = None if selected == "(All)" else selected

    product_types = sorted({p.product_type for p in catalog_for_filters})
    access_types = ["Public", "Partner", "Private"]
    tiers = ["Free", "Paid", "Enterprise"]

    st.session_state.ui["product_type_filter"] = st.multiselect("Product type", product_types, default=st.session_state.ui.get("product_type_filter", []))
    st.session_state.ui["access_filter"] = st.multiselect("Access", access_types, default=st.session_state.ui.get("access_filter", []))
    st.session_state.ui["tier_filter"] = st.multiselect("Tier", tiers, default=st.session_state.ui.get("tier_filter", []))

    st.divider()
    st.header("🔑 Active Token (Developer)")
    tok = st.session_state.subscription.get("token")
    if tok:
        st.caption("Bearer token")
        st.code(f"Bearer {tok}")
        st.caption(f"Issued at: {st.session_state.subscription.get('issued_at')}")
        st.caption(f"Subscription tier: {st.session_state.subscription.get('tier')}")
    else:
        st.info("No token generated yet. Use Developer View → Token.")


# -----------------------------
# Header
# -----------------------------
left, right = st.columns([0.74, 0.26])
with left:
    st.title(APP_TITLE)
    st.markdown(f"<div class='subtle'>{APP_SUBTITLE}</div>", unsafe_allow_html=True)
with right:
    st.caption("API Base (Developer)")
    st.code(API_GATEWAY_BASE)

st.divider()


# -----------------------------
# Main Tabs (Business-first + Developer view)
# -----------------------------
tab_marketplace, tab_products, tab_developer, tab_docs = st.tabs(
    ["🏠 Marketplace", "📦 Data Products", "⚙️ Developer View", "📘 Demo Notes"]
)


# -----------------------------
# Marketplace (business landing)
# -----------------------------
with tab_marketplace:
    catalog = merged_catalog()
    cats = categories_from_catalog(catalog)

    st.subheader("Marketplace Landing")
    st.caption("Choose a domain/category and browse products via business-friendly tiles (technical details are in Developer View).")

    st.markdown("### Browse by Domain")
    cols = st.columns(4)
    for i, c in enumerate(cats):
        with cols[i % 4]:
            if st.button(c, use_container_width=True):
                st.session_state.ui["selected_category"] = c
                st.success(f"Selected domain: {c}")

    st.markdown("### Featured Data Products")
    featured = [p for p in catalog if matches_filters(p)][:8]
    if not featured:
        st.info("No products match your filters.")
    else:
        cols_per_row = 4
        rows = (len(featured) + cols_per_row - 1) // cols_per_row
        idx = 0
        for _ in range(rows):
            cols = st.columns(cols_per_row)
            for col in cols:
                if idx >= len(featured):
                    break
                p = featured[idx]
                idx += 1
                with col:
                    st.markdown(
                        f"""
                        <div class="card">
                            <h4>{p.name}</h4>
                            <div class="meta">
                                {pill_type(p.product_type)}
                                {pill_tier(p.tier)}
                                {pill_access(p.access)}
                                {pill(p.category, "pill-dataset")}
                            </div>
                            <div class="divider-soft"></div>
                            <p class="subtle">{p.description}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("View", key=f"view_{p.id}", use_container_width=True):
                        st.session_state.ui["selected_product_id"] = p.id
                        st.success("Open Data Products tab to see details.")

    st.divider()

    # Provider Studio on landing (provider flow)
    persona = st.session_state.auth.get("persona") or ""
    if (persona or "").lower() == "data provider":
        st.markdown("## 🧩 Provider Studio (Publish a Product)")
        st.caption("Create a new listing to simulate provider publishing flow. This will appear for other users in other browsers.")

        with st.form("provider_publish_form", clear_on_submit=True):
            name = st.text_input("Product name", placeholder="e.g., Valuation Insights Dashboard")
            desc = st.text_area("Business description", placeholder="What does this product do for business users?")
            category = st.selectbox("Domain/Category", cats if cats else ["Listings"])
            product_type = st.selectbox("Product type", ["API", "Analytics", "Dashboard", "Dataset"])
            tier = st.selectbox("Tier", ["Free", "Paid", "Enterprise"])
            access = st.selectbox("Access", ["Public", "Partner", "Private"])
            tags = st.text_input("Tags (comma-separated)", placeholder="e.g., trends, valuation, executive")

            add_api_endpoints = st.checkbox("If API product, attach demo endpoints (List/Detail/Export)", value=(product_type == "API"))

            submitted = st.form_submit_button("Publish Listing", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Product name is required.")
                else:
                    endpoints = []
                    if product_type == "API" and add_api_endpoints:
                        endpoints = [
                            {"name": "List listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings"},
                            {"name": "Get listing by id", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/{{listing_id}}"},
                            {"name": "Export listings", "method": "GET", "path": f"{API_VERSION_PREFIX}/listings/export"},
                        ]

                    new_prod = Product(
                        id=f"custom-{uuid.uuid4().hex[:10]}",
                        name=name.strip(),
                        description=desc.strip() or "Business product listing (demo).",
                        category=category,
                        product_type=product_type,
                        tier=tier,
                        access=access,
                        provider="Brillio (Demo Provider)",
                        business_owner="Data Provider",
                        features=["Published via Provider Studio (demo)"],
                        tags=[t.strip() for t in tags.split(",") if t.strip()] or ["Demo"],
                        endpoints=endpoints,
                    )
                    publish_custom_product(new_prod)
                    st.success("Published. Open another browser as consumer/agent to see it in Marketplace.")


# -----------------------------
# Data Products (business catalog + request access + details)
# -----------------------------
with tab_products:
    catalog = merged_catalog()
    filtered = [p for p in catalog if matches_filters(p)]

    st.subheader("Data Products")
    st.caption(f"Showing {len(filtered)} product(s) that match your filters.")

    # Selected product details panel
    selected_id = st.session_state.ui.get("selected_product_id")
    selected_prod = None
    if selected_id:
        for p in catalog:
            if p.id == selected_id:
                selected_prod = p
                break

    if selected_prod:
        st.markdown("### Product Details")
        st.markdown(
            f"""
            <div class="card">
                <h4>{selected_prod.name}</h4>
                <div class="meta">
                    {pill_type(selected_prod.product_type)}
                    {pill_tier(selected_prod.tier)}
                    {pill_access(selected_prod.access)}
                    {pill(selected_prod.category, "pill-dataset")}
                </div>
                <div class="divider-soft"></div>
                <p class="subtle">{selected_prod.description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns([0.34, 0.33, 0.33])
        with c1:
            st.write("**Provider**")
            st.write(selected_prod.provider)
        with c2:
            st.write("**Business Owner**")
            st.write(selected_prod.business_owner)
        with c3:
            st.write("**Access**")
            st.write(selected_prod.access)

        st.write("**Key features**")
        for f in selected_prod.features:
            st.write(f"- {f}")

        if selected_prod.tags:
            st.write("**Tags**")
            st.write(", ".join(selected_prod.tags))

        # Access / Request access
        st.divider()
        username = st.session_state.auth.get("username")
        persona = st.session_state.auth.get("persona") or ""

        if user_has_access(selected_prod, username):
            st.success("✅ You have access to this product (demo rules).")
            if is_api_product(selected_prod):
                st.info("For API products: go to **Developer View** to generate token and try endpoints.")
        else:
            st.warning("🔒 You do not have access to this product yet.")
            if not st.session_state.auth.get("logged_in"):
                st.info("Login to request access.")
            else:
                if st.button("Request Access", type="primary"):
                    create_access_request(selected_prod.id, username, persona)
                    st.success("Access request submitted (provider can approve in another browser).")

        st.divider()
        if st.button("Clear selection"):
            st.session_state.ui["selected_product_id"] = None
            st.rerun()

    # Grid of tiles
    if not filtered:
        st.info("No products match your filters.")
    else:
        cols_per_row = 3
        rows = (len(filtered) + cols_per_row - 1) // cols_per_row
        idx = 0
        for _ in range(rows):
            cols = st.columns(cols_per_row)
            for col in cols:
                if idx >= len(filtered):
                    break
                p = filtered[idx]
                idx += 1
                with col:
                    st.markdown(
                        f"""
                        <div class="card">
                            <h4>{p.name}</h4>
                            <div class="meta">
                                {pill_type(p.product_type)}
                                {pill_tier(p.tier)}
                                {pill_access(p.access)}
                                {pill(p.category, "pill-dataset")}
                            </div>
                            <div class="divider-soft"></div>
                            <p class="subtle">{p.description}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("View", key=f"tile_{p.id}", use_container_width=True):
                            st.session_state.ui["selected_product_id"] = p.id
                            st.rerun()
                    with b2:
                        # show quick access indicator
                        has = user_has_access(p, st.session_state.auth.get("username"))
                        st.write("✅" if has else "🔒")


# -----------------------------
# Developer View (technical only: access approvals + token + API explorer)
# -----------------------------
with tab_developer:
    st.subheader("Developer View")
    st.caption("Technical actions are separated from business browsing: approvals, token generation, API explorer.")

    require_requests()

    if not st.session_state.auth.get("logged_in"):
        st.warning("Login required to use Developer View.")
    else:
        username = st.session_state.auth.get("username")
        persona = st.session_state.auth.get("persona") or ""

        # Provider approvals (shared across sessions)
        if (persona or "").lower() == "data provider":
            st.markdown("### ✅ Provider: Approve Access Requests")
            state = load_shared_state()
            reqs = access_requests_from_state(state)
            pending = [r for r in reqs if r.get("status") == "PENDING"]

            if not pending:
                st.info("No pending requests.")
            else:
                for r in pending:
                    prod_id = r.get("product_id")
                    prod = next((x for x in merged_catalog() if x.id == prod_id), None)
                    st.markdown(
                        f"- **{r.get('requester')}** ({r.get('requester_persona')}) requested **{prod.name if prod else prod_id}** at {r.get('created_at')}"
                    )
                    a, b = st.columns([0.15, 0.85])
                    with a:
                        if st.button("Approve", key=f"ap_{r['id']}"):
                            approve_request(r["id"])
                            st.success("Approved.")
                            st.rerun()
                    with b:
                        if st.button("Reject", key=f"rej_{r['id']}"):
                            reject_request(r["id"])
                            st.warning("Rejected.")
                            st.rerun()

            st.divider()

        # Token generation (only for API products the user can access)
        st.markdown("### 🔑 Token Generation")
        catalog = merged_catalog()
        accessible_api_products = [p for p in catalog if is_api_product(p) and user_has_access(p, username)]

        if not accessible_api_products:
            st.info("No accessible API products for your user. Request access to an API product from Data Products tab.")
        else:
            name_to_id = {p.name: p.id for p in accessible_api_products}
            default_name = accessible_api_products[0].name
            chosen = st.selectbox("Choose API subscription product", list(name_to_id.keys()), index=0)
            chosen_id = name_to_id[chosen]
            chosen_prod = next(p for p in accessible_api_products if p.id == chosen_id)

            st.write("**Selected subscription**")
            st.write(f"- Product: **{chosen_prod.name}**")
            st.write(f"- Tier: **{chosen_prod.tier}**")
            st.write("**What this unlocks (demo):**")
            if chosen_prod.tier == "Free":
                st.write("- ✅ List listings")
                st.write("- ❌ Listing detail")
                st.write("- ❌ Export")
            elif chosen_prod.tier == "Paid":
                st.write("- ✅ List listings")
                st.write("- ✅ Listing detail")
                st.write("- ❌ Export")
            else:
                st.write("- ✅ List listings")
                st.write("- ✅ Listing detail")
                st.write("- ✅ Export (S3 presigned URL)")

            c1, c2 = st.columns([0.25, 0.75])
            with c1:
                if st.button("Generate Token", type="primary"):
                    tok = generate_demo_token(username, persona, chosen_prod)
                    st.session_state.subscription.update(
                        {
                            "product_id": chosen_prod.id,
                            "tier": chosen_prod.tier,
                            "token": tok,
                            "issued_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                    st.success("Token generated and activated.")
            with c2:
                tok = st.session_state.subscription.get("token")
                if tok:
                    st.caption("Active token")
                    st.code(f"Bearer {tok}")

            with st.expander("Token payload (decoded)"):
                tok = st.session_state.subscription.get("token")
                if not tok:
                    st.info("Generate a token first.")
                else:
                    payload = decode_token_payload(tok)
                    if payload:
                        st.json(payload)
                    else:
                        st.warning("Unable to decode token payload.")

        st.divider()

        # API Explorer (only your 3 endpoints)
        st.markdown("### 🧪 API Explorer (Only 3 Demo Endpoints)")
        st.caption("Uses only: /v1/listings, /v1/listings/{listing_id}, /v1/listings/export")

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
            listing_id = (params.pop("listing_id", "") or "").strip()
            path = path.replace("{listing_id}", listing_id)

        url = build_url(path)
        st.write("**Generated cURL**")
        st.code(build_curl(url, params, st.session_state.subscription.get("token")), language="bash")

        run_col, raw_col = st.columns([0.25, 0.75])
        with run_col:
            run = st.button("Run", type="primary", disabled=not allowed)
        with raw_col:
            show_raw = st.checkbox("Show raw JSON", value=False)

        if not allowed:
            st.info("Generate a token with the required tier in Developer View → Token Generation.")

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
                        trimmed = apply_rbac_to_listings(payload, persona)
                        if pd is not None:
                            st.dataframe(pd.DataFrame(trimmed), use_container_width=True)
                        else:
                            st.json(trimmed)
                        if "pagination" in data:
                            st.caption("Pagination")
                            st.json(data.get("pagination"))

                    elif isinstance(payload, dict):
                        # single record or export payload
                        if "LISTING_ID" in payload:
                            trimmed = apply_rbac_to_listings([payload], persona)
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
# Docs / Demo Notes
# -----------------------------
with tab_docs:
    st.subheader("Demo Notes (Provider + Consumer with Two Browsers)")
    st.markdown(
        """
### Recommended demo flow (matches meeting action items)
**Browser A (Provider persona):**
1. Login as `provider / provider123`
2. Go to **Marketplace** tab → **Provider Studio** → Publish a product (optional)
3. Go to **Developer View** → Approve pending access requests (if any)

**Browser B (Consumer/Agent persona):**
1. Login as `agent / agent123` or `consumer / consumer123`
2. Go to **Marketplace** tab → pick a domain/category → open product tile
3. Go to **Data Products** → View details → Request Access (for Partner/Private)
4. After provider approves, refresh → Access becomes available
5. For API products: Go to **Developer View** → Generate token → Run API Explorer calls

### Why the split (Business vs Developer)
- Business tabs focus on *what products exist and why they matter*
- Developer tab focuses on *how to integrate (token, APIs, cURL)*

### Reminder: Only these endpoints are used (as per original POC)
- GET /v1/listings
- GET /v1/listings/{listing_id}
- GET /v1/listings/export
"""
    )

    st.write("**API Base**")
    st.code(API_GATEWAY_BASE)

    st.write("**Sample users**")
    st.json({k: {"password": v["password"], "persona": v["display"]} for k, v in SAMPLE_USERS.items()})
