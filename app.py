"""MOVE Data Product Marketplace — demo app.

Flow  : Marketplace Landing → All Products → Listings Demo → Developer Tools → Business View
Demo  : Listings domain — REST API (3 endpoints) + Snowflake Native (no-copy private listing)
Persona: agent (provider) · consumer (business) · developer (technical)
See README.md for full narrative and demo script.
"""

import base64, json, os, time, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlencode

import streamlit as st

try:    import pandas as pd
except Exception:   pd = None
try:    import requests
except Exception:   requests = None

# ─── Config ───────────────────────────────────────────────────────────────────
API_BASE   = os.getenv("API_GATEWAY_BASE",   "https://7fsd5a0ox6.execute-api.us-east-2.amazonaws.com").rstrip("/")
API_PREFIX = os.getenv("API_VERSION_PREFIX", "/v1")

st.set_page_config(page_title="MOVE Data Product Marketplace", layout="wide", page_icon="🏠")

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container{padding-top:.7rem;padding-bottom:2.5rem}
h1,h2,h3{letter-spacing:-.015em}
[data-testid="stSidebar"]{border-right:1px solid rgba(49,51,63,.12)}

/* ─ Hero ─────────────────────────────────────────────────── */
.hero{background:linear-gradient(135deg,#09213a 0%,#0e3059 55%,#1554a0 100%);
  border-radius:16px;padding:30px 38px 26px;margin-bottom:4px}
.hero-ey{font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(255,255,255,.48);margin-bottom:5px}
.hero-t{font-size:1.95rem;font-weight:900;color:#fff;line-height:1.08;margin-bottom:5px}
.hero-s{font-size:.9rem;color:rgba(255,255,255,.78);margin-bottom:18px;max-width:660px}
.hero-stats{display:flex;gap:28px;flex-wrap:wrap}
.hv{font-size:1.6rem;font-weight:900;color:#fff;line-height:1}
.hl{font-size:.72rem;color:rgba(255,255,255,.56);margin-top:2px}

/* ─ Product-type grid ────────────────────────────────────── */
.pt-grid{display:flex;gap:10px;flex-wrap:wrap;margin:4px 0}
.pt-card{flex:1;min-width:120px;border-radius:12px;padding:15px 12px;text-align:center;
  border:1.5px solid transparent;cursor:pointer;transition:box-shadow .15s}
.pt-card:hover{box-shadow:0 4px 18px rgba(0,0,0,.10)}
.pt-icon{font-size:1.7rem;margin-bottom:6px}
.pt-name{font-weight:750;font-size:.88rem;margin-bottom:3px}
.pt-count{font-size:.74rem;font-weight:600;margin-bottom:3px}
.pt-desc{font-size:.73rem;color:rgba(49,51,63,.6);line-height:1.2rem}
.pt-api    {background:rgba(21,101,192,.06);border-color:rgba(21,101,192,.22)}
.pt-analytics{background:rgba(26,122,68,.06);border-color:rgba(26,122,68,.22)}
.pt-stream {background:rgba(106,27,154,.06);border-color:rgba(106,27,154,.22)}
.pt-dataset{background:rgba(69,39,160,.06);border-color:rgba(69,39,160,.22)}
.pt-report {background:rgba(230,81,0,.06);border-color:rgba(230,81,0,.22)}
.pt-sf     {background:rgba(2,119,189,.06);border-color:rgba(2,119,189,.28)}

/* ─ How it works ─────────────────────────────────────────── */
.hiw-grid{display:flex;gap:14px;margin:4px 0}
.hiw-card{flex:1;border-radius:12px;padding:18px 16px;border:1px solid rgba(49,51,63,.11);
  background:#fafbfd}
.hiw-num{width:28px;height:28px;border-radius:50%;background:#0e3059;color:#fff;
  font-weight:800;font-size:.82rem;display:flex;align-items:center;justify-content:center;
  margin-bottom:8px}
.hiw-title{font-weight:750;font-size:.92rem;margin-bottom:4px}
.hiw-desc{font-size:.8rem;color:rgba(49,51,63,.65);line-height:1.3rem}

/* ─ Domain tiles ─────────────────────────────────────────── */
.dom-tile{border-radius:11px;padding:14px 10px;text-align:center;
  box-shadow:0 1px 5px rgba(0,0,0,.04);height:100%}
.dt-icon{font-size:1.55rem;margin-bottom:5px}
.dt-name{font-weight:750;font-size:.88rem;margin-bottom:2px}
.dt-desc{font-size:.73rem;color:rgba(49,51,63,.58);line-height:1.18rem}

/* ─ Product cards ────────────────────────────────────────── */
.mkt-card{border:1px solid rgba(49,51,63,.12);border-radius:13px;
  padding:14px 14px 12px;
  background:linear-gradient(180deg,#fff 0%,rgba(255,255,255,.93) 100%);
  box-shadow:0 1px 7px rgba(0,0,0,.05);height:100%}
.mkt-title{font-weight:750;font-size:.96rem;margin-bottom:4px}
.mkt-desc{color:rgba(49,51,63,.72);font-size:.85rem;line-height:1.22rem;margin-bottom:7px}
.mkt-meta{margin:4px 0 6px}
.price{font-weight:850;font-size:1rem;margin-top:5px}
.small{font-size:.77rem;color:rgba(49,51,63,.66)}

/* ─ Access path cards ────────────────────────────────────── */
.ap-grid{display:flex;gap:14px;margin:4px 0}
.ap-card{flex:1;border-radius:13px;padding:18px 20px;border:1.5px solid transparent}
.ap-rest{background:rgba(21,101,192,.05);border-color:rgba(21,101,192,.22)}
.ap-sf  {background:rgba(2,119,189,.05); border-color:rgba(2,119,189,.28)}
.ap-icon{font-size:1.6rem;margin-bottom:6px}
.ap-title{font-weight:800;font-size:1rem;margin-bottom:2px}
.ap-sub{font-size:.78rem;color:rgba(49,51,63,.6);margin-bottom:10px}
.ap-row{font-size:.81rem;padding:2px 0;color:rgba(49,51,63,.8)}
.ap-code{font-family:monospace;font-size:.76rem;background:rgba(49,51,63,.06);
  border-radius:5px;padding:8px 10px;margin-top:9px;color:rgba(49,51,63,.78);
  border:1px solid rgba(49,51,63,.1);line-height:1.55rem}
.ap-tag{display:inline-block;margin-top:9px;padding:3px 10px;border-radius:999px;
  font-size:.74rem;font-weight:700}
.ap-tag-rest{background:rgba(21,101,192,.12);color:#1565c0;border:1px solid rgba(21,101,192,.28)}
.ap-tag-sf  {background:rgba(2,119,189,.12); color:#01579b;border:1px solid rgba(2,119,189,.28)}

/* ─ Demo step banner ─────────────────────────────────────── */
.demo-step{background:rgba(14,48,89,.06);border:1px solid rgba(14,48,89,.14);
  border-radius:10px;padding:10px 16px;margin-bottom:8px}
.demo-step-label{font-size:.68rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:rgba(49,51,63,.45);margin-bottom:3px}
.demo-step-text{font-weight:700;font-size:.95rem;color:#0e3059}

/* ─ Badges ───────────────────────────────────────────────── */
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.7rem;
  font-weight:650;margin-right:4px;margin-bottom:3px;
  border:1px solid rgba(49,51,63,.14);background:rgba(49,51,63,.04)}
.b-free  {background:rgba(46,204,113,.1); border-color:rgba(46,204,113,.35)}
.b-paid  {background:rgba(52,152,219,.1); border-color:rgba(52,152,219,.35)}
.b-ent   {background:rgba(155,89,182,.1); border-color:rgba(155,89,182,.35)}
.b-pub   {background:rgba(39,174,96,.1);  border-color:rgba(39,174,96,.35)}
.b-part  {background:rgba(52,152,219,.1); border-color:rgba(52,152,219,.35)}
.b-priv  {background:rgba(231,76,60,.1);  border-color:rgba(231,76,60,.35)}
.b-api       {background:rgba(21,101,192,.11); border-color:rgba(21,101,192,.38);color:#1565c0;font-weight:700}
.b-analytics {background:rgba(26,122,68,.11);  border-color:rgba(26,122,68,.38); color:#1a7a44;font-weight:700}
.b-stream    {background:rgba(106,27,154,.11); border-color:rgba(106,27,154,.38);color:#6a1b9a;font-weight:700}
.b-dataset   {background:rgba(69,39,160,.11);  border-color:rgba(69,39,160,.38); color:#4527a0;font-weight:700}
.b-report    {background:rgba(230,81,0,.11);   border-color:rgba(230,81,0,.38);  color:#e65100;font-weight:700}
.b-snowflake {background:rgba(2,119,189,.11);  border-color:rgba(2,119,189,.38); color:#01579b;font-weight:700}

/* ─ Enablers / Value ─────────────────────────────────────── */
.en-bar{display:flex;gap:12px}
.en-card{flex:1;border:1px solid rgba(49,51,63,.1);border-radius:10px;padding:12px 13px;
  background:rgba(249,250,252,.9);display:flex;align-items:flex-start;gap:9px}
.en-icon{font-size:1.25rem;margin-top:1px}
.en-label{font-weight:700;font-size:.86rem;margin-bottom:2px}
.en-desc{font-size:.74rem;color:rgba(49,51,63,.6);line-height:1.2rem}
.val-section{background:linear-gradient(135deg,#09213a,#0e3059 60%,#1554a0 100%);
  border-radius:13px;padding:22px 26px;margin-top:8px}
.val-heading{color:#fff;font-weight:800;font-size:.95rem;margin-bottom:12px}
.val-grid{display:flex;gap:12px;flex-wrap:wrap}
.val-card{flex:1;min-width:145px;background:rgba(255,255,255,.09);border-radius:9px;
  padding:13px 14px;border:1px solid rgba(255,255,255,.12)}
.val-icon{font-size:1.35rem;margin-bottom:5px}
.val-label{color:#fff;font-weight:750;font-size:.88rem;margin-bottom:3px}
.val-desc{color:rgba(255,255,255,.68);font-size:.76rem;line-height:1.2rem}

/* ─ Provider ─────────────────────────────────────────────── */
.prov-card{border:2px dashed rgba(52,152,219,.32);border-radius:12px;
  padding:18px;background:rgba(52,152,219,.02)}

/* ─ Business view ─────────────────────────────────────────── */
.biz-card{border:1px solid rgba(49,51,63,.12);border-radius:13px;padding:16px;
  background:#fff;box-shadow:0 1px 6px rgba(0,0,0,.04)}
.biz-thumb{border-radius:8px;height:120px;display:flex;align-items:center;
  justify-content:center;font-size:2.5rem;margin-bottom:10px}

code{font-size:.81rem}

/* ─ Snowflake listing card ────────────────────────────────── */
.sf-listing-card{background:linear-gradient(135deg,#0d2f4f 0%,#1a4f7a 60%,#29b5e8 100%);
  border-radius:14px;padding:24px 28px 20px;margin-bottom:4px;position:relative}
.sf-listing-eyebrow{font-size:.68rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:rgba(255,255,255,.5);margin-bottom:6px}
.sf-listing-title{font-size:1.55rem;font-weight:900;color:#fff;line-height:1.1;margin-bottom:5px}
.sf-listing-sub{font-size:.88rem;color:rgba(255,255,255,.78);margin-bottom:14px}
.sf-listing-tags{display:flex;gap:8px;flex-wrap:wrap}
.sf-tag{padding:3px 10px;border-radius:999px;font-size:.73rem;font-weight:700;
  background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.22)}
.sf-tag-installed{background:rgba(41,181,232,.3);border-color:rgba(41,181,232,.5);color:#b3edfb}
.sf-listing-meta{display:flex;gap:24px;margin-top:14px;flex-wrap:wrap}
.sf-meta-item{font-size:.78rem;color:rgba(255,255,255,.6)}
.sf-meta-val{font-weight:700;color:#fff;font-size:.9rem}

/* ─ Data dictionary table ────────────────────────────────── */
.dd-table{width:100%;border-collapse:collapse;font-size:.82rem}
.dd-table th{background:#f0f2f6;padding:7px 10px;text-align:left;font-weight:700;
  border-bottom:2px solid rgba(49,51,63,.15)}
.dd-table td{padding:6px 10px;border-bottom:1px solid rgba(49,51,63,.07);vertical-align:top}
.dd-table tr:hover td{background:rgba(41,181,232,.04)}
.dd-type{font-family:monospace;font-size:.75rem;color:#5a6a80;background:rgba(49,51,63,.06);
  border-radius:4px;padding:1px 6px}
.dd-secured{font-size:.7rem;font-weight:700;color:#e65100;background:rgba(230,81,0,.1);
  border-radius:4px;padding:1px 6px;border:1px solid rgba(230,81,0,.2)}
.dd-flag{color:#6a1b9a;font-weight:700}

/* ─ Registration form card ───────────────────────────────── */
.reg-card{border:2px solid rgba(41,181,232,.28);border-radius:14px;
  padding:22px 24px;background:rgba(41,181,232,.03)}
</style>
""", unsafe_allow_html=True)

# ─── Data model ───────────────────────────────────────────────────────────────
@dataclass
class Product:
    id: str
    name: str
    description: str
    domain: str
    product_type: str    # api | analytics | stream | dataset | report | snowflake
    delivery_tech: str   # human label: REST/HTTP · Kafka · Kinesis · S3/Parquet · Tableau · Snowflake Share
    tier: str            # Free | Paid | Enterprise
    access: str          # Public | Partner | Private
    price_monthly: Optional[float]
    features: List[str]
    tags: List[str]
    endpoints: List[Dict[str, str]] = field(default_factory=list)
    snowflake_share: Optional[str] = None
    snowflake_view:  Optional[str] = None
    is_demo: bool = False   # highlighted in the Listings Demo tab
    provider: str = "Brillio / MOVE"

# ─── Static content ───────────────────────────────────────────────────────────
PRODUCT_TYPES = [
    {"type": "api",       "icon": "🔌", "name": "REST APIs",       "css": "pt-api",
     "desc": "HTTP endpoints, Bearer token auth. Works with any language or tool."},
    {"type": "analytics", "icon": "📊", "name": "Analytics",       "css": "pt-analytics",
     "desc": "Embeddable dashboards and interactive visualisations. No code needed."},
    {"type": "stream",    "icon": "⚡", "name": "Event Streams",   "css": "pt-stream",
     "desc": "Real-time feeds via Apache Kafka or Amazon Kinesis for live pipelines."},
    {"type": "dataset",   "icon": "📦", "name": "Datasets",        "css": "pt-dataset",
     "desc": "Bulk exports to S3 in Parquet, CSV, or JSON. Scheduled or on-demand."},
    {"type": "report",    "icon": "📋", "name": "BI Reports",      "css": "pt-report",
     "desc": "Pre-built Tableau, Looker, or Power BI reports. Embed or download."},
    {"type": "snowflake", "icon": "❄️", "name": "Snowflake Native","css": "pt-sf",
     "desc": "Private Listings with secure views. Zero copy, zero ETL, always live."},
]

DOMAINS = [
    {"name": "Listings",           "icon": "🏠", "desc": "Active & historical property listings"},
    {"name": "Consumer Journey",   "icon": "🛒", "desc": "Buyer & seller lifecycle analytics"},
    {"name": "Agent",              "icon": "🤝", "desc": "Agent profiles, performance & recruiting"},
    {"name": "Market Intelligence","icon": "📈", "desc": "Price trends, DOM & inventory signals"},
    {"name": "Leads",              "icon": "🎯", "desc": "Lead ingestion, scoring & routing"},
    {"name": "Ads",                "icon": "📢", "desc": "Ad impressions, CTR & revenue attribution"},
    {"name": "Transactions",       "icon": "📝", "desc": "Closed deals, compliance & audit data"},
]

JOURNEY = [
    {"step": "Discover", "icon": "🔍", "desc": "Find products"},
    {"step": "Define",   "icon": "📋", "desc": "Govern & own"},
    {"step": "Develop",  "icon": "⚙️",  "desc": "Build & publish"},
    {"step": "Deliver",  "icon": "🚀", "desc": "APIs & shares"},
    {"step": "Access",   "icon": "🔑", "desc": "Subscribe & use"},
]

HOW_IT_WORKS = [
    {"num": "1", "title": "Browse & Discover",
     "desc": "Explore 60+ data products across MOVE's business domains. Filter by type, tier, or domain. Request access in seconds."},
    {"num": "2", "title": "Subscribe & Access",
     "desc": "REST users generate a Bearer token tied to their subscription tier. Snowflake users accept a Private Listing and query in-place."},
    {"num": "3", "title": "Integrate & Build",
     "desc": "Call REST endpoints, query Snowflake secure views, subscribe to Kafka streams, or embed BI dashboards directly into your product."},
]

ENABLERS = [
    {"icon": "🛡️", "label": "AI Governance",  "desc": "Policy-driven access, data ownership, and audit trails."},
    {"icon": "✅", "label": "Data Quality",    "desc": "Automated profiling, freshness checks, SLA monitoring."},
    {"icon": "⚙️", "label": "Data Ops",        "desc": "CI/CD pipelines, lineage tracking, automated deployment."},
]

VALUES = [
    {"icon": "⚡", "label": "Faster Onboarding",    "desc": "Self-serve discovery cuts time-to-data from weeks to hours."},
    {"icon": "🎯", "label": "Trusted Intelligence", "desc": "Governed, quality-checked — a single source of truth."},
    {"icon": "💰", "label": "New Revenue Streams",  "desc": "Monetise assets via internal charge-back or public Snowflake listing."},
]

# ─── Comprehensive product catalog ───────────────────────────────────────────
_P = API_PREFIX

CATALOG: List[Product] = [

  # ══════════════════════════════════════════════════════════════════════════
  # LISTINGS  (demo domain — REST + Snowflake shown live)
  # ══════════════════════════════════════════════════════════════════════════

  # REST API tiers ─────────────────────────────────────────────────────────
  Product("api-list-free", "Listings API — Starter",
    "Free-tier access to active listings. Ideal for evaluation and quick prototypes.",
    "Listings","api","REST/HTTP","Free","Public",0.0,
    ["1,000 calls/month","Active listings only","Filters: status, limit","Community support"],
    ["REST","Free","Starter"],
    endpoints=[{"name":"List listings","method":"GET","path":f"{_P}/listings"}],
    is_demo=True),

  Product("api-list-std", "Listings API — Standard",
    "Standard listing access with detail endpoint — for agent portals and CRM integrations.",
    "Listings","api","REST/HTTP","Paid","Public",300.0,
    ["10,000 calls/month","List + detail endpoints","Filters: status, limit, offset","Standard SLA"],
    ["REST","CRM","Active"],
    endpoints=[
      {"name":"List listings","method":"GET","path":f"{_P}/listings"},
      {"name":"Listing detail","method":"GET","path":f"{_P}/listings/{{listing_id}}"},
    ], is_demo=True),

  Product("api-list-ent", "Listings API — Enterprise",
    "Full REST access including bulk CSV export to S3. For large-scale pipelines.",
    "Listings","api","REST/HTTP","Enterprise","Private",5000.0,
    ["Unlimited calls","List + detail + export","S3 pre-signed URLs","Dedicated SLA"],
    ["REST","Bulk","Export"],
    endpoints=[
      {"name":"List listings","method":"GET","path":f"{_P}/listings"},
      {"name":"Listing detail","method":"GET","path":f"{_P}/listings/{{listing_id}}"},
      {"name":"Export to S3","method":"GET","path":f"{_P}/listings/export"},
    ], is_demo=True),

  # Snowflake Native ───────────────────────────────────────────────────────
  Product("sf-list", "MOVE Listings — Active Inventory Share",
    "Query MOVE's active inventory in your Snowflake account. Zero copy — column & row security via secure view.",
    "Listings","snowflake","Snowflake Private Share","Enterprise","Private",4000.0,
    ["No data copy — lives in MOVE's Snowflake","Secure view: column & row-level security",
     "Live data — no ETL, no scheduled refresh","Natively governed by Snowflake"],
    ["No-Copy","Active","Secure View"],
    snowflake_share="BRILLIO_MOVE_LISTINGS_V1",
    snowflake_view="MOVE_DB.LISTINGS.ACTIVE_LISTINGS_VW", is_demo=True),

  Product("sf-list-hist", "MOVE Listings — Historical Archive Share",
    "Five-year historical listing archive accessible as a Snowflake secure view. Zero copy.",
    "Listings","snowflake","Snowflake Private Share","Enterprise","Private",5500.0,
    ["5-year listing history","No data copy","Price, DOM, status change history",
     "Partitioned by year — query specific cohorts"],
    ["No-Copy","Historical","Archive"],
    snowflake_share="BRILLIO_MOVE_LISTINGS_HIST_V1",
    snowflake_view="MOVE_DB.LISTINGS.LISTING_HISTORY_VW"),

  # Analytics / Dashboards ─────────────────────────────────────────────────
  Product("analytics-list", "Listings Performance Dashboard",
    "Embeddable analytics: active inventory counts, median price trends, and DOM distribution by metro.",
    "Listings","analytics","Embedded / Streamlit","Paid","Public",599.0,
    ["Active inventory counts","Median price trend (12-month)","DOM distribution histogram",
     "Metro / ZIP drill-down","Weekly refresh"],
    ["Dashboard","Inventory","DOM"]),

  Product("analytics-list-comp", "Comparable Listings Analyzer",
    "Automated comp selection and price-per-sqft analysis. Embed in agent portals or run ad-hoc.",
    "Listings","analytics","Embedded / Streamlit","Paid","Partner",899.0,
    ["Automated comp selection by geo + attributes","Price-per-sqft benchmarking",
     "Adjustable radius & filter controls","Agent-portal embed ready"],
    ["Comps","Pricing","Embed"]),

  # Event Streams ──────────────────────────────────────────────────────────
  Product("stream-list", "Active Listings Event Stream",
    "Real-time Kafka stream of listing create/update/delete events. Sub-second latency.",
    "Listings","stream","Apache Kafka","Paid","Partner",800.0,
    ["Kafka topic: move.listings.events","Create / update / delete event types",
     "Avro schema + Schema Registry","< 1-second end-to-end latency"],
    ["Kafka","Real-Time","Events"], is_demo=True),

  Product("stream-list-price", "Listing Price Change Stream",
    "Kinesis stream firing on every listing price reduction or increase.",
    "Listings","stream","Amazon Kinesis","Paid","Partner",650.0,
    ["Kinesis: move.listings.price_changes","Old/new price, delta, pct change",
     "Millisecond latency","Ideal for alert engines and dashboards"],
    ["Kinesis","Price Alert","Real-Time"]),

  # Bulk Datasets ──────────────────────────────────────────────────────────
  Product("dataset-list", "Master Listing Dataset",
    "Full listing history (5 years, 2M+ records) in Parquet on S3. Nightly snapshot.",
    "Listings","dataset","S3 / Parquet","Enterprise","Private",3000.0,
    ["2M+ historical records","Nightly S3 snapshot","Parquet + CSV available","Schema docs included"],
    ["S3","Parquet","History"]),

  Product("dataset-list-offmkt", "Off-Market Listings Dataset",
    "Withdrawn, expired, and off-market listings — ideal for investment opportunity scoring.",
    "Listings","dataset","S3 / Parquet","Enterprise","Private",2200.0,
    ["Withdrawn + expired + cancelled listings","Price reduction history included",
     "Monthly S3 snapshot","Schema aligned with active listings"],
    ["S3","Off-Market","Investment"]),

  # BI Reports ─────────────────────────────────────────────────────────────
  Product("report-list", "Listing Price Index Report",
    "Pre-built Tableau report: price-per-sqft trends, DOM distributions, and inventory heatmaps.",
    "Listings","report","Tableau Embedded","Paid","Public",500.0,
    ["Price-per-sqft trends","DOM distribution charts","Inventory heatmap by ZIP",
     "Monthly refresh, PDF export"],
    ["Tableau","Price Index","Monthly"]),

  Product("report-list-aging", "Listing Aging & DOM Report",
    "Power BI report tracking days-on-market aging buckets, stale inventory flags, and price-cut frequency.",
    "Listings","report","Power BI Embedded","Paid","Partner",550.0,
    ["DOM aging buckets (0-7, 8-30, 31-60, 60+ days)","Stale inventory flags",
     "Price-cut frequency by market","Monthly refresh, Teams/SharePoint embed"],
    ["Power BI","DOM","Aging"]),

  # ══════════════════════════════════════════════════════════════════════════
  # CONSUMER JOURNEY
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-cj", "Consumer Journey API",
    "Track the full buyer/seller lifecycle: search, view, inquiry, offer, close.",
    "Consumer Journey","api","REST/HTTP","Paid","Partner",900.0,
    ["Full funnel: search → close","Cohort and segment filters",
     "10,000 calls/month","Partner-only access"],
    ["REST","Funnel","Buyer"]),

  Product("api-cj-segments", "Consumer Segments API",
    "Retrieve buyer/seller intent segments: first-time buyer, upsizer, investor, relocator.",
    "Consumer Journey","api","REST/HTTP","Paid","Partner",750.0,
    ["Intent segment labels per consumer","Confidence scores","Geo + price range signals",
     "5,000 calls/month"],
    ["REST","Segments","Intent"]),

  Product("analytics-cj", "Consumer Behavior Dashboard",
    "Embeddable dashboard: funnel drop-off, session behavior, and conversion rates.",
    "Consumer Journey","analytics","Embedded / Streamlit","Paid","Public",699.0,
    ["Funnel drop-off visualisation","Session & engagement metrics",
     "Weekly refresh","Iframe embed or share link"],
    ["Dashboard","Funnel","Embed"]),

  Product("analytics-cj-cohort", "Consumer Cohort Analysis",
    "Cohort retention and reactivation analytics: compare buyer cohorts across acquisition channels.",
    "Consumer Journey","analytics","Embedded / Streamlit","Enterprise","Partner",1200.0,
    ["Cohort retention curves","Channel attribution breakdown",
     "Churn and reactivation signals","Bi-weekly refresh"],
    ["Cohorts","Retention","Attribution"]),

  Product("stream-cj", "Consumer Events Stream",
    "Kinesis stream of consumer page-view, search, and inquiry events in real time.",
    "Consumer Journey","stream","Amazon Kinesis","Enterprise","Private",1500.0,
    ["Kinesis: move.consumer.events","Page-view, search, inquiry events",
     "PII masked at source","Millisecond latency"],
    ["Kinesis","Events","PII-safe"]),

  Product("dataset-cj", "Consumer Behavior Dataset",
    "Anonymised consumer session and funnel dataset. Quarterly snapshots in Parquet.",
    "Consumer Journey","dataset","S3 / Parquet","Enterprise","Private",2500.0,
    ["Anonymised session + funnel records","12-month rolling window",
     "Quarterly S3 snapshot","Schema docs + data dictionary"],
    ["S3","Sessions","Anonymised"]),

  Product("report-cj", "Consumer Intent Report",
    "Tableau report: buyer intent signals, search-to-inquiry conversion, and market readiness index.",
    "Consumer Journey","report","Tableau Embedded","Paid","Partner",620.0,
    ["Buyer intent signal scoring","Search-to-inquiry conversion rates",
     "Market readiness index by metro","Monthly refresh"],
    ["Tableau","Intent","Conversion"]),

  Product("sf-cj", "Consumer Journey — Snowflake View",
    "Query consumer funnel data directly in your Snowflake account. No copy, partner-only.",
    "Consumer Journey","snowflake","Snowflake Private Share","Paid","Partner",950.0,
    ["Funnel and cohort tables","No data copy","Partner role-based column visibility",
     "Weekly refresh, live via share"],
    ["No-Copy","Funnel","Partner"],
    snowflake_share="BRILLIO_MOVE_CONSUMER_V1",
    snowflake_view="MOVE_DB.CONSUMERS.CONSUMER_JOURNEY_VW"),

  # ══════════════════════════════════════════════════════════════════════════
  # AGENT
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-agent", "Agent Profile API",
    "Curated agent profiles: bio, license, transaction history, ratings.",
    "Agent","api","REST/HTTP","Paid","Public",450.0,
    ["Agent bio, license, ratings","Transaction history","10,000 calls/month","Public access"],
    ["REST","Profiles","CRM"]),

  Product("api-agent-perf", "Agent Performance Metrics API",
    "Live performance KPIs per agent: volume, GCI, avg DOM, list-to-sale ratio.",
    "Agent","api","REST/HTTP","Paid","Partner",600.0,
    ["Volume, GCI, avg DOM","List-to-sale price ratio","30 / 90 / 12-month windows",
     "Filterable by geo, brokerage, tier"],
    ["REST","KPIs","Performance"]),

  Product("analytics-agent", "Agent Performance Dashboard",
    "Interactive leaderboard and trend analysis for agent productivity and market share.",
    "Agent","analytics","Embedded / Streamlit","Paid","Partner",799.0,
    ["Leaderboard by volume, GCI, DOM","Market share by geo","Year-over-year trends",
     "Embed in franchise portal"],
    ["Dashboard","Leaderboard","Market Share"]),

  Product("stream-agent", "Agent Activity Stream",
    "Kafka stream of agent listing publishes, price changes, and status updates.",
    "Agent","stream","Apache Kafka","Paid","Partner",550.0,
    ["Kafka: move.agent.activity","Listing publish, price change, close events",
     "Avro schema","< 2-second latency"],
    ["Kafka","Activity","Events"]),

  Product("report-agent", "Agent Performance Report",
    "Pre-built Looker report: agent volume rankings, conversion rates, and recruiting signals.",
    "Agent","report","Looker Embedded","Paid","Partner",600.0,
    ["Volume & conversion rankings","Recruiting signal scoring",
     "Monthly refresh","Looker embed or PDF"],
    ["Looker","Recruiting","Rankings"]),

  Product("dataset-agent", "Agent Transaction Dataset",
    "Complete agent-level transaction history in CSV. Updated monthly via S3.",
    "Agent","dataset","S3 / CSV","Paid","Partner",700.0,
    ["Agent transaction history (5 yrs)","GCI, unit volume, DOM stats",
     "Monthly S3 drop","CSV + Parquet"],
    ["S3","CSV","Transactions"]),

  Product("sf-agent", "Agent Data — Snowflake Share",
    "Query agent profiles and performance KPIs in your Snowflake account. Partner-only.",
    "Agent","snowflake","Snowflake Private Share","Paid","Partner",850.0,
    ["Agent profile + KPI tables","No data copy","Column-level security on PII",
     "Monthly refresh via share"],
    ["No-Copy","Profiles","Partner"],
    snowflake_share="BRILLIO_MOVE_AGENT_V1",
    snowflake_view="MOVE_DB.AGENTS.AGENT_PROFILES_VW"),

  # ══════════════════════════════════════════════════════════════════════════
  # MARKET INTELLIGENCE
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-market", "Market Intelligence API",
    "Programmatic access to metro/ZIP market metrics: median price, DOM, inventory.",
    "Market Intelligence","api","REST/HTTP","Paid","Public",600.0,
    ["Metro & ZIP granularity","Median price, DOM, inventory","10,000 calls/month","Weekly refresh"],
    ["REST","KPIs","Market"]),

  Product("api-market-forecast", "Market Forecast API",
    "90-day price appreciation and inventory forecasts powered by MOVE's ML models.",
    "Market Intelligence","api","REST/HTTP","Enterprise","Partner",2000.0,
    ["90-day price & inventory forecast","Metro + ZIP granularity","Confidence intervals",
     "Model version pinning for reproducibility"],
    ["REST","Forecast","ML"]),

  Product("analytics-market", "Market Trends Dashboard",
    "Interactive dashboard: price trends, supply/demand heatmap, and competitive analysis.",
    "Market Intelligence","analytics","Embedded / Streamlit","Paid","Public",799.0,
    ["Price trend charts","Supply/demand heatmap","Comp market analysis",
     "Embeddable iframe, weekly refresh"],
    ["Dashboard","Heatmap","Trends"]),

  Product("analytics-market-heatmap", "Geo Price Heatmap",
    "ZIP-code level price-per-sqft heatmap with year-over-year delta. Embeddable Mapbox visual.",
    "Market Intelligence","analytics","Embedded / Mapbox","Paid","Public",699.0,
    ["ZIP-code price-per-sqft","YoY delta layer","Interactive pan/zoom","Weekly refresh"],
    ["Mapbox","Heatmap","Geo"]),

  Product("stream-market", "Market Signals Stream",
    "Kafka stream of weekly market stat updates: median price, DOM, new listing counts per ZIP.",
    "Market Intelligence","stream","Apache Kafka","Paid","Partner",700.0,
    ["Kafka: move.market.weekly_stats","Median price, DOM, inventory per ZIP",
     "JSON payload + schema","Weekly batch-to-stream"],
    ["Kafka","Stats","Weekly"]),

  Product("dataset-market", "Market Historical Dataset",
    "10-year metro/ZIP market statistics. Monthly snapshots in Parquet on S3.",
    "Market Intelligence","dataset","S3 / Parquet","Enterprise","Private",2800.0,
    ["10-year monthly stats per ZIP","Median price, DOM, inventory, absorption rate",
     "Monthly S3 snapshot","Schema docs + data dictionary"],
    ["S3","Historical","10-Year"]),

  Product("report-market", "Market Summary Report",
    "Looker report: monthly market health scorecard, inventory turns, and demand index.",
    "Market Intelligence","report","Looker Embedded","Paid","Partner",580.0,
    ["Monthly market health scorecard","Inventory turn rate","Demand index by metro",
     "Looker embed, auto-refresh monthly"],
    ["Looker","Scorecard","Monthly"]),

  Product("sf-market", "Market Intelligence — Snowflake View",
    "Query MOVE's market KPIs from your Snowflake account. Weekly-refreshed secure view.",
    "Market Intelligence","snowflake","Snowflake Private Share","Paid","Partner",900.0,
    ["Median price, DOM, inventory KPIs","Metro & ZIP granularity",
     "No copy — query from your account","Partner role-based access"],
    ["No-Copy","KPIs","Partner"],
    snowflake_share="BRILLIO_MOVE_MARKET_V1",
    snowflake_view="MOVE_DB.MARKET.MARKET_INTEL_VW"),

  # ══════════════════════════════════════════════════════════════════════════
  # LEADS
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-leads", "Leads Engine API",
    "Ingest, score, and route buyer/seller leads to agents and franchises.",
    "Leads","api","REST/HTTP","Paid","Partner",1200.0,
    ["Lead ingestion + scoring","Routing rules by geo and tier",
     "Webhook callbacks on status change","Partner-only"],
    ["REST","Lead Routing","CRM"]),

  Product("api-leads-score", "Lead Scoring API",
    "On-demand lead quality scoring: returns intent score, timeline, and geo match.",
    "Leads","api","REST/HTTP","Paid","Partner",900.0,
    ["Intent score 0–100","Estimated timeline to close","Geo and price range match",
     "5,000 calls/month"],
    ["REST","Scoring","ML"]),

  Product("analytics-leads", "Lead Performance Dashboard",
    "Embeddable dashboard: lead volume, conversion funnel, source attribution, and ROI.",
    "Leads","analytics","Embedded / Streamlit","Paid","Partner",850.0,
    ["Lead volume by source","Conversion funnel: lead → inquiry → close",
     "Source ROI analysis","Weekly refresh"],
    ["Dashboard","Conversion","ROI"]),

  Product("stream-leads", "Lead Routing Stream",
    "Kafka topic delivering scored leads to downstream CRM and notification systems.",
    "Leads","stream","Apache Kafka","Paid","Partner",750.0,
    ["Kafka: move.leads.scored","Lead score + routing metadata",
     "Avro schema","< 500ms latency"],
    ["Kafka","Leads","CRM"]),

  Product("stream-leads-alerts", "High-Intent Lead Alert Stream",
    "Kinesis stream firing on leads with intent score ≥ 80. For real-time CRM push and SMS.",
    "Leads","stream","Amazon Kinesis","Enterprise","Private",1100.0,
    ["Kinesis: move.leads.high_intent","Score ≥ 80 threshold filter",
     "Lead details + contact info (masked)","< 200ms latency"],
    ["Kinesis","High-Intent","Alerts"]),

  Product("dataset-leads", "Lead History Dataset",
    "Historical lead records with outcomes: converted, lost, stale. Quarterly Parquet on S3.",
    "Leads","dataset","S3 / Parquet","Enterprise","Private",1800.0,
    ["Leads + outcomes (converted / lost / stale)","Source, score, agent assignment",
     "Quarterly S3 snapshot","Schema docs included"],
    ["S3","History","Outcomes"]),

  Product("report-leads", "Lead Quality Report",
    "Power BI report: lead quality distribution, source ranking, and conversion rate by agent.",
    "Leads","report","Power BI Embedded","Paid","Partner",520.0,
    ["Quality distribution histogram","Source ranking by conversion","Conversion by agent & brokerage",
     "Monthly refresh, Teams embed"],
    ["Power BI","Quality","Source Ranking"]),

  Product("sf-leads", "Leads — Snowflake Share",
    "Query lead records and scoring history in your Snowflake account. PII masked.",
    "Leads","snowflake","Snowflake Private Share","Enterprise","Private",1400.0,
    ["Lead + score + outcome tables","PII masked at column level",
     "No data copy","Quarterly refresh via share"],
    ["No-Copy","Scoring","PII-safe"],
    snowflake_share="BRILLIO_MOVE_LEADS_V1",
    snowflake_view="MOVE_DB.LEADS.SCORED_LEADS_VW"),

  # ══════════════════════════════════════════════════════════════════════════
  # ADS
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-ads", "Ads Performance API",
    "Query impression, click, and revenue metrics by campaign, placement, and date.",
    "Ads","api","REST/HTTP","Paid","Partner",800.0,
    ["Impression, CTR, revenue by campaign","Filters: placement, date, geo",
     "5,000 calls/month","Partner-only"],
    ["REST","Campaigns","Attribution"]),

  Product("api-ads-audience", "Ad Audience Targeting API",
    "Build and query audience segments for listing-page ad targeting.",
    "Ads","api","REST/HTTP","Enterprise","Private",1500.0,
    ["Audience segment definitions","Reach estimates","Geo + intent filters",
     "Private access, 2,000 calls/month"],
    ["REST","Targeting","Audiences"]),

  Product("analytics-ads", "Ads Revenue Dashboard",
    "Impression, click, and revenue attribution across MOVE listing and search placements.",
    "Ads","analytics","Embedded / Looker","Paid","Partner",1100.0,
    ["Impression, CTR, revenue by campaign","Daily refresh","90-day lookback",
     "Looker embed or API-delivered"],
    ["Looker","Attribution","CTR"]),

  Product("analytics-ads-reach", "Ad Reach & Frequency Dashboard",
    "Reach and frequency analytics: unique viewers, impression frequency caps, audience overlap.",
    "Ads","analytics","Embedded / Looker","Paid","Partner",950.0,
    ["Unique viewer counts","Impression frequency distribution","Audience overlap analysis",
     "Weekly refresh"],
    ["Looker","Reach","Frequency"]),

  Product("stream-ads", "Ad Impression Stream",
    "Kinesis stream of ad impression and click events for real-time bidding and attribution.",
    "Ads","stream","Amazon Kinesis","Enterprise","Private",2000.0,
    ["Kinesis: move.ads.impressions","Impression + click events","Sub-second latency","PII-masked"],
    ["Kinesis","Impressions","Real-Time"]),

  Product("dataset-ads", "Ad Campaign Dataset",
    "Full campaign performance history: impressions, clicks, revenue. Monthly Parquet on S3.",
    "Ads","dataset","S3 / Parquet","Enterprise","Private",2400.0,
    ["Campaign-level performance history","Impression, click, revenue columns",
     "Monthly S3 snapshot","Media-buy attribution included"],
    ["S3","Campaigns","History"]),

  Product("report-ads", "Ad Attribution Report",
    "Looker report: last-touch and multi-touch attribution for MOVE ad placements.",
    "Ads","report","Looker Embedded","Paid","Partner",700.0,
    ["Last-touch attribution model","Multi-touch (linear) model","Revenue lift by placement",
     "Monthly refresh"],
    ["Looker","Attribution","Revenue Lift"]),

  Product("sf-ads", "Ads Analytics — Snowflake Share",
    "Query ad performance data directly in your Snowflake account. Aggregated, no PII.",
    "Ads","snowflake","Snowflake Private Share","Enterprise","Private",1800.0,
    ["Campaign + placement performance tables","No PII — aggregated only",
     "No data copy","Monthly refresh via share"],
    ["No-Copy","Campaigns","Aggregated"],
    snowflake_share="BRILLIO_MOVE_ADS_V1",
    snowflake_view="MOVE_DB.ADS.AD_PERFORMANCE_VW"),

  # ══════════════════════════════════════════════════════════════════════════
  # TRANSACTIONS
  # ══════════════════════════════════════════════════════════════════════════

  Product("api-txn", "Transactions API",
    "Access closed transaction records: price, date, agent, property attributes.",
    "Transactions","api","REST/HTTP","Paid","Partner",1000.0,
    ["Closed transactions with full detail","Filters: date, geo, agent, price range",
     "Partner-only access","5,000 calls/month"],
    ["REST","Closed","Compliance"]),

  Product("api-txn-comps", "Transaction Comps API",
    "On-demand comparable sales lookup: return the 5–10 closest comps for any address.",
    "Transactions","api","REST/HTTP","Paid","Partner",1100.0,
    ["Comparable sales by address or geo","Adjustable radius, date range, beds/baths",
     "Sold price, adjusted price, distance","5,000 calls/month"],
    ["REST","Comps","Valuation"]),

  Product("analytics-txn", "Transaction Insights Dashboard",
    "Closed sale analytics: price distribution, GCI by brokerage, seasonal velocity.",
    "Transactions","analytics","Embedded / Streamlit","Paid","Partner",920.0,
    ["Closed price distribution","GCI by brokerage & agent","Seasonal velocity chart",
     "Monthly refresh, embed-ready"],
    ["Dashboard","GCI","Velocity"]),

  Product("stream-txn", "Transaction Events Stream",
    "Kafka stream firing on every closed transaction. Includes sale price, agent, and property.",
    "Transactions","stream","Apache Kafka","Paid","Partner",900.0,
    ["Kafka: move.transactions.closed","Sale price, agent, property attributes",
     "Avro schema","Near-real-time (< 5 min post-close)"],
    ["Kafka","Closed","Events"]),

  Product("dataset-txn", "Closed Transactions Dataset",
    "Historical closed transaction dataset (10 years, 5M+ records) in Parquet on S3.",
    "Transactions","dataset","S3 / Parquet","Enterprise","Private",3500.0,
    ["5M+ closed transactions","10-year history","Monthly S3 snapshot","Parquet + schema docs"],
    ["S3","Parquet","Historical"]),

  Product("dataset-txn-public", "Public Records Reconciled Dataset",
    "Closed transactions reconciled with county public records. Deduped and normalised.",
    "Transactions","dataset","S3 / Parquet","Enterprise","Private",4000.0,
    ["MLS + public record reconciliation","Deduped and geo-coded","10-year history",
     "Monthly S3 snapshot"],
    ["S3","Public Records","Reconciled"]),

  Product("report-txn", "Transaction Summary Report",
    "Power BI report: monthly closed volume, avg sale price, agent productivity scorecard.",
    "Transactions","report","Power BI Embedded","Paid","Partner",650.0,
    ["Monthly closed volume & avg price","Agent productivity scorecard",
     "Brokerage market share","Monthly refresh, Teams embed"],
    ["Power BI","Volume","Scorecard"]),

  Product("sf-txn", "Closed Deals — Snowflake Share",
    "Query closed transaction history in your Snowflake account. Row-level security by region.",
    "Transactions","snowflake","Snowflake Private Share","Enterprise","Private",3200.0,
    ["Closed transactions table (10-year)","Row-level security by region / brokerage",
     "No data copy","Monthly refresh via share"],
    ["No-Copy","Historical","Row-Security"],
    snowflake_share="BRILLIO_MOVE_TRANSACTIONS_V1",
    snowflake_view="MOVE_DB.TRANSACTIONS.CLOSED_DEALS_VW"),
]

CATALOG_BY_ID = {p.id: p for p in CATALOG}

# ─── Users ────────────────────────────────────────────────────────────────────
USERS = {
    "agent":    {"password":"agent123",    "display":"Real Estate Agent", "role":"provider"},
    "consumer": {"password":"consumer123", "display":"Data Consumer",     "role":"consumer"},
    "developer":{"password":"dev123",      "display":"Developer",         "role":"developer"},
}

# ─── Session ──────────────────────────────────────────────────────────────────
for key, default in [
    ("auth",  {"logged_in":False,"username":None,"persona":None,"role":None}),
    ("sub",   {"product_id":"api-list-free","tier":"Free","token":None,"issued_at":None}),
    ("dom_filter", None),
    ("pt_filter",  None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ──────────────────────────────────────────────────────────────────
_TIER_MAP = {"free":"b-free","paid":"b-paid"}
_ACC_MAP  = {"public":"b-pub","partner":"b-part"}
_TYPE_MAP = {"api":"b-api","analytics":"b-analytics","stream":"b-stream",
             "dataset":"b-dataset","report":"b-report","snowflake":"b-snowflake"}
_ICON_MAP = {"api":"🔌","analytics":"📊","stream":"⚡","dataset":"📦",
             "report":"📋","snowflake":"❄️"}

def bc_tier(t): return _TIER_MAP.get((t or "").lower(), "b-ent")
def bc_acc(a):  return _ACC_MAP.get((a or "").lower(), "b-priv")
def bc_type(t): return _TYPE_MAP.get((t or "").lower(), "badge")
def picon(t):   return _ICON_MAP.get((t or "").lower(), "📁")

def money(v):
    if v is None: return "$ Custom"
    try: v=float(v)
    except: return str(v)
    if v<=0: return "Free"
    return f"${int(v):,}" if float(v).is_integer() else f"${v:,.2f}"

def build_url(path): return f"{API_BASE}{path}"

def tier_ok(req, have):
    o={"Free":0,"Paid":1,"Enterprise":2}
    return o.get(have,0) >= o.get(req,0) if have else req=="Free"

def gen_token(u, persona, prod):
    p={"sub":u,"persona":persona,"subscription":{"id":prod.id,"name":prod.name,"tier":prod.tier},
       "iat":int(time.time()),"jti":str(uuid.uuid4())}
    b64=base64.urlsafe_b64encode(json.dumps(p,separators=(",",":")).encode()).decode().rstrip("=")
    sig=base64.urlsafe_b64encode(os.urandom(12)).decode().rstrip("=")
    return f"{b64}.{sig}"

def auth_hdr():
    t=st.session_state.sub.get("token")
    return {"Authorization":f"Bearer {t}"} if t else {}

def curl_cmd(url, params=None, token=None):
    qs=urlencode({k:v for k,v in (params or {}).items() if v not in (None,"")})
    c=f"curl --location '{url}{'?'+qs if qs else ''}'"
    if token: c+=f" \\\n  -H 'Authorization: Bearer {token}'"
    return c

def rbac(rows, role):
    if not rows: return rows
    r=(role or "").lower()
    if "consumer" in r:
        k={"LISTING_ID","CITY","STATE","LIST_PRICE","POSTAL_CODE"}
        return [{k2:v for k2,v in row.items() if k2 in k} for row in rows]
    if "provider" in r or "agent" in r:
        k={"LISTING_ID","CITY","STATE","POSTAL_CODE","LIST_PRICE","BED_COUNT","BATH_COUNT",
           "BUILDING_SQFT","YEAR_BUILT","DATA_SOURCE"}
        return [{k2:v for k2,v in row.items() if k2 in k} for row in rows]
    return rows

def need_requests():
    if requests is None:
        st.error("pip install requests"); st.stop()

def product_card_html(p: Product) -> str:
    price  = money(p.price_monthly)
    period = " / month" if (p.price_monthly and p.price_monthly > 0) else ""
    tags   = "".join([f'<span class="badge">{t}</span>' for t in p.tags[:4]])
    return f"""<div class="mkt-card">
  <div class="mkt-title">{picon(p.product_type)} {p.name}</div>
  <div class="mkt-meta">
    <span class="badge {bc_type(p.product_type)}">{p.product_type.upper()}</span>
    <span class="badge">{p.delivery_tech}</span>
    <span class="badge {bc_acc(p.access)}">{p.access}</span>
    <span class="badge {bc_tier(p.tier)}">{p.tier}</span>
  </div>
  <div class="mkt-desc">{p.description}</div>
  <div class="price">{price}<span class="small">{period}</span></div>
  <div style="margin-top:7px">{tags}</div>
</div>"""

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔐 Login")
    if not st.session_state.auth["logged_in"]:
        st.caption("agent · consumer · developer")
        un = st.text_input("Username", placeholder="agent / consumer / developer")
        pw = st.text_input("Password", type="password", placeholder="e.g., agent123")
        if st.button("Login", type="primary"):
            u = USERS.get((un or "").strip().lower())
            if u and pw == u["password"]:
                st.session_state.auth.update({"logged_in":True,"username":un.strip().lower(),
                    "persona":u["display"],"role":u["role"]})
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        r=st.session_state.auth["role"]
        e={"provider":"📤","consumer":"📥","developer":"🛠️"}.get(r,"👤")
        st.success(f"{e} {st.session_state.auth['persona']}")
        st.caption(f"@{st.session_state.auth['username']}  ·  {r}")
        if st.button("Logout"):
            st.session_state.auth={"logged_in":False,"username":None,"persona":None,"role":None}
            st.session_state.sub["token"]=None
            st.rerun()

    st.divider()
    if st.session_state.sub.get("token"):
        st.header("🔑 Token")
        if prod := CATALOG_BY_ID.get(st.session_state.sub.get("product_id")):
            st.caption(prod.name); st.write(f"Tier: **{st.session_state.sub.get('tier')}**")
        st.code(f"Bearer {st.session_state.sub['token'][:26]}…")
        st.divider()

    st.header("🔍 Filters")
    srch     = st.text_input("Search", placeholder="Search products…")
    dom_sel  = st.multiselect("Domain",       [d["name"] for d in DOMAINS], default=[])
    type_sel = st.multiselect("Product Type", [t["name"] for t in PRODUCT_TYPES], default=[])
    tier_sel = st.multiselect("Tier",         ["Free","Paid","Enterprise"], default=[])
    acc_sel  = st.multiselect("Access",       ["Public","Partner","Private"], default=[])
    st.caption("Leave empty = include all.")

# ─── Filter ───────────────────────────────────────────────────────────────────
_TYPE_NAME_MAP = {t["name"]: t["type"] for t in PRODUCT_TYPES}

def matches(p: Product, external: bool=False) -> bool:
    if external and p.access != "Public": return False
    adom = st.session_state.dom_filter
    apt  = st.session_state.pt_filter
    if srch:
        hay=" ".join([p.name,p.description,p.domain,p.tier,p.product_type,
                      p.delivery_tech," ".join(p.tags)]).lower()
        if srch.strip().lower() not in hay: return False
    if adom and p.domain != adom: return False
    if apt  and p.product_type != apt: return False
    if dom_sel  and p.domain not in dom_sel: return False
    if type_sel and p.product_type not in [_TYPE_NAME_MAP.get(n,n) for n in type_sel]: return False
    if tier_sel and p.tier not in tier_sel: return False
    if acc_sel  and p.access not in acc_sel: return False
    return True

def render_grid(products, external=False):
    fil = [p for p in products if matches(p, external)]
    if not fil:
        st.info("No products match your current filters."); return
    # counts by type
    cnt: Dict[str,int] = {}
    for p in fil: cnt[p.product_type] = cnt.get(p.product_type,0)+1
    summary = "  ".join([f"{picon(t)} **{c}** {t}" for t,c in cnt.items()])
    st.caption(f"**{len(fil)}** product(s)  |  {summary}")
    COLS=3
    for i in range(0, len(fil), COLS):
        chunk = fil[i:i+COLS]
        cols  = st.columns(COLS)
        for col, p in zip(cols, chunk):
            with col:
                st.markdown(product_card_html(p), unsafe_allow_html=True)
                with st.expander("Details"):
                    st.write(f"**Provider:** {p.provider}  ·  **Delivery:** {p.delivery_tech}")
                    for f in p.features: st.write(f"- {f}")
                    if p.endpoints:
                        st.write("**Endpoints:**")
                        for e in p.endpoints: st.code(f"{e['method']} {build_url(e['path'])}")
                    if p.snowflake_share:
                        st.write("**Snowflake (no-copy):**")
                        st.code(f"CREATE DATABASE MOVE_MKT\n  FROM SHARE {p.snowflake_share};\n"
                                f"SELECT * FROM {p.snowflake_view} LIMIT 100;", language="sql")

# ─── Hero (always visible, above the tabs) ────────────────────────────────────
n_products = len(CATALOG)
n_domains  = len(DOMAINS)
n_types    = len(PRODUCT_TYPES)
st.markdown(f"""<div class="hero">
  <div class="hero-ey">MOVE · Data as a Product</div>
  <div class="hero-t">Data Product Marketplace</div>
  <div class="hero-s">Discover, subscribe, and integrate real estate data products —
    APIs, analytics, event streams, datasets, BI reports, and Snowflake native shares.</div>
  <div class="hero-stats">
    <div><div class="hv">{n_products}</div><div class="hl">Data Products</div></div>
    <div><div class="hv">{n_domains}</div><div class="hl">Domains</div></div>
    <div><div class="hv">{n_types}</div><div class="hl">Product Types</div></div>
    <div><div class="hv">2</div><div class="hl">Delivery Mechanisms</div></div>
  </div>
</div>""", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
t_market, t_products, t_demo, t_dev, t_biz, t_provider, t_docs = st.tabs([
    "🏪 Marketplace",
    "📦 All Products",
    "🏠 Listings Demo",
    "🛠️ Developer Tools",
    "📊 Business View",
    "📤 Provider Hub",
    "📄 Documentation",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKETPLACE LANDING
# ══════════════════════════════════════════════════════════════════════════════
with t_market:

    # Product Type tiles
    st.subheader("Browse by Product Type")
    cnt_by_type = {}
    for p in CATALOG: cnt_by_type[p.product_type] = cnt_by_type.get(p.product_type,0)+1

    active_pt = st.session_state.pt_filter
    pt_cols   = st.columns(len(PRODUCT_TYPES))
    for i, pt in enumerate(PRODUCT_TYPES):
        with pt_cols[i]:
            is_on  = active_pt == pt["type"]
            border = "2px solid #0e3059" if is_on else "1.5px solid transparent"
            st.markdown(
                f'<div class="{pt["css"]} pt-card" style="border:{border}">'
                f'<div class="pt-icon">{pt["icon"]}</div>'
                f'<div class="pt-name">{pt["name"]}</div>'
                f'<div class="pt-count">{cnt_by_type.get(pt["type"],0)} products</div>'
                f'<div class="pt-desc">{pt["desc"]}</div></div>',
                unsafe_allow_html=True)
            label = "✓ Active" if is_on else "Filter"
            if st.button(label, key=f"pt_{pt['type']}", use_container_width=True):
                st.session_state.pt_filter = None if is_on else pt["type"]
                st.rerun()

    # Domain tiles
    st.subheader("Browse by Domain")
    active_dom = st.session_state.dom_filter
    dom_cols   = st.columns(len(DOMAINS))
    for i, dom in enumerate(DOMAINS):
        with dom_cols[i]:
            is_on  = active_dom == dom["name"]
            border = "2px solid #0e3059" if is_on else "1px solid rgba(49,51,63,.12)"
            bg     = "rgba(14,48,89,.07)" if is_on else "linear-gradient(145deg,#fff,#f5f7fb)"
            st.markdown(
                f'<div class="dom-tile" style="border:{border};background:{bg}">'
                f'<div class="dt-icon">{dom["icon"]}</div>'
                f'<div class="dt-name">{dom["name"]}</div>'
                f'<div class="dt-desc">{dom["desc"]}</div></div>',
                unsafe_allow_html=True)
            label = "✓ Active" if is_on else "Filter"
            if st.button(label, key=f"dom_{dom['name']}", use_container_width=True):
                st.session_state.dom_filter = None if is_on else dom["name"]
                st.rerun()

    # Internal / External
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    mkt_view   = st.radio("Marketplace View",
        ["🏢 Internal Marketplace","🌐 External (Snowflake Marketplace)"],
        horizontal=True)
    is_ext = "External" in mkt_view
    st.caption("Public products only — Snowflake Marketplace view." if is_ext
               else "All products — internal view for authenticated MOVE teams.")

    # Featured products
    featured_ids = [
        "api-list-free",     # Listings REST — Free tier (entry point)
        "sf-list",           # Listings Snowflake no-copy (flagship)
        "stream-list",       # Listings Kafka stream
        "analytics-market",  # Market Trends Dashboard
        "analytics-cj",      # Consumer Behavior Dashboard
        "report-list",       # Listing Price Index (Tableau)
        "api-market-forecast",# ML forecast API
        "analytics-agent",   # Agent leaderboard
        "sf-txn",            # Closed Deals Snowflake share
        "stream-ads",        # Ad Impression Kinesis
        "dataset-list",      # Master Listing Dataset
        "api-leads",         # Leads Engine API
    ]
    featured     = [p for p in CATALOG if p.id in featured_ids]
    dom_lbl = f" · {active_dom}" if active_dom else ""
    pt_lbl  = f" · {active_pt.capitalize()}" if active_pt else ""
    st.subheader(f"Featured Products{dom_lbl}{pt_lbl}")
    render_grid(featured, is_ext)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ALL PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
with t_products:
    st.subheader("All Data Products")
    st.caption("Use the sidebar filters to narrow by domain, type, tier, or access level.")
    render_grid(CATALOG)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LISTINGS DEMO
# ══════════════════════════════════════════════════════════════════════════════
with t_demo:
    st.subheader("🏠 Listings — Product Demo")
    st.caption("This tab demonstrates the two delivery paths for MOVE's Listings data products.")

    list_prods = [p for p in CATALOG if p.domain == "Listings"]
    cnt_by_type2: Dict[str,int] = {}
    for p in list_prods: cnt_by_type2[p.product_type]=cnt_by_type2.get(p.product_type,0)+1
    st.markdown(
        "**" + str(len(list_prods)) + " Listings Products:** " +
        "  ".join([f"{picon(t)} {c} {t}" for t,c in cnt_by_type2.items()]),
        unsafe_allow_html=False)

    # Two paths overview
    st.markdown("""<div class="ap-grid">
  <div class="ap-card ap-rest">
    <div class="ap-icon">🌐</div>
    <div class="ap-title">REST API</div>
    <div class="ap-sub">For non-Snowflake consumers</div>
    <div class="ap-row">✓ Bearer token authentication</div>
    <div class="ap-row">✓ 3 live endpoints on AWS API Gateway</div>
    <div class="ap-row">✓ Free / Paid / Enterprise tiers</div>
    <div class="ap-row">✓ Works with any HTTP client or language</div>
    <div class="ap-code">GET /v1/listings<br>GET /v1/listings/{id}<br>GET /v1/listings/export</div>
    <div><span class="ap-tag ap-tag-rest">🌐 REST / HTTP</span></div>
  </div>
  <div class="ap-card ap-sf">
    <div class="ap-icon">❄️</div>
    <div class="ap-title">Snowflake Native (No-Copy)</div>
    <div class="ap-sub">For Snowflake customers</div>
    <div class="ap-row">✓ Private Listing — data never leaves MOVE's Snowflake</div>
    <div class="ap-row">✓ Consumer queries a Secure View in their own account</div>
    <div class="ap-row">✓ Column & row-level security enforced by Snowflake</div>
    <div class="ap-row">✓ Zero ETL, zero duplication, always live</div>
    <div class="ap-code">CREATE DATABASE MOVE_MKT<br>&nbsp;&nbsp;FROM SHARE BRILLIO_MOVE_LISTINGS_V1;<br>SELECT * FROM MOVE_MKT.LISTINGS.ACTIVE_LISTINGS_VW;</div>
    <div><span class="ap-tag ap-tag-sf">❄️ Snowflake No-Copy</span></div>
  </div>
</div>""", unsafe_allow_html=True)

    st.divider()

    demo_rest, demo_sf, demo_others = st.tabs(
        ["🌐 REST API Demo", "❄️ Snowflake Demo", "📦 Other Listings Products"])

    # ── REST demo ─────────────────────────────────────────────────────────────
    with demo_rest:
        st.subheader("Listings REST API — Live Demo")

        # Step 1: subscribe / token
        st.markdown('<div class="demo-step"><div class="demo-step-label">Step 1</div>'
                    '<div class="demo-step-text">Subscribe and generate a Bearer token</div></div>',
                    unsafe_allow_html=True)

        rest_prods = [p for p in CATALOG if p.domain=="Listings" and p.product_type=="api"]
        opts = {p.name: p.id for p in rest_prods}
        cur  = st.session_state.sub["product_id"]
        if cur not in {p.id for p in rest_prods}: cur = rest_prods[0].id
        default_name = CATALOG_BY_ID.get(cur, rest_prods[0]).name

        sel_name = st.selectbox("Choose a Listings API tier",list(opts.keys()),
                                index=list(opts.keys()).index(default_name) if default_name in opts else 0)
        sel = CATALOG_BY_ID[opts[sel_name]]

        c1,c2,c3 = st.columns(3)
        c1.metric("Tier", sel.tier); c2.metric("Price", money(sel.price_monthly)+"/mo" if sel.price_monthly else "Free")
        c3.metric("Endpoints", len(sel.endpoints))

        tier_map = {"Free":["✅ List","❌ Detail","❌ Export"],
                    "Paid":["✅ List","✅ Detail","❌ Export"],
                    "Enterprise":["✅ List","✅ Detail","✅ Export"]}
        st.write("**Access:**  " + "  ".join(tier_map.get(sel.tier,[])))

        if st.button("🔑 Generate Bearer Token", type="primary", key="demo_tok"):
            if not st.session_state.auth["logged_in"]:
                st.warning("Login first (consumer / consumer123)")
            else:
                tok = gen_token(st.session_state.auth["username"],
                                st.session_state.auth["persona"], sel)
                st.session_state.sub.update({"product_id":sel.id,"tier":sel.tier,
                    "token":tok,"issued_at":time.strftime("%Y-%m-%d %H:%M:%S")})
                st.success("Token generated — ready to call the API.")

        if st.session_state.sub.get("token"):
            st.code(f"Bearer {st.session_state.sub['token']}")

        st.divider()

        # Step 2: call API
        st.markdown('<div class="demo-step"><div class="demo-step-label">Step 2</div>'
                    '<div class="demo-step-text">Call a live endpoint</div></div>',
                    unsafe_allow_html=True)
        need_requests()
        token_tier = st.session_state.sub.get("tier") if st.session_state.sub.get("token") else None

        EP_DEMO = {
            "GET /v1/listings — List active listings": {
                "path":f"{API_PREFIX}/listings",
                "params":[("limit","10"),("offset","0"),("status","ACTIVE")],
                "min_tier":"Free"},
            "GET /v1/listings/{id} — Listing detail": {
                "path":f"{API_PREFIX}/listings/{{listing_id}}",
                "params":[("listing_id","c03a9346f9")],
                "min_tier":"Paid"},
            "GET /v1/listings/export — Bulk CSV to S3": {
                "path":f"{API_PREFIX}/listings/export",
                "params":[("limit","100"),("status","ACTIVE"),("state",""),("city","")],
                "min_tier":"Enterprise"},
        }
        ep_choice = st.selectbox("Endpoint", list(EP_DEMO.keys()))
        ep = EP_DEMO[ep_choice]
        allowed = tier_ok(ep["min_tier"], token_tier)

        col_r, col_t = st.columns(2)
        col_r.write(f"**Required:** `{ep['min_tier']}`")
        col_t.write(f"**Your tier:** `{token_tier or '— no token'}`")

        params: Dict[str,str] = {}
        pc = st.columns(2)
        for i,(k,dv) in enumerate(ep["params"]):
            with pc[i%2]: params[k]=st.text_input(k,value=dv,key=f"dp_{k}_{i}")

        path = ep["path"]
        if "{listing_id}" in path:
            path = path.replace("{listing_id}", params.pop("listing_id","").strip())
        url = build_url(path)
        st.code(curl_cmd(url, params, st.session_state.sub.get("token")), language="bash")

        bc, _ = st.columns([.22,.78])
        with bc:
            run = st.button("▶ Run", type="primary", disabled=not allowed, key="demo_run")
            raw = st.checkbox("Raw JSON", key="demo_raw")
        if not allowed:
            st.info(f"Subscribe to **{ep['min_tier']}** tier above to unlock this endpoint.")

        if run:
            try:
                resp = requests.get(url, params={k:v for k,v in params.items() if v},
                                    headers=auth_hdr(), timeout=30)
                st.write(f"**Status:** {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data,dict) and data.get("success"):
                    payload = data.get("data")
                    if isinstance(payload,list):
                        trimmed = rbac(payload, st.session_state.auth.get("role"))
                        st.dataframe(pd.DataFrame(trimmed),use_container_width=True) if pd else st.json(trimmed)
                        if "pagination" in data: st.json(data["pagination"])
                    elif isinstance(payload,dict):
                        if "LISTING_ID" in payload:
                            t2 = rbac([payload], st.session_state.auth.get("role"))
                            st.json(t2[0] if t2 else payload)
                        else:
                            st.json(payload)
                        dl = payload.get("download")
                        if isinstance(dl,dict) and dl.get("presigned_url"):
                            st.success("Export ready")
                            st.markdown(f"[Download CSV]({dl['presigned_url']})")
                else:
                    st.json(data)
                if raw: st.code(json.dumps(data,indent=2),language="json")
            except Exception as e:
                st.error(f"Request failed: {e}")

    # ── Snowflake demo ────────────────────────────────────────────────────────
    with demo_sf:

        # ── Marketplace listing card ──────────────────────────────────────────
        st.markdown("""<div class="sf-listing-card">
  <div class="sf-listing-eyebrow">❄️ Snowflake Marketplace · Private Listing</div>
  <div class="sf-listing-title">POC_BRILLIO_MOVE_LISTINGS</div>
  <div class="sf-listing-sub">Real Estate Listings Data Product — Premium Property Intelligence</div>
  <div class="sf-listing-tags">
    <span class="sf-tag">Zero-Copy Data Sharing</span>
    <span class="sf-tag">SQL-Native Access</span>
    <span class="sf-tag">Daily Refresh</span>
    <span class="sf-tag">All US States</span>
    <span class="sf-tag sf-tag-installed">✓ Installed</span>
  </div>
  <div class="sf-listing-meta">
    <div><div class="sf-meta-val">MJODLCP.BRILLIO_PARTNER</div><div class="sf-meta-item">Provider account</div></div>
    <div><div class="sf-meta-val">DATA.V_LISTINGS_GOLD</div><div class="sf-meta-item">Primary view</div></div>
    <div><div class="sf-meta-val">Private</div><div class="sf-meta-item">Access type</div></div>
    <div><div class="sf-meta-val">Daily</div><div class="sf-meta-item">Data freshness</div></div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Sub-tabs ──────────────────────────────────────────────────────────
        sf_overview, sf_dict, sf_sql, sf_register = st.tabs([
            "📋 Overview", "📊 Data Dictionary", "🚀 Quick Start", "🔐 Get Access"])

        # ── Overview ──────────────────────────────────────────────────────────
        with sf_overview:
            col_l, col_r = st.columns([3, 2])
            with col_l:
                st.markdown("""
Access comprehensive real estate listings data directly in your Snowflake account with
**zero data movement**. MOVE's Data Product provides curated property information including
pricing, property features, location data, and market status flags to power your real estate
analytics, market research, and business intelligence workflows.

**Key Features**
- ❄️ Zero-copy data sharing — no data egress costs, real-time access
- 🏠 Property details: beds, baths, square footage, and location
- 📈 Market intelligence flags — foreclosures, new construction, pending sales
- 💰 Pricing information with historical price-change tracking
- 🔗 Multi-source aggregation for comprehensive market coverage
- 🛠️ SQL-native access via secure views and stored procedures
""")
            with col_r:
                st.markdown("**Data Coverage**")
                st.markdown("""
| Attribute | Value |
|---|---|
| Property Types | Residential, Commercial, Rental |
| Geographic Coverage | United States (all states) |
| Data Freshness | Daily (multi-MLS + public sources) |
| Historical Data | Price change + status history |
| Primary View | `DATA.V_LISTINGS_GOLD` |
| Provider Account | `MJODLCP.BRILLIO_PARTNER` |
""")
                st.markdown("**Ideal For**")
                for who in [
                    "Real estate market analysts & researchers",
                    "Property investment firms & REITs",
                    "Mortgage lenders & financial institutions",
                    "PropTech companies & applications",
                    "Data science teams building pricing models",
                ]:
                    st.write(f"✓ {who}")

            st.divider()
            st.subheader("Business Need: Market Analysis")
            st.caption("Power real estate market analysis with comprehensive property data across "
                       "locations, price points, and property types to identify trends and generate "
                       "investment insights.")

        # ── Data Dictionary ────────────────────────────────────────────────────
        with sf_dict:
            st.subheader("V_LISTINGS_GOLD — Column Reference")
            st.caption("Columns marked 🔒 are secured (column-level security) — visibility depends on your role.")

            DD = [
                ("LISTING_ID",                "VARCHAR",       False, False, "Unique listing identifier"),
                ("PROPERTY_ID",               "VARCHAR",       False, False, "Unique property identifier"),
                ("LISTING_STATUS",            "VARCHAR",       False, False, "ACTIVE · PENDING · SOLD · WITHDRAWN"),
                ("PHOTO_COUNT",               "NUMBER",        False, False, "Number of photos attached to listing"),
                ("PRIMARY_PHOTO_URL",         "VARCHAR",       False, False, "URL of the primary listing photo"),
                ("RDC_LISTING_URL",           "VARCHAR",       False, False, "Realtor.com canonical listing URL"),
                ("LISTING_START_DATE",        "DATE",          False, False, "Date listing was first published"),
                ("LISTING_END_DATE",          "DATE",          False, False, "Date listing was closed or expired"),
                ("LAST_STATUS_CHANGE_DATE",   "DATE",          False, False, "Most recent status transition date"),
                ("LIST_PRICE",                "NUMBER",        False, False, "Current listed price in USD"),
                ("LAST_PRICE_CHANGE_AMOUNT",  "NUMBER",        False, False, "Amount of most recent price change (+ / -)"),
                ("PRICE_PER_SQFT",            "NUMBER",        False, False, "Calculated list price per square foot"),
                ("BED_COUNT",                 "NUMBER",        True,  False, "Number of bedrooms"),
                ("BATH_COUNT",                "NUMBER",        True,  False, "Number of bathrooms"),
                ("BUILDING_SQFT",             "NUMBER",        True,  False, "Total interior square footage"),
                ("LOT_SQFT",                  "NUMBER",        False, False, "Lot size in square feet"),
                ("YEAR_BUILT",                "NUMBER",        False, False, "Year the property was built"),
                ("STORIES",                   "NUMBER",        False, False, "Number of floors/stories"),
                ("CITY",                      "VARCHAR",       False, False, "City name"),
                ("STATE",                     "VARCHAR",       False, False, "2-letter state abbreviation"),
                ("POSTAL_CODE",               "NUMBER",        False, False, "ZIP / postal code"),
                ("LATITUDE",                  "NUMBER",        False, False, "Geographic latitude (WGS84)"),
                ("LONGITUDE",                 "NUMBER",        False, False, "Geographic longitude (WGS84)"),
                ("FLAG_IS_FOR_RENT",          "BOOLEAN",       False, True,  "True if rental listing"),
                ("FLAG_IS_NEW_CONSTRUCTION",  "BOOLEAN",       False, True,  "True if newly built property"),
                ("FLAG_IS_PENDING",           "BOOLEAN",       False, True,  "True if sale is pending / under contract"),
                ("FLAG_IS_FORECLOSURE",       "BOOLEAN",       False, True,  "True if foreclosure / REO listing"),
                ("DATA_SOURCE",               "VARCHAR",       True,  False, "Source system identifier"),
                ("RECORD_SOURCE",             "VARCHAR",       False, False, "Originating feed (e.g., rdc)"),
                ("SNAPSHOT_DATE",             "DATE",          False, False, "Date of the snapshot batch"),
                ("LAST_UPDATED_TS",           "TIMESTAMP_NTZ", False, False, "Exact timestamp of last record update"),
            ]
            rows = ""
            for col, dtype, secured, flag, desc in DD:
                sec_badge   = '<span class="dd-secured">🔒 secured</span>' if secured else ""
                flag_marker = ' <span class="dd-flag">⚑ flag</span>' if flag else ""
                rows += (f'<tr><td><strong>{col}</strong>{flag_marker}</td>'
                         f'<td><span class="dd-type">{dtype}</span></td>'
                         f'<td>{sec_badge}</td>'
                         f'<td style="color:rgba(49,51,63,.75)">{desc}</td></tr>')
            st.markdown(
                f'<table class="dd-table"><thead><tr>'
                f'<th>Column</th><th>Type</th><th>Security</th><th>Description</th>'
                f'</tr></thead><tbody>{rows}</tbody></table>',
                unsafe_allow_html=True)
            st.caption("🔒 Secured columns are masked based on the Snowflake role assigned when access was granted. "
                       "Contact MOVE to upgrade your role.")

        # ── Quick Start SQL ────────────────────────────────────────────────────
        with sf_sql:
            st.subheader("Quick Start SQL Examples")
            st.caption("Copy-paste into Snowflake Worksheets after installing the private listing.")

            st.markdown('<div class="demo-step"><div class="demo-step-label">Step 1 — One-time setup</div>'
                        '<div class="demo-step-text">Install the listing and mount the database</div></div>',
                        unsafe_allow_html=True)
            st.code("""-- 1. Accept POC_BRILLIO_MOVE_LISTINGS in Snowflake Marketplace UI
--    (provider: MJODLCP.BRILLIO_PARTNER)

-- 2. Mount the share as a local database
CREATE DATABASE MOVE_MKT
  FROM SHARE MJODLCP.BRILLIO_PARTNER.POC_BRILLIO_MOVE_LISTINGS;

-- 3. Grant access to your analysts
GRANT IMPORTED PRIVILEGES ON DATABASE MOVE_MKT
  TO ROLE ANALYST;""", language="sql")

            st.markdown('<div class="demo-step" style="margin-top:10px"><div class="demo-step-label">Step 2 — Start querying</div>'
                        '<div class="demo-step-text">Query DATA.V_LISTINGS_GOLD directly</div></div>',
                        unsafe_allow_html=True)

            q1, q2 = st.columns(2)
            with q1:
                st.write("**Active listings by state & price range**")
                st.code("""SELECT
  CITY,
  BED_COUNT,
  BATH_COUNT,
  BUILDING_SQFT,
  LIST_PRICE,
  LAST_PRICE_CHANGE_AMOUNT,
  FLAG_IS_NEW_CONSTRUCTION,
  FLAG_IS_FORECLOSURE
FROM MOVE_MKT.DATA.V_LISTINGS_GOLD
WHERE STATE = 'TX'
  AND LIST_PRICE BETWEEN 500000 AND 1000000
  AND FLAG_IS_PENDING = FALSE
ORDER BY LAST_PRICE_CHANGE_AMOUNT DESC
LIMIT 100;""", language="sql")

                st.write("**Market summary by metro**")
                st.code("""SELECT
  CITY,
  STATE,
  COUNT(*)                       AS TOTAL_LISTINGS,
  ROUND(AVG(LIST_PRICE), 0)      AS AVG_LIST_PRICE,
  ROUND(AVG(PRICE_PER_SQFT), 0)  AS AVG_PRICE_SQFT,
  SUM(CASE WHEN FLAG_IS_PENDING
       THEN 1 ELSE 0 END)        AS PENDING_COUNT
FROM MOVE_MKT.DATA.V_LISTINGS_GOLD
WHERE LISTING_STATUS = 'ACTIVE'
GROUP BY CITY, STATE
ORDER BY TOTAL_LISTINGS DESC
LIMIT 25;""", language="sql")

            with q2:
                st.write("**New construction opportunities**")
                st.code("""SELECT
  CITY, STATE, POSTAL_CODE,
  LIST_PRICE,
  BED_COUNT, BATH_COUNT,
  BUILDING_SQFT,
  LISTING_START_DATE
FROM MOVE_MKT.DATA.V_LISTINGS_GOLD
WHERE FLAG_IS_NEW_CONSTRUCTION = TRUE
  AND LISTING_STATUS = 'ACTIVE'
  AND LIST_PRICE < 750000
ORDER BY LISTING_START_DATE DESC
LIMIT 50;""", language="sql")

                st.write("**Foreclosure & distressed properties**")
                st.code("""SELECT
  CITY, STATE, POSTAL_CODE,
  LIST_PRICE,
  LAST_PRICE_CHANGE_AMOUNT,
  LATITUDE, LONGITUDE
FROM MOVE_MKT.DATA.V_LISTINGS_GOLD
WHERE FLAG_IS_FORECLOSURE = TRUE
  AND LISTING_STATUS = 'ACTIVE'
ORDER BY LIST_PRICE ASC
LIMIT 100;""", language="sql")

            st.write("**Price trend analysis (with history)**")
            st.code("""SELECT
  LISTING_ID,
  CITY, STATE,
  LIST_PRICE,
  LAST_PRICE_CHANGE_AMOUNT,
  ROUND(LAST_PRICE_CHANGE_AMOUNT / NULLIF(LIST_PRICE,0) * 100, 2)
    AS PCT_PRICE_CHANGE,
  LAST_STATUS_CHANGE_DATE,
  SNAPSHOT_DATE
FROM MOVE_MKT.DATA.V_LISTINGS_GOLD
WHERE LAST_PRICE_CHANGE_AMOUNT IS NOT NULL
  AND LISTING_STATUS IN ('ACTIVE', 'PENDING')
ORDER BY ABS(LAST_PRICE_CHANGE_AMOUNT) DESC
LIMIT 200;""", language="sql")

            st.info("**No-copy guarantee:** Every SELECT executes inside MOVE's Snowflake account. "
                    "Results stream to your session — no data is persisted in your storage. "
                    "Column-level security on BED_COUNT, BATH_COUNT, BUILDING_SQFT, and DATA_SOURCE "
                    "is enforced natively by Snowflake based on your assigned role.")

        # ── Get Access (Registration) ─────────────────────────────────────────
        with sf_register:
            st.subheader("Request Access to POC_BRILLIO_MOVE_LISTINGS")
            st.caption("Fill in your Snowflake account details. MOVE will grant the private listing "
                       "directly to your account — no enrollment, no complex setup.")

            st.markdown('<div class="reg-card">', unsafe_allow_html=True)
            with st.form("sf_register_form"):
                st.write("**Organisation & Contact**")
                rc1, rc2 = st.columns(2)
                with rc1:
                    reg_company = st.text_input("Company / Organisation name *",
                                                placeholder="e.g., Acme Analytics Inc.")
                    reg_email   = st.text_input("Business email *",
                                                placeholder="you@company.com")
                with rc2:
                    reg_name    = st.text_input("Full name *", placeholder="Jane Smith")
                    reg_role    = st.selectbox("Your role",
                        ["Data Analyst", "Data Engineer", "Data Scientist",
                         "Business Intelligence", "Product Manager", "Other"])

                st.write("**Snowflake Account Details**")
                sa1, sa2 = st.columns(2)
                with sa1:
                    reg_account = st.text_input("Snowflake Account Identifier *",
                        placeholder="e.g., xy12345.us-east-1",
                        help="Found in Admin → Accounts in your Snowflake UI, or run: SELECT CURRENT_ACCOUNT()")
                    reg_org     = st.text_input("Snowflake Organisation ID",
                        placeholder="e.g., MYORG",
                        help="Run SELECT CURRENT_ORGANIZATION_NAME() in Snowflake")
                with sa2:
                    reg_region  = st.selectbox("Snowflake Cloud Region",
                        ["AWS us-east-1", "AWS us-east-2", "AWS us-west-2",
                         "AWS eu-west-1", "Azure eastus2", "Azure westeurope",
                         "GCP us-central1", "Other"])
                    reg_edition = st.selectbox("Snowflake Edition",
                        ["Enterprise", "Business Critical", "Standard", "Not sure"])

                st.write("**Access Details**")
                reg_use   = st.text_area("Describe your use case *",
                    placeholder="e.g., Building a property valuation model; analysing inventory trends in Southeast markets…",
                    height=90)
                reg_role_sf = st.text_input("Snowflake role to grant access to",
                    placeholder="e.g., ANALYST, DATA_TEAM, SYSADMIN",
                    help="The role in your Snowflake account that should receive IMPORTED PRIVILEGES on the share.")
                reg_tier  = st.selectbox("Access tier requested",
                    ["Standard (Consumer role — public fields)",
                     "Partner (Agent role — enriched fields)",
                     "Enterprise (Developer role — full payload)"])

                st.caption("* Required fields. Brillio / MOVE will review your request and "
                           "grant the private listing to your Snowflake account within 1 business day.")

                submitted = st.form_submit_button("🚀 Submit Access Request", type="primary")
            st.markdown('</div>', unsafe_allow_html=True)

            if submitted:
                missing = [f for f, v in [
                    ("Company name", reg_company), ("Email", reg_email),
                    ("Full name", reg_name), ("Account identifier", reg_account),
                    ("Use case", reg_use)] if not (v or "").strip()]
                if missing:
                    st.error(f"Please fill in: {', '.join(missing)}")
                else:
                    st.success(f"✅ Access request submitted for **{reg_company}**!")
                    st.info(
                        f"MOVE will grant `POC_BRILLIO_MOVE_LISTINGS` to Snowflake account "
                        f"`{reg_account.strip()}` within 1 business day. "
                        f"Once granted, run:\n\n"
                        f"```sql\nCREATE DATABASE MOVE_MKT\n"
                        f"  FROM SHARE MJODLCP.BRILLIO_PARTNER.POC_BRILLIO_MOVE_LISTINGS;\n\n"
                        f"GRANT IMPORTED PRIVILEGES ON DATABASE MOVE_MKT\n"
                        f"  TO ROLE {(reg_role_sf or 'ANALYST').upper().strip()};\n```"
                    )
                    st.balloons()

    # ── Other Listings products ───────────────────────────────────────────────
    with demo_others:
        st.subheader("Other Listings Data Products")
        st.caption("Beyond REST API and Snowflake — stream, bulk dataset, and BI report.")
        others = [p for p in CATALOG if p.domain=="Listings" and p.id not in
                  {"api-list-free","api-list-std","api-list-ent","sf-list"}]
        render_grid(others)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DEVELOPER TOOLS
# ══════════════════════════════════════════════════════════════════════════════
with t_dev:
    st.subheader("🛠️ Developer Tools")
    if not st.session_state.auth["logged_in"]:
        st.warning("Login as `developer` / `dev123` for full technical access.")

    dev_rest, dev_sf = st.tabs(["🌐 REST API Explorer", "❄️ Snowflake SQL Explorer"])

    with dev_rest:
        need_requests()
        st.subheader("REST API Explorer")
        st.caption("Live calls to AWS API Gateway. Requires a Bearer token from the Listings Demo tab.")
        token_tier = st.session_state.sub.get("tier") if st.session_state.sub.get("token") else None

        ENDPOINTS = {
            "List listings":          {"path":f"{API_PREFIX}/listings",
                                       "params":[("limit","10"),("offset","0"),("status","ACTIVE")],"min_tier":"Free"},
            "Get listing by id":      {"path":f"{API_PREFIX}/listings/{{listing_id}}",
                                       "params":[("listing_id","c03a9346f9")],"min_tier":"Paid"},
            "Export (CSV → S3)":      {"path":f"{API_PREFIX}/listings/export",
                                       "params":[("limit","100"),("status","ACTIVE"),("state",""),
                                                 ("city",""),("postal_code",""),("min_price",""),
                                                 ("max_price",""),("min_beds",""),("max_beds","")],
                                       "min_tier":"Enterprise"},
        }
        choice  = st.selectbox("Endpoint", list(ENDPOINTS.keys()))
        ep      = ENDPOINTS[choice]
        allowed = tier_ok(ep["min_tier"], token_tier)
        r1,r2   = st.columns(2)
        r1.write(f"**Required:** `{ep['min_tier']}`")
        r2.write(f"**Your tier:** `{token_tier or '— no token'}`")

        params: Dict[str,str] = {}
        pc=st.columns(2)
        for i,(k,dv) in enumerate(ep["params"]):
            with pc[i%2]: params[k]=st.text_input(k,value=dv,key=f"dev_{k}_{i}")
        path=ep["path"]
        if "{listing_id}" in path: path=path.replace("{listing_id}",params.pop("listing_id","").strip())
        url=build_url(path)
        st.code(curl_cmd(url,params,st.session_state.sub.get("token")),language="bash")
        bc,_=st.columns([.22,.78])
        with bc:
            run=st.button("▶ Run",type="primary",disabled=not allowed,key="dev_run")
            raw=st.checkbox("Raw JSON",key="dev_raw")
        if not allowed: st.info(f"Need **{ep['min_tier']}** token from Listings Demo tab.")
        if run:
            try:
                resp=requests.get(url,params={k:v for k,v in params.items() if v},
                                  headers=auth_hdr(),timeout=30)
                st.write(f"**Status:** {resp.status_code}"); resp.raise_for_status()
                data=resp.json()
                if isinstance(data,dict) and data.get("success"):
                    payload=data.get("data")
                    if isinstance(payload,list):
                        t2=rbac(payload,st.session_state.auth.get("role"))
                        st.dataframe(pd.DataFrame(t2),use_container_width=True) if pd else st.json(t2)
                    elif isinstance(payload,dict):
                        t2=rbac([payload],st.session_state.auth.get("role")) if "LISTING_ID" in payload else [payload]
                        st.json(t2[0] if t2 else payload)
                        dl=payload.get("download")
                        if isinstance(dl,dict) and dl.get("presigned_url"):
                            st.success("Export ready"); st.markdown(f"[Download CSV]({dl['presigned_url']})")
                else: st.json(data)
                if raw: st.code(json.dumps(data,indent=2),language="json")
            except Exception as e: st.error(f"Request failed: {e}")
        with st.expander("Token Decoder"):
            tok=st.session_state.sub.get("token")
            if not tok: st.info("Generate a token in Listings Demo first.")
            else:
                try:
                    part=tok.split(".")[0]
                    st.json(json.loads(base64.urlsafe_b64decode(part+"="*(-len(part)%4)).decode()))
                except: st.write("Unable to decode.")

    with dev_sf:
        st.subheader("Snowflake SQL Explorer")
        sf_prods=[p for p in CATALOG if p.snowflake_share]
        chosen=st.selectbox("Product",[p.name for p in sf_prods])
        sfp=next(p for p in sf_prods if p.name==chosen)
        st.write(f"**Share:** `{sfp.snowflake_share}`  ·  **View:** `{sfp.snowflake_view}`")
        c1,c2=st.columns(2)
        with c1:
            st.write("**Mount share (one-time)**")
            st.code(f"CREATE DATABASE MOVE_MKT\n  FROM SHARE {sfp.snowflake_share};\n"
                    f"GRANT IMPORTED PRIVILEGES ON DATABASE MOVE_MKT TO ROLE ANALYST;",language="sql")
        with c2:
            st.write("**Query secure view**")
            st.code(f"SELECT *\nFROM {sfp.snowflake_view}\nWHERE STATUS = 'ACTIVE'\nLIMIT 100;",language="sql")
        st.write("**Aggregation example**")
        st.code(f"SELECT CITY, STATE,\n  ROUND(AVG(LIST_PRICE),0) AS AVG_PRICE,\n"
                f"  COUNT(*) AS LISTINGS\nFROM {sfp.snowflake_view}\nGROUP BY CITY, STATE\n"
                f"ORDER BY LISTINGS DESC LIMIT 20;",language="sql")
        st.info("Data runs in MOVE's Snowflake. Zero copy — nothing persists in the consumer's account.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BUSINESS VIEW (non-technical)
# ══════════════════════════════════════════════════════════════════════════════
with t_biz:
    st.subheader("📊 Business View")
    st.caption("Discover data products and request access — no technical setup required.")

    if not st.session_state.auth["logged_in"]:
        st.warning("Login as `consumer` / `consumer123` to explore the business view.")
    else:
        st.write(f"Welcome, **{st.session_state.auth['persona']}**.")

    st.divider()

    biz_tabs = st.tabs(["📊 Dashboards & Analytics", "📋 BI Reports", "📦 Datasets & Feeds",
                        "🛒 My Subscriptions"])

    with biz_tabs[0]:
        st.subheader("Dashboards & Analytics")
        st.caption("Embedded visualisations — no code, just insights.")
        dash_prods=[p for p in CATALOG if p.product_type=="analytics"]
        BG={"Listings":"#1554a0","Consumer Journey":"#1a7a44","Market Intelligence":"#6a1b9a",
            "Ads":"#e65100","Agent":"#0f3460"}
        cols=st.columns(3)
        for i,p in enumerate(dash_prods):
            with cols[i%3]:
                color=BG.get(p.domain,"#0e3059")
                st.markdown(
                    f'<div class="biz-card">'
                    f'<div class="biz-thumb" style="background:linear-gradient(135deg,{color}ee,{color}88)">'
                    f'{picon(p.product_type)}</div>'
                    f'<strong>{p.name}</strong><br>'
                    f'<span style="font-size:.82rem;color:rgba(49,51,63,.65)">{p.domain}</span><br>'
                    f'<span style="font-size:.78rem;margin-top:4px;display:block">{p.description[:90]}…</span>'
                    f'</div>', unsafe_allow_html=True)
                st.markdown(f"**{money(p.price_monthly)}/mo** · {p.tier}")
                if st.button("Request Access", key=f"biz_dash_{p.id}", use_container_width=True):
                    st.success(f"Access request submitted for **{p.name}**. Your team will be notified.")

    with biz_tabs[1]:
        st.subheader("BI Reports")
        st.caption("Pre-built reports in Tableau, Looker, and Power BI.")
        rpt_prods=[p for p in CATALOG if p.product_type=="report"]
        for p in rpt_prods:
            with st.expander(f"📋 {p.name}  ·  {p.delivery_tech}  ·  {money(p.price_monthly)}/mo"):
                st.write(p.description)
                st.write("**What's included:**")
                for f in p.features: st.write(f"- {f}")
                if st.button("Request Access", key=f"biz_rpt_{p.id}"):
                    st.success(f"Request submitted for **{p.name}**.")

    with biz_tabs[2]:
        st.subheader("Datasets & Event Streams")
        st.caption("Bulk datasets (S3/Snowflake) and real-time event streams for data teams.")
        bulk_prods=[p for p in CATALOG if p.product_type in ("dataset","stream","snowflake")]
        for p in bulk_prods:
            with st.expander(f"{picon(p.product_type)} {p.name}  ·  {p.delivery_tech}  ·  {money(p.price_monthly)}/mo"):
                st.write(p.description)
                for f in p.features: st.write(f"- {f}")
                if p.snowflake_share:
                    st.write(f"**Share:** `{p.snowflake_share}`")
                if st.button("Request Access", key=f"biz_bulk_{p.id}"):
                    st.success(f"Request submitted for **{p.name}**.")

    with biz_tabs[3]:
        st.subheader("My Subscriptions")
        tok=st.session_state.sub.get("token")
        if tok and (prod:=CATALOG_BY_ID.get(st.session_state.sub.get("product_id"))):
            st.success(f"Active: **{prod.name}**  ·  {prod.tier}  ·  {money(prod.price_monthly)}/mo")
            st.write(f"Token issued: {st.session_state.sub.get('issued_at')}")
            if prod.product_type=="api":
                st.info("Use **Developer Tools → REST API Explorer** to call this API with your token.")
            elif prod.product_type=="snowflake":
                st.info("Use **Developer Tools → Snowflake SQL Explorer** to query the secure view.")
        else:
            st.info("No active subscriptions. Go to **Listings Demo → REST API Demo** to subscribe.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — PROVIDER HUB
# ══════════════════════════════════════════════════════════════════════════════
with t_provider:
    st.subheader("📤 Provider Hub")
    st.caption("Publish and manage your data products on the marketplace.")

    if not st.session_state.auth["logged_in"]:
        st.warning("Login as `agent` / `agent123` to access the Provider Hub.")
    elif st.session_state.auth.get("role") != "provider":
        st.info(f"Provider Hub is for Real Estate Agent persona. You are logged in as **{st.session_state.auth['persona']}**.")
    else:
        st.success(f"Welcome, **{st.session_state.auth['persona']}**")
        st.divider()

        st.subheader("My Published Products")
        MOCK={"api-list-free":("3","2,100",None),"api-list-std":("12","48,200",300.*12),
              "api-list-ent":("2","310k",5000.*2),"sf-list":("4","—",4000.*4),
              "stream-list":("3","—",800.*3)}
        for p in [x for x in CATALOG if x.domain=="Listings"]:
            s,c,r=MOCK.get(p.id,("—","—",None))
            with st.expander(f"{picon(p.product_type)} {p.name}  ·  {p.delivery_tech}  ·  {money(p.price_monthly)}/mo"):
                a,b,d=st.columns(3)
                a.metric("Subscribers",s); b.metric("Calls/Queries (30d)",c)
                d.metric("Revenue (30d)", money(r) if r is not None else "—")
                st.write(p.description)

        st.divider()
        st.subheader("Publish a New Data Product")
        st.markdown('<div class="prov-card">', unsafe_allow_html=True)
        with st.form("pub"):
            ca,cb=st.columns(2)
            with ca:
                n_name=st.text_input("Product Name",placeholder="e.g., Off-Market Listings Feed")
                n_dom =st.selectbox("Domain",[d["name"] for d in DOMAINS])
                n_type=st.selectbox("Product Type",[t["name"] for t in PRODUCT_TYPES])
            with cb:
                n_dlv =st.selectbox("Delivery",["REST/HTTP","Apache Kafka","Amazon Kinesis",
                                                 "S3/Parquet","Tableau Embedded","Snowflake Share"])
                n_tier=st.selectbox("Tier",["Free","Paid","Enterprise"])
                n_acc =st.selectbox("Access",["Public","Partner","Private"])
                n_price=st.number_input("Price ($/month)",min_value=0.,value=0.,step=50.)
            n_desc=st.text_area("Description",placeholder="Describe what this data product provides…")
            sub=st.form_submit_button("🚀 Publish to Marketplace",type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
        if sub:
            if not (n_name or "").strip(): st.error("Product name is required.")
            else: st.success(f"✅ **{n_name}** submitted for review."); st.balloons()

        st.divider()
        c1,c2=st.columns(2)
        with c1:
            st.info("**Snowflake Marketplace Listing**\n\n"
                    "To list publicly on Snowflake Marketplace, Brillio must enroll as a data provider. "
                    "Requires management approval + provider data submitted to Snowflake.\n\n"
                    "For *private* listings (partner-only), create the share and grant directly — "
                    "no enrollment needed.")
        with c2:
            st.info("**Two-Browser Demo**\n\n"
                    "Open a second browser as `consumer` / `consumer123`. "
                    "Show the agent publishing here while the consumer browses and subscribes in "
                    "Listings Demo / Business View — demonstrating the full provider → consumer flow.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — DOCUMENTATION
# ══════════════════════════════════════════════════════════════════════════════
with t_docs:
    st.subheader("📄 Documentation")
    st.caption("Platform narrative, delivery mechanisms, personas, RBAC, and demo guide.")

    doc_tabs = st.tabs(["🚀 How It Works", "⚡ Platform Enablers", "💡 Why Data as a Product",
                        "👤 Personas & Access", "📋 Demo Guide"])

    # ── How it works ──────────────────────────────────────────────────────────
    with doc_tabs[0]:
        st.subheader("How It Works")
        hiw_html = "".join([
            f'<div class="hiw-card">'
            f'<div class="hiw-num">{h["num"]}</div>'
            f'<div class="hiw-title">{h["title"]}</div>'
            f'<div class="hiw-desc">{h["desc"]}</div></div>'
            for h in HOW_IT_WORKS])
        st.markdown(f'<div class="hiw-grid">{hiw_html}</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Two Delivery Mechanisms")
        st.markdown("""<div class="ap-grid">
  <div class="ap-card ap-rest">
    <div class="ap-icon">🌐</div>
    <div class="ap-title">REST API</div>
    <div class="ap-sub">For non-Snowflake consumers</div>
    <div class="ap-row">✓ Bearer token authentication</div>
    <div class="ap-row">✓ 3 live endpoints on AWS API Gateway</div>
    <div class="ap-row">✓ Free / Paid / Enterprise tier gating</div>
    <div class="ap-row">✓ Works with any HTTP client or language</div>
    <div class="ap-code">GET /v1/listings<br>GET /v1/listings/{id}<br>GET /v1/listings/export</div>
    <div><span class="ap-tag ap-tag-rest">🌐 REST / HTTP</span></div>
  </div>
  <div class="ap-card ap-sf">
    <div class="ap-icon">❄️</div>
    <div class="ap-title">Snowflake Native (No-Copy)</div>
    <div class="ap-sub">For Snowflake customers</div>
    <div class="ap-row">✓ Private Listing — data never leaves MOVE's Snowflake</div>
    <div class="ap-row">✓ Consumer queries a Secure View in their own account</div>
    <div class="ap-row">✓ Column & row-level security enforced by Snowflake</div>
    <div class="ap-row">✓ Zero ETL, zero duplication, always live</div>
    <div class="ap-code">CREATE DATABASE MOVE_MKT<br>&nbsp;&nbsp;FROM SHARE BRILLIO_MOVE_LISTINGS_V1;<br>SELECT * FROM MOVE_MKT.LISTINGS.ACTIVE_LISTINGS_VW;</div>
    <div><span class="ap-tag ap-tag-sf">❄️ Snowflake No-Copy</span></div>
  </div>
</div>""", unsafe_allow_html=True)

        st.write("**REST API vs Snowflake Native — comparison**")
        st.markdown("""
| | 🌐 REST API | ❄️ Snowflake Native |
|---|---|---|
| Auth | Bearer token | Snowflake role |
| Data movement | Streamed JSON/CSV | Zero copy |
| Security | Tier gating + app RBAC | Secure View + role |
| Latency | HTTP round-trip | Native SF query |
| Aggregations | Client-side | Server-side in SF |
| Best for | Any HTTP client | Snowflake analytics |
""")

    # ── Platform Enablers ─────────────────────────────────────────────────────
    with doc_tabs[1]:
        st.subheader("Platform Enablers")
        en_html = "".join([
            f'<div class="en-card"><div class="en-icon">{e["icon"]}</div>'
            f'<div><div class="en-label">{e["label"]}</div>'
            f'<div class="en-desc">{e["desc"]}</div></div></div>'
            for e in ENABLERS])
        st.markdown(f'<div class="en-bar">{en_html}</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("""
### AI Governance
Policy-driven access control ensures every product has a defined owner, data classification, and audit trail.
- Data contracts enforced at publish time
- Lineage tracked end-to-end via OpenLineage
- Access policies reviewed quarterly

### Data Quality
Automated profiling and freshness checks run on every pipeline before data is exposed in the marketplace.
- Schema validation on ingest
- Row-count and null-rate SLAs per product
- Freshness alerts via PagerDuty

### Data Ops
CI/CD-style pipelines for data product deployment. New products go through dev → staging → prod promotion.
- Automated deployment via dbt + Airflow
- Rollback-capable versioning
- Snowflake CLONE for zero-downtime schema changes
""")

    # ── Why Data as a Product ─────────────────────────────────────────────────
    with doc_tabs[2]:
        vc = "".join([f'<div class="val-card"><div class="val-icon">{v["icon"]}</div>'
                      f'<div class="val-label">{v["label"]}</div>'
                      f'<div class="val-desc">{v["desc"]}</div></div>' for v in VALUES])
        st.markdown(f'<div class="val-section"><div class="val-heading">✅ Why Data as a Product?</div>'
                    f'<div class="val-grid">{vc}</div></div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("""
### The Data Product Lifecycle

Every data domain at MOVE goes through a structured lifecycle before it appears in the marketplace:

| Stage | What happens |
|---|---|
| 🔍 **Discover** | Identify business-relevant data sources and map to domains |
| 📋 **Define** | Assign ownership, schema contracts, SLAs, and access policy |
| ⚙️ **Develop** | Build pipelines, secure views, API endpoints, and dashboards |
| 🚀 **Deliver** | Publish to marketplace as versioned, governed data products |
| 🔑 **Access** | Consumers self-subscribe; usage is metered and audited |

This lifecycle ensures MOVE's data assets are trusted, discoverable, and reusable — not siloed.

### Product Type Reference

| Type | Icon | Delivery | Best for |
|---|---|---|---|
| REST APIs | 🔌 | AWS API Gateway + Bearer token | Any language, CRM integrations |
| Analytics | 📊 | Embedded Streamlit / Looker | Non-technical business users |
| Event Streams | ⚡ | Apache Kafka / Amazon Kinesis | Real-time pipelines |
| Datasets | 📦 | S3 / Parquet | Bulk ML training, archival |
| BI Reports | 📋 | Tableau / Looker / Power BI | Scheduled reporting |
| Snowflake Native | ❄️ | Snowflake Private Share | Snowflake customers, zero-copy |
""")

    # ── Personas & Access ─────────────────────────────────────────────────────
    with doc_tabs[3]:
        st.subheader("Personas & Access")
        st.markdown("""
### Demo Personas

| Username | Password | Role | Description |
|---|---|---|---|
| `agent` | `agent123` | Provider | Real Estate Agent — publishes and manages data products |
| `consumer` | `consumer123` | Consumer | Data Consumer — browses, subscribes, and accesses products |
| `developer` | `dev123` | Developer | Developer — integrates APIs and queries Snowflake views |

### Two-Browser Demo
Open **Browser A** as `agent` and **Browser B** as `consumer` to demonstrate the full
provider → consumer flow simultaneously.

---

### Tier Gating (REST API)

| Tier | `/listings` | `/listings/{id}` | `/listings/export` | Price |
|---|---|---|---|---|
| Free | ✅ | ❌ | ❌ | $0 |
| Paid | ✅ | ✅ | ❌ | $300/mo |
| Enterprise | ✅ | ✅ | ✅ | $5,000/mo |

---

### RBAC — Field Visibility by Role

| Role | Fields visible |
|---|---|
| Consumer | LISTING_ID, CITY, STATE, LIST_PRICE, POSTAL_CODE |
| Agent / Provider | + BED_COUNT, BATH_COUNT, BUILDING_SQFT, YEAR_BUILT, DATA_SOURCE |
| Developer | Full payload |

The Snowflake Secure View applies column-level security natively — the consumer sees only
the columns their role is authorized to access, without any application-layer logic.

---

### Snowflake Marketplace Enrollment

| Listing type | Enrollment required? | How |
|---|---|---|
| Public listing | ✅ Yes | Brillio management approval + Snowflake provider review |
| Private listing (partner) | ❌ No | Create share, grant to consumer's Snowflake account |
""")

    # ── Demo Guide ────────────────────────────────────────────────────────────
    with doc_tabs[4]:
        st.subheader("Slide-Aligned Demo Guide")
        st.markdown("""
| # | Step | Tab | What to show | What to say |
|---|---|---|---|---|
| 1 | Open Marketplace | 🏪 Marketplace | Hero stats + product type tiles | *"This is MOVE's Data Product Marketplace — 60 products across 7 domains."* |
| 2 | Filter by type | 🏪 Marketplace | Click REST APIs tile | *"Filter to just REST APIs — 15 products."* |
| 3 | Filter by domain | 🏪 Marketplace | Click Listings domain tile | *"Drill into Listings — the domain we'll demo today."* |
| 4 | Show all products | 📦 All Products | Full grid | *"60 products spanning APIs, analytics, streams, datasets, reports, and Snowflake native."* |
| 5 | Two access paths | 🏠 Listings Demo | Access path cards | *"We deliver two ways — REST for non-Snowflake users, Snowflake Native for zero-copy."* |
| 6 | Generate token | 🏠 → REST API Demo | Token generator | *"Subscribe, generate a Bearer token — self-serve, seconds."* |
| 7 | Call live endpoint | 🏠 → REST API Demo | Run button | *"Live call to AWS API Gateway — data filtered by RBAC."* |
| 8 | Snowflake demo | 🏠 → Snowflake Demo | SQL code blocks | *"For Snowflake users — no copy, no ETL, query runs inside MOVE's account."* |
| 9 | Business view | 📊 Business View | Dashboard cards | *"Non-technical consumers browse and request access here — no SQL needed."* |
| 10 | Provider publishes | 📤 Provider Hub | Publish form | *"The agent publishes new products, sees subscribers and revenue."* |
| 11 | API Explorer | 🛠️ Developer Tools | REST explorer | *"Developers test endpoints live with their token."* |
| 12 | Snowflake SQL | 🛠️ → SF SQL Explorer | SQL explorer | *"Query any Snowflake share with generated SQL — copy-paste ready."* |
| 13 | Close | 📄 Documentation | Why Data as Product | *"Faster onboarding, trusted intelligence, new revenue streams."* |
""")

        st.caption("Master narrative: *We are enabling Data as a Product by moving from raw data sources "
                   "to governed, discoverable, and reusable data products aligned to business domains.*")
