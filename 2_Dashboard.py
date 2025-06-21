import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import numpy as np
import uuid # For generating API keys

# Load environment variables
load_dotenv()

# MongoDB Connection
mongo_uri = os.getenv("MONGODB_URI")

try:
    client = MongoClient(mongo_uri)
    db = client["apiman"]
    logs_collection = db["api_usage_logs"]
    tickets_collection = db["support_tickets"]
    # New collections for API Keys and Users
    api_keys_collection = db["api_keys"] 
    users_collection = db["users"] 
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop()


st.set_page_config(layout="wide", page_title="API Admin Dashboard", initial_sidebar_state="collapsed")

# --- Configuration for APIs (Enhanced) ---
API_CONFIGS = {
    "Image API": {
        "cost_per_call": 0.002,
        "quota_daily": 10000,
        "rate_limit_per_second": 10,
        "base_latency_ms": 50, # Base value for latency
        "latency_variation": 20, # Max +/- ms variation
        "base_error_rate_percent": 0.5, # Base value for error rate
        "error_rate_variation": 0.5, # Max +/- % variation
        "documentation_url": "https://docs.example.com/imageapi",
        "latest_version": "v2.1",
        "endpoints": ["/process", "/info", "/status"]
    },
    "Video API": {
        "cost_per_call": 0.001,
        "quota_daily": 5000,
        "rate_limit_per_second": 5,
        "base_latency_ms": 80,
        "latency_variation": 30,
        "base_error_rate_percent": 1.2,
        "error_rate_variation": 1.0,
        "documentation_url": "https://docs.example.com/videoapi",
        "latest_version": "v1.5",
        "endpoints": ["/stream", "/upload", "/metadata"]
    },
    "Weather API": {
        "cost_per_call": 0.0005,
        "quota_daily": 20000,
        "rate_limit_per_second": 20,
        "base_latency_ms": 30,
        "latency_variation": 10,
        "base_error_rate_percent": 0.1,
        "error_rate_variation": 0.1,
        "documentation_url": "https://docs.example.com/weatherapi",
        "latest_version": "v3.0",
        "endpoints": ["/current", "/forecast", "/historical"]
    },
    "Ecommerce API": {
        "cost_per_call": 0.001,
        "quota_daily": 15000,
        "rate_limit_per_second": 15,
        "base_latency_ms": 60,
        "latency_variation": 25,
        "base_error_rate_percent": 0.8,
        "error_rate_variation": 0.7,
        "documentation_url": "https://docs.example.com/ecommerceapi",
        "latest_version": "v2.3",
        "endpoints": ["/products", "/orders", "/users", "/checkout"]
    },
    "QR Code API": {
        "cost_per_call": 0.001,
        "quota_daily": 8000,
        "rate_limit_per_second": 8,
        "base_latency_ms": 45,
        "latency_variation": 15,
        "base_error_rate_percent": 0.3,
        "error_rate_variation": 0.3,
        "documentation_url": "https://docs.example.com/qrcodeapi",
        "latest_version": "v1.2",
        "endpoints": ["/generate", "/decode"]
    },
    "Profile Photo API": {
        "cost_per_call": 0.001,
        "quota_daily": 7000,
        "rate_limit_per_second": 7,
        "base_latency_ms": 70,
        "latency_variation": 28,
        "base_error_rate_percent": 0.6,
        "error_rate_variation": 0.6,
        "documentation_url": "https://docs.example.com/profilephotoapi",
        "latest_version": "v2.0",
        "endpoints": ["/upload", "/crop", "/filter"]
    },
    "Jokes API": {
        "cost_per_call": 0.001,
        "quota_daily": 25000,
        "rate_limit_per_second": 25,
        "base_latency_ms": 25,
        "latency_variation": 10,
        "base_error_rate_percent": 0.05,
        "error_rate_variation": 0.05,
        "documentation_url": "https://docs.example.com/jokesapi",
        "latest_version": "v1.0",
        "endpoints": ["/random", "/category", "/search"]
    }
}

# --- Dummy Data Generation (Enhanced) ---
@st.cache_data(ttl=3600) # Cache dummy data generation for an hour
def generate_dummy_log_data(num_entries=50000): # Increased entries for better trends
    
    apis = list(API_CONFIGS.keys())
    users = ["user_" + str(i) for i in range(1, 21)] # 20 dummy users
    status_codes = [200] * 50 + [400] * 5 + [401] * 2 + [404] * 3 + [500] * 5 # More realistic distribution
    countries = ["USA", "Germany", "India", "Brazil", "Japan", "UK", "Canada", "Australia", "France", "China", "Mexico"]

    log_entries = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=90) # Generate 90 days of data

    for _ in range(num_entries):
        # Convert numpy types to standard Python types for MongoDB compatibility
        api = str(np.random.choice(apis))
        user_id = str(np.random.choice(users))
        timestamp = start_time + (end_time - start_time) * np.random.rand()
        status_code = int(np.random.choice(status_codes)) 
        country = str(np.random.choice(countries))
        
        api_config = API_CONFIGS.get(api, {})
        api_version = api_config.get("latest_version", "v1.0")
        endpoint = str(np.random.choice(api_config.get("endpoints", ["/default"])))
        
        # Simulate latency for more realistic health data
        base_latency = api_config.get("base_latency_ms", 50)
        latency_variation = api_config.get("latency_variation", 20)
        latency = float(max(10, base_latency + (np.random.rand() * 2 - 1) * latency_variation))

        log_entries.append({
            "api": api,
            "timestamp": timestamp,
            "user_id": user_id,
            "status_code": status_code,
            "country": country,
            "api_version": api_version,
            "endpoint": endpoint,
            "latency_ms": latency
        })
    return log_entries

# Ensure some dummy data is in MongoDB if collections are empty
if logs_collection.count_documents({}) == 0:
    st.info("No logs found in MongoDB. Generating dummy data (this may take a moment)...")
    dummy_logs = generate_dummy_log_data(50000)
    logs_collection.insert_many(dummy_logs)
    st.success("Dummy log data generated and inserted!")
    st.cache_data.clear() # Clear cache to load new data
    st.rerun()

if users_collection.count_documents({}) == 0:
    st.info("No users found. Generating dummy users...")
    dummy_users = [{"user_id": f"user_{i}", "email": f"user{i}@example.com", "role": "developer", "last_login": datetime.utcnow().isoformat()} for i in range(1, 21)]
    users_collection.insert_many(dummy_users)
    st.success("Dummy users generated!")
    st.cache_data.clear()
    st.rerun()

