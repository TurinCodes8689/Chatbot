import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import numpy as np # For generating more complex dummy data

# Load environment variables
load_dotenv()

# MongoDB Connection
# Use st.secrets for deployment on Streamlit Cloud, otherwise os.getenv
mongo_uri = os.getenv("MONGODB_URI") # For local testing
# mongo_uri = st.secrets["MONGODB_URI"] # Uncomment for Streamlit Cloud deployment

try:
    client = MongoClient(mongo_uri)
    db = client["apiman"]
    logs_collection = db["api_usage_logs"]
    tickets_collection = db["support_tickets"]
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop() # Stop the app if DB connection fails


st.set_page_config(layout="wide", page_title="API Admin Dashboard", initial_sidebar_state="collapsed") # Wide layout, no sidebar

# --- Configuration for APIs (You might move this to a DB for dynamic management) ---
# Ensure every API has a valid quota_daily to prevent "Quota info not available" messages
API_CONFIGS = {
    "Image API": {
        "cost_per_call": 0.002,
        "quota_daily": 10000, # Example daily quota
        "rate_limit_per_second": 10
    },
    "Video API": {
        "cost_per_call": 0.001, # Set a cost for consistency if desired
        "quota_daily": 5000,
        "rate_limit_per_second": 5
    },
    "Weather API": {
        "cost_per_call": 0.0005, # Set a cost for consistency if desired
        "quota_daily": 20000,
        "rate_limit_per_second": 20
    },
    "Ecommerce API": {
        "cost_per_call": 0.001,
        "quota_daily": 15000,
        "rate_limit_per_second": 15
    },
    "QR Code API": {
        "cost_per_call": 0.001,
        "quota_daily": 8000,
        "rate_limit_per_second": 8
    },
    "Profile Photo API": {
        "cost_per_call": 0.001,
        "quota_daily": 7000,
        "rate_limit_per_second": 7
    },
    "Jokes API": {
        "cost_per_call": 0.001,
        "quota_daily": 25000,
        "rate_limit_per_second": 25
    }
}


# --- Helper Functions ---
@st.cache_data(ttl=3600) # Cache data for an hour to reduce DB calls
def get_api_logs():
    return list(logs_collection.find())

def calculate_daily_usage(df, api_name, include_dummy_trend=True):
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=29) # Last 30 days including today
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    df_api = pd.DataFrame()
    if 'api' in df.columns: # Check if 'api' column exists in the main DataFrame
        df_api = df[df["api"] == api_name]

    if not df_api.empty:
        df_daily = df_api.groupby(pd.Grouper(key="timestamp", freq="D")).size().reset_index(name="Count")
        df_daily.columns = ["Date", "Count"]
        full_df = pd.DataFrame(all_dates, columns=["Date"])
        daily_usage = pd.merge(full_df, df_daily, on="Date", how="left").fillna(0)
    elif include_dummy_trend: # If no logs for this API and dummy trend is requested
        # Generate dummy trend data for 30 days
        dummy_counts = []
        base_value = API_CONFIGS.get(api_name, {}).get("quota_daily", 1000) / 10 # A tenth of quota as base
        if base_value == 0: base_value = 100 # Avoid zero base for APIs with 0 cost
        
        # Create a more varied dummy trend
        for day_idx in range(len(all_dates)):
            # Simple sinusoidal pattern + randomness for a trend
            trend_factor = np.sin(day_idx / 5) * (base_value / 2) # Fluctuations
            random_noise = np.random.normal(0, base_value / 4) # Noise
            count = max(0, int(base_value + trend_factor + random_noise)) # Ensure non-negative
            dummy_counts.append(count)
            
        daily_usage = pd.DataFrame({"Date": all_dates, "Count": dummy_counts})
    else:
        return pd.DataFrame(columns=["Date", "Count"]) # Return empty if no logs and no dummy trend requested
        
    return daily_usage


def calculate_current_daily_usage(df, api_name):
    # Ensure df has 'api' column before filtering
    if 'api' not in df.columns or df.empty:
        return 0 # No logs or no api column means 0 usage

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    current_day_usage = df[(df["api"] == api_name) & (df["timestamp"] >= today_start)].shape[0]
    return current_day_usage

# --- Streamlit UI ---

st.title("🚀 API Management Dashboard")

# Load all logs once
log_data = get_api_logs()
df_logs = pd.DataFrame()

