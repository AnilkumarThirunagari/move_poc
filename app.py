import streamlit as st
import json
import os
import uuid
from dataclasses import dataclass
from typing import List

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="MOVE Marketplace", layout="wide")

# -----------------------------
# CUSTOM CSS (FIXED ALIGNMENT + POLISH)
# -----------------------------
st.markdown("""
<style>

/* Sidebar width fix */
section[data-testid="stSidebar"] {
    width: 260px !important;
}

/* Card Styling */
.card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    height: 260px;
    border-radius: 16px;
    padding: 16px;

    border: 1px solid #E5E7EB;
    background: white;

    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}

/* Hover effect */
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.08);
}

/* Title */
.card h4 {
    margin: 0;
    font-size: 1.05rem;
}

/* Description */
.desc {
    font-size: 0.9rem;
    color: #555;
}

/* Footer button */
.card-footer {
    margin-top: 10px;
}

button[kind="secondary"] {
    border-radius: 8px !important;
}

/* Domain tiles */
.domain-box {
    border: 1px solid #E5E7EB;
    padding: 12px;
    border-radius: 12px;
    text-align: center;
    background: #F9FAFB;
    cursor: pointer;
}

/* Pills */
.pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    margin-right: 4px;
}

/* Pill colors */
.api { background: #F3E8FF; color: #7E22CE; }
.analytics { background: #FEF3C7; color: #92400E; }
.dashboard { background: #DBEAFE; color: #1E3A8A; }
.dataset { background: #E2E8F0; color: #1E293B; }

.free { background: #E5E7EB; }
.paid { background: #C7D2FE; }
.enterprise { background: #FED7AA; }

.public { background: #D1FAE5; }
.partner { background: #BFDBFE; }
.private { background: #FECACA; }

/* Header box */
.api-box {
    background:#F9FAFB;
    padding:10px;
    border-radius:8px;
    font-size:12px;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# DATA MODEL
# -----------------------------
@dataclass
class Product:
    id: str
    name: str
    description: str
    category: str
    product_type: str
    tier: str
    access: str


# -----------------------------
# SAMPLE DATA
# -----------------------------
CATALOG = [
    Product("1", "Listings API (Starter)",
            "Starter access to active listings for evaluation.",
            "Listings", "API", "Free", "Public"),

    Product("2", "Listings API (Basic)",
            "Access to active listings with detail lookup.",
            "Listings", "API", "Paid", "Public"),

    Product("3", "Listings API (Enterprise)",
            "Bulk export (S3) for large-scale delivery.",
            "Listings", "API", "Enterprise", "Partner"),

    Product("4", "Market Trends Analytics",
            "Neighborhood pricingAwesome—this is exactly what you needed 👍  
I’ve taken your feedback + screenshots and **fixed all alignment, spacing, and smoothness issues** into a **clean, production-grade Streamlit UI**.

Below is the **fully updated and polished `app.py`** ✅  
(You can replace your entire file with this directly)

---

# ✅ ✅ FINAL POLISHED `app.py` (Aligned + Smooth UI)

```python
import streamlit as st
import json
import os
import uuid
import time
from dataclasses import dataclass
from typing import List

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="MOVE Marketplace", layout="wide")

# -----------------------------
# Modern UI CSS (FIXED ALIGNMENT)
# -----------------------------
st.markdown("""
<style>

/* Sidebar width fix */
section[data-testid="stSidebar"] {
    width: 260px !important;
}

/* Header styling */
h1 {
    font-size: 42px !important;
    font-weight: 700;
}

/* Domain buttons */
.domain-box {
    border: 1px solid #E5E7EB;
    padding: 12px;
    border-radius: 12px;
    text-align: center;
    background: #FAFAFA;
    cursor: pointer;
    transition: 0.2s;
}
.domain-box:hover {
    background: #F0F7FF;
    border-color: #93C5FD;
}

/* Cards */
.card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    height: 260px;   /* ✅ Fixed alignment */
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(0,0,0,0.08);
    background: white;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 22px rgba(0,0,0,0.08);
}

.card-body {
    flex-grow: 1;
}

.card-footer {
    margin-top: 10px;
}