# --- Helper Functions ---
@st.cache_data(ttl=600) # Cache for 10 minutes
def get_api_logs(start_date=None, end_date=None):
    query = {}
    if start_date:
        query["timestamp"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
    if end_date:
        if "timestamp" not in query:
            query["timestamp"] = {}
        query["timestamp"]["$lte"] = datetime.combine(end_date, datetime.max.time())
            
    logs = list(logs_collection.find(query))
    df = pd.DataFrame(logs)
    if 'timestamp' in df.columns and not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    else:
        # Fallback for empty/missing timestamp, ensures df has correct column types
        st.warning("Logs found but 'timestamp' column is missing or empty. Initializing with default.")
        df['timestamp'] = pd.to_datetime([]) # Empty datetime series
        
    # Ensure all expected columns are present, adding defaults if necessary
    expected_cols = ["api", "timestamp", "user_id", "status_code", "country", "api_version", "endpoint", "latency_ms"]
    for col in expected_cols:
        if col not in df.columns:
            if col == 'api': df[col] = "unknown_api"
            elif col == 'user_id': df[col] = "unknown_user"
            elif col == 'status_code': df[col] = 200
            elif col == 'country': df[col] = "Unknown"
            elif col == 'api_version': df[col] = "v1.0"
            elif col == 'endpoint': df[col] = "/default"
            elif col == 'latency_ms': df[col] = 50.0 # Ensure float type
            else: df[col] = None
    
    return df.copy() # Return a copy to prevent SettingWithCopyWarning

def calculate_daily_usage(df, api_name=None, start_date=None, end_date=None):
    if df.empty:
        end_date_default = end_date if end_date else datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date_default = start_date if start_date else end_date_default - timedelta(days=29)
        all_dates = pd.date_range(start=start_date_default, end=end_date_default, freq='D')
        
        dummy_counts = []
        base_value = API_CONFIGS.get(api_name, {}).get("quota_daily", 1000) / 10 if api_name else 500
        if base_value == 0: base_value = 100
        
        for day_idx in range(len(all_dates)):
            trend_factor = np.sin(day_idx / 5) * (base_value / 2)
            random_noise = np.random.normal(0, base_value / 4)
            count = max(0, int(base_value + trend_factor + random_noise))
            dummy_counts.append(count)
            
        return pd.DataFrame({"Date": all_dates, "Count": dummy_counts})

    df_filtered = df
    if api_name:
        df_filtered = df_filtered[df_filtered["api"] == api_name]
    
    df_daily = df_filtered.groupby(pd.Grouper(key="timestamp", freq="D")).size().reset_index(name="Count")
    df_daily.columns = ["Date", "Count"]

    end_date_range = df_daily['Date'].max() if not df_daily.empty else datetime.utcnow()
    start_date_range = df_daily['Date'].min() if not df_daily.empty else end_date_range - timedelta(days=29)
    
    if start_date and end_date:
        start_date_range = datetime.combine(start_date, datetime.min.time())
        end_date_range = datetime.combine(end_date, datetime.max.time())
        
    all_dates = pd.date_range(start=start_date_range, end=end_date_range, freq='D')
    full_df = pd.DataFrame(all_dates, columns=["Date"])
    
    daily_usage = pd.merge(full_df, df_daily, on="Date", how="left").fillna(0)
    return daily_usage

def calculate_current_daily_usage(df, api_name):
    if 'api' not in df.columns or df.empty:
        return 0

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    current_day_usage = df[(df["api"] == api_name) & (df["timestamp"] >= today_start)].shape[0]
    return current_day_usage

def get_api_health(api_name):
    config = API_CONFIGS.get(api_name, {})
    
    base_latency = config.get("base_latency_ms", 50)
    latency_variation = config.get("latency_variation", 20)
    base_error_rate = config.get("base_error_rate_percent", 0.5)
    error_rate_variation = config.get("error_rate_variation", 0.5)

    latency_rand = base_latency + (np.random.rand() * 2 - 1) * latency_variation
    latency_rand = max(10.0, latency_rand) # Ensure float type

    error_rate_rand = base_error_rate + (np.random.rand() * 2 - 1) * error_rate_variation
    error_rate_rand = max(0.01, error_rate_rand) 

    status = "healthy"
    icon = "🟢"
    # Criteria for warning/critical, now relative to base values
    if error_rate_rand > (base_error_rate * 2) or latency_rand > (base_latency * 1.5): 
        status = "warning"
        icon = "🟡"
    if error_rate_rand > (base_error_rate * 4) or latency_rand > (base_latency * 2.5): 
        status = "critical"
        icon = "🔴"
    
    return status, icon, round(latency_rand, 1), round(error_rate_rand, 2)


# --- API Key Management Functions ---
def generate_api_key(user_id, api_name):
    key_id = str(uuid.uuid4())
    api_key_str = "sk-" + str(uuid.uuid4()).replace("-", "") # Example format
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=365) # Key valid for 1 year
    
    api_keys_collection.insert_one({
        "key_id": key_id,
        "api_key": api_key_str,
        "user_id": user_id,
        "api": api_name,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "active"
    })
    st.success(f"New API Key generated for {user_id} for {api_name}: `{api_key_str}`")
    st.cache_data.clear()
    st.rerun()

def update_api_key_status(key_id, status):
    api_keys_collection.update_one({"key_id": key_id}, {"$set": {"status": status}})
    st.success(f"API Key {key_id} status updated to {status}!")
    st.cache_data.clear()
    st.rerun()

# --- User Management (Simulated) ---
@st.cache_data(ttl=600)
def get_users():
    return list(users_collection.find())


# --- Streamlit UI ---

st.title("🚀 API Management Dashboard")

# --- Global Date Range Filter ---
with st.sidebar:
    st.header("Global Filters")
    today = datetime.utcnow().date()
    default_start_date = today - timedelta(days=29) # Last 30 days
    
    date_range = st.date_input(
        "Select Date Range",
        value=(default_start_date, today),
        min_value=today - timedelta(days=365), # Allow wider range
        max_value=today,
        key="global_date_range"
    )

    selected_start_date = date_range[0]
    selected_end_date = date_range[1] if len(date_range) > 1 else date_range[0]

    st.markdown("---")
    st.header("Admin Tools & Settings")
    
    # Simulate User Role for Admin tools
    current_user_role = st.selectbox(
        "Simulate User Role:",
        ["Developer", "Admin", "Viewer"],
        index=1, # Default to Admin for demonstration
        key="user_role_selector"
    )

    # Auto-refresh checkbox
    auto_refresh = st.checkbox("Enable Auto-Refresh (Every 60s)", value=False, key="auto_refresh_checkbox")
    if auto_refresh:
        from streamlit_extras.rerun_with_delay import rerun_with_delay
        rerun_with_delay(delay_seconds=60)


df_logs = get_api_logs(start_date=selected_start_date, end_date=selected_end_date)
# Filter out "unknown_api" if it's just a placeholder and not real
df_logs = df_logs[df_logs['api'] != 'unknown_api'] 


st.markdown(" ")

# --- Top-Level API Navigation (Horizontal Tabs) ---
# Add new top-level tabs for Users and Admin
api_tabs_list = ["Overview"] + sorted(list(API_CONFIGS.keys())) + ["Users", "Admin Tools", "Changelog"]
selected_api_tab = st.tabs(api_tabs_list)