# Define expected columns for the DataFrame
# Ensure 'api' and 'timestamp' are always present for logic to work
expected_log_columns = ["api", "timestamp", "user_id", "status_code"] # Add other columns present in your logs if any

if log_data:
    df_logs = pd.DataFrame(log_data)
    # Ensure 'timestamp' column is datetime
    if 'timestamp' in df_logs.columns:
        df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"])
    else:
        st.warning("Logs found but 'timestamp' column is missing. Some features may not work correctly.")
        # If timestamp is missing, create a dummy one for existing rows, defaulting to today
        df_logs['timestamp'] = datetime.utcnow()
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp']) # Ensure it's datetime type
        

    # Check for missing expected columns and add them if they don't exist
    for col in expected_log_columns:
        if col not in df_logs.columns:
            st.warning(f"Logs found but '{col}' column is missing. Adding a default placeholder column.")
            # Add the missing column with a default/placeholder value
            if col == 'api':
                df_logs[col] = "unknown_api"
            elif col == 'user_id':
                df_logs[col] = "unknown_user"
            elif col == 'status_code':
                df_logs[col] = 200 # Default to success
            else:
                df_logs[col] = None # Or an appropriate default
else:
    # Create an empty DataFrame with the expected columns if no logs are found
    df_logs = pd.DataFrame(columns=expected_log_columns)
    # Add a dummy timestamp column, initialized as empty but with datetime dtype
    df_logs['timestamp'] = pd.Series(dtype='datetime64[ns]')


st.markdown("   ")

# --- Top-Level API Navigation (Horizontal Tabs) ---
# Add "Overview" as a default tab to see aggregated info
api_tabs_list = ["Overview"] + sorted(list(API_CONFIGS.keys()))
selected_api_tab = st.tabs(api_tabs_list)

