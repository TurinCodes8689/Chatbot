import os
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from twilio.rest import Client
from datetime import datetime, timedelta, timezone
import pandas as pd # For usage statistics table
import re # Import the regular expression module

from langchain.chat_models import init_chat_model
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage


# THIS MUST BE THE VERY FIRST STREAMLIT COMMAND IN THE SCRIPT
st.set_page_config(
    page_title="APIMAN - APIHub Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Environment Variables ---
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID") or st.secrets.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN") or st.secrets.get("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER") or st.secrets.get("TWILIO_NUMBER")
SUPPORT_PHONE_NUMBER = os.getenv("SUPPORT_PHONE_NUMBER") or st.secrets.get("SUPPORT_PHONE_NUMBER")
MONGO_URI = os.getenv("MONGODB_URI") or st.secrets.get("MONGODB_URI")

# --- Essential Configuration Checks ---
if not SUPPORT_PHONE_NUMBER:
    st.error("🚫 Configuration Error: SUPPORT_PHONE_NUMBER environment variable not set. Please configure it to enable support features.")
    st.stop()
if not GROQ_API_KEY:
    st.error("🚫 Configuration Error: GROQ_API_KEY is not set. Please configure it to enable AI chat capabilities.")
    st.stop()
if not MONGO_URI:
    st.error("🚫 Configuration Error: MONGODB_URI is not set. Please configure it for database operations.")
    st.stop()
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_NUMBER:
    st.warning("⚠️ Warning: Twilio credentials not fully configured. WhatsApp notifications for support tickets may not work.")

# --- Database Client Initialization ---
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["apiman"]
    tickets_collection = db["support_tickets"]
    api_logs_collection = db["api_usage_logs"] # Still here for context, though not heavily used
except Exception as e:
    st.error(f"❌ Database Connection Failed: Could not connect to MongoDB. Please check your MONGO_URI. Error: {e}")
    st.stop()

# --- Initialize Chat Model ---
@st.cache_resource
def get_chat_model():
    """Caches the LLM model to prevent re-initialization on every rerun."""
    try:
        return init_chat_model(
            model="llama3-8b-8192",
            model_provider="groq",
            api_key=GROQ_API_KEY,
            temperature=0
        )
    except Exception as e:
        st.error(f"🚫 AI Model Initialization Failed: Could not initialize the chat model. Please check your GROQ_API_KEY. Error: {e}")
        st.stop()

chat_model = get_chat_model()

# --- WhatsApp Notification Function (Bot Logic - KEPT AS IS) ---
def send_whatsapp_notification(ticket_id, message_content):
    """Sends a WhatsApp message to the support number."""
    try:
        twilio_rest_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twilio_rest_client.messages.create(
            body=f"📢 New Support Ticket #{ticket_id}\n\nDetails: {message_content}\n\nOpened at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            from_="whatsapp:" + TWILIO_NUMBER,
            to="whatsapp:" + SUPPORT_PHONE_NUMBER
        )
        st.info(f"✅ WhatsApp notification sent for Ticket #{ticket_id}.")
    except Exception as e:
        st.warning(f"⚠️ Failed to send WhatsApp notification for Ticket #{ticket_id}. Please check Twilio configuration. Error: {e}")