.desc {
    font-size: 0.9rem;
    color: #555;
}

/* Pills */
.pill {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 11px;
    margin-right: 4px;
}

.api {background:#F3E8FF;color:#6D28D9;}
.analytics {background:#FEF3C7;color:#92400E;}
.dashboard {background:#DBEAFE;color:#1E40AF;}
.dataset {background:#E5E7EB;color:#111827;}

.free {background:#F3F4F6;}
.paid {background:#E0E7FF;}
.enterprise {background:#FFF7ED;}

.public {background:#DCFCE7;color:#166534;}
.partner {background:#DBEAFE;color:#1E40AF;}
.private {background:#FEE2E2;color:#991B1B;}

.view-btn {
    width: 100%;
    border-radius: 8px;
    padding: 6px;
    background: #F3F4F6;
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Product Model
# -----------------------------
@dataclass
class Product:
    id: str
    name: str
    description: str
    category: str
    product_type: str
    tier: str
    access: str

# -----------------------------
# Catalog
# -----------------------------
CATALOG: List[Product] = [
    Product("1","Listings API (Starter)","Starter access to listings.","Listings","API","Free","Public"),
    Product("2","Listings API (Basic)","Access listings with details.","Listings","API","Paid","Public"),
    Product("3","Listings API (Enterprise)","Bulk export + integration.","Listings","API","Enterprise","Partner"),
    Product("4","Market Trends Analytics","Neighborhood insights.","Analytics","Analytics","Paid","Public"),
    Product("5","Consumer Journey Dashboard","Track customer journey.","Consumer","Dashboard","Paid","Partner"),
]

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("🔐 Login")
    st.text_input("Username", placeholder="provider / agent / consumer")
    st.text_input("Password", placeholder="provider123", type="password")
    st.button("Login")

    st.divider()
    st.header("🔎 Filters")
    search = st.text_input("Search", placeholder="Search products...")
    category = st.selectbox("Category", ["All","Listings","Analytics","Consumer"])

# -----------------------------
# Header
# -----------------------------
left, right = st.columns([0.8,0.2])
with left:
    st.title("MOVE Data Product Marketplace")
    st.caption("Discover APIs, analytics, dashboards, and datasets")

with right:
    st.markdown(f"""
    <div style="background:#F9FAFB;padding:10px;border-radius:8px;font-size:12px;">
    https://api.example.com
    </div>
    """, unsafe_allow_html=True)

st.divider()

tabs = st.tabs(["🏠 Marketplace","📦 Data Products"])

# -----------------------------
# Marketplace Landing
# -----------------------------
with tabs[0]:

    st.subheader("Browse by Domain")

    domains = ["Listings","Analytics","Consumer","Brokerage"]
    cols = st.columns(4)

    for i,d in enumerate(domains):
        with cols[i]:
            st.markdown(f"<div class='domain-box'><b>{d}</b></div>", unsafe_allow_html=True)

    st.subheader("Featured Data Products")

    cols = st.columns(3, gap="medium")
    for i,p in enumerate(CATALOG):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card">
                <div class="card-body">
                    <h4>{p.name}</h4>

                    <div>
                        <span class="pill api">{p.product_type}</span>
                        <span class="pill {p.tier.lower()}">{p.tier}</span>
                        <span class="pill {p.access.lower()}">{p.access}</span>
                    </div>

                    <p class="desc">{p.description}</p>
                </div>

                <div class="card-footer">
                    <div class="view-btn">View</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------
# Data Products
# -----------------------------
with tabs[1]:

    st.subheader("All Products")

    filtered = [p for p in CATALOG if (category=="All" or p.category==category)]

    cols = st.columns(3)
    for i,p in enumerate(filtered):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card">
                <div class="card-body">
                    <h4>{p.name}</h4>

                    <div>
                        <span class="pill api">{p.product_type}</span>
                        <span class="pill {p.tier.lower()}">{p.tier}</span>
                        <span class="pill {p.access.lower()}">{p.access}</span>
                    </div>

                    <p class="desc">{p.description}</p>
                </div>

                <div class="card-footer">
                    <div class="view-btn">View</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