# Iterate through each tab to display content
for i, api_name_in_tab in enumerate(api_tabs_list):
    with selected_api_tab[i]:
        if api_name_in_tab == "Overview":
            st.subheader("Overall API Usage Summary")
            
            # Check if df_logs has an 'api' column and is not truly empty (meaning no logs at all)
            if not df_logs.empty and 'api' in df_logs.columns and df_logs['api'].any(): # .any() checks if there's any non-NaN api name
                api_counts = df_logs["api"].value_counts().reset_index()
                api_counts.columns = ["API", "Calls"]
                api_counts["Cost ($)"] = api_counts.apply(
                    lambda row: round(row["Calls"] * API_CONFIGS.get(row["API"], {}).get("cost_per_call", 0), 3), axis=1
                )
                st.dataframe(api_counts, use_container_width=True)

                st.subheader("API Usage Over Time (All APIs Combined)")
                df_daily_all = df_logs.groupby([pd.Grouper(key="timestamp", freq="D"), "api"]).size().reset_index(name="Count")
                
                # Check if df_daily_all is actually populated with real log data
                if not df_daily_all.empty and df_daily_all['Count'].sum() > 0:
                    fig_all_usage = px.line(df_daily_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)")
                    fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                    st.plotly_chart(fig_all_usage, use_container_width=True)
                else:
                    # Generate realistic dummy data for combined usage if no real logs or all counts are zero
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
                    fig_all_usage = px.line(df_dummy_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)")
                    fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                    st.plotly_chart(fig_all_usage, use_container_width=True)


            else:
                # st.warning("No API usage data available for the overview. Displaying dummy overview data.")
                # Display dummy data for API counts if df_logs is empty or missing 'api' column
                dummy_api_counts = pd.DataFrame({
                    "API": list(API_CONFIGS.keys()),
                    "Calls": [np.random.randint(500, 5000) for _ in API_CONFIGS], # Random calls
                    "Cost ($)": [round(np.random.rand() * 10, 2) for _ in API_CONFIGS] # Random cost
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
                fig_all_usage = px.line(df_dummy_all, x="timestamp", y="Count", color="api", title="Daily API Usage (All APIs Combined)")
                fig_all_usage.update_layout(hovermode="x unified", legend_title_text='API')
                st.plotly_chart(fig_all_usage, use_container_width=True)

        else:
            # Content for individual API tabs
            st.header(f"📊 {api_name_in_tab} - Detailed Monitoring")
            api_config = API_CONFIGS.get(api_name_in_tab, {})
            quota_daily = api_config.get("quota_daily", "N/A") # Default to N/A for display purposes if not explicitly set
            rate_limit_per_second = api_config.get("rate_limit_per_second", "N/A")
            cost_per_call = api_config.get("cost_per_call", "N/A")

            # Second-level navigation (radio buttons for sub-options)
            selected_option = st.radio(
                "Select a metric:",
                ["Usage per API", "Quota per API", "Rate Limit per API", "Progress Bar"],
                key=f"option_{api_name_in_tab}",
                horizontal=True
            )

            st.markdown("---") # Separator below radio buttons

            # Conditional display based on selected option
            if selected_option == "Usage per API":
                st.subheader(f"Daily API Usage Trend for {api_name_in_tab}")
                
                # Pass df_logs and api_name_in_tab to calculate_daily_usage, now it handles dummy trends
                daily_usage_df = calculate_daily_usage(df_logs, api_name_in_tab, include_dummy_trend=True)
                
                # Calculate total calls from actual logs if available, otherwise from the dummy data sum
                total_calls = df_logs[df_logs["api"] == api_name_in_tab].shape[0] if not df_logs.empty and 'api' in df_logs.columns else daily_usage_df['Count'].sum()

                col_metric, col_graph = st.columns([1, 3])
                with col_metric:
                    st.metric(label=f"Total Calls for {api_name_in_tab} (Last 30 Days)", value=f"{total_calls:,}")
                    st.write("This graph shows the daily number of API calls over the last 30 days.")
                with col_graph:
                    fig_api_usage = px.line(daily_usage_df, x="Date", y="Count",
                                             title=f"Daily API Usage for {api_name_in_tab} (Last 30 Days)")
                    fig_api_usage.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Number of Calls")
                    st.plotly_chart(fig_api_usage, use_container_width=True)

            elif selected_option == "Quota per API":
                st.subheader(f"Quota Information and Trend for {api_name_in_tab}")
                
                # Retrieve quota again, defaulting to 0 for calculations if not set
                quota_val = api_config.get("quota_daily", 0) 

                if quota_val > 0: # Ensure a valid, positive quota exists
                    st.info(f"**Configured Daily Quota:** {quota_val:,} calls")
                    st.info(f"**Cost per Call:** ${cost_per_call}")

                    current_daily_usage = calculate_current_daily_usage(df_logs, api_name_in_tab)
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
                        # Generate data for quota trend graph
                        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                        start_date = end_date - timedelta(days=29)
                        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
                        
                        quota_trend_data = []
                        
                        # Get actual daily usage (if any) or dummy trend data
                        daily_usage_for_quota = calculate_daily_usage(df_logs, api_name_in_tab, include_dummy_trend=True)
                        daily_usage_dict = daily_usage_for_quota.set_index('Date')['Count'].to_dict()

                        for date in all_dates:
                            usage = daily_usage_dict.get(date, 0) # Use the dummy or actual usage
                            quota_trend_data.append({"Date": date, "Usage": usage, "Daily Quota": quota_val})

                        df_quota_trend = pd.DataFrame(quota_trend_data)
                        
                        fig_quota_trend = px.line(df_quota_trend, x="Date", y=["Usage", "Daily Quota"],
                                                     title=f"Daily Usage vs. Quota for {api_name_in_tab}")
                        fig_quota_trend.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Count")
                        st.plotly_chart(fig_quota_trend, use_container_width=True)

                else:
                    st.warning("Daily quota information is not configured or is zero for this API. Quota trend graph cannot be displayed.")
                    st.info("Please set a positive 'quota_daily' in the API_CONFIGS for this API.")


            elif selected_option == "Rate Limit per API":
                st.subheader(f"Rate Limit Information and Trend for {api_name_in_tab}")
                if rate_limit_per_second != "N/A":
                    st.info(f"**Configured Rate Limit:** {rate_limit_per_second} calls per second")
                    st.markdown("""
                    <p>The rate limit dictates the maximum number of requests allowed within a one-second window to prevent system overload and ensure fair usage. Adhering to this limit is crucial for stable API performance.</p>
                    """, unsafe_allow_html=True)
                    
                    # Generate data for rate limit trend graph (it's constant, but shown as a line)
                    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    start_date = end_date - timedelta(days=29)
                    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
                    
                    rate_limit_trend_data = []
                    for date in all_dates:
                        rate_limit_trend_data.append({"Date": date, "Rate Limit": rate_limit_per_second})
                    
                    df_rate_limit_trend = pd.DataFrame(rate_limit_trend_data)
                    
                    fig_rate_limit_trend = px.line(df_rate_limit_trend, x="Date", y="Rate Limit",
                                                     title=f"Configured Daily Rate Limit for {api_name_in_tab}")
                    fig_rate_limit_trend.update_layout(hovermode="x unified", xaxis_title="Date", yaxis_title="Calls per Second")
                    st.plotly_chart(fig_rate_limit_trend, use_container_width=True)

                else:
                    st.warning("Rate limit information is not configured for this API.")
                    st.info("No rate limit trend graph can be displayed without a configured rate limit.")

            elif selected_option == "Progress Bar":
                st.subheader(f"Daily Usage Progress for {api_name_in_tab}")
                
                api_config = API_CONFIGS.get(api_name_in_tab, {})
                quota_daily = api_config.get("quota_daily", 0) # Default to 0 if not found or N/A

                if quota_daily > 0: # Ensure a valid, positive quota exists
                    # Check if there is actual log data for the specific API and today
                    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    actual_current_daily_usage = 0
                    if not df_logs.empty and 'api' in df_logs.columns:
                        actual_current_daily_usage = df_logs[(df_logs["api"] == api_name_in_tab) & (df_logs["timestamp"] >= today_start)].shape[0]

                    if actual_current_daily_usage > 0: # Use actual data if available
                        current_daily_usage = actual_current_daily_usage
                        st.info("Displaying real-time usage progress.")
                    else: # Generate random dummy usage if no actual data for today
                        # Generate a random number up to the quota, but not exceeding it
                        current_daily_usage = np.random.randint(0, quota_daily + 1)
                        st.info("No real-time usage data available for today. Displaying simulated progress.")

                    progress_percentage = min((current_daily_usage / quota_daily) * 100, 100) # Cap at 100%

                    st.metric(label="Usage Today / Daily Quota", value=f"{current_daily_usage:,} / {quota_daily:,}")
                    st.progress(progress_percentage / 100) # st.progress expects a value between 0.0 and 1.0

                    if progress_percentage >= 100:
                        st.error("Daily quota reached! No more calls can be made today without exceeding the limit.")
                    elif progress_percentage >= 80:
                        st.warning("Approaching daily quota limit! Usage is at 80% or more.")
                    else:
                        st.success("Daily usage is well within limits.")
                else:
                    st.warning("Daily quota information is not configured or is zero for this API. Progress bar cannot be displayed.")
                    st.info("Please set a positive 'quota_daily' in the API_CONFIGS for this API.")

st.markdown("---") # Separator before support tickets

# --- Open Support Tickets (Always at the bottom) ---
st.subheader("📊 Open Support Tickets")

open_tickets = list(tickets_collection.find({"status": "open"}))

if open_tickets:
    # Sort tickets by aging time (hours_open) for better prioritization
    # Calculate hours_open for sorting
    for ticket in open_tickets:
        created_at = datetime.fromisoformat(ticket["created_at"])
        ticket["hours_open"] = round((datetime.utcnow() - created_at).total_seconds() / 3600, 2)
    
    open_tickets_sorted = sorted(open_tickets, key=lambda x: x["hours_open"], reverse=True)

    for ticket in open_tickets_sorted:
        col1_t, col2_t = st.columns([4, 1])
        with col1_t:
            st.markdown(f"""
            <div style="background-color: #1a1e27; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                <p style="font-size: 1.1rem; margin-bottom: 5px;"><strong>Ticket ID:</strong> <code>{ticket['_id']}</code></p>
                <p style="margin-bottom: 5px;"><strong>Query:</strong> {ticket['query']}</p>
                <p style="margin-bottom: 5px;"><strong>Contact:</strong> {ticket.get('contact', 'anonymous')}</p>
                <p style="margin-bottom: 5px;"><strong>Status:</strong> <span style="color:orange; font-weight:bold;">{ticket['status']}</span></p>
                <p style="margin-bottom: 0;"><strong>Aging Time:</strong> <span style="color:#FFA07A; font-weight:bold;">{ticket['hours_open']} hours</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col2_t:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) # Spacer for alignment
            if st.button("✅ Close Ticket", key=str(ticket["_id"])):
                tickets_collection.update_one({"_id": ticket["_id"]}, {"$set": {"status": "closed"}})
                st.success(f"Ticket #{ticket['_id']} closed successfully!")
                st.experimental_rerun() # Rerun to refresh ticket list
else:
    st.info("🎉 No open support tickets at the moment. All clear!")


# --- Custom CSS for a stunning UI (Enhanced for the new structure) ---
st.markdown("""
<style>
    /* Overall App Styling */
    .stApp {
        background-color: #0e1117; /* Dark background */
        color: #FAFAFA; /* Light text */
        font-family: 'Segoe UI', sans-serif; /* Modern font */
    }

    /* Main Title */
    h1 {
        color: #90CAF9; /* Light Blue */
        text-align: center;
        padding-bottom: 15px;
        border-bottom: 2px solid #2e3440; /* Subtle underline */
        margin-bottom: 30px;
        font-size: 2.5rem;
    }

    /* Subheaders */
    h2, h3, h4, h5, h6 {
        color: #BBDEFB; /* Lighter Blue */
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #3f51b5; /* Accent border */
        padding-left: 10px;
    }
    h2 { font-size: 1.8rem; }
    h3 { font-size: 1.5rem; }

    /* Buttons */
    .stButton>button {
        background-color: #4CAF50; /* Green */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.3s ease, transform 0.2s ease;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px); /* Slight lift on hover */
    }

    /* Top-level Tabs (API Navigation - like a navbar) */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center; /* Center the tabs horizontally */
        gap: 25px; /* Space between tabs */
        padding-bottom: 15px; /* Space below tabs */
        border-bottom: 1px solid #2e3440; /* Separator line */
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 25px;
        border-radius: 10px;
        transition: background-color 0.3s, color 0.3s, box-shadow 0.3s;
        font-weight: bold;
        color: #BBDEFB; /* Inactive tab text */
        background-color: #1a1e27; /* Inactive tab background */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2e3440; /* Hover effect */
        color: #E0E0E0;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #3f51b5; /* Selected tab color (Deep Indigo) */
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
        border-bottom: 3px solid #66BB6A; /* Green underline for selected tab */
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.15rem; /* Larger font for main API tabs */
        font-weight: bold;
        margin: 0;
    }

    /* Second-level Navigation (Radio Buttons for sub-options) */
    .stRadio > label { /* This targets the label text */
        font-weight: bold;
        font-size: 1.1rem;
        color: #90CAF9;
    }
    .stRadio [data-baseweb="radio"] { /* This targets the individual radio button container */
        background-color: #1a1e27;
        border-radius: 8px;
        padding: 8px 15px;
        margin-right: 10px;
        transition: background-color 0.3s;
        border: 1px solid #2e3440;
    }
    .stRadio [data-baseweb="radio"]:hover {
        background-color: #2e3440;
    }
    .stRadio [data-baseweb="radio"][aria-checked="true"] {
        background-color: #5C6BC0; /* Slightly lighter indigo for selected radio */
        color: white;
        border: 1px solid #5C6BC0;
    }

    /* Alerts (info, warning, error) */
    .stAlert {
        border-radius: 8px;
        padding: 15px;
        font-size: 1rem;
        margin-top: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Metrics (KPIs) */
    .stMetric > div > div:first-child { /* Label */
        font-size: 1.1rem;
        color: #BBDEFB;
        font-weight: normal;
    }
    .stMetric > div > div:last-child { /* Value */
        font-size: 2.2rem;
        font-weight: bold;
        color: #E0E0E0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* Subtle shadow for value */
    }

    /* Plotly chart container */
    .stPlotlyChart {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #2e3440; /* Border around charts */
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }

    /* General text/paragraph styling */
    p {
        font-size: 1rem;
        line-height: 1.6;
        color: #FAFAFA;
    }
    b, strong {
        color: #E0E0E0;
    }
    code {
        background-color: #2e3440;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.9rem;
        color: #BBDEFB;
    }

    /* Horizontal Rule */
    hr {
        border-top: 1px solid #2e3440;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* Support Ticket Cards */
    div[data-testid="stMarkdown"] > div > div > div[style*="background-color: #1a1e27"] {
        border: 1px solid #2e3440;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #1a1e27;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMarkdown"] p {
        margin-bottom: 0.5em; /* Adjust paragraph spacing inside ticket cards */
    }

</style>
""", unsafe_allow_html=True)