# --- Create Support Ticket Function (Bot Logic - KEPT AS IS) ---
def create_support_ticket(query_text, contact_info="anonymous user"):
    """
    Creates a new support ticket in MongoDB and sends a WhatsApp notification.
    """
    ticket_data = {
        "query": query_text,
        "contact": contact_info,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    try:
        result = tickets_collection.insert_one(ticket_data)
        ticket_id = str(result.inserted_id)
        send_whatsapp_notification(ticket_id, query_text)
        return ticket_id
    except Exception as e:
        st.error(f"❌ Failed to create support ticket in database. Error: {e}")
        return None

# --- APIMAN System Prompt (Bot Logic - KEPT AS IS) ---
SYSTEM_PROMPT = """
You are APIMAN, an advanced, highly intelligent, and helpful chatbot for APIHub. Your primary purpose is to assist users with APIHub-related questions and provide accurate, concise information.

Your expertise covers the following areas exclusively:
- API Endpoints: Details about available API URLs, versions, and their purposes.
- Authentication: How to generate, use, and manage API keys, access tokens (OAuth 2.0, JWT), and authentication flows.
- Rate Limits: Information on request limits, headers, and best practices to avoid hitting rate limits.
- Error Codes: Explanations of common HTTP status codes (4xx, 5xx), specific API error messages, and troubleshooting steps.
- Data Formats: Expected request and response data structures (JSON, XML), required headers (Content-Type, Accept), and data validation.

If a user's question falls outside these specific topics, is ambiguous, or cannot be confidently answered based on your knowledge, you MUST respond with the following phrase, and nothing else:
"I cannot resolve this. A support ticket will be created."

Always maintain a professional, friendly, and precise tone.
"""

# --- Helper functions to generate Markdown for specific commands ---
def _get_recent_tickets_markdown():
    """Generates a Markdown string for recent support tickets."""
    markdown_output = "### 📋 Recent Support Tickets\n"
    markdown_output += "A quick overview of recently opened tickets:\n\n"
    try:
        recent_tickets_data = list(tickets_collection.find().sort("created_at", -1).limit(5))
        if recent_tickets_data:
            ticket_records = []
            for t in recent_tickets_data:
                # Truncate subject if too long for display
                subject = t["query"].split('\n')[0]
                if len(subject) > 50:
                    subject = subject[:47] + "..."
                ticket_records.append({
                    "ID": str(t["_id"])[-6:], # Show last 6 chars of ID for brevity
                    "Subject": subject,
                    "Status": t["status"].capitalize(),
                    "Created": datetime.fromisoformat(t["created_at"]).strftime("%Y-%m-%d %H:%M")
                })
            recent_tickets_df = pd.DataFrame(ticket_records)
            # Convert DataFrame to Markdown table
            markdown_output += recent_tickets_df.to_markdown(index=False)
        else:
            markdown_output += "No recent tickets found in the database.\n"
    except Exception as e:
        markdown_output += f"⚠️ Could not load recent tickets: {e}\n"
        markdown_output += "Displaying mock data for recent tickets instead.\n\n"
        mock_tickets = {
            "ID": ["#A1B2C3", "#D4E5F6", "#G7H8I9", "#J0K1L2", "#M3N4O5"],
            "Subject": ["API Key Issue", "Rate Limit Exceeded", "Auth Token Expired", "Data Format Error", "Endpoint Not Found"],
            "Status": ["Open", "Pending", "Closed", "Open", "Resolved"],
            "Created": [
                (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            ]
        }
        markdown_output += pd.DataFrame(mock_tickets).to_markdown(index=False)
    return markdown_output

def _get_api_stats_markdown():
    """Generates a Markdown string for API usage statistics."""
    markdown_output = "### 📈 API Usage Statistics\n"
    markdown_output += "Insights into your API consumption (mock data):\n\n"
    markdown_output += "**Total Requests (24h):** 1,245,678 (↑ 12.5%)\n"
    markdown_output += "**Avg Latency (ms):** 75 (↓ 5ms)\n\n"
    markdown_output += "#### Daily Request Volume\n"
    chart_data = pd.DataFrame(
        {
            "Date": pd.to_datetime(pd.date_range(end=datetime.now(), periods=7, freq='D')),
            "Requests": [1500, 1800, 2200, 1900, 2500, 2300, 2700],
        }
    )
    # Streamlit line chart cannot be directly embedded as Markdown,
    # so we'll describe it or use a simple textual representation.
    # For a true chart in chat, a custom component would be needed.
    markdown_output += "```\n"
    markdown_output += "Date          Requests\n"
    markdown_output += "----------  ----------\n"
    for index, row in chart_data.iterrows():
        markdown_output += f"{row['Date'].strftime('%Y-%m-%d')}  {row['Requests']}\n"
    markdown_output += "```\n"
    markdown_output += "*(Note: Full interactive chart not displayable in chat history as Markdown)*"
    return markdown_output

def _get_contact_info_markdown():
    """Generates a Markdown string for contact information."""
    markdown_output = "### 📞 Contact & Resources\n"
    markdown_output += "If you need further assistance or prefer direct contact, here are some options:\n\n"
    markdown_output += "- 📧 [support@apihub.com](mailto:support@apihub.com)\n"
    markdown_output += "- 📞 +1 (800) API-HELP\n"
    markdown_output += "- 📚 [APIHub Documentation](https://docs.apihub.com) (Opens in new tab)\n"
    return markdown_output

# --- Function to render the Manual Support Ticket Form ---
def render_manual_ticket_form():
    """Renders the manual support ticket form in the main content area."""
    st.subheader("📝 Manual Support Ticket")
    st.markdown("<p style='color: var(--gemini-subtle-text);'>Fill this form if you prefer to directly create a detailed support ticket.</p>", unsafe_allow_html=True)
    with st.form("ticket_form", clear_on_submit=True):
        subject = st.text_input("Subject of your Issue", help="A concise summary of your problem or request.", key="manual_subject")
        details = st.text_area("Full Description", help="Provide comprehensive details: steps to reproduce, expected vs. actual behavior, error messages, and any relevant IDs.", height=150, key="manual_details")
        contact = st.text_input("Your Contact Email / Username", help="How can we reach you regarding this ticket?", value="", key="manual_contact")

        col1, col2 = st.columns([1, 1])
        with col1:
            submit_ticket_button = st.form_submit_button("Submit New Ticket")
        with col2:
            back_to_chat_button = st.form_submit_button("Back to Chat")

        if submit_ticket_button:
            if not (subject and details):
                st.warning("Please provide both a **Subject** and a **Full Description** for the ticket.")
            else:
                full_query = f"Subject: {subject}\n\nDescription:\n{details}"
                new_ticket_id = create_support_ticket(full_query, contact if contact else "anonymous")
                if new_ticket_id:
                    st.success(f"🚀 **Ticket #{new_ticket_id}** submitted successfully! We've received your request and will process it soon.")
                    st.toast(f"Ticket #{new_ticket_id} created!", icon="✅")
                    st.session_state.show_manual_form = False # Hide form after submission
                    st.session_state.chat_history.append({"role": "assistant", "content": f"Manual ticket `#{new_ticket_id}` has been created. Our team will get back to you shortly. Feel free to ask more questions!"})
                    st.rerun()
                else:
                    st.error("❗ Failed to submit ticket. Please check your inputs or try again later.")
        elif back_to_chat_button:
            st.session_state.show_manual_form = False
            st.rerun()

# --- Custom CSS for Stunning UI and Animations ---
st.markdown("""
    <style>
    /* Import Google Font - Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --gemini-dark-bg: #0A0A0A; /* Even darker background */
        --gemini-card-bg: #151515; /* Slightly darker card background */
        --gemini-text-color: #E8E8E8;
        --gemini-subtle-text: #B0B0B0;
        --gemini-accent-blue: #63B3ED;
        --gemini-accent-teal: #81E6D9;
        --gemini-gradient-blue: linear-gradient(145deg, #63B3ED, #4299E1);
        --gemini-gradient-teal: linear-gradient(145deg, #81E6D9, #4FD1C5);
        --gemini-shadow-dark: rgba(0, 0, 0, 0.7);
        --gemini-shadow-light: rgba(0, 0, 0, 0.4);
        --gemini-border-color: #383838; /* Stronger border contrast */
        --gemini-input-bg: #202020; /* Darker input background */
        --submit-button-green: linear-gradient(145deg, #4CAF50, #2E8B57); /* Green gradient */
        --submit-button-green-hover: linear-gradient(145deg, #2E8B57, #4CAF50);
        --cancel-button-red: linear-gradient(145deg, #FF6B6B, #E53E3E); /* Red gradient */
        --cancel-button-red-hover: linear-gradient(145deg, #E53E3E, #FF6B6B);
    }

    /* Keyframe Animations */
    @keyframes fadeInSlideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0px var(--gemini-accent-teal); }
        50% { box-shadow: 0 0 10px 5px var(--gemini-accent-teal); }
        100% { box-shadow: 0 0 0px var(--gemini-accent-teal); }
    }

    @keyframes alertEntry {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* General body styling for Streamlit's default dark theme */
    .stApp {
        background: var(--gemini-dark-bg);
        color: var(--gemini-text-color);
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        transition: background-color 0.5s ease;
        overflow-x: hidden; /* Prevent horizontal scroll */
    }

    /* Scrollbar styling for a sleeker look */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--gemini-dark-bg);
    }
    ::-webkit-scrollbar-thumb {
        background: #4A5568;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #607C8E;
    }

    /* Main header styling */
    .st-emotion-cache-18ni7ap { /* Target main header container */
        background-color: var(--gemini-card-bg);
        padding: 1.5rem 2rem;
        border-bottom: 1px solid var(--gemini-border-color);
        box-shadow: 0 6px 25px var(--gemini-shadow-dark);
        margin-bottom: 2rem;
        border-radius: 0 0 20px 20px;
    }
    h1 {
        color: var(--gemini-accent-blue);
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.05em;
        text-shadow: 0 3px 6px rgba(0,0,0,0.6);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    h1 img {
        transition: transform 0.3s ease-in-out;
        animation: pulseGlow 3s infinite alternate;
    }
    h1 img:hover {
        transform: scale(1.05);
    }


    /* Subheader styling */
    h2 {
        color: var(--gemini-accent-blue);
        border-bottom: 2px solid var(--gemini-border-color);
        padding-bottom: 0.7rem;
        margin-bottom: 1.8rem;
        font-weight: 600;
        text-shadow: 0 1px 3px var(--gemini-shadow-light);
    }

    /* Card-like containers for sections */
    div[data-testid="stVerticalBlock"] > div.st-emotion-cache-ocqkz7 { /* General container for form */
        background-color: var(--gemini-card-bg);
        border-radius: 20px;
        padding: 2.2rem;
        margin-bottom: 2.5rem;
        box-shadow: 0 8px 30px var(--gemini-shadow-dark);
        border: 1px solid var(--gemini-border-color);
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stVerticalBlock"] > div.st-emotion-cache-ocqkz7:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7);
    }

    /* Text input and text area styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    div[data-testid="stForm"] .stTextInput input,
    div[data-testid="stForm"] .stTextArea textarea {
        background-color: var(--gemini-input-bg);
        color: var(--gemini-text-color);
        border: 1px solid #4A5568;
        border-radius: 15px;
        padding: 14px 20px;
        font-size: 1.05rem;
        transition: all 0.4s ease-in-out;
        box-shadow: inset 0 3px 8px rgba(0, 0, 0, 0.5);
        width: 100%; /* Ensure inputs take full width of their container */
        box-sizing: border-box; /* Include padding and border in the element's total width and height */
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    div[data-testid="stForm"] .stTextInput input:focus,
    div[data-testid="stForm"] .stTextArea textarea:focus {
        border-color: var(--gemini-accent-blue);
        box-shadow: 0 0 0 4px rgba(99, 179, 237, 0.4), inset 0 3px 8px rgba(0, 0, 0, 0.7);
        background-color: #3A4555;
        outline: none;
    }
    /* Specific target for Streamlit's input containers to control margin */
    div[data-testid="stForm"] > div > div > div.st-emotion-cache-1c7vj7f > div { /* targeting the specific div wrapper around each input */
        margin-bottom: 1.5rem;
    }


    /* Button styling with animations */
    /* Base button style applies to all stButton elements */
    .stButton > button {
        border: none;
        border-radius: 12px;
        padding: 14px 30px;
        font-size: 1.15rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        letter-spacing: 0.05em;
        position: relative;
        overflow: hidden;
        display: block; /* Ensures buttons take full width of their column */
        width: 100%;
        text-align: center; /* Center text within button */
    }

    /* Submit New Ticket - Green */
    div[data-testid="stForm"] .stButton:nth-of-type(1) > button { /* Target the first button in the form's columns */
        background: var(--submit-button-green);
        color: white;
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3); /* Green shadow */
    }
    div[data-testid="stForm"] .stButton:nth-of-type(1) > button:hover {
        background: var(--submit-button-green-hover);
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 10px 25px rgba(76, 175, 80, 0.4);
    }
    div[data-testid="stForm"] .stButton:nth-of-type(1) > button:active {
        transform: translateY(0) scale(0.98);
        box-shadow: 0 3px 10px rgba(76, 175, 80, 0.2);
    }

    /* Back to Chat - Red */
    div[data-testid="stForm"] .stButton:nth-of-type(2) > button { /* Target the second button in the form's columns */
        background: var(--cancel-button-red);
        color: white;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3); /* Red shadow */
    }
    div[data-testid="stForm"] .stButton:nth-of-type(2) > button:hover {
        background: var(--cancel-button-red-hover);
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
    }
    div[data-testid="stForm"] .stButton:nth-of-type(2) > button:active {
        transform: translateY(0) scale(0.98);
        box-shadow: 0 3px 10px rgba(255, 107, 107, 0.2);
    }


    /* Ripple effect for buttons (Pure CSS) */
    .stButton > button::after {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        background: rgba(255, 255, 255, 0.2);
        opacity: 0;
        transition: all 0.5s ease;
        border-radius: 50%;
        transform: scale(0);
        z-index: 1; /* Ensure ripple is above content */
    }
    .stButton > button:active::after {
        opacity: 1;
        transform: scale(2);
        transition: 0s;
    }


    /* Expander styling */
    .stExpander details {
        background-color: #2D3748;
        border-radius: 15px;
        padding: 18px 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        border: 1px solid #4A5568;
        transition: all 0.3s ease-in-out;
    }
    .stExpander details:hover {
        background-color: #3A4555;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }
    .stExpander details summary {
        color: var(--gemini-text-color);
        font-weight: 600;
        font-size: 1.15rem;
        cursor: pointer;
    }
    .stExpander > div > div { /* Target content area of expander */
        background-color: var(--gemini-card-bg);
        border-radius: 0 0 15px 15px;
        padding: 18px 25px;
        border-top: 1px solid var(--gemini-border-color);
        margin-top: -8px;
    }

    /* Chat messages styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 20px;
        overflow-y: auto;
        max-height: 480px;
        border: 1px solid var(--gemini-border-color);
        border-radius: 20px;
        background-color: var(--gemini-card-bg);
        box-shadow: inset 0 0 15px rgba(0,0,0,0.6);
        position: relative;
    }

    .chat-message {
        display: flex;
        align-items: flex-start;
        font-size: 1rem;
        animation: fadeInSlideUp 0.5s ease-out forwards;
        opacity: 0;
        margin-bottom: 0;
    }

    .chat-message-user {
        justify-content: flex-end;
        align-self: flex-end;
        text-align: right;
    }

    .chat-message-assistant {
        justify-content: flex-start;
        align-self: flex-start;
        text-align: left;
    }

    .chat-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        flex-shrink: 0;
        box-shadow: 0 3px 10px rgba(0,0,0,0.4);
        z-index: 2; /* Ensure avatar is above ripple */
    }

    .user-avatar {
        background: var(--gemini-gradient-blue);
        color: white;
        margin-left: 18px;
    }

    .assistant-avatar {
        background: var(--gemini-gradient-teal);
        color: var(--gemini-dark-bg);
        margin-right: 18px;
    }

    .message-bubble {
        padding: 15px 22px;
        border-radius: 25px;
        max-width: 70%;
        position: relative;
        box-shadow: 0 5px 15px rgba(0,0,0,0.4);
        transition: transform 0.2s ease-out;
        word-wrap: break-word;
        z-index: 1; /* Ensure bubble is below avatar if overlapping */
    }

    .chat-message-user .message-bubble {
        background: linear-gradient(145deg, #00008B, #1A1A5A); /* Darker blue gradient */
        color: white;
        border-bottom-right-radius: 8px;
    }

    # .chat-message-assistant .message-bubble {
    #     background: var(--gemini-gradient-teal);
    #     color: var(--gemini-dark-bg);
    #     border-bottom-left-radius: 8px;
    # }

    /* Loading spinner customization */
    .stSpinner > div > div {
        border-top-color: var(--gemini-accent-blue) !important;
        border-left-color: var(--gemini-accent-blue) !important;
        animation: spin 1s linear infinite;
    }
    .stSpinner > div > div > div {
        color: var(--gemini-accent-blue);
        font-size: 1.1rem;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }


    /* Success, Warning, Error message styling */
    .stAlert {
        border-radius: 12px;
        padding: 18px;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        border: none;
        box-shadow: 0 3px 12px rgba(0,0,0,0.3);
        animation: alertEntry 0.6s ease-out forwards;
        opacity: 0;
        z-index: 100; /* Ensure alerts are on top */
    }
    .stAlert.success {
        background-color: #2D3748;
        color: #48BB78;
        border-left: 6px solid #48BB78;
    }
    .stAlert.warning {
        background-color: #2D3748;
        color: #ECC94B;
        border-left: 6px solid #ECC94B;
    }
    .stAlert.error {
        background-color: #2D3748;
        color: #FC8181;
        border-left: 6px solid #FC8181;
    }

    /* Table styling for recent tickets/usage stats */
    .stMarkdown table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1.5rem;
        background-color: #2D3748;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        color: var(--gemini-text-color);
    }
    .stMarkdown th {
        background-color: #4A5568;
        color: #CBD5E0;
        padding: 14px 18px;
        text-align: left;
        font-weight: 700;
        border-bottom: 1px solid #607C8E;
    }
    .stMarkdown td {
        padding: 12px 18px;
        border-bottom: 1px solid #4A5568;
    }
    .stMarkdown tr:nth-child(even) {
        background-color: #3A4555;
    }
    .stMarkdown tr:hover {
        background-color: #4A5568;
        transition: background-color 0.2s ease;
    }


    /* Metric styling */
    .stMetric {
        background-color: var(--gemini-card-bg);
        border-radius: 15px;
        padding: 1.8rem;
        text-align: center;
        box-shadow: 0 5px 18px rgba(0,0,0,0.5);
        transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
    }
    .stMetric:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.6);
    }
    .stMetric > div > div > div { /* Metric label */
        color: var(--gemini-subtle-text);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .stMetric > div > div > div:nth-child(2) { /* Metric value */
        color: var(--gemini-accent-teal);
        font-size: 2.5rem;
        font-weight: 700;
    }
    .stMetric > div > div > div:nth-child(3) { /* Metric delta */
        color: #48BB78;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .negative-delta {
        color: #FC8181 !important;
    }

    /* Footer styling */
    .footer {
        padding: 2rem;
        text-align: center;
        color: var(--gemini-subtle-text);
        font-size: 0.95rem;
        margin-top: 4rem;
        border-top: 1px solid var(--gemini-border-color);
        background-color: var(--gemini-card-bg);
        border-radius: 20px 20px 0 0;
        box-shadow: 0 -6px 20px var(--gemini-shadow-dark);
    }
    .footer a {
        color: var(--gemini-accent-blue);
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .footer a:hover {
        color: #4299E1;
        text-decoration: underline;
    }

    /* Streamlit's hidden elements to avoid clashes */
    div.st-emotion-cache-nahz7x {
        background-color: transparent;
    }
    div.st-emotion-cache-17l70w3 {
        background-color: transparent;
    }

    /* For direct markdown content (like tables generated by helper functions) */
    div[data-testid="stMarkdownContainer"] {
        color: var(--gemini-text-color);
    }

    /* Global styling for input containers to ensure padding and shadow consistency */
    div[data-testid="stForm"] > div > div > div:first-child > div,
    div[data-testid="stForm"] > div > div > div:nth-child(2) > div,
    div[data-testid="stForm"] > div > div > div:nth-child(3) > div {
        background-color: var(--gemini-input-bg);
        border-radius: 15px;
        padding: 10px 15px;
        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.3);
        border: 1px solid #3A4555;
        transition: all 0.3s ease;
    }
    div[data-testid="stForm"] > div > div > div:first-child > div:focus-within,
    div[data-testid="stForm"] > div > div > div:nth-child(2) > div:focus-within,
    div[data-testid="stForm"] > div > div > div:nth-child(3) > div:focus-within {
        border-color: var(--gemini-accent-blue);
        box-shadow: 0 0 0 3px rgba(99, 179, 237, 0.3), inset 0 2px 5px rgba(0, 0, 0, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.markdown("<h1><img src='https://placehold.co/70x70/81E6D9/1A202C?text=API' style='vertical-align:middle; margin-right:20px; border-radius:15px;'>APIMAN: Your APIHub Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: var(--gemini-subtle-text); font-size: 1.2rem; margin-top: -15px; margin-bottom: 30px;'>Empowering your API journey with instant answers and seamless support.</p>", unsafe_allow_html=True)

# Initialize chat history and form state in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_success_alert" not in st.session_state:
    st.session_state.show_success_alert = False
if "success_ticket_id" not in st.session_state:
    st.session_state.success_ticket_id = None
if "show_error_alert" not in st.session_state:
    st.session_state.show_error_alert = False
if "show_manual_form" not in st.session_state:
    st.session_state.show_manual_form = False # New state variable for showing manual form

# --- Main Content Area ---
# The main layout is now a single column for the chat assistant or the manual form
main_col = st.columns([1])[0]

with main_col: # This column will dynamically show chat or the form
    if st.session_state.show_manual_form:
        render_manual_ticket_form()
    else:
        # --- Chat Assistant Section ---
        st.subheader("💬 Chat with APIMAN")
        st.markdown('<div id="chat-history-scroll-area" class="chat-container">', unsafe_allow_html=True)

        for msg_idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message chat-message-user">
                        <div class="message-bubble">
                            <strong>You:</strong> {msg['content']}
                        </div>
                        <div class="chat-avatar user-avatar">👤</div>
                    </div>
                    """, unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                clean_md = re.sub(r"</?div[^>]*>", "", msg["content"], flags=re.IGNORECASE)

                st.markdown("""
                    <div class="chat-message chat-message-assistant">
                        <div class="chat-avatar assistant-avatar">🤖</div>
                        <div class="message-bubble">
                            ...
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(clean_md, unsafe_allow_html=False)

                st.markdown("""
                        </div>
                    </div>
                """, unsafe_allow_html=True)



        st.markdown('</div>', unsafe_allow_html=True)

        # JavaScript to auto-scroll chat to bottom
        st.markdown("""
            <script>
                var chatHistoryDiv = document.getElementById('chat-history-scroll-area');
                if (chatHistoryDiv) {
                    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
                }
            </script>
        """, unsafe_allow_html=True)

        # --- User Input for Chat ---
        user_input = st.chat_input("Ask APIMAN about APIHub or type 'show help' for commands...", key="chat_input")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.show_success_alert = False
            st.session_state.show_error_alert = False
            st.rerun()

        # --- Bot Response Generation (Bot Logic with Command Handling) ---
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            current_user_query = st.session_state.chat_history[-1]["content"].lower().strip()
            bot_response_content = ""

            # Check for specific commands first
            if "show recent support tickets" in current_user_query or "show tickets" in current_user_query:
                bot_response_content = _get_recent_tickets_markdown()
            elif "show api usage statistics" in current_user_query or "show api stats" in current_user_query:
                bot_response_content = _get_api_stats_markdown()
            elif "show contact information" in current_user_query or "show contact" in current_user_query or "contact support" in current_user_query:
                bot_response_content = _get_contact_info_markdown()
            elif "show help" in current_user_query or "commands" in current_user_query:
                bot_response_content = """
                ### ℹ️ APIMAN Commands:
                You can ask me to:
                - `show recent support tickets` or `show tickets`: See a list of your latest support tickets.
                - `show api usage statistics` or `show api stats`: Get an overview of your API consumption.
                - `show contact information` or `show contact`: Find ways to reach our support team.
                - `create manual support ticket` or `new ticket`: Open a form to submit a detailed support ticket.
                - And of course, ask any question about APIHub endpoints, authentication, rate limits, errors, and data formats!
                """
            elif "create manual support ticket" in current_user_query or "new ticket" in current_user_query:
                st.session_state.show_manual_form = True # Trigger the manual form display
                st.session_state.chat_history.append({"role": "assistant", "content": "Alright, please fill out the details for your support ticket."})
                st.rerun() # Rerun to switch to form view
            else:
                with st.spinner("APIMAN is processing your query..."):
                    try:
                        messages = [SystemMessage(content=SYSTEM_PROMPT)] + [
                            HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"])
                            for msg in st.session_state.chat_history[-5:]
                        ]
                        if not messages or messages[-1].content.lower().strip() != current_user_query or messages[-1].type != "human":
                             messages.append(HumanMessage(content=current_user_query))

                        llm_response = chat_model.invoke(messages).content

                        # Use regex to remove all occurrences of </div> (and potential variations)
                        llm_response = re.sub(r'</\s*div\s*>', '', llm_response).strip()


                        trigger_phrases = [
                            "i cannot resolve this", "off-topic", "not related",
                            "i'm not sure", "contact support", "ticket will be created",
                            "unable to provide an answer"
                        ]
                        needs_ticket = any(phrase in llm_response.lower() for phrase in trigger_phrases)

                        if needs_ticket:
                            ticket_id_for_bot = create_support_ticket(current_user_query)
                            if ticket_id_for_bot:
                                llm_response += f"\n\n🚨 **Important:** A support ticket (`#{ticket_id_for_bot}`) has been automatically created for your query. Our team will review it and get back to you shortly."
                                st.session_state.show_success_alert = True
                                st.session_state.success_ticket_id = ticket_id_for_bot
                            else:
                                llm_response += f"\n\n⚠️ **Note:** I tried to create a support ticket, but encountered an error. Please try again or contact support directly."

                        bot_response_content = llm_response

                    except Exception as e:
                        ticket_id_on_error = create_support_ticket(current_user_query, contact_info="AI Chatbot Failure")
                        if ticket_id_on_error:
                            bot_response_content = f"Oops! I encountered an internal error while processing your request: '{e}'. Don't worry, a support ticket (`#{ticket_id_on_error}`) has been automatically created for this issue. Our team will investigate!"
                            st.session_state.show_error_alert = True
                        else:
                            bot_response_content = f"Oops! I encountered an internal error: '{e}'. I also failed to create a support ticket automatically. Please try again or contact support directly."

            st.session_state.chat_history.append({"role": "assistant", "content": bot_response_content})
            st.rerun()

        # --- Display Alerts (Success/Error from auto-ticket creation) ---
        if st.session_state.show_success_alert and st.session_state.success_ticket_id:
            st.success(f"🎉 **Success!** Ticket `#{st.session_state.success_ticket_id}` created by APIMAN. We'll be in touch!")
        if st.session_state.show_error_alert:
            st.error("❌ **Error!** APIMAN encountered an issue and created a fallback ticket.")

# # --- Footer Section ---
# st.markdown("""
#     <div class="footer">
#         <p>&copy; 2025 APIMAN. All rights reserved. | Powered by <a href="https://streamlit.io" target="_blank">Streamlit</a> & <a href="https://groq.com" target="_blank">Groq</a></p>
#     </div>
#     """, unsafe_allow_html=True)
