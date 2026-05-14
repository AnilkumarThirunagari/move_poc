import streamlit as st
from dataclasses import dataclass
from typing import List

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Marketplace", layout="wide")

# -----------------------------
# CSS (UI FIXES APPLIED)
# -----------------------------
st.markdown("""
<style>

/* ✅ Fix sidebar width */
section[data-testid="stSidebar"] {
    width: 250px !important;
}

/* ✅ Card Styling */
.card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    height: 260px;
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(0,0,0,0.08);
    background: white;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}

/* ✅ Hover effect */
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 22px rgba(0,0,0,0.1);
}

.card-body {
    flex-grow: 1;
}

.card-footer {
    margin-top: 10px;
}

/* ✅ Button alignment */
.view-btn {
    width: 100%;
    border-radius: 8px;
    padding: 6px;
    background: #F3F4F6;
    text-align: center;
}

/* ✅ Tags */
.tag {
    display: inline-block;
    padding: 4px 8px;
    margin-right: 5px;
    margin-top: 6px;
    border-radius: 20px;
    font-size: 11px;
}

/* Types */
.api { background:#EDE9FE; color:#5B21B6; }
.analytics { background:#FEF3C7; color:#92400E; }
.dashboard { background:#DBEAFE; color:#1E40AF; }
.dataset { background:#F3F4F6; color:#111827; }

/* Tier */
.free { background:#F3F4F6; }
.paid { background:#E0E7FF; }
.enterprise { background:#FEF3C7; }

/* Access */
.public { background:#DCFCE7; }
.partner { background:#DBEAFE; }
.private { background:#FEE2E2; }

/* ✅ Domain buttons */
.domain {
    border: 1px solid #E5E7EB;
    padding: 12px;
    border-radius: 12px;
    text-align: center;
    background: #FAFAFA;
    cursor: pointer;
    transition: 0.2s;
}

.domain:hover {
    background:#F3F4F6;
}

/* ✅ Header box */
.api-box {
    background:#F9FAFB;
    padding:10px;
    border-radius:8px;
    font-size:12px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Product Model
# -----------------------------
@dataclass
class Product:
    name: str
    description: str
    category: str
    product_type: str
    tier: str
    access: str

# -----------------------------
# Sample Data
# -----------------------------
products = [
    Product("Listings API (Starter)", "Starter access to listings", "Listings", "API", "Free", "Public"),
    Product("Listings API (Basic)", "Access listings with details", "Listings", "API", "Paid", "Public"),
    Product("Listings API (Enterprise)", "Bulk export & enterprise access", "Listings", "API", "Enterprise", "Partner"),
    Product("Market Trends Analytics", "Neighborhood-level trends", "Analytics", "Analytics", "Paid", "Public"),
    Product("Consumer Journey Dashboard", "Track user journey", "Consumer", "Dashboard", "Paid", "Partner"),
    Product("Agent Dataset", "Agent & office dataset", "Brokerage", "Dataset", "Enterprise", "Private"),
]

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🔐 Login")
st.sidebar.text_input("Username")
st.sidebar.text_input("Password", type="password")
st.sidebar.button("Login")

st.sidebar.markdown("---")
st.sidebar.title("🔎 Filters")
st.sidebar.text_input("Search")

# -----------------------------
# Header
# -----------------------------
col1, col2 = st.columns([0.8, 0.2], vertical_alignment="center")

with col1:
    st.title("MOVE Data Product Marketplace")
    st.caption("Discover APIs, analytics, dashboards, and datasets")

with col2:
    st.markdown(f"<div class='api-box'>API Base<br>https://api.example.com</div>", unsafe_allow_html=True)

st.divider()

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["🏠 Marketplace", "📦 Products", "⚙️ Developer"])

# -----------------------------
# Tab 1: Marketplace
# -----------------------------
with tab1:

    st.subheader("Browse by Domain")

    domains = ["Listings", "Analytics", "Consumer", "Brokerage"]
    cols = st.columns(4)

    for i, d in enumerate(domains):
        with cols[i]:
            st.markdown(f"<div class='domain'><b>{d}</b></div>", unsafe_allow_html=True)

    st.subheader("Featured Data Products")

    cols = st.columns(3, gap="medium")

    for i, p in enumerate(products):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card">
                <div class="card-body">
                    <h4>{p.name}</h4>

                    <div>
                        <span class="tag api">{p.product_type}</span>
                        <span class="tag {p.tier.lower()}">{p.tier}</span>
                        <span class="tag {p.access.lower()}">{p.access}</span>
                    </div>

                    <p style="font-size:13px;color:#555;">{p.description}</p>
                </div>

                <div class="card-footer">
                    <div class="view-btn">View</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------
# Tab 2: Products
# -----------------------------
with tab2:
    st.subheader("All Data Products")

    for p in products:
        st.write(f"**{p.name}** — {p.description}")

# -----------------------------
# Tab 3: Developer
# -----------------------------
with tab3:
    st.subheader("Developer View")

    st.info("Technical features like token & API testing go here")

    if st.button("Generate Token"):
        st.success("Token generated (demo)")