for i, tab_name in enumerate(api_tabs_list):
    with selected_api_tab[i]:
        if tab_name == "Overview":
            st.subheader("Overall API Usage Summary")
            
            col1, col2, col3 = st.columns(3)
            total_calls_overall = df_logs.shape[0]
            total_cost_overall = df_logs.apply(lambda row: API_CONFIGS.get(row["api"], {}).get("cost_per_call", 0), axis=1).sum()

            with col1:
                st.metric(label="Total Calls (Selected Period)", value=f"{total_calls_overall:,}")
            with col2:
                st.metric(label="Total Estimated Cost (Selected Period)", value=f"${total_cost_overall:,.2f}")
            with col3:
                # Placeholder for average latency overall
                avg_latency_overall = df_logs['latency_ms'].mean() if not df_logs.empty else 0
                st.metric(label="Avg Latency (Selected Period)", value=f"{avg_latency_overall:.1f} ms")


            if not df_logs.empty and 'api' in df_logs.columns and df_logs['api'].any():
                api_counts = df_logs["api"].value_counts().reset_index()
                api_counts.columns = ["API", "Calls"]
                api_counts["Cost ($)"] = api_counts.apply(
                    lambda row: round(row["Calls"] * API_CONFIGS.get(row["API"], {}).get("cost_per_call", 0), 3), axis=1
                )
                st.dataframe(api_counts, use_container_width=True)

                st.subheader("API Usage Over Time (All APIs Combined)")
                df_daily_all = df_logs.groupby([pd.Grouper(key="timestamp", freq="D"), "api"]).size().reset_index(name="Count")
                
                if not df_daily_all.empty and df_daily_all['Count'].sum() > 0:
                    fig_all_usage = px.line(df_daily_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)", template="plotly_white")
                    fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                    st.plotly_chart(fig_all_usage, use_container_width=True)
                else:
                    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    start_date = end_date - timedelta(days=29)
                    all_dates_dummy = pd.date_range(start=start_date, end=end_date, freq='D')
                    dummy_data_all = []
                    for date_idx, date in enumerate(all_dates_dummy):
                        for api in API_CONFIGS.keys():
                            base_value = API_CONFIGS.get(api, {}).get("quota_daily", 1000) / 10 
                            if base_value == 0: base_value = 100
                            
                            trend_factor = np.sin(date_idx / 4) * (base_value / 2)
                            random_noise = np.random.normal(0, base_value / 4)
                            count = max(0, int(base_value + trend_factor + random_noise))
                            dummy_data_all.append({"timestamp": date, "api": api, "Count": count})
                    df_dummy_all = pd.DataFrame(dummy_data_all)
                    fig_all_usage = px.line(df_dummy_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)", template="plotly_white")
                    fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                    st.plotly_chart(fig_all_usage, use_container_width=True)
            else:
                dummy_api_counts = pd.DataFrame({
                    "API": list(API_CONFIGS.keys()),
                    "Calls": [np.random.randint(500, 5000) for _ in API_CONFIGS],
                    "Cost ($)": [round(np.random.rand() * 10, 2) for _ in API_CONFIGS]
                })
                st.dataframe(dummy_api_counts, use_container_width=True)

                st.subheader("API Usage Over Time (All APIs Combined)")
                end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=29)
                all_dates_dummy = pd.date_range(start=start_date, end=end_date, freq='D')
                dummy_data_all = []
                for date_idx, date in enumerate(all_dates_dummy):
                    for api in API_CONFIGS.keys():
                        base_value = API_CONFIGS.get(api, {}).get("quota_daily", 1000) / 10 
                        if base_value == 0: base_value = 100
                        trend_factor = np.sin(date_idx / 4) * (base_value / 2)
                        random_noise = np.random.normal(0, base_value / 4)
                        count = max(0, int(base_value + trend_factor + random_noise))
                        dummy_data_all.append({"timestamp": date, "api": api, "Count": count})
                df_dummy_all = pd.DataFrame(dummy_data_all)
                fig_all_usage = px.line(df_dummy_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)", template="plotly_white")
                fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                st.plotly_chart(fig_all_usage, use_container_width=True)

            
            # Feature: Top Users/Consumers (3)
            st.subheader("Top API Consumers")
            if not df_logs.empty and 'user_id' in df_logs.columns:
                top_users = df_logs["user_id"].value_counts().reset_index()
                top_users.columns = ["User ID", "Total Calls"]
                st.dataframe(top_users.head(10), use_container_width=True)
            else:
                st.info("No user data available to show top consumers.")

            # Feature: Geographical Usage Map (6)
            st.subheader("Geographical Usage Overview")
            if not df_logs.empty and 'country' in df_logs.columns and df_logs['country'].nunique() > 1:
                country_counts = df_logs['country'].value_counts().reset_index()
                country_counts.columns = ['Country', 'Calls']
                
                # Simple dummy lat/long for countries for a basic map
                country_coords = {
                    "USA": (37.0902, -95.7129), "Germany": (51.1657, 10.4515), "India": (20.5937, 78.9629),
                    "Brazil": (-14.2350, -51.9253), "Japan": (36.2048, 138.2529), "UK": (55.3781, -3.4360),
                    "Canada": (56.1304, -106.3468), "Australia": (-25.2744, 133.7751), "France": (46.2276, 2.2137), 
                    "China": (35.8617, 104.1954), "Mexico": (23.6345, -102.5528), "Unknown": (0,0)
                }
                country_counts['lat'] = country_counts['Country'].apply(lambda c: country_coords.get(c, (0,0))[0])
                country_counts['lon'] = country_counts['Country'].apply(lambda c: country_coords.get(c, (0,0))[1])

                fig_geo = px.scatter_geo(country_counts, locations="Country", locationmode='country names', 
                                         size="Calls", hover_name="Country",
                                         projection="natural earth", title="API Calls by Country",
                                         color_discrete_sequence=px.colors.qualitative.Plotly,
                                         size_max=50) # Increase size_max for better visibility
                fig_geo.update_layout(height=500, margin={"r":0,"t":50,"l":0,"b":0},
                                      paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a") # Dark grey map background
                st.plotly_chart(fig_geo, use_container_width=True)
            else:
                st.info("Geographical data not available or insufficient for plotting.")


            # Feature: Billing Period Cost Summary (14)
            st.subheader("Current Billing Period Cost Summary")
            st.info("Assuming a monthly billing cycle, starting on the 1st of each month.")
            
            first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            df_current_month = df_logs[df_logs["timestamp"] >= first_day_of_month]
            
            current_month_cost = df_current_month.apply(lambda row: API_CONFIGS.get(row["api"], {}).get("cost_per_call", 0), axis=1).sum()
            current_month_calls = df_current_month.shape[0]

            col_curr_cost, col_proj_cost = st.columns(2)
            with col_curr_cost:
                st.metric(label="Calls This Month", value=f"{current_month_calls:,}")
                st.metric(label="Cost This Month", value=f"${current_month_cost:,.2f}")
            with col_proj_cost:
                # Simple projection: current cost / days passed * days in month
                days_in_month = (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1) - datetime.utcnow().replace(day=1)
                days_in_month = days_in_month.days
                
                days_passed = (datetime.utcnow() - first_day_of_month).days + 1
                if days_passed == 0: days_passed = 1 # Avoid division by zero
                
                projected_month_cost = (current_month_cost / days_passed) * days_in_month
                st.metric(label="Projected Cost This Month", value=f"${projected_month_cost:,.2f}")
                st.markdown(f"<p>Based on usage over {days_passed} days. (Total {days_in_month} days in month)</p>", unsafe_allow_html=True)
                
                if projected_month_cost > 500: # Example threshold
                    st.warning("Projected monthly cost is high. Review your API usage patterns.")
                else:
                    st.success("Projected monthly cost is well within limits.")

        elif tab_name in API_CONFIGS:
            # Content for individual API tabs
            st.header(f"📊 {tab_name} - Detailed Monitoring")
            api_config = API_CONFIGS.get(tab_name, {})
            quota_daily = api_config.get("quota_daily", "N/A")
            rate_limit_per_second = api_config.get("rate_limit_per_second", "N/A")
            cost_per_call = api_config.get("cost_per_call", "N/A")
            documentation_url = api_config.get("documentation_url", "#")
            latest_version = api_config.get("latest_version", "N/A")
            endpoints = api_config.get("endpoints", [])

            # Display key API info - ADDED CUSTOM CLASS `api-info-display-card`
            st.markdown(f"""
            <div class="api-info-display-card">
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                    <p style="margin: 5px 15px; font-size: 1.1em;"><strong>Version:</strong> {latest_version}</p>
                    <p style="margin: 5px 15px; font-size: 1.1em;"><strong>Daily Quota:</strong> {quota_daily:,} calls</p>
                    <p style="margin: 5px 15px; font-size: 1.1em;"><strong>Rate Limit:</strong> {rate_limit_per_second} req/sec</p>
                    <p style="margin: 5px 15px; font-size: 1.1em;"><strong>Cost/Call:</strong> ${cost_per_call}</p>
                </div>
                <div style="text-align: center; margin-top: 15px;">
                    <a href="{documentation_url}" target="_blank" class="button-link">🔗 View Documentation</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- Second-level navigation (Now using tabs for scrollability) ---
            st.markdown("<h4>Select a metric:</h4>", unsafe_allow_html=True)
            sub_options = ["Usage per API", "Quota per API", "Rate Limit per API", "Progress Bar", "API Health", 
                           "Cost Projection", "Error Breakdown", "Latency Distribution", "API Version Metrics", "Endpoint Metrics"]
            
            # Change from st.radio to st.tabs for horizontal scrolling
            metric_tabs = st.tabs(sub_options)

            # Iterate through the newly created tabs and render content based on selected tab
            for metric_index, selected_option_label in enumerate(sub_options):
                with metric_tabs[metric_index]: # Use 'with' context manager for each tab
                    # The selected_option_label now acts as the condition for content rendering
                    
                    # st.markdown("---") # Add a separator below the tabs

                    df_api_filtered = df_logs[df_logs["api"] == tab_name]

                    if selected_option_label == "Usage per API":
                        st.subheader(f"Daily API Usage Trend for {tab_name}")
                        
                        daily_usage_df = calculate_daily_usage(df_api_filtered, tab_name, start_date=selected_start_date, end_date=selected_end_date)
                        
                        total_calls = df_api_filtered.shape[0] if not df_api_filtered.empty else daily_usage_df['Count'].sum()

                        col_metric, col_graph = st.columns([1, 3])
                        with col_metric:
                            st.metric(label=f"Total Calls for {tab_name} (Selected Period)", value=f"{total_calls:,}")
                            st.markdown("<p>This graph shows the daily number of API calls over the selected period.</p>", unsafe_allow_html=True)
                            st.download_button(
                                label="Download Usage Data",
                                data=daily_usage_df.to_csv(index=False).encode('utf-8'),
                                file_name=f"{tab_name}_daily_usage.csv",
                                mime="text/csv",
                                key=f"download_usage_{tab_name}"
                            )
                        with col_graph:
                            fig_api_usage = px.line(daily_usage_df, x="Date", y="Count",
                                                     title=f"Daily API Usage for {tab_name}", template="plotly_white")
                            fig_api_usage.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Number of Calls")
                            st.plotly_chart(fig_api_usage, use_container_width=True)

                    elif selected_option_label == "Quota per API":
                        st.subheader(f"Quota Information and Trend for {tab_name}")
                        
                        quota_val = api_config.get("quota_daily", 0) 

                        if quota_val > 0:
                            st.info(f"**Configured Daily Quota:** {quota_val:,} calls")
                            st.info(f"**Cost per Call:** ${cost_per_call}")

                            current_daily_usage = calculate_current_daily_usage(df_api_filtered, tab_name)
                            remaining_quota = quota_val - current_daily_usage

                            col_metric_quota, col_graph_quota = st.columns([1, 3])
                            with col_metric_quota:
                                st.metric(label="Current Daily Usage", value=f"{current_daily_usage:,} calls")
                                st.metric(label="Remaining Daily Quota", value=f"{remaining_quota:,} calls")
                                if remaining_quota <= 0:
                                    st.error("Daily quota exceeded! Consider increasing the limit or optimizing usage.")
                                elif remaining_quota < quota_val * 0.2:
                                    st.warning("Daily quota is running low! Only 20% or less remaining.")
                                else:
                                    st.success("Daily quota is well within limits.")
                            
                            with col_graph_quota:
                                daily_usage_for_quota = calculate_daily_usage(df_api_filtered, tab_name, start_date=selected_start_date, end_date=selected_end_date)
                                daily_usage_dict = daily_usage_for_quota.set_index('Date')['Count'].to_dict()

                                all_dates_for_plot = pd.date_range(start=daily_usage_for_quota['Date'].min(), end=daily_usage_for_quota['Date'].max(), freq='D')
                                quota_trend_data = []
                                for date in all_dates_for_plot:
                                    usage = daily_usage_dict.get(date, 0)
                                    quota_trend_data.append({"Date": date, "Usage": usage, "Daily Quota": quota_val})

                                df_quota_trend = pd.DataFrame(quota_trend_data)
                                
                                fig_quota_trend = px.line(df_quota_trend, x="Date", y=["Usage", "Daily Quota"],
                                                            title=f"Daily Usage vs. Quota for {tab_name}", template="plotly_white")
                                fig_quota_trend.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Count")
                                st.plotly_chart(fig_quota_trend, use_container_width=True)

                        else:
                            st.warning("Daily quota information is not configured or is zero for this API. Quota trend graph cannot be displayed.")
                            st.info("Please set a positive 'quota_daily' in the API_CONFIGS for this API.")


                    elif selected_option_label == "Rate Limit per API":
                        st.subheader(f"Rate Limit Information and Trend for {tab_name}")
                        if rate_limit_per_second != "N/A":
                            st.info(f"**Configured Rate Limit:** {rate_limit_per_second} calls per second")
                            st.markdown("""
                            <p>The rate limit dictates the maximum number of requests allowed within a one-second window to prevent system overload and ensure fair usage. Adhering to this limit is crucial for stable API performance.</p>
                            """, unsafe_allow_html=True)
                            
                            end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            start_date = end_date - timedelta(days=29)
                            all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
                            
                            rate_limit_trend_data = []
                            for date in all_dates:
                                rate_limit_trend_data.append({"Date": date, "Rate Limit": rate_limit_per_second})
                            
                            df_rate_limit_trend = pd.DataFrame(rate_limit_trend_data)
                            
                            fig_rate_limit_trend = px.line(df_rate_limit_trend, x="Date", y="Rate Limit",
                                                            title=f"Configured Daily Rate Limit for {tab_name}", template="plotly_white")
                            fig_rate_limit_trend.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Calls per Second")
                            st.plotly_chart(fig_rate_limit_trend, use_container_width=True)

                        else:
                            st.warning("Rate limit information is not configured for this API.")
                            st.info("No rate limit trend graph can be displayed without a configured rate limit.")

                    elif selected_option_label == "Progress Bar":
                        st.subheader(f"Daily Usage Progress for {tab_name}")
                        
                        api_config = API_CONFIGS.get(tab_name, {})
                        quota_daily = api_config.get("quota_daily", 0)

                        if quota_daily > 0:
                            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            actual_current_daily_usage = 0
                            if not df_api_filtered.empty and 'api' in df_api_filtered.columns:
                                actual_current_daily_usage = df_api_filtered[(df_api_filtered["timestamp"] >= today_start)].shape[0]

                            if actual_current_daily_usage > 0:
                                current_daily_usage = actual_current_daily_usage
                                st.info("Displaying real-time usage progress from actual logs.")
                            else:
                                current_daily_usage = np.random.randint(0, quota_daily + 1)
                                st.info("No real-time usage data available for today. Displaying simulated progress.")

                            progress_percentage = min((current_daily_usage / quota_daily) * 100, 100)

                            st.metric(label="Usage Today / Daily Quota", value=f"{current_daily_usage:,} / {quota_daily:,}")
                            st.progress(progress_percentage / 100)

                            if progress_percentage >= 100:
                                st.error("Daily quota reached! No more calls can be made today without exceeding the limit.")
                            elif progress_percentage >= 80:
                                st.warning("Approaching daily quota limit! Usage is at 80% or more.")
                            else:
                                st.success("Daily usage is well within limits.")
                        else:
                            st.warning("Daily quota information is not configured or is zero for this API. Progress bar cannot be displayed.")
                            st.info("Please set a positive 'quota_daily' in the API_CONFIGS for this API.")

                    elif selected_option_label == "API Health":
                        st.subheader(f"Real-time Health Status for {tab_name}")
                        
                        status, icon, latency, error_rate = get_api_health(tab_name)
                        
                        status_color = "green"
                        if status == "warning": status_color = "orange"
                        if status == "critical": status_color = "red"

                        st.markdown(f"""
                        <div class="api-health-card">
                            <div class="health-icon">
                                <span style="font-size: 3.5rem; animation: pulse-{status_color} 1.5s infinite alternate;">{icon}</span>
                            </div>
                            <div class="health-details">
                                <p style="font-size: 1.5rem; font-weight: bold; color: {status_color}; text-transform: uppercase;">Status: {status}</p>
                                <p>Average Latency: <strong>{latency} ms</strong></p>
                                <p>Error Rate: <strong>{error_rate}%</strong></p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("This section simulates the real-time health of the API based on latency and error rates. Values change on each interaction.")

                    elif selected_option_label == "Cost Projection":
                        st.subheader(f"Projected Daily Cost for {tab_name}")

                        api_config = API_CONFIGS.get(tab_name, {})
                        cost_per_call = api_config.get("cost_per_call", 0)
                        
                        if cost_per_call > 0:
                            current_daily_usage = calculate_current_daily_usage(df_api_filtered, tab_name)
                            
                            hours_passed = (datetime.utcnow() - datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600
                            if hours_passed == 0: hours_passed = 0.1 # Avoid division by zero, min 0.1 hours
                            
                            projected_total_daily_calls = (current_daily_usage / hours_passed) * 24
                            projected_cost = projected_total_daily_calls * cost_per_call

                            col_proj_metric, col_proj_graph = st.columns([1, 3])
                            with col_proj_metric:
                                st.metric(label="Current Usage Today", value=f"{current_daily_usage:,} calls")
                                st.metric(label="Projected Total Calls Today", value=f"{int(projected_total_daily_calls):,}")
                                st.metric(label="Projected Daily Cost", value=f"${projected_cost:,.2f}")
                                if projected_cost > 100:
                                    st.warning("Projected daily cost is high! Monitor usage closely.")
                            
                            with col_proj_graph:
                                cost_data = pd.DataFrame({
                                    "Category": ["Current Cost", "Projected Additional Cost"],
                                    "Cost": [current_daily_usage * cost_per_call, (projected_total_daily_calls - current_daily_usage) * cost_per_call]
                                })
                                fig_cost_proj = px.bar(cost_data, x="Category", y="Cost", 
                                                        title=f"Cost Projection for {tab_name}",
                                                        color="Category",
                                                        color_discrete_map={"Current Cost": "#5b9bd5", "Projected Additional Cost": "#ff8a65"},
                                                        template="plotly_white")
                                fig_cost_proj.update_layout(showlegend=False, xaxis_title="", yaxis_title="Cost ($)",
                                                            hovermode="x unified")
                                st.plotly_chart(fig_cost_proj, use_container_width=True)

                        else:
                            st.warning("Cost per call is not configured for this API. Cost projection cannot be displayed.")

                    elif selected_option_label == "Error Breakdown": # Feature (4)
                        st.subheader(f"Error Status Code Breakdown for {tab_name}")
                        if not df_api_filtered.empty and 'status_code' in df_api_filtered.columns:
                            error_codes = df_api_filtered[df_api_filtered["status_code"] >= 400]
                            if not error_codes.empty:
                                error_counts = error_codes["status_code"].value_counts().reset_index()
                                error_counts.columns = ["Status Code", "Count"]
                                fig_errors = px.pie(error_counts, names="Status Code", values="Count", 
                                                    title=f"Error Status Codes for {tab_name}",
                                                    hole=0.4,
                                                    color_discrete_sequence=px.colors.sequential.RdBu)
                                fig_errors.update_traces(textinfo='percent+label', pull=[0.05]*len(error_counts))
                                st.plotly_chart(fig_errors, use_container_width=True)
                            else:
                                st.success(f"No error status codes (>=400) found for {tab_name} in the selected period. API is running perfectly!")
                                # Add some dummy error data if no errors are present in filtered logs
                                if np.random.rand() > 0.5: # 50% chance to show a dummy error if none exist
                                    dummy_error_data = pd.DataFrame({
                                        "Status Code": [400, 401, 500],
                                        "Count": [np.random.randint(5, 20), np.random.randint(2, 10), np.random.randint(1, 5)]
                                    })
                                    fig_errors_dummy = px.pie(dummy_error_data, names="Status Code", values="Count", 
                                                        title=f"Simulated Error Status Codes for {tab_name}",
                                                        hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                                    fig_errors_dummy.update_traces(textinfo='percent+label', pull=[0.05]*len(dummy_error_data))
                                    st.plotly_chart(fig_errors_dummy, use_container_width=True)

                        else:
                            st.info(f"No data available to show error breakdown for {tab_name}.")

                    elif selected_option_label == "Latency Distribution": # Feature (5)
                        st.subheader(f"API Latency Distribution for {tab_name}")
                        if not df_api_filtered.empty and 'latency_ms' in df_api_filtered.columns:
                            fig_latency = px.histogram(df_api_filtered, x="latency_ms", nbins=50, 
                                                    title=f"Latency Distribution for {tab_name}",
                                                    labels={"latency_ms": "Latency (ms)"},
                                                    template="plotly_white",
                                                    color_discrete_sequence=[px.colors.qualitative.Plotly[2]])
                            fig_latency.update_layout(bargap=0.1)
                            st.plotly_chart(fig_latency, use_container_width=True)
                            
                            st.markdown("<h4>Key Latency Percentiles:</h4>", unsafe_allow_html=True)
                            p50 = df_api_filtered['latency_ms'].quantile(0.5)
                            p90 = df_api_filtered['latency_ms'].quantile(0.9)
                            p99 = df_api_filtered['latency_ms'].quantile(0.99)
                            col_p50, col_p90, col_p99 = st.columns(3)
                            with col_p50: st.metric("50th Percentile (Median)", f"{p50:.1f} ms")
                            with col_p90: st.metric("90th Percentile", f"{p90:.1f} ms")
                            with col_p99: st.metric("99th Percentile", f"{p99:.1f} ms")
                        else:
                            st.info(f"No latency data available for {tab_name}.")

                    elif selected_option_label == "API Version Metrics": # Feature (7)
                        st.subheader(f"API Version Usage for {tab_name}")
                        if not df_api_filtered.empty and 'api_version' in df_api_filtered.columns:
                            version_counts = df_api_filtered["api_version"].value_counts().reset_index()
                            version_counts.columns = ["API Version", "Calls"]
                            fig_versions = px.bar(version_counts, x="API Version", y="Calls", 
                                                title=f"Usage by API Version for {tab_name}",
                                                color="API Version",
                                                template="plotly_white")
                            st.plotly_chart(fig_versions, use_container_width=True)
                            st.markdown(f"<p>Latest Version: <strong>{latest_version}</strong></p>", unsafe_allow_html=True)
                        else:
                            st.info(f"No API version data available for {tab_name}.")

                    elif selected_option_label == "Endpoint Metrics": # Feature (13)
                        st.subheader(f"Endpoint Usage for {tab_name}")
                        if not df_api_filtered.empty and 'endpoint' in df_api_filtered.columns:
                            endpoint_counts = df_api_filtered["endpoint"].value_counts().reset_index()
                            endpoint_counts.columns = ["Endpoint", "Calls"]
                            fig_endpoints = px.bar(endpoint_counts, x="Endpoint", y="Calls", 
                                                title=f"Usage by Endpoint for {tab_name}",
                                                color="Endpoint",
                                                template="plotly_white")
                            st.plotly_chart(fig_endpoints, use_container_width=True)
                        else:
                            st.info(f"No endpoint data available for {tab_name}.")


        elif tab_name == "Users": # Feature: User Profile/Management (1, 2)
            st.header("👤 User Management")

            user_tabs = st.tabs(["User List & API Keys", "Add New User"])

            with user_tabs[0]:
                st.markdown("<h3>Registered Users and Their API Keys</h3>", unsafe_allow_html=True)
                users_data = get_users()
                if users_data:
                    for user in users_data:
                        st.markdown(f"""
                        <div class="user-card">
                            <div class="user-header">
                                <h4>{user['user_id']} ({user.get('email', 'N/A')})</h4>
                                <span class="user-role">{user.get('role', 'N/A').upper()}</span>
                            </div>
                            <p>Last Login: <strong>{datetime.fromisoformat(user['last_login']).strftime('%Y-%m-%d %H:%M')}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Display API Keys for this user
                        user_api_keys = list(api_keys_collection.find({"user_id": user['user_id']}))
                        if user_api_keys:
                            st.markdown("<h5>Associated API Keys:</h5>", unsafe_allow_html=True)
                            key_data = []
                            for key in user_api_keys:
                                status_color = "green" if key['status'] == 'active' else "red"
                                key_data.append({
                                    "Key ID": key['key_id'],
                                    "API Key (partial)": f"{key['api_key'][:8]}...",
                                    "API": key['api'],
                                    "Created At": datetime.fromisoformat(key['created_at']).strftime('%Y-%m-%d'),
                                    "Expires At": datetime.fromisoformat(key['expires_at']).strftime('%Y-%m-%d'),
                                    "Status": f"<span style='color:{status_color}; font-weight:bold;'>{key['status'].upper()}</span>"
                                })
                            st.write(pd.DataFrame(key_data).to_html(escape=False), unsafe_allow_html=True)

                            # Actions on keys (if Admin)
                            if current_user_role == "Admin":
                                with st.expander(f"Manage API Keys for {user['user_id']}"):
                                    for key in user_api_keys:
                                        col_key_id, col_status_btn = st.columns([3, 1])
                                        with col_key_id:
                                            st.write(f"Key `{key['api_key'][:8]}...` for {key['api']} (Status: {key['status']})")
                                        with col_status_btn:
                                            if key['status'] == 'active':
                                                if st.button("🔴 Deactivate", key=f"deactivate_{key['key_id']}"):
                                                    update_api_key_status(key['key_id'], "inactive")
                                            else:
                                                if st.button("🟢 Activate", key=f"activate_{key['key_id']}"):
                                                    update_api_key_status(key['key_id'], "active")
                                            # Feature: API Key Rotation Reminders (2.4)
                                            expires_at = datetime.fromisoformat(key['expires_at'])
                                            if expires_at < datetime.utcnow() + timedelta(days=30) and key['status'] == 'active':
                                                st.warning(f"Key expires soon ({expires_at.strftime('%Y-%m-%d')})! Consider rotation.")
                                            elif expires_at < datetime.utcnow() and key['status'] == 'active':
                                                st.error("Key has expired! Please deactivate or rotate.")

                        else:
                            st.info(f"No API keys found for {user['user_id']}.")
                            if current_user_role == "Admin":
                                if st.button(f"Generate New Key for {user['user_id']}", key=f"gen_key_{user['user_id']}"):
                                    api_for_new_key = st.selectbox(f"Select API for new key for {user['user_id']}", list(API_CONFIGS.keys()))
                                    generate_api_key(user['user_id'], api_for_new_key)
                        st.markdown("---")
                else:
                    st.info("No registered users found. Add some dummy users if this is unexpected.")
                    if st.button("Generate Dummy Users (Admin Only)"):
                        st.warning("Switch to Admin role in sidebar to generate users.") # Remind user about role


            with user_tabs[1]:
                st.markdown("<h3>Create a New User Account</h3>", unsafe_allow_html=True)
                if current_user_role == "Admin":
                    with st.form("new_user_form"):
                        new_user_id = st.text_input("New User ID (e.g., username)", key="new_user_id_input")
                        new_user_email = st.text_input("User Email", key="new_user_email_input")
                        new_user_role = st.selectbox("User Role", ["developer", "admin", "viewer"], key="new_user_role_select")
                        submitted = st.form_submit_button("Add User")
                        if submitted:
                            if new_user_id and new_user_email:
                                users_collection.insert_one({
                                    "user_id": new_user_id,
                                    "email": new_user_email,
                                    "role": new_user_role,
                                    "last_login": datetime.utcnow().isoformat(),
                                    "created_at": datetime.utcnow().isoformat()
                                })
                                st.success(f"User {new_user_id} added successfully!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("User ID and Email are required.")
                else:
                    st.warning("You need 'Admin' role to add new users.")


        elif tab_name == "Admin Tools":
            st.header("⚙️ Admin Configuration & Tools")

            admin_sub_tabs = st.tabs(["API Key Generation", "Configurable Alerts", "Cost Allocation (Placeholder)"])

            with admin_sub_tabs[0]: # Feature: Generate API Keys (2.1)
                st.markdown("<h3>Generate New API Keys</h3>", unsafe_allow_html=True)
                if current_user_role == "Admin":
                    with st.form("generate_key_form"):
                        # Get current users to populate selectbox
                        all_users = get_users()
                        user_ids = [u['user_id'] for u in all_users]
                        key_user_id = st.selectbox("Select User for Key", user_ids + ["Create New User..."])
                        
                        new_user_for_key_input = None
                        if key_user_id == "Create New User...":
                            new_user_for_key_input = st.text_input("Enter New User ID for Key", key="new_user_for_key_input")

                        api_for_key_generation = st.selectbox("Select API for Key", list(API_CONFIGS.keys()), key="api_for_key_generation")
                        submitted_key_gen = st.form_submit_button("Generate Key")

                        if submitted_key_gen:
                            if key_user_id == "Create New User...":
                                if new_user_for_key_input:
                                    # Add the new user first
                                    users_collection.insert_one({
                                        "user_id": new_user_for_key_input, "email": f"{new_user_for_key_input}@example.com", 
                                        "role": "developer", "last_login": datetime.utcnow().isoformat(),
                                        "created_at": datetime.utcnow().isoformat()
                                    })
                                    generate_api_key(new_user_for_key_input, api_for_key_generation)
                                else:
                                    st.error("Please enter a user ID for the new user.")
                            else:
                                generate_api_key(key_user_id, api_for_key_generation)
                else:
                    st.warning("You need 'Admin' role to generate API keys.")

            with admin_sub_tabs[1]: # Feature: Configurable Alerts (9) & Anomaly Detection (10)
                st.markdown("<h3>Alert Configuration (Admin Only)</h3>", unsafe_allow_html=True)
                if current_user_role == "Admin":
                    st.info("Here, you would configure rules for alerts (e.g., email me if Image API error rate > 5%).")
                    st.write("Current Dummy Alerts:")
                    
                    st.markdown("""
                    <div class="alert-config-card">
                        <h5>High Error Rate Alert (Image API)</h5>
                        <p><strong>Condition:</strong> `Image API` error rate > `2.0%` for `5 minutes`</p>
                        <p><strong>Notification:</strong> Email to `admin@example.com`, Slack to `#alerts`</p>
                        <span class="alert-status-badge active">Active</span>
                    </div>
                    <div class="alert-config-card">
                        <h5>Quota Exceeded Alert (Video API)</h5>
                        <p><strong>Condition:</strong> `Video API` usage > `90%` of daily quota</p>
                        <p><strong>Notification:</strong> Email to `devteam@example.com`</p>
                        <span class="alert-status-badge active">Active</span>
                    </div>
                    <div class="alert-config-card inactive">
                        <h5>High Latency Alert (Weather API)</h5>
                        <p><strong>Condition:</strong> `Weather API` avg latency > `100ms` for `10 minutes`</p>
                        <p><strong>Notification:</strong> PagerDuty</p>
                        <span class="alert-status-badge">Inactive</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<h3>Anomaly Detection Status</h3>", unsafe_allow_html=True)
                    # Simulate anomaly detection based on random chance
                    if np.random.rand() < 0.2: # 20% chance of an anomaly
                        st.error("🚨 Anomaly Detected: Unusual spike in `Ecommerce API` calls from a new region (China) at 02:30 AM IST. Investigate immediately!")
                    else:
                        st.success("✅ No major anomalies detected recently.")
                else:
                    st.warning("You need 'Admin' role to configure alerts or view anomaly details.")

            with admin_sub_tabs[2]: # Feature: Cost Allocation (15)
                st.markdown("<h3>Cost Allocation (Placeholder)</h3>", unsafe_allow_html=True)
                st.info("This section would allow configuration and visualization of API costs attributed to different departments, projects, or teams.")
                st.markdown("""
                <div class="placeholder-card">
                    <p>Imagine graphs and tables breaking down costs by:</p>
                    <ul>
                        <li>Department (e.g., Marketing, Engineering, Sales)</li>
                        <li>Project (e.g., Mobile App v1, Web Platform v2)</li>
                        <li>Cost Centers</li>
                    </ul>
                    <p>Requires additional data points in logs (e.g., `department_id`, `project_id`).</p>
                </div>
                """, unsafe_allow_html=True)


        elif tab_name == "Changelog": # Feature: API Changelog (11)
            st.header("📜 API Changelog & Version History")
            st.info("This section provides a history of changes and updates across all APIs.")

            changelogs = {
                "Image API": [
                    {"version": "v2.1", "date": "2025-06-15", "changes": "Improved image processing algorithm, reduced latency by 10%."},
                    {"version": "v2.0", "date": "2025-05-01", "changes": "Major update: New `/process` endpoint, deprecated `/old_process`. Improved stability."},
                    {"version": "v1.0", "date": "2024-11-20", "changes": "Initial release."}
                ],
                "Video API": [
                    {"version": "v1.5", "date": "2025-04-10", "changes": "Added support for MP4 format. Bug fixes for streaming."},
                    {"version": "v1.2", "date": "2025-02-01", "changes": "Enhanced metadata extraction."},
                    {"version": "v1.0", "date": "2024-12-05", "changes": "Initial release."}
                ],
                "Weather API": [
                    {"version": "v3.0", "date": "2025-06-01", "changes": "Migrated to new data source, improved accuracy. New historical data endpoint."},
                    {"version": "v2.1", "date": "2025-03-20", "changes": "Minor bug fixes and performance improvements."},
                    {"version": "v2.0", "date": "2024-10-10", "changes": "Major overhaul, new `forecast` endpoint introduced."},
                ],
                "Ecommerce API": [
                    {"version": "v2.3", "date": "2025-05-20", "changes": "Optimized product search API for faster results."},
                    {"version": "v2.2", "date": "2025-03-01", "changes": "Introduced new `/checkout` endpoint for streamlined purchases."},
                    {"version": "v2.0", "date": "2024-11-15", "changes": "Initial release of full e-commerce suite."}
                ],
                "QR Code API": [
                    {"version": "v1.2", "date": "2025-04-05", "changes": "Added support for various QR code types."},
                    {"version": "v1.0", "date": "2025-01-10", "changes": "Initial release."},
                ],
                "Profile Photo API": [
                    {"version": "v2.0", "date": "2025-05-10", "changes": "Improved image resizing and cropping features."},
                    {"version": "v1.0", "date": "2024-12-20", "changes": "Initial release."}
                ],
                "Jokes API": [
                    {"version": "v1.0", "date": "2025-02-14", "changes": "Initial release with various joke categories."}
                ]
            }

            for api, entries in changelogs.items():
                st.markdown(f"<h3>{api} Changelog</h3>", unsafe_allow_html=True)
                for entry in entries:
                    st.markdown(f"""
                    <div class="changelog-entry">
                        <div class="version-date">
                            <span class="version-tag">{entry['version']}</span>
                            <span class="change-date">{entry['date']}</span>
                        </div>
                        <p>{entry['changes']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")


st.markdown("---")

# --- Open Support Tickets (Always at the bottom) ---
st.subheader("📊 Support Tickets")

support_tab_titles = ["Open Tickets", "Closed Tickets"]
support_tabs = st.tabs(support_tab_titles)

with support_tabs[0]:
    st.markdown("<h3>Currently Active Support Requests</h3>", unsafe_allow_html=True)
    open_tickets = list(tickets_collection.find({"status": "open"}))

    if open_tickets:
        for ticket in open_tickets:
            created_at = datetime.fromisoformat(ticket["created_at"])
            ticket["hours_open"] = round((datetime.utcnow() - created_at).total_seconds() / 3600, 2)
        
        open_tickets_sorted = sorted(open_tickets, key=lambda x: x["hours_open"], reverse=True)

        for ticket in open_tickets_sorted:
            border_color = "#7cb342"
            if ticket["hours_open"] > 24:
                border_color = "#ff8a65"
            if ticket["hours_open"] > 72:
                border_color = "#ef5350"

            st.markdown(f"""
            <div class="ticket-card" style="border-left: 8px solid {border_color};">
                <div class="ticket-header">
                    <span class="ticket-id">Ticket ID: <code>{ticket['_id']}</code></span>
                    <span class="ticket-aging">Aging: <strong>{ticket['hours_open']} hours</strong></span>
                </div>
                <p><strong>Query:</strong> {ticket['query']}</p>
                <p><strong>Contact:</strong> {ticket.get('contact', 'anonymous')}</p>
                <p><strong>Status:</strong> <span class="status-open">OPEN</span></p>
                <div class="ticket-button-container">
                    <!-- Only one Streamlit button, styled with CSS -->
                </div>
            </div>
            """, unsafe_allow_html=True)
            # This is the *single* Streamlit button. The CSS below will style it red.
            if st.button("Close Ticket", key=f"close_btn_{ticket['_id']}", use_container_width=True):
                tickets_collection.update_one({"_id": ticket["_id"]}, {"$set": {"status": "closed", "closed_at": datetime.utcnow().isoformat()}})
                st.success(f"Ticket #{ticket['_id']} closed successfully!")
                st.rerun()

    else:
        st.info("🎉 No open support tickets at the moment. All clear!")

with support_tabs[1]:
    st.markdown("<h3>Recently Closed Support Requests</h3>", unsafe_allow_html=True)
    closed_tickets = list(tickets_collection.find({"status": "closed"}).sort("closed_at", -1).limit(20))

    if closed_tickets:
        for ticket in closed_tickets:
            closed_at_str = ticket.get("closed_at", datetime.utcnow().isoformat())
            closed_at = datetime.fromisoformat(closed_at_str)
            
            st.markdown(f"""
            <div class="ticket-card closed-ticket">
                <div class="ticket-header">
                    <span class="ticket-id">Ticket ID: <code>{ticket['_id']}</code></code></span>
                    <span class="ticket-aging">Closed: <strong>{closed_at.strftime('%Y-%m-%d %H:%M')}</strong></span>
                </div>
                <p><strong>Query:</strong> {ticket['query']}</p>
                <p><strong>Contact:</strong> {ticket.get('contact', 'anonymous')}</p>
                <p><strong>Status:</strong> <span class="status-closed">CLOSED</span></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No closed support tickets found.")

# --- Custom CSS for a stunning UI ---
st.markdown("""
<style>
    /* Overall App Styling */
    .stApp {
        background-color: #000000; /* Solid Black Background */
        color: #e0e6f0; /* Soft white/light grey text */
        font-family: 'Inter', sans-serif; /* Modern font */
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Main Title */
    h1 {
        color: #5b9bd5; /* Steel Blue for title */
        text-align: center;
        padding-bottom: 25px;
        border-bottom: 2px solid #4a6078; /* Clean separator */
        margin-bottom: 50px;
        font-size: 3.2rem; /* Larger font size */
        letter-spacing: 1.5px; /* Spacing for a cleaner look */
        font-weight: 700; /* Bold title */
        text-shadow: 0px 0px 10px rgba(91, 155, 213, 0.4); /* Subtle glow */
    }

    /* Subheaders */
    h2, h3, h4, h5, h6 {
        color: #ab47bc; /* Amethyst */
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        border-left: 6px solid #7cb342; /* Lime Green accent border */
        padding-left: 18px;
        font-weight: 600; /* Semi-bold */
        letter-spacing: 0.8px;
        opacity: 0; /* Initial state for animation */
        transform: translateY(20px); /* Initial state for animation */
        animation: fadeInSlideUp 0.8s ease-out forwards; /* Apply animation */
    }
    h2 { font-size: 2.3rem; }
    h3 { font-size: 1.9rem; }
    h4 { font-size: 1.6rem; color: #5b9bd5; margin-bottom: 1rem; } /* Reverted h4 color to blue for contrast */
    h5 { font-size: 1.3rem; color: #7cb342; margin-bottom: 0.8rem; }


    /* Keyframe for fade-in slide up */
    @keyframes fadeInSlideUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Buttons */
    .stButton>button {
        background-color: red; /* Lime Green */
        color: #1a1a1a; /* Dark text for contrast */
        border-radius: 10px;
        border: none;
        padding: 14px 30px;
        font-size: 1.15rem;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease; /* Bouncier transform */
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.15); /* Soft 3D */
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background-color: orange; 
        transform: translateY(-5px) scale(1.03); /* More lift and scale */
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), inset 0 1px 4px rgba(255, 255, 255, 0.2);
    }
    .stButton>button:active {
        transform: translateY(1px) scale(0.97); /* Deeper press */
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2), inset 0 1px 3px rgba(255, 255, 255, 0.08);
    }

    /* Close Ticket Button specific styling */
    .stButton button[key*="close_btn_"] { /* Target close ticket buttons by key prefix */
        background-color: #ef5350 !important; /* Red color */
        color: white !important;
        border: none;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
    }
    .stButton button[key*="close_btn_"]:hover {
        background-color: #c62828 !important; /* Darker red on hover */
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
    }
    .stButton button[key*="close_btn_"]:active {
        transform: translateY(1px) !important;
        box_shadow: 0 1px 4px rgba(0, 0, 0, 0.1) !important;
    }


    /* Generic link button style (for Docs link) */
    .button-link {
        display: inline-block;
        background-color: #4a4a4a; /* Changed blue to dark grey */
        color: white !important; /* Important to override default link color */
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        transition: background-color 0.3s, transform 0.2s;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
    }
    .button-link:hover {
        background-color: #333333; /* Darker grey on hover */
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4);
    }

    /* Top-level Tabs (API Navigation) - For main API tabs AND now for metrics tabs */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: flex-start; /* Align tabs to start (left) */
        gap: 20px; /* Consistent gap between tabs */
        padding-bottom: 25px;
        border-bottom: 2px solid #4a6078;
        margin-bottom: 40px;
        overflow-x: auto; /* Enable horizontal scrolling */
        white-space: nowrap; /* Prevent tabs from wrapping */
        -webkit-overflow-scrolling: touch; /* Smoother scrolling on touch devices */
        padding-top: 10px;
        padding-left: 20px; /* Crucial: Add sufficient left padding to reveal clipped content */
        padding-right: 20px; /* Add right padding for consistency */
    }

    /* Style the scrollbar for tabs */
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        height: 10px; /* Thicker scrollbar */
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
        background: #1a1a1a; /* Black track */
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        background: #4a4a4a; /* Dark grey thumb */
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover {
        background: #333333; /* Even darker grey on hover */
    }

    .stTabs [data-baseweb="tab"] {
        padding: 16px 28px;
        border-radius: 15px;
        transition: background-color 0.3s, color 0.3s, box-shadow 0.3s, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        font-weight: 600;
        color: #b0c4de;
        background-color: #2b3e50;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.1);
        border: 1px solid #4a6078;
        flex-shrink: 0;
        animation: tabFadeIn 0.5s ease-out forwards;
        opacity: 0;
    }
    /* Add animation delay for each tab */
    .stTabs [data-baseweb="tab"]:nth-child(1) { animation-delay: 0.1s; }
    .stTabs [data-baseweb="tab"]:nth-child(2) { animation-delay: 0.2s; }
    .stTabs [data-baseweb="tab"]:nth-child(3) { animation-delay: 0.3s; }
    .stTabs [data-baseweb="tab"]:nth-child(4) { animation-delay: 0.4s; }
    .stTabs [data-baseweb="tab"]:nth-child(5) { animation-delay: 0.5s; }
    .stTabs [data-baseweb="tab"]:nth-child(6) { animation-delay: 0.6s; }
    .stTabs [data-baseweb="tab"]:nth-child(7) { animation-delay: 0.7s; }
    .stTabs [data-baseweb="tab"]:nth-child(8) { animation-delay: 0.8s; }
    .stTabs [data-baseweb="tab"]:nth-child(9) { animation-delay: 0.9s; }
    .stTabs [data-baseweb="tab"]:nth-child(10) { animation-delay: 1.0s; } /* For new tabs */
    .stTabs [data-baseweb="tab"]:nth-child(11) { animation-delay: 1.1s; }
    .stTabs [data-baseweb="tab"]:nth-child(12) { animation-delay: 1.2s; }


    @keyframes tabFadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #3d5a73;
        color: #e0e6f0;
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.2);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #5b9bd5; /* Keep blue for selected tab background */
        color: white;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), inset 0 2px 5px rgba(255, 255, 255, 0.3);
        border: 1px solid #5b9bd5;
        transform: translateY(-3px);
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0;
    }

    /* Adjustments for the new metric tabs - inherit from stTabs styles now */
    /* The `stRadio` specific styles are removed as it's no longer a radio group */
    /* The .stRadio > label will still apply to the "Select a metric" H4 if it were there,
       but now it's a direct H4 which will inherit its styling from the H4 rule */
    /* No special overrides needed for scrollability on the metric tabs themselves,
       as they will now correctly use the .stTabs [data-baseweb="tab-list"] styling */


    /* Alerts */
    .stAlert {
        border-radius: 12px;
        padding: 20px 25px;
        font-size: 1.05rem;
        margin-top: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        animation: fadeIn 0.5s ease-out forwards;
    }
    .stAlert.st-success { background-color: #1e3a24; border-left: 8px solid #7cb342; }
    .stAlert.st-info { background-color: #1e2e3a; border-left: 8px solid #4a4a4a; } /* Changed blue to dark grey for info alerts */
    .stAlert.st-warning { background-color: #3a321e; border-left: 8px solid #ff8a65; }
    .stAlert.st-error { background-color: #3a1e1e; border-left: 8px solid #ef5350; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    /* Metrics (KPIs) with dynamic values and subtle animation */
    .stMetric > div {
        background-color: #101115; /* Updated to new color #101115 */
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        overflow: hidden;
    }
    .stMetric > div:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5), inset 0 1px 4px rgba(255, 255, 255, 0.2);
    }
    .stMetric > div > div:first-child {
        font-size: 1.25rem;
        color: #b0c4de;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .stMetric > div > div:last-child {
        font-size: 3.2rem;
        font-weight: 700;
        color: #e0e6f0;
        text-shadow: 1px 1px 5px rgba(0,0,0,0.5);
        animation: valueFadeInUp 0.6s ease-out;
    }
    @keyframes valueFadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Plotly chart container */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #4a6078;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
        margin-top: 25px;
        animation: fadeInScale 0.7s ease-out forwards;
        opacity: 0;
        transform: scale(0.98);
    }
    @keyframes fadeInScale {
        to { opacity: 1; transform: scale(1); }
    }

    /* Streamlit dataframes */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #4a6078;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
        margin-top: 25px;
    }
    .stDataFrame table {
        color: #e0e6f0;
        background-color: #2b3e50;
    }
    .stDataFrame th {
        background-color: #3d5a73 !important;
        color: #b0c4de !important;
        font-weight: bold;
        border-bottom: 1px solid #4a6078;
    }
    .stDataFrame td {
        background-color: #101115 !important;
        color: #e0e6f0 !important;
        border-bottom: 1px solid rgba(74, 96, 120, 0.2);
    }

    /* General text/paragraph styling */
    p {
        font-size: 1.05rem;
        line-height: 1.7;
        color: #e0e6f0;
    }
    b, strong {
        color: #e0e6f0;
    }
    code {
        background-color: #3d5a73;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 0.95rem;
        color: #b0c4de;
        font-family: 'Fira Code', 'Cascadia Code', monospace;
        font-weight: normal;
    }

    /* Horizontal Rule */
    hr {
        border-top: 3px solid #4a6078;
        margin-top: 3.5rem;
        margin-bottom: 3.5rem;
    }

    /* Support Ticket Cards */
    .ticket-card {
        background-color: #101115;
        border: 1px solid #4a6078;
        border-radius: 12px;
        padding: 20px 25px;
        margin-bottom: 20px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3), inset 0 1px 3px rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        animation: ticketSlideIn 0.6s ease-out forwards;
        opacity: 0;
        transform: translateX(-20px);
    }
    .ticket-card:nth-child(1) { animation-delay: 0.1s; }
    .ticket-card:nth-child(2) { animation-delay: 0.2s; }
    .ticket-card:nth-child(3) { animation-delay: 0.3s; }
    .ticket-card:nth-child(4) { animation-delay: 0.4s; }

    @keyframes ticketSlideIn {
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .ticket-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4), inset 0 1px 4px rgba(255, 255, 255, 0.15);
    }

    .ticket-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(74, 96, 120, 0.3);
    }

    .ticket-id {
        font-size: 1.1rem;
        font-weight: 600;
        color: #b0c4de;
    }
    .ticket-id code {
        background-color: #3d5a73;
        color: #b0c4de;
        padding: 2px 6px;
        border-radius: 4px;
    }

    .ticket-aging {
        font-size: 0.95rem;
        color: #e0e6f0;
    }
    .ticket-aging strong {
        color: #ff8a65;
    }

    .ticket-card p {
        margin-bottom: 0.8em;
    }

    .status-open {
        color: #7cb342;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.95rem;
    }
    .status-closed {
        color: #5b9bd5;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.95rem;
    }

    .closed-ticket {
        opacity: 0.7;
        filter: grayscale(20%);
        border-left: 8px solid #5b9bd5 !important;
    }

    .ticket-button-container {
        margin-top: 15px;
        text-align: right;
    }

    /* API Health Card Styling and Animations */
    .api-health-card {
        display: flex;
        align-items: center;
        background-color: #101115;
        border-radius: 12px;
        padding: 25px 30px;
        margin-top: 25px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4), inset 0 1px 3px rgba(255, 255, 255, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fadeIn 0.8s ease-out forwards;
        opacity: 0;
    }
    .api-health-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5), inset 0 1px 4px rgba(255, 255, 255, 0.2);
        background-color: #1A1C1A;
    }

    .health-icon {
        margin-right: 25px;
        line-height: 1;
    }

    .health-details p {
        margin: 0;
        padding: 0;
        line-height: 1.5;
        font-size: 1.1rem;
    }
    .health-details strong {
        font-size: 1.2rem;
    }

    /* Pulse animations for health icons */
    @keyframes pulse-green {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    @keyframes pulse-orange {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.15); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    @keyframes pulse-red {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.6; }
        100% { transform: scale(1); opacity: 1; }
    }

    /* User Card Styling */
    .user-card {
        background-color: #101115;
        border: 1px solid #4a6078;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    .user-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        background-color: #1A1C1A;
    }
    .user-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(74, 96, 120, 0.3);
    }
    .user-header h4 {
        margin: 0;
        color: #5b9bd5;
        font-size: 1.4rem;
    }
    .user-role {
        background-color: #ab47bc;
        color: white;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .user-card p {
        margin-bottom: 0.5em;
    }

    /* Alert Config Card Styling */
    .alert-config-card {
        background-color: #101115;
        border: 1px solid #4a6078;
        border-left: 8px solid #ab47bc; /* Amethyst accent */
        border-radius: 12px;
        padding: 20px 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    .alert-config-card.inactive {
        opacity: 0.6;
        border-left: 8px solid #4a6078; /* Grey accent for inactive */
    }
    .alert-config-card h5 {
        margin-top: 0;
        color: #7cb342;
        font-size: 1.3rem;
    }
    .alert-config-card p {
        margin-bottom: 0.5em;
    }
    .alert-status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 5px;
        font-size: 0.85rem;
        font-weight: bold;
        text-transform: uppercase;
        margin-top: 10px;
        background-color: #ff8a65; /* Default for inactive/general */
        color: #1a1a1a;
    }
    .alert-status-badge.active {
        background-color: #7cb342;
    }

    /* Placeholder Card */
    .placeholder-card {
        background-color: #101115;
        border: 1px solid #4a6078;
        border-radius: 12px;
        padding: 20px 25px;
        margin-top: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .placeholder-card ul {
        list-style-type: disc;
        margin-left: 20px;
        padding-left: 0;
    }
    .placeholder-card li {
        margin-bottom: 5px;
        color: #e0e6f0;
    }

    /* Changelog Entry */
    .changelog-entry {
        background-color: #101115;
        border: 1px solid #4a6078;
        border-left: 8px solid #4a4a4a; /* Changed blue accent to dark grey */
        border-radius: 12px;
        padding: 20px 25px;
        margin-bottom: 15px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        animation: fadeIn 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(10px);
    }
    .changelog-entry:nth-child(odd) { animation-delay: 0.1s; }
    .changelog-entry:nth-child(even) { animation-delay: 0.2s; }
    .changelog-entry .version-date {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .changelog-entry .version-tag {
        background-color: #ab47bc;
        color: white;
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.9em;
        margin-right: 15px;
    }
    .changelog-entry .change-date {
        color: #b0c4de;
        font-size: 0.95em;
    }
    .changelog-entry p {
        margin: 0;
        font-size: 1em;
        color: #e0e6f0;
    }

    /* Streamlit Date Input specific styling */
    .stDateInput > label {
        color: #ab47bc; /* Match subheader color */
        font-weight: bold;
        font-size: 1.25rem;
        margin-bottom: 15px;
    }
    .stDateInput [data-baseweb="input"] {
        background-color: #2b3e50;
        color: #e0e6f0;
        border: 1px solid #4a6078;
        border-radius: 8px;
        padding: 8px 12px;
    }
    .stDateInput [data-baseweb="input"] input {
        color: #e0e6f0;
    }
    .stDateInput [data-baseweb="button"] { /* Calendar icon button */
        background-color: #3d5a73;
        color: #b0c4de;
        border-radius: 8px;
    }
    .stDateInput [data-baseweb="button"]:hover {
        background-color: #4a6078;
    }
    
    /* New CSS rule for the API Info Display Card */
    .api-info-display-card {
        background-color: #101115; /* The requested color */
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #4a6078; /* Added a subtle border */
    }

    :root {
        --primary-font: 'Inter', sans-serif;
        --background-color: #000000; /* THIS LINE */
        --secondary-background-color: #1a1a1a;
        /* ... other variables ... */
    }

</style>
""", unsafe_allow_html=True)
