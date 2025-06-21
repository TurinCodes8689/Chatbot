import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from pymongo import MongoClient
from twilio.rest import Client
from datetime import datetime
from langchain.chat_models import init_chat_model
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage

# Load environment variables from .env file (for local development)
load_dotenv()

# Use st.secrets for deployment on Streamlit Cloud, fall back to os.getenv for local
groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID") or st.secrets.get("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN") or st.secrets.get("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER") or st.secrets.get("TWILIO_NUMBER")
support_number = os.getenv("SUPPORT_PHONE_NUMBER") or st.secrets.get("SUPPORT_PHONE_NUMBER")
mongo_uri = os.getenv("MONGODB_URI") or st.secrets.get("MONGODB_URI")


if not support_number:
    st.error("SUPPORT_PHONE_NUMBER environment variable not set. Please set it in .env or Streamlit secrets.")
    st.stop()

# Initialize MongoDB Client
try:
    client = MongoClient(mongo_uri)
    db = client["apiman"]
    tickets = db["support_tickets"]
    logs = db["api_usage_logs"]
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")
    st.stop()

# Initialize Chat Model
try:
    chat_model = init_chat_model(
        model="llama3-8b-8192",
        model_provider="groq",
        api_key=groq_api_key,
        temperature=0
    )
except Exception as e:
    st.error(f"Failed to initialize Groq chat model: {e}")
    st.stop()

# Initialize Twilio Client
twilio_client = None
if twilio_sid and twilio_token:
    try:
        twilio_client = Client(twilio_sid, twilio_token)
    except Exception as e:
        st.warning(f"Failed to initialize Twilio client: {e}. WhatsApp notifications will not work.")
else:
    st.warning("Twilio credentials not set. WhatsApp notifications will not work.")


def send_whatsapp(ticket_id, message):
    if twilio_client and twilio_number and support_number:
        try:
            twilio_client.messages.create(
                body=f"Support Ticket #{ticket_id}\n{message}",
                from_="whatsapp:" + twilio_number,
                to="whatsapp:" + support_number
            )
        except Exception as e:
            st.warning(f"Failed to send WhatsApp message: {e}")
    else:
        st.info("WhatsApp message not sent: Twilio not configured or support number missing.")


def create_ticket(query, contact="anonymous"):
    ticket = {
        "query": query,
        "contact": contact,
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }
    result = tickets.insert_one(ticket)
    send_whatsapp(str(result.inserted_id), query)
    return str(result.inserted_id)

SYSTEM_PROMPT = """
You are APIMAN, a chatbot for APIHub. Only answer APIHub-related questions about:
- Endpoints
- Authentication (keys, tokens)
- Rate limits
- Errors
- Data formats

If the question is off-topic or unclear, say:
"I cannot resolve this. A support ticket will be created."
"""

# Streamlit UI (This part will be replaced by the embedded HTML for visuals)
# For the backend, we still need to process messages received from the frontend's JavaScript.
# However, the direct Streamlit chat input will be removed in favor of the HTML-based one.

# This section is for handling messages that might come *back* from the HTML component
# if you were to implement a custom communication channel (e.g., bi-directional messages).
# For now, this Streamlit file primarily serves to embed the HTML and handle backend logic.

# The current Streamlit chat history is not directly used for display in the new HTML UI,
# but it's kept for logical consistency if you wanted to bridge them.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Custom HTML, CSS, and JavaScript for Stunning Visuals and Voice Input ---
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive 3D Zipper Reveal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Absolute reset for html and body inside the iframe */
        html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
            font-family: 'Inter', sans-serif;
            perspective: 1800px; /* Stronger global perspective for more pronounced 3D */
        }

        body {
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); /* Base gradient */
        }

        /* Animated Background for entire page */
        #fullPageBackgroundWrapper {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: linear-gradient(45deg, #1a1a2e, #0f3460, #16213e, #0f3460); /* More dynamic gradient */
            background-size: 400% 400%; /* Larger size for animation */
            animation: gradientAnimation 15s ease infinite; /* Slow, smooth animation */
            /* Subtle noise pattern */
            background-image: url('data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjEiIGdlb21ldHJ5PSIwIDAgNTAwIDUwMCIgcHJlc2VydmVBc3BlY3RSYXRpbz0ibm9uZSIgdmlld0JveD0iMCAwNTAwIDUwMCIgd2lkdGg9IjUwMCIgaGVpZ2h0PSI1MDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPGcgb3BhY2l0eT0iMC4wOCI+CiAgICA8Y2lyY2xlIGN4PSIyNTAiIGN5PSIyNTAiIHI9IjEwMCIgZmlsbD0iI2ZmZiIvPgogICAgPGNpcmNsZSBjeD0iMTAwIiBjeT0iMTAwIiByPSI1MCIgZmlsbD0iI2ZmZiIvPgogICAgPGNpcmNsZSBjeD0iNDAwIiBjeT0iNDAwIiByPSI3NSIgZmlsbD0iI2ZmZiIvPgogICAgPGNpcmNsZSBjeD0iNDUwIiBjeT0iNzAiIHI9IjM1IiBmaWxsPSIjZmZmIi8+CiAgICA8Y2lyY2xlIGN4PSI1MCIgY3k9IjQyMCIgcj0iNjAiIGZpbGw9IiNmZmYiLz4KICA8L2c+Cjwvc3ZnPg==');
            background-blend-mode: overlay;
        }

        @keyframes gradientAnimation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .full-content-background {
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(180deg, #0a203f, #102d51, #153965); /* Darker, richer background */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
            transform: scale(0.95) translateZ(-100px); /* Slightly scaled down and pushed back */
            transition: opacity 0.8s ease-in-out, transform 0.8s ease-in-out;
            z-index: -1;
            background-image:
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 30px 30px; /* Slightly larger grid cells */
            background-position: center center;
            transform-style: preserve-3d;
        }

        .full-content-background.revealed {
            opacity: 1;
            pointer-events: auto;
            transform: scale(1) translateZ(0); /* Pops forward when revealed */
        }

        /* The peeling side panels - Enhanced 3D Look */
        .side-panel {
            position: absolute;
            top: 0;
            width: 50vw;
            height: 100vh;
            background: url(https://www.transparenttextures.com/patterns/carbon-fibre-v2.png) repeat center center #252525; /* Darker carbon fiber */
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow:
                inset 0 0 100px rgba(0,0,0,0.8), /* Deeper inner shadow */
                0 0 120px 20px rgba(0,0,0,0.9), /* Larger, softer outer shadow */
                0 0 30px rgba(0,0,0,0.6); /* Closer, sharper shadow */
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2.5rem;
            box-sizing: border-box;
            overflow-y: auto;
            transition: transform 0.1s linear, border-radius 0.1s linear, border-top-color 0.1s linear, box-shadow 0.1s linear;
            transform-style: preserve-3d;
            border-image-slice: 1;
            border-image-source: linear-gradient(to bottom, #7b68ee, #483d8b); /* Vibrant gradient border */
        }

        .side-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to bottom, rgba(255,255,255,0.1), rgba(0,0,0,0.3)); /* More pronounced gloss */
            z-index: 1;
            pointer-events: none;
            border-radius: inherit;
        }

        .side-panel.left {
            left: 0;
            transform-origin: right bottom;
            border-right: 0.35em solid #555; /* Thicker border */
            border-top-color: rgba(210, 210, 210, 0);
            border-top-right-radius: 0;
        }

        .side-panel.right {
            right: 0;
            transform-origin: left bottom;
            border-left: 0.35em solid #555; /* Thicker border */
            border-top-color: rgba(210, 210, 210, 0);
            border-top-left-radius: 0;
        }

        /* Fixed Zipper Track - More defined */
        .fixed-zipper-track {
            position: fixed;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60px; /* Even wider for stronger presence */
            height: 100vh;
            background: linear-gradient(to right, #777, #444, #777); /* More metallic sheen */
            border-left: 3px solid #999; /* Thicker, more pronounced borders */
            border-right: 3px solid #999;
            box-shadow:
                inset 0 0 20px rgba(0,0,0,0.9), /* Deeper inner shadow */
                0 0 35px rgba(0,0,0,0.7); /* Outer glow */
            z-index: 5;
            overflow: hidden;
            opacity: 1;
            transition: opacity 0.5s ease-out;
            pointer-events: auto;
        }

        .fixed-zipper-track::before,
        .fixed-zipper-track::after {
            content: "";
            position: absolute;
            top: 0;
            width: 25px; /* Wider, more prominent teeth */
            height: 100%;
            background-repeat: repeat-y;
            background-size: 100% 40px; /* Taller teeth pattern */
            filter: drop-shadow(1px 1px 4px rgba(0,0,0,0.8)); /* Stronger tooth shadow */
        }

        .fixed-zipper-track::before { /* Left teeth */
            left: 0;
            background-image: linear-gradient(to right, #ccc 0%, #999 50%, transparent 50%, transparent 100%);
            border-right: 1px solid #aaa;
        }

        .fixed-zipper-track::after { /* Right teeth */
            right: 0;
            background-image: linear-gradient(to left, #ccc 0%, #999 50%, transparent 50%, transparent 100%);
            border-left: 1px solid #aaa;
        }

        /* Zipper Mechanism (handle and track) - Highly Detailed 3D */
        #zipper-container {
            position: fixed;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 8em; /* Even wider total width */
            height: 12em; /* Taller slider */
            z-index: 100;
            cursor: grab;
            touch-action: none;
            opacity: 1;
            transition: opacity 0.5s ease-out, transform 0.1s linear;
            filter: drop-shadow(0 10px 30px rgba(0,0,0,0.9)); /* Stronger, softer overall shadow */
        }

        .slider {
            width: 5em; /* Larger slider body */
            height: 5em;
            position: absolute;
            left: 1.5em;
            border-radius: 15px 15px 30px 30px; /* More pronounced rounding */
            border: 0.7em solid transparent;
            border-top: 6em solid #555; /* Main body of slider, darker base */
            border-bottom: 0;
            top: 0.5em;
            background: linear-gradient(to bottom, #bbb, #888); /* Brighter, more defined metallic gradient */
            box-shadow:
                inset 0 4px 10px rgba(255,255,255,0.4), /* Stronger inner highlight */
                inset 0 -4px 10px rgba(0,0,0,0.7), /* Stronger inner shadow */
                0 6px 20px rgba(0,0,0,0.5); /* Subtle self-shadow */
            transform-origin: center top;
        }

        .slider:before {
            content: "";
            border-top: 4px solid #eee; /* Even lighter highlight */
            width: 5em;
            position: absolute;
            left: -0.7em;
            top: -6.1em;
            border-radius: 15px 15px 0 0;
            height: 0.6em;
            box-shadow: 0 -6px 20px 0px rgba(0,0,0,0.9);
            background: linear-gradient(to bottom, #ddd, #aaa); /* More prominent metallic top */
        }

        .slider:after {
            content: "";
            border-bottom: 4px solid #eee;
            width: 4em;
            position: absolute;
            left: 0.5em;
            top: -8px;
            border-radius: 0 0 15px 15px;
            height: 0.6em;
            box-shadow: 0 -6px 20px 0px rgba(0,0,0,0.9);
            background: linear-gradient(to bottom, #aaa, #ddd);
        }

        .hook {
            width: 1.5em; /* Thicker hook */
            height: 3em; /* Longer hook */
            background: #555;
            display: block;
            border-radius: 1.5em;
            border: 4px solid #eee; /* Lighter, more defined border */
            position: absolute;
            top: 2em;
            left: 3.25em;
            box-shadow:
                inset 0 0 10px rgba(0,0,0,0.8),
                0 4px 10px rgba(0,0,0,0.6);
            background: linear-gradient(to right, #888, #666);
        }

        .pull-tab {
            width: 4.5em; /* Wider tab */
            height: 6em; /* Longer tab */
            border: 4px solid #eee;
            display: block;
            position: absolute;
            left: 1.75em;
            top: 4em; /* Adjusted position */
            border-radius: 30px 30px 0 0;
            background: linear-gradient(to bottom, #aaa, #888);
            border-bottom: 0;
            transform-origin: center top;
            transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55); /* More bouncy transition */
            transform: rotateX(25deg); /* Start slightly tilted */
            box-shadow: 0 -6px 25px 0px rgba(0,0,0,0.9),
                        0 6px 20px rgba(0,0,0,0.4);
        }

        .pull-tab.up {
            transform: rotateX(155deg);
            box-shadow: 0 10px 30px rgba(0,0,0,0.7),
                        0 -6px 12px rgba(0,0,0,0.3);
        }

        .pull-tab:before {
            content: "";
            background: radial-gradient(circle at center, transparent 0, transparent 1.2em, #ddd 1.25em, #ddd 1.3em, #777 1.4em, #777 100%); /* More defined inner hole */
            width: 4.5em;
            height: 5em;
            position: absolute;
            margin-top: 5em;
            left: -4px;
            border-radius: 15px 15px 30px 30px;
            border: 4px solid #eee;
            box-shadow: 0 4px 12px 0px rgba(0,0,0,0.7);
            background-blend-mode: overlay;
        }

        .pull-tab:after {
            content: "";
            width: 4.5em;
            border-left: 4px solid #ddd;
            height: 2em; /* Taller */
            position: absolute;
            left: -4px;
            top: 4.7em;
            border-right: 4px solid #ddd;
            background: linear-gradient(to bottom, #888, #666);
        }

        /* Feature/Prospect Cards - More stunning 3D */
        .card-wrapper {
            width: 90%;
            max-width: 400px; /* Wider cards */
            margin-bottom: 3rem;
            position: relative;
            cursor: pointer;
            border-radius: 25px; /* More rounded corners */
            overflow: hidden;
            background-color: rgba(255, 255, 255, 0.05); /* More transparent background */
            box-shadow:
                0 15px 40px rgba(0,0,0,0.6), /* Main shadow */
                0 0 50px rgba(0,0,0,0.4) inset, /* Inner glow */
                0 0 20px rgba(0,220,255,0.3); /* Subtle blue outer glow */
            transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                        box-shadow 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                        background-color 0.5s ease;
            backdrop-filter: blur(10px); /* Stronger frosted glass effect */
            border: 2px solid rgba(255, 255, 255, 0.15); /* More prominent border */
            transform-style: preserve-3d;
        }

        .card-wrapper::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to bottom, rgba(255,255,255,0.08), transparent 60%, rgba(0,0,0,0.15));
            z-index: 1;
            border-radius: inherit;
            pointer-events: none;
        }

        .card-wrapper:hover {
            transform: translateY(-20px) scale(1.08) rotateX(7deg) translateZ(50px); /* More pronounced pop, tilt, and forward movement */
            box-shadow:
                0 25px 60px rgba(0,0,0,0.8), /* Deeper main shadow on hover */
                0 0 70px rgba(0,0,0,0.6) inset,
                0 0 40px rgba(0,220,255,0.6); /* Brighter outer glow */
            background-color: rgba(255, 255, 255, 0.1);
        }

        .card-image {
            width: 100%;
            height: 220px; /* Taller images */
            object-fit: cover;
            border-top-left-radius: 25px;
            border-top-right-radius: 25px;
            opacity: 0.85; /* More prominent image */
            filter: brightness(0.7) contrast(1.1); /* Slight photo enhancement */
            transition: filter 0.4s ease;
        }

        .card-wrapper:hover .card-image {
            filter: brightness(1) contrast(1.2); /* Image brightens on hover */
        }

        .card-content {
            padding: 2rem; /* More padding */
            background: linear-gradient(to bottom, rgba(0,0,0,0.6), rgba(0,0,0,0.8)); /* Darker, richer gradient */
            position: relative;
            z-index: 2;
            color: #e0e0e0; /* Lighter text color */
            border-bottom-left-radius: 25px;
            border-bottom-right-radius: 25px;
        }

        .card-title {
            font-size: 2rem; /* Even larger title */
            font-weight: 900; /* Ultra bolder */
            margin-bottom: 1.2rem;
            color: #ffffff;
            text-shadow: 0 3px 8px rgba(0,0,0,0.8), 0 0 15px rgba(0,200,255,0.4); /* Stronger, glowing text shadow */
        }

        .card-description {
            font-size: 1.1rem; /* Slightly larger description */
            color: #b0b0b0; /* Brighter grey for description */
            line-height: 1.7;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.7s ease-out, opacity 0.7s ease-out; /* Slower, smoother reveal */
            opacity: 0;
            text-shadow: 0 1px 3px rgba(0,0,0,0.6);
        }

        .card-wrapper:hover .card-description {
            max-height: 300px; /* Allow more text to show */
            opacity: 1;
        }

        /* Auth Page Styling - Highly Detailed 3D */
        .auth-container {
            background-color: rgba(0, 0, 0, 0.5); /* Darker, more solid base */
            backdrop-filter: blur(20px) brightness(0.7); /* Stronger blur, slightly darker */
            padding: 3.5rem; /* More generous padding */
            border-radius: 30px; /* More rounded */
            box-shadow:
                0 30px 90px rgba(0, 0, 0, 0.7), /* Large, soft shadow */
                0 0 60px rgba(0,255,255,0.3) inset, /* Inner cyan glow */
                0 0 40px rgba(0,255,255,0.5), /* Outer cyan glow */
                inset 0 0 40px rgba(0,0,0,0.9); /* Deep inner shadow for recess */
            max-width: 550px; /* Wider container */
            width: 90%;
            text-align: center;
            display: none;
            border: 4px solid rgba(0, 255, 255, 0.5); /* Glowing cyan border */
            transform-style: preserve-3d;
            animation: fadeInScale 1s ease-out forwards; /* Add an entry animation */
            position: relative; /* For particle effect */
            overflow: hidden;
        }
        
        /* Particle effect for auth container */
        .auth-container::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at top left, rgba(0,200,255,0.1) 0%, transparent 40%),
                        radial-gradient(circle at bottom right, rgba(255,0,255,0.1) 0%, transparent 40%);
            mix-blend-mode: screen;
            pointer-events: none;
            animation: particleShift 15s infinite alternate ease-in-out;
            z-index: -1;
        }

        @keyframes particleShift {
            0% { transform: translate(0, 0); }
            100% { transform: translate(10%, 10%); }
        }

        @keyframes fadeInScale {
            from { opacity: 0; transform: scale(0.8) translateY(50px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .auth-container h2 {
            font-size: 3.8rem; /* Much larger title */
            font-weight: 900; /* Ultra bold */
            color: #e0f7fa; /* Lighter cyan-tinged white */
            margin-bottom: 3rem;
            text-shadow:
                0 4px 10px rgba(0,0,0,0.9), /* Deeper text shadow */
                0 0 25px rgba(0,200,255,0.8); /* Stronger cyan glow for text */
        }

        .auth-form {
            position: relative; /* Needed for floating labels */
        }

        .input-group {
            position: relative;
            margin-bottom: 2rem;
        }

        .auth-form input {
            width: calc(100% - 28px); /* Account for more padding/border */
            padding: 20px 14px; /* More padding */
            border: 3px solid #00aaff; /* Brighter blue border */
            border-radius: 15px; /* More rounded */
            font-size: 1.25rem; /* Larger font */
            background-color: rgba(0, 0, 0, 0.7); /* Even darker input fields */
            color: #e6f7ff; /* Lighter text color */
            transition: border-color 0.4s ease, box-shadow 0.4s ease, background-color 0.4s ease, transform 0.2s ease;
            box-shadow: inset 0 4px 10px rgba(0,0,0,0.9), inset 0 -2px 4px rgba(255,255,255,0.15); /* Stronger inset shadow */
            text-shadow: 0 1px 3px rgba(0,0,0,0.6);
            /* Important for floating label: padding-top ensures space */
            padding-top: 30px;
            outline: none; /* Remove default outline */
        }
        
        .auth-form label {
            position: absolute;
            top: 20px; /* Initial position for floating label */
            left: 14px;
            color: #99d0e6;
            font-size: 1.25rem;
            pointer-events: none; /* Allows clicks to pass through */
            transition: all 0.3s ease-out;
            text-shadow: 0 1px 2px rgba(0,0,0,0.4);
            z-index: 1; /* Ensure label is above input when floating */
        }

        /* The key fix: label floats when input is focused OR has content */
        .auth-form input:focus + label,
        .auth-form input.has-content + label { /* Using a class instead of :not(:placeholder-shown) */
            top: 5px; /* Move up when focused or has content */
            font-size: 0.9rem;
            color: #00eaff;
            text-shadow: 0 0 5px rgba(0,255,255,0.7);
        }

        .auth-form input:focus {
            border-color: #00eaff; /* Brighter focus glow */
            box-shadow:
                0 0 0 8px rgba(0, 234, 255, 0.5), /* Stronger outer glow on focus */
                inset 0 4px 10px rgba(0,0,0,0.9),
                inset 0 -2px 4px rgba(255,255,255,0.15);
            background-color: rgba(0, 0, 0, 0.8);
            transform: translateY(-2px); /* Slight lift on focus */
        }

        /* Password strength meter */
        .password-strength-container {
            width: 100%;
            height: 10px;
            background-color: rgba(255,255,255,0.1);
            border-radius: 5px;
            margin-top: -1rem; /* Adjust to align with input */
            margin-bottom: 1.5rem;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }

        .password-strength-bar {
            height: 100%;
            width: 0%;
            background-color: #f0f0f0; /* Default */
            border-radius: 5px;
            transition: width 0.3s ease-out, background-color 0.3s ease-out;
        }
        .password-strength-bar.weak { background-color: #dc3545; }
        .password-strength-bar.medium { background-color: #ffc107; }
        .password-strength-bar.strong { background-color: #28a745; }

        .password-strength-text {
            font-size: 0.9rem;
            color: #aaa;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
            text-align: left;
            padding-left: 5px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }

        /* Show Password Toggle */
        .password-toggle {
            position: absolute;
            right: 25px;
            top: 25px; /* Adjusted to new input padding */
            color: #99d0e6;
            cursor: pointer;
            font-size: 1.2rem;
            z-index: 2; /* Above input */
            transition: color 0.3s ease;
        }
        .password-toggle:hover {
            color: #00eaff;
        }

        /* Validation Icons */
        .validation-icon {
            position: absolute;
            right: 25px;
            top: 25px; /* Adjusted to new input padding */
            font-size: 1.2rem;
            z-index: 2;
        }
        .validation-icon.valid { color: #28a745; }
        .validation-icon.invalid { color: #dc3545; }

        .auth-form button {
            width: 100%;
            padding: 20px; /* More padding */
            background: linear-gradient(90deg, #007bff, #00d0ff, #007bff); /* More vibrant, multi-color blue gradient */
            background-size: 300% auto; /* For animated gradient */
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1.4rem; /* Larger font */
            font-weight: 800; /* Bolder */
            cursor: pointer;
            transition: background-position 0.6s ease, transform 0.3s ease, box-shadow 0.4s ease;
            margin-top: 2rem;
            box-shadow:
                0 10px 30px rgba(0, 123, 255, 0.5), /* Main button shadow */
                inset 0 3px 8px rgba(255,255,255,0.4), /* Top highlight */
                inset 0 -4px 10px rgba(0,0,0,0.7); /* Bottom shadow */
            text-shadow: 0 2px 5px rgba(0,0,0,0.6);
            border: 2px solid rgba(0, 200, 255, 0.6); /* Subtle border matching glow */
            position: relative;
            overflow: hidden;
        }

        .auth-form button.loading {
            pointer-events: none;
            background-position: 100% center; /* Keep gradient static when loading */
        }

        .auth-form button .spinner {
            display: none;
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid #fff;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
        }

        .auth-form button.loading .spinner {
            display: inline-block;
        }

        .auth-form button.loading .button-text {
            visibility: hidden;
        }

        @keyframes spin {
            0% { transform: translate(-50%, -50%) rotate(0deg); }
            100% { transform: translate(-50%, -50%) rotate(360deg); }
        }

        .auth-form button:hover {
            background-position: right center; /* Animate gradient */
            transform: translateY(-8px) scale(1.03); /* More lift and slight scale */
            box-shadow:
                0 20px 45px rgba(0, 123, 255, 0.7), /* Stronger shadow on hover */
                inset 0 3px 8px rgba(255,255,255,0.4),
                inset 0 -4px 10px rgba(0,0,0,0.7);
            border-color: rgba(0, 255, 255, 0.9);
        }

        .auth-form button:active {
            transform: translateY(0px) scale(0.99); /* Press down effect */
            box-shadow:
                0 5px 20px rgba(0, 123, 255, 0.3), /* Subtler shadow when pressed */
                inset 0 2px 5px rgba(255,255,255,0.2),
                inset 0 4px 10px rgba(0,0,0,0.9); /* Deeper inner shadow */
        }

        .auth-toggle {
            margin-top: 2.5rem;
            font-size: 1.15rem; /* Slightly larger toggle text */
            color: #d0eaff; /* Lighter, blue-tinged text */
            text-shadow: 0 1px 3px rgba(0,0,0,0.6);
        }

        .auth-toggle a {
            color: #00eaff; /* Brighter, glowing link color */
            text-decoration: none;
            font-weight: 700;
            transition: color 0.3s ease, text-shadow 0.3s ease;
        }

        .auth-toggle a:hover {
            text-decoration: underline;
            color: #00ffff; /* Even brighter on hover */
            text-shadow: 0 0 10px rgba(0,255,255,0.9);
        }

        /* Chatbot Styling - Enhanced 3D Look */
        .chatbot-container {
            width: 90%;
            max-width: 750px; /* Even wider chatbot */
            height: 550px; /* Taller chatbot */
            background-color: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(20px) brightness(0.7);
            border-radius: 30px; /* More rounded */
            box-shadow:
                0 30px 90px rgba(0, 0, 0, 0.7),
                0 0 60px rgba(0,255,255,0.3) inset,
                0 0 40px rgba(0,255,255,0.5),
                inset 0 0 40px rgba(0,0,0,0.9);
            display: none;
            flex-direction: column;
            margin-top: 3rem;
            overflow: hidden;
            border: 4px solid rgba(0, 255, 255, 0.5);
            animation: fadeInScale 1s ease-out forwards;
        }

        .chat-messages {
            flex-grow: 1;
            padding: 1.8rem; /* More padding */
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px; /* More space between messages */
            background-color: rgba(0, 0, 0, 0.4); /* Darker chat background */
            border-bottom: 2px solid rgba(255,255,255,0.1);
            scrollbar-width: thin;
            scrollbar-color: #00aaff #333;
        }
        .chat-messages::-webkit-scrollbar {
            width: 10px;
        }
        .chat-messages::-webkit-scrollbar-track {
            background: #333;
            border-radius: 10px;
        }
        .chat-messages::-webkit-scrollbar-thumb {
            background-color: #00aaff;
            border-radius: 10px;
            border: 3px solid #333;
        }

        .chat-message {
            max-width: 85%; /* Wider messages */
            padding: 1.2rem 1.8rem; /* More padding */
            border-radius: 30px; /* More rounded */
            line-height: 1.7;
            word-wrap: break-word;
            box-shadow: 0 5px 20px rgba(0,0,0,0.4), inset 0 2px 6px rgba(255,255,255,0.15);
            animation: messagePopIn 0.4s ease-out; /* Pop-in animation */
        }
        
        @keyframes messagePopIn {
            from { opacity: 0; transform: translateY(10px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .chat-message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #0069d9, #00b0ff); /* Diagonal blue gradient */
            color: white;
            border-bottom-right-radius: 15px; /* Slightly less rounded on one corner */
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
        }

        .chat-message.bot {
            align-self: flex-start;
            background: linear-gradient(135deg, #4a4a4a, #6a6a6a); /* Diagonal grey gradient */
            color: #f5f5f5;
            border-bottom-left-radius: 15px;
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
        }

        .chat-input-area {
            display: flex;
            padding: 1.5rem; /* More padding */
            border-top: 2px solid #555;
            background-color: rgba(0, 0, 0, 0.6); /* Darker input area */
            align-items: center;
        }

        .chat-input-area input {
            flex-grow: 1;
            padding: 18px; /* More padding */
            border: 3px solid #00aaff;
            border-radius: 35px; /* Fully rounded, larger */
            margin-right: 10px; /* Space for microphone icon */
            font-size: 1.15rem;
            background-color: rgba(0, 0, 0, 0.7);
            color: #e6f7ff;
            box-shadow: inset 0 3px 8px rgba(0,0,0,0.8), inset 0 -1px 3px rgba(255,255,255,0.15);
            transition: border-color 0.4s ease, box-shadow 0.4s ease;
            outline: none;
        }

        .chat-input-area input:focus {
            border-color: #00eaff;
            box-shadow:
                0 0 0 6px rgba(0, 234, 255, 0.5),
                inset 0 3px 8px rgba(0,0,0,0.8),
                inset 0 -1px 3px rgba(255,255,255,0.15);
        }

        .chat-input-area .microphone-btn {
            background: none;
            border: none;
            color: #00eaff; /* Bright cyan */
            font-size: 1.8rem; /* Larger icon */
            cursor: pointer;
            padding: 8px;
            border-radius: 50%;
            transition: background-color 0.3s ease, transform 0.2s ease, color 0.3s ease;
            position: relative;
            margin-right: 10px; /* Space between mic and send */
            box-shadow: 0 0 0 rgba(0,255,255,0); /* Initial shadow for pulse */
        }
        
        .chat-input-area .microphone-btn:hover {
            background-color: rgba(0,255,255,0.1);
            transform: scale(1.1);
            color: #00ffff;
        }

        .chat-input-area .microphone-btn.listening {
            color: #ff0077; /* Red/pink when listening */
            animation: pulse-mic 1.5s infinite ease-in-out;
            box-shadow: 0 0 15px rgba(255,0,119,0.7); /* Stronger pink shadow */
        }

        @keyframes pulse-mic {
            0% { box-shadow: 0 0 0 rgba(255,0,119,0.7); }
            50% { box-shadow: 0 0 20px rgba(255,0,119,1); }
            100% { box-shadow: 0 0 0 rgba(255,0,119,0.7); }
        }

        .chat-input-area button {
            padding: 15px 35px; /* Larger button */
            background: linear-gradient(90deg, #007bff, #00c0ff);
            color: white;
            border: none;
            border-radius: 35px;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
            font-weight: 700;
            box-shadow: 0 6px 20px rgba(0, 123, 255, 0.5), inset 0 2px 5px rgba(255,255,255,0.25);
            text-shadow: 0 1px 3px rgba(0,0,0,0.4);
        }

        .chat-input-area button:hover {
            background: linear-gradient(90deg, #0056b3, #0099e6);
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0, 123, 255, 0.7), inset 0 2px 5px rgba(255,255,255,0.25);
        }
        .chat-input-area button:active {
            transform: translateY(0);
            box-shadow: 0 3px 10px rgba(0, 123, 255, 0.3), inset 0 2px 5px rgba(255,255,255,0.25);
        }


        /* Message Box Styling - Enhanced */
        #messageBox {
            background-color: #333;
            color: white;
            padding: 15px 30px; /* More padding */
            border-radius: 12px; /* More rounded */
            box-shadow: 0 8px 25px rgba(0,0,0,0.6); /* Stronger shadow */
            z-index: 200;
            transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55); /* Bouncier transform transition */
            position: fixed;
            bottom: 30px;
            right: 30px;
            opacity: 0;
            pointer-events: none;
            font-weight: 600; /* Bolder text */
            min-width: 250px; /* Ensure a minimum width */
            text-align: center;
            border: 2px solid rgba(255,255,255,0.25); /* Subtle border */
            transform: translateY(20px); /* Start slightly off-screen */
        }

        #messageBox.active {
            opacity: 1;
            transform: translateY(0);
            pointer-events: auto;
        }

        #messageBox.error {
            background-color: #c82333; /* Darker red */
            box-shadow: 0 8px 25px rgba(200,35,51,0.6); /* Red glow for errors */
            border-color: rgba(220,53,69,0.5);
        }
        #messageBox.success {
            background-color: #218838; /* Darker green */
            box-shadow: 0 8px 25px rgba(33,136,56,0.6); /* Green glow for success */
            border-color: rgba(40,167,69,0.5);
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .side-panel {
                width: 100vw;
                padding: 1.5rem;
            }
            .side-panel.left { transform: translateX(0); }
            .side-panel.right { transform: translateX(0); }
            #zipper-container {
                left: calc(50% - 4em); /* Adjust for wider zipper */
            }
            .card-wrapper {
                max-width: 95%;
                margin-bottom: 2rem;
            }
            .auth-container {
                padding: 2.5rem;
            }
            .auth-container h2 {
                font-size: 2.8rem;
            }
            .auth-form input {
                padding: 15px 10px;
                font-size: 1.1rem;
                padding-top: 25px;
            }
            .auth-form label {
                top: 15px;
                font-size: 1.1rem;
            }
            .auth-form input:focus + label,
            .auth-form input.has-content + label { /* Updated for .has-content */
                top: 3px;
                font-size: 0.8rem;
            }
            .auth-form button {
                padding: 15px;
                font-size: 1.2rem;
            }
            .chatbot-container {
                height: 450px;
                margin-top: 2rem;
            }
             .chat-input-area input {
                padding: 12px;
                margin-right: 10px;
                font-size: 1rem;
            }
            .chat-input-area button {
                padding: 10px 25px;
                font-size: 1rem;
            }
            .card-title {
                font-size: 1.8rem;
            }
            .card-description {
                font-size: 1rem;
            }
            .password-toggle, .validation-icon {
                top: 20px;
                right: 15px;
            }
            #messageBox {
                bottom: 20px;
                right: 20px;
                padding: 12px 20px;
                min-width: 180px;
            }
        }

         @media (max-width: 480px) {
            .auth-container h2 {
                font-size: 2.2rem;
            }
            .auth-form input {
                padding: 10px;
                font-size: 0.95rem;
                padding-top: 20px;
            }
            .auth-form label {
                top: 10px;
                font-size: 0.95rem;
            }
            .auth-form input:focus + label,
            .auth-form input.has-content + label { /* Updated for .has-content */
                top: 2px;
                font-size: 0.7rem;
            }
            .auth-form button {
                padding: 12px;
                font-size: 1.1rem;
            }
            .auth-toggle {
                font-size: 0.9rem;
            }
            .chat-message {
                max-width: 95%;
                padding: 1rem 1.2rem;
            }
            .chat-input-area input {
                font-size: 0.9rem;
            }
            .chat-input-area button {
                font-size: 0.9rem;
            }
            .card-title {
                font-size: 1.6rem;
            }
            .card-description {
                font-size: 0.9rem;
            }
            .password-toggle, .validation-icon {
                top: 15px;
                right: 10px;
                font-size: 1rem;
            }
            #messageBox {
                bottom: 15px;
                right: 15px;
                padding: 10px 15px;
                min-width: 150px;
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>
    <div id="fullPageBackgroundWrapper"></div>

    <div class="full-content-background" id="fullContentBackground">
        <div class="auth-container" id="authContainer">
            <h2 id="authTitle">Sign In</h2>
            <form class="auth-form" id="authForm">
                <div class="input-group">
                    <input type="text" id="username">
                    <label for="username" id="usernameLabel">Name</label>
                    <i class="fas fa-check-circle validation-icon valid-username" style="display:none;"></i>
                    <i class="fas fa-times-circle validation-icon invalid-username" style="display:none;"></i>
                </div>
                <div class="input-group">
                    <input type="email" id="email" required>
                    <label for="email">Email</label>
                    <i class="fas fa-check-circle validation-icon valid-email" style="display:none;"></i>
                    <i class="fas fa-times-circle validation-icon invalid-email" style="display:none;"></i>
                </div>
                <div class="input-group">
                    <input type="password" id="password" required>
                    <label for="password">Password</label>
                    <i class="fas fa-eye password-toggle" id="togglePassword"></i>
                    <i class="fas fa-check-circle validation-icon valid-password" style="display:none;"></i>
                    <i class="fas fa-times-circle validation-icon invalid-password" style="display:none;"></i>
                    <div class="password-strength-container">
                        <div class="password-strength-bar" id="passwordStrengthBar"></div>
                    </div>
                    <div class="password-strength-text" id="passwordStrengthText"></div>
                </div>
                <button type="submit" id="authSubmitBtn">
                    <span class="button-text">Sign In</span>
                    <div class="spinner"></div>
                </button>
            </form>
            <p class="auth-toggle">
                Don't have an account? <a href="#" id="toggleAuth">Sign Up</a>
            </p>
        </div>

        <div class="chatbot-container">
            <div class="chat-messages" id="chatMessages">
                <div class="chat-message bot">Hello! How can I help you today?</div>
            </div>
            <div class="chat-input-area">
                <button id="microphoneBtn" class="microphone-btn"><i class="fas fa-microphone"></i></button>
                <input type="text" id="chatInput" placeholder="Type your message...">
                <button id="sendChatBtn">Send</button>
            </div>
            <button id="signOutBtn" class="auth-form button" style="margin-top: 1rem; background: linear-gradient(90deg, #dc3545, #e05663); border-color: rgba(220,53,69,0.6);">Sign Out</button>
        </div>
    </div>

    <div class="fixed-zipper-track" id="fixedZipperTrack"></div>

    <div class="side-panel left" id="leftPanel">
        <h2 class="text-5xl font-bold mb-10 text-center text-white" style="text-shadow: 0 0 20px rgba(0,255,255,0.8), 0 0 8px rgba(0,255,255,0.6);">Bot Features</h2>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1596547668581-22874136696b?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Feature 1" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Natural Language Processing</h3>
                <p class="card-description">Our bot understands and processes human language with remarkable accuracy, allowing for natural and intuitive conversations. It can comprehend context, sentiment, and user intent, providing intelligent and relevant responses.</p>
            </div>
        </div>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1516110833957-e17ad1421061?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Feature 2" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Contextual Memory</h3>
                <p class="card-description">The bot remembers past interactions within a conversation, providing more relevant and personalized responses. It can refer back to previous topics and details, ensuring continuity and a seamless user experience.</p>
            </div>
        </div>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1581091226065-96105f25a720?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Feature 3" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Seamless Integrations</h3>
                <p class="card-description">Easily connects with popular applications and services, enhancing its utility across various platforms and workflows. Supports robust APIs for custom integrations, making it a versatile tool for any ecosystem.</p>
            </div>
        </div>
    </div>

    <div class="side-panel right" id="rightPanel">
        <h2 class="text-5xl font-bold mb-10 text-center text-white" style="text-shadow: 0 0 20px rgba(255,0,255,0.8), 0 0 8px rgba(255,0,255,0.6);">Future Prospects</h2>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1510519153173-95388c7d6c6e?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Prospect 1" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Advanced Personalization</h3>
                <p class="card-description">Future updates will enable the bot to learn and adapt to individual user preferences and behaviors over time, offering highly tailored experiences and recommendations. This will create truly unique and effective interactions.</p>
            </div>
        </div>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1550005825-911e0e88383e?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Prospect 2" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Multimodal Communication</h3>
                <p class="card-description">The bot will evolve to understand and generate responses not just through text, but also through voice, images, and video, creating a richer and more immersive interaction experience across all senses.</p>
            </div>
        </div>
        <div class="card-wrapper">
            <img src="https://images.unsplash.com/photo-1579705353592-2ce96a793a61?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="Prospect 3" class="card-image">
            <div class="card-content">
                <h3 class="card-title">Proactive Assistance</h3>
                <p class="card-description">Moving beyond reactive responses, the bot will anticipate user needs and offer proactive suggestions or complete tasks autonomously, significantly boosting user productivity and satisfaction in a seamless manner.</p>
            </div>
        </div>
    </div>

    <div id="zipper-container">
        <span class="slider"></span>
        <span class="pull-tab" id="pullTab"></span>
        <span class="hook"></span>
    </div>

    <div id="messageBox"></div>

    <script type="module">
        // Global variables for Firebase - These are placeholders.
        // REPLACE with your actual Firebase config if deploying outside Canvas.
        const appId = 'your-streamlit-app-id'; // You can define a unique ID for your Streamlit app
        const firebaseConfig = {
            // Replace with your actual Firebase project configuration
            apiKey: "YOUR_API_KEY", // IMPORTANT: Fill this in!
            authDomain: "YOUR_AUTH_DOMAIN", // IMPORTANT: Fill this in!
            projectId: "YOUR_PROJECT_ID", // IMPORTANT: Fill this in!
            storageBucket: "YOUR_STORAGE_BUCKET",
            messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
            appId: "YOUR_APP_ID" // IMPORTANT: Fill this in!
        };
        const initialAuthToken = null; // Not used outside Canvas environment typically

        // Firebase imports
        import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
        import { getAuth, signInAnonymously, createUserWithEmailAndPassword, signInWithEmailAndPassword, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
        import { getFirestore, doc, setDoc, collection, addDoc, onSnapshot, query, orderBy, serverTimestamp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

        // Initialize Firebase
        let app;
        let db;
        let auth;
        let userId = 'anonymous'; // Default to anonymous
        let isFirebaseActive = false; // Flag to check if Firebase is properly initialized

        // Function to initialize Firebase and authenticate
        async function initializeFirebaseAndAuth() {
            try {
                // Check if Firebase config is provided and not default placeholders
                if (Object.keys(firebaseConfig).length > 0 && firebaseConfig.apiKey && firebaseConfig.apiKey !== "YOUR_API_KEY") {
                    app = initializeApp(firebaseConfig);
                    db = getFirestore(app);
                    auth = getAuth(app);
                    isFirebaseActive = true;

                    // Sign in anonymously if no user is already logged in
                    onAuthStateChanged(auth, async (user) => {
                        if (!user) {
                            try {
                                await signInAnonymously(auth);
                                console.log("Signed in anonymously.");
                            } catch (anonError) {
                                console.error("Error signing in anonymously:", anonError);
                                showMessageBox("Anonymous sign-in failed. Some features may be limited.", "error");
                                userId = crypto.randomUUID(); // Fallback to a random ID
                                isFirebaseActive = false;
                            }
                        } else {
                            userId = user.uid;
                            console.log("User ID:", userId);
                            // Only set up chat listener if user is logged in (including anonymously) and Firebase is active
                            if (isFirebaseActive) {
                                setupChatListener();
                            }
                        }
                    });
                } else {
                    console.warn("Firebase config not provided or incomplete. Auth and Firestore will not be fully functional.");
                    showMessageBox("Firebase not configured. Auth and chat persistence will be disabled. Update the firebaseConfig in the HTML.", "error");
                    // Disable relevant UI elements if Firebase is not active
                    if(authSubmitBtn) authSubmitBtn.disabled = true;
                    if(sendChatBtn) sendChatBtn.disabled = true;
                    if(chatInput) chatInput.disabled = true;
                    if(microphoneBtn) microphoneBtn.disabled = true;
                    if(signOutBtn) signOutBtn.style.display = 'none'; // Hide sign out button
                    userId = crypto.randomUUID(); // Use a temporary UUID for local chat
                }
            } catch (error) {
                console.error("Error initializing Firebase or during authentication:", error);
                showMessageBox(`Error initializing Firebase: ${error.message}. Auth and chat persistence disabled. Update the firebaseConfig in the HTML.`, "error");
                if(authSubmitBtn) authSubmitBtn.disabled = true;
                if(sendChatBtn) sendChatBtn.disabled = true;
                if(chatInput) chatInput.disabled = true;
                if(microphoneBtn) microphoneBtn.disabled = true;
                if(signOutBtn) signOutBtn.style.display = 'none'; // Hide sign out button
                userId = crypto.randomUUID(); // Use a temporary UUID for local chat
                isFirebaseActive = false;
            }
        }

        // Call the initialization function
        initializeFirebaseAndAuth();

        // DOM Elements
        const zipperContainer = document.getElementById('zipper-container');
        const pullTab = document.getElementById('pullTab');
        const leftPanel = document.getElementById('leftPanel');
        const rightPanel = document.getElementById('rightPanel');
        const fixedZipperTrack = document.getElementById('fixedZipperTrack');
        const fullContentBackground = document.getElementById('fullContentBackground');
        const authContainer = document.getElementById('authContainer');
        const chatbotContainer = document.querySelector('.chatbot-container');
        const authForm = document.getElementById('authForm');
        const authTitle = document.getElementById('authTitle');
        const usernameInput = document.getElementById('username');
        const usernameLabel = document.getElementById('usernameLabel');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const authSubmitBtn = document.getElementById('authSubmitBtn');
        const toggleAuthBtn = document.getElementById('toggleAuth');
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendChatBtn = document.getElementById('sendChatBtn');
        const togglePassword = document.getElementById('togglePassword');
        const passwordStrengthBar = document.getElementById('passwordStrengthBar');
        const passwordStrengthText = document.getElementById('passwordStrengthText');
        const microphoneBtn = document.getElementById('microphoneBtn');
        const signOutBtn = document.getElementById('signOutBtn');


        // Validation icons
        const emailValidIcon = document.querySelector('.valid-email');
        const emailInvalidIcon = document.querySelector('.invalid-email');
        const passwordValidIcon = document.querySelector('.valid-password');
        const passwordInvalidIcon = document.querySelector('.invalid-password');
        const usernameValidIcon = document.querySelector('.valid-username');
        const usernameInvalidIcon = document.querySelector('.invalid-username');


        let isDragging = false;
        let initialClientY;
        let initialZipperTop;
        let maxZipperTop; // Max top value for the zipper container

        let isSigningUp = false;
        let recognition; // For Web Speech API

        // Message Box functionality (instead of alert)
        function showMessageBox(message, type = 'info') {
            const messageBox = document.getElementById('messageBox');
            messageBox.textContent = message;
            messageBox.classList.remove('error', 'success', 'active', 'info');
            messageBox.classList.add(type);
            messageBox.classList.add('active'); // Trigger animation

            setTimeout(() => {
                messageBox.classList.remove('active'); // Fade out
            }, 3000);
        }

        // --- Zipper Drag Logic ---
        function startDrag(e) {
            isDragging = true;
            zipperContainer.style.cursor = 'grabbing';
            const clientY = e.clientY || e.touches[0].clientY;
            initialClientY = clientY;
            initialZipperTop = zipperContainer.offsetTop;

            pullTab.classList.remove('up');

            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', endDrag);
            document.addEventListener('touchmove', drag, { passive: false });
            document.addEventListener('touchend', endDrag);
        }

        function drag(e) {
            if (!isDragging) return;

            e.preventDefault();
            const clientY = e.clientY || e.touches[0].clientY;
            const deltaY = clientY - initialClientY;
            let newTop = initialZipperTop + deltaY;

            newTop = Math.max(0, Math.min(newTop, maxZipperTop));
            zipperContainer.style.top = `${newTop}px`;

            updatePanels(newTop);
        }

        function endDrag() {
            isDragging = false;
            zipperContainer.style.cursor = 'grab';

            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', endDrag);
            document.removeEventListener('touchmove', drag);
            document.removeEventListener('touchend', endDrag);

            const currentZipperTop = zipperContainer.offsetTop;
            const openThreshold = maxZipperTop * 0.7;

            if (currentZipperTop >= openThreshold) {
                zipperContainer.style.top = `${maxZipperTop}px`;
                updatePanels(maxZipperTop);
                fullContentBackground.classList.add('revealed');
                authContainer.style.display = 'block'; // Show auth container
                chatbotContainer.style.display = 'none';
                signOutBtn.style.display = 'none'; // Initially hide sign out button in auth view

                zipperContainer.style.opacity = '0';
                zipperContainer.style.pointerEvents = 'none';
                fixedZipperTrack.style.opacity = '0';
                fixedZipperTrack.style.pointerEvents = 'none';

                // Check if user is already authenticated
                if (auth && auth.currentUser && !auth.currentUser.isAnonymous) {
                     showChatbotAfterAuth();
                }

            } else {
                zipperContainer.style.top = '0px';
                updatePanels(0);
                fullContentBackground.classList.remove('revealed');
                authContainer.style.display = 'none';
                chatbotContainer.style.display = 'none';

                zipperContainer.style.opacity = '1';
                zipperContainer.style.pointerEvents = 'auto';
                fixedZipperTrack.style.opacity = '1';
                fixedZipperTrack.style.pointerEvents = 'auto';
            }
        }

        function updatePanels(currentZipperTop) {
            const progress = currentZipperTop / maxZipperTop;

            const panelTransformOffset = progress * 100;
            const panelSkewAngle = progress * 10;
            const panelRotateY = progress * 7; // Slightly more rotation
            const panelTranslateZ = progress * 70; // More Z-axis translation for deeper 3D

            leftPanel.style.transform = `translateX(-${panelTransformOffset}vw) skewY(-${panelSkewAngle}deg) rotateY(${panelRotateY}deg) translateZ(${panelTranslateZ}px)`;
            rightPanel.style.transform = `translateX(${panelTransformOffset}vw) skewY(${panelSkewAngle}deg) rotateY(-${panelRotateY}deg) translateZ(${panelTranslateZ}px)`;

            const borderRadiusValue = progress * 180; // Larger radius
            leftPanel.style.borderTopRightRadius = `${borderRadiusValue}px`;
            rightPanel.style.borderTopLeftRadius = `${borderRadiusValue}px`;

            const borderOpacity = progress * 1.5; // Fade in faster
            leftPanel.style.borderTopColor = `rgba(210, 210, 210, ${Math.min(1, borderOpacity)})`;
            rightPanel.style.borderTopColor = `rgba(210, 210, 210, ${Math.min(1, borderOpacity)})`;

            fullContentBackground.style.opacity = Math.min(1, progress * 2);
            fullContentBackground.style.transform = `scale(${0.95 + (0.05 * Math.min(1, progress * 2))}) translateZ(${ -100 + (100 * Math.min(1, progress * 2))}px)`; // Scale and move Z

            if (progress > 0.1) {
                pullTab.classList.add('up');
            } else {
                pullTab.classList.remove('up');
            }
        }

        // Initialize layout and event listeners on window load
        window.onload = () => {
            maxZipperTop = window.innerHeight - zipperContainer.offsetHeight;

            zipperContainer.style.top = '0px';
            updatePanels(0);

            zipperContainer.addEventListener('mousedown', startDrag);
            zipperContainer.addEventListener('touchstart', startDrag, { passive: false });

            // Ensure labels are correctly positioned on load, especially for autofilled fields
            document.querySelectorAll('.input-group input').forEach(input => {
                if (input.value !== '') {
                    input.classList.add('has-content');
                }
                input.addEventListener('input', () => {
                    if (input.value !== '') {
                        input.classList.add('has-content');
                    } else {
                        input.classList.remove('has-content');
                    }
                    // Re-validate on input change
                    if (input.id === 'email') validateEmail();
                    if (input.id === 'password') validatePassword();
                    if (input.id === 'username') validateUsername();
                });
            });
        };

        window.onresize = () => {
            maxZipperTop = window.innerHeight - zipperContainer.offsetHeight;
            const currentZipperTop = zipperContainer.offsetTop;
            updatePanels(currentZipperTop);
        };

        // --- Authentication & Chatbot Logic ---
        function showChatbotAfterAuth() {
            authContainer.style.display = 'none';
            chatbotContainer.style.display = 'flex';
            signOutBtn.style.display = 'block'; // Show sign out button
            chatMessages.scrollTop = chatMessages.scrollHeight;
            showMessageBox("Welcome! You can now chat.", "success");
            // Clear current chat messages for a fresh start with authenticated user
            chatMessages.innerHTML = '<div class="chat-message bot">Hello! How can I help you today?</div>';
            // Setup listener for this user's chat
            if (isFirebaseActive && auth && auth.currentUser) {
                setupChatListener();
            } else {
                console.warn("Firebase not active or user not authenticated for chat listener setup.");
            }
        }

        // Real-time Input Validation and Floating Labels
        function validateEmail() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (emailInput.value === '') {
                emailValidIcon.style.display = 'none';
                emailInvalidIcon.style.display = 'none';
                return false;
            }
            if (emailRegex.test(emailInput.value)) {
                emailValidIcon.style.display = 'inline-block';
                emailInvalidIcon.style.display = 'none';
                return true;
            } else {
                emailValidIcon.style.display = 'none';
                emailInvalidIcon.style.display = 'inline-block';
                return false;
            }
        }

        function validatePassword() {
            const password = passwordInput.value;
            let strength = 0;
            let feedback = '';

            if (password.length >= 6) {
                strength += 1;
                feedback += 'Length (6+ chars) ';
            }
            if (/[A-Z]/.test(password)) {
                strength += 1;
                feedback += 'Uppercase ';
            }
            if (/[a-z]/.test(password)) {
                strength += 1;
                feedback += 'Lowercase ';
            }
            if (/[0-9]/.test(password)) {
                strength += 1;
                feedback += 'Number ';
            }
            if (/[^A-Za-z0-9]/.test(password)) {
                strength += 1;
                feedback += 'Special Char ';
            }

            let barWidth = (strength / 5) * 100;
            passwordStrengthBar.style.width = `${barWidth}%`;
            passwordStrengthBar.classList.remove('weak', 'medium', 'strong');

            if (strength <= 2) {
                passwordStrengthBar.classList.add('weak');
                passwordStrengthText.textContent = 'Weak';
                passwordStrengthText.style.color = '#dc3545';
                passwordValidIcon.style.display = 'none';
                passwordInvalidIcon.style.display = 'inline-block';
            } else if (strength <= 4) {
                passwordStrengthBar.classList.add('medium');
                passwordStrengthText.textContent = 'Medium';
                passwordStrengthText.style.color = '#ffc107';
                passwordValidIcon.style.display = 'none';
                passwordInvalidIcon.style.display = 'inline-block'; // Still invalid if not strong enough
            } else {
                passwordStrengthBar.classList.add('strong');
                passwordStrengthText.textContent = 'Strong';
                passwordStrengthText.style.color = '#28a745';
                passwordValidIcon.style.display = 'inline-block';
                passwordInvalidIcon.style.display = 'none';
            }

            if (password.length === 0) {
                passwordStrengthBar.style.width = '0%';
                passwordStrengthText.textContent = '';
                passwordValidIcon.style.display = 'none';
                passwordInvalidIcon.style.display = 'none';
                return false;
            }
            return strength >= 5; // Return true only if strong
        }

        function validateUsername() {
            if (usernameInput.value.length >= 3) {
                usernameValidIcon.style.display = 'inline-block';
                usernameInvalidIcon.style.display = 'none';
                return true;
            } else if (usernameInput.value.length > 0) {
                usernameValidIcon.style.display = 'none';
                usernameInvalidIcon.style.display = 'inline-block';
                return false;
            } else {
                usernameValidIcon.style.display = 'none';
                usernameInvalidIcon.style.display = 'none';
                return false;
            }
        }


        // Toggle Password Visibility
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            togglePassword.classList.toggle('fa-eye');
            togglePassword.classList.toggle('fa-eye-slash');
        });


        // Authentication form submission
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Disable button and show spinner
            authSubmitBtn.classList.add('loading');
            authSubmitBtn.disabled = true;

            const email = emailInput.value;
            const password = passwordInput.value;
            const username = usernameInput.value;

            // Perform full validation before sending to Firebase
            const isEmailValid = validateEmail();
            const isPasswordStrong = validatePassword(); // This checks for strength, not just length
            let isUsernameValid = true;
            if (isSigningUp) {
                isUsernameValid = validateUsername();
            }

            if (!isEmailValid || !isPasswordStrong || (isSigningUp && !isUsernameValid)) {
                showMessageBox("Please correct the form errors.", "error");
                authSubmitBtn.classList.remove('loading');
                authSubmitBtn.disabled = false;
                return;
            }

            if (!isFirebaseActive) { // Use the flag to check Firebase status
                showMessageBox("Authentication service not available. Check Firebase configuration.", "error");
                authSubmitBtn.classList.remove('loading');
                authSubmitBtn.disabled = false;
                return;
            }

            try {
                if (isSigningUp) {
                    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                    const user = userCredential.user;
                    await setDoc(doc(db, "artifacts", appId, "users", user.uid, "profile", "data"), {
                        username: username,
                        email: email,
                        createdAt: serverTimestamp()
                    });
                    showMessageBox("Account created successfully! You are now signed in.", "success");
                    showChatbotAfterAuth();
                } else {
                    await signInWithEmailAndPassword(auth, email, password);
                    showMessageBox("Signed in successfully!", "success");
                    showChatbotAfterAuth();
                }
            } catch (error) {
                console.error("Auth error:", error);
                let errorMessage = "Authentication failed. Please try again.";
                if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
                    errorMessage = "Invalid email or password.";
                } else if (error.code === 'auth/email-already-in-use') {
                    errorMessage = "Email already in use. Try signing in or use a different email.";
                } else if (error.code === 'auth/weak-password') {
                    errorMessage = "Password is too weak. Please choose a stronger password.";
                }
                showMessageBox(`Authentication failed: ${errorMessage}`, "error");
            } finally {
                authSubmitBtn.classList.remove('loading');
                authSubmitBtn.disabled = false;
            }
        });

        // Toggle between Sign In and Sign Up
        toggleAuthBtn.addEventListener('click', (e) => {
            e.preventDefault();
            isSigningUp = !isSigningUp;

            // Clear input fields and reset validation/strength feedback
            emailInput.value = '';
            passwordInput.value = '';
            usernameInput.value = '';
            passwordStrengthBar.style.width = '0%';
            passwordStrengthText.textContent = '';
            emailValidIcon.style.display = 'none';
            emailInvalidIcon.style.display = 'none';
            passwordValidIcon.style.display = 'none';
            passwordInvalidIcon.style.display = 'none';
            usernameValidIcon.style.display = 'none';
            usernameInvalidIcon.style.display = 'none';

            // Remove the 'has-content' class on toggle to ensure labels are reset
            emailInput.classList.remove('has-content');
            passwordInput.classList.remove('has-content');
            usernameInput.classList.remove('has-content');


            if (isSigningUp) {
                authTitle.textContent = 'Create Your Account'; // More inviting text
                authSubmitBtn.querySelector('.button-text').textContent = 'Sign Up';
                usernameInput.style.display = 'block';
                usernameLabel.style.display = 'block'; // Show label for username
                usernameInput.setAttribute('required', 'required'); // Make username required for signup
                usernameInput.closest('.input-group').style.marginBottom = '2rem'; // Ensure margin for username input
                toggleAuthBtn.parentNode.innerHTML = `Already have an account? <a href="#" id="toggleAuth">Sign In</a>`;
            } else {
                authTitle.textContent = 'Welcome Back!'; // More inviting text
                authSubmitBtn.querySelector('.button-text').textContent = 'Sign In';
                usernameInput.style.display = 'none';
                usernameLabel.style.display = 'none'; // Hide label for username
                usernameInput.removeAttribute('required'); // Make username not required for signin
                usernameInput.closest('.input-group').style.marginBottom = '0'; // Remove margin if hidden
                toggleAuthBtn.parentNode.innerHTML = `Don't have an account? <a href="#" id="toggleAuth">Sign Up</a>`;
            }
            // Re-attach event listener for the dynamically created 'toggleAuth' link
            document.getElementById('toggleAuth').addEventListener('click', (e) => toggleAuthBtn.click());
        });

        // Sign Out functionality
        signOutBtn.addEventListener('click', async () => {
            if (auth && auth.currentUser && !auth.currentUser.isAnonymous) {
                try {
                    await signOut(auth);
                    showMessageBox("Signed out successfully!", "info");
                    authContainer.style.display = 'block'; // Show auth container
                    chatbotContainer.style.display = 'none'; // Hide chatbot
                    signOutBtn.style.display = 'none'; // Hide sign out button
                    // Clear chat messages on sign out
                    chatMessages.innerHTML = '<div class="chat-message bot">Hello! How can I help you today?</div>';
                    // Reset auth forms
                    toggleAuthBtn.click(); // Switch to default sign-in view
                } catch (error) {
                    console.error("Error signing out:", error);
                    showMessageBox(`Sign out failed: ${error.message}`, "error");
                }
            } else {
                showMessageBox("No user to sign out or already signed out.", "info");
            }
        });

        // Chat send message functionality
        sendChatBtn.addEventListener('click', async () => {
            const messageText = chatInput.value.trim();
            if (messageText === '') return;

            addMessageToChat('user', messageText);
            chatInput.value = '';

            if (!isFirebaseActive) { // Use the flag
                showMessageBox("Chat persistence is disabled (Firebase not configured or user not authenticated).", "error");
                // Simulate bot response locally if Firebase is not active
                setTimeout(() => {
                    const botResponse = `You said: "${messageText}". Chat persistence is offline.`;
                    addMessageToChat('bot', botResponse);
                }, 500);
                return;
            }

            try {
                // Send message to Streamlit backend via parent window for AI processing
                // This is a placeholder for actual communication.
                // In a real app, you'd use Streamlit.setComponentValue or websockets.
                window.parent.postMessage({
                    type: 'chat_message',
                    sender: 'user',
                    message: messageText,
                    userId: userId // Pass userId for backend persistence
                }, '*'); // Replace '*' with your Streamlit app's origin in production

                // Add to Firestore immediately for optimistic update
                await addDoc(collection(db, "artifacts", appId, "users", userId, "chats"), {
                    sender: 'user',
                    message: messageText,
                    timestamp: serverTimestamp()
                });

                // Simulate bot response here for now, as actual Streamlit communication is complex
                // You would typically wait for a response from the Streamlit backend
                setTimeout(async () => {
                     const botResponse = `Acknowledged: "${messageText}". I'm designed to assist with various queries. (This is a simulated response. Real AI response comes from Streamlit backend if fully integrated).`;
                    addMessageToChat('bot', botResponse);
                    await addDoc(collection(db, "artifacts", appId, "users", userId, "chats"), {
                        sender: 'bot',
                        message: botResponse,
                        timestamp: serverTimestamp()
                    });
                }, 1000);


            } catch (error) {
                console.error("Error sending message to Firebase:", error);
                showMessageBox(`Failed to send message: ${error.message}`, "error");
            }
        });

        // Function to add messages to the chat display
        function addMessageToChat(sender, message) {
            const messageElement = document.createElement('div');
            messageElement.classList.add('chat-message', sender);
            messageElement.textContent = message;
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Listen for chat messages from Firestore
        let unsubscribeChatListener; // To store the unsubscribe function

        function setupChatListener() {
            if (unsubscribeChatListener) {
                unsubscribeChatListener(); // Unsubscribe from previous listener if exists
            }
            if (isFirebaseActive && auth && auth.currentUser) {
                const q = query(collection(db, "artifacts", appId, "users", auth.currentUser.uid, "chats"), orderBy("timestamp"));
                unsubscribeChatListener = onSnapshot(q, (snapshot) => {
                    snapshot.docChanges().forEach((change) => {
                        if (change.type === "added") {
                            const data = change.doc.data();
                            // Check if message already exists to prevent duplicates on re-render/re-listen
                            if (data.sender && data.message && !chatMessages.querySelector(`[data-id="${change.doc.id}"]`)) {
                                const messageElement = document.createElement('div');
                                messageElement.classList.add('chat-message', data.sender);
                                messageElement.textContent = data.message;
                                messageElement.setAttribute('data-id', change.doc.id); // Add a data-id for tracking
                                chatMessages.appendChild(messageElement);
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        }
                    });
                }, (error) => {
                    console.error("Error listening to chat messages:", error);
                    showMessageBox("Failed to load chat history.", "error");
                });
            }
        }
        
        // --- Speech Recognition (Voice Type) ---
        // Check if Web Speech API is supported
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const SpeechGrammarList = window.SpeechGrammarList || window.webkitSpeechGrammarList;
        const SpeechRecognitionEvent = window.SpeechRecognitionEvent || window.webkitSpeechRecognitionEvent;

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.continuous = false; // Listen for a single utterance
            recognition.lang = 'en-US';
            recognition.interimResults = false; // Only return final results
            recognition.maxAlternatives = 1;

            microphoneBtn.addEventListener('click', () => {
                if (microphoneBtn.classList.contains('listening')) {
                    // If already listening, stop
                    recognition.stop();
                    microphoneBtn.classList.remove('listening');
                    showMessageBox("Stopped listening.", "info");
                } else {
                    // Start listening
                    try {
                        recognition.start();
                        microphoneBtn.classList.add('listening');
                        chatInput.value = "Listening..."; // Provide immediate feedback
                        showMessageBox("Listening... Say 'stop' or click again to finish.", "info");
                    } catch (e) {
                        console.error("Speech recognition error:", e);
                        showMessageBox("Speech recognition failed to start. Ensure microphone access.", "error");
                        microphoneBtn.classList.remove('listening');
                    }
                }
            });

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                chatInput.value = transcript;
                microphoneBtn.classList.remove('listening');
                showMessageBox("Voice input received. Click send to chat.", "success");
                // Automatically send if "stop" is said, or if a significant phrase is detected
                if (transcript.toLowerCase().includes('stop')) {
                    recognition.stop();
                    chatInput.value = transcript.replace(/stop/i, '').trim(); // Remove 'stop' from input
                    sendChatBtn.click(); // Auto-send the message
                }
            };

            recognition.onspeechend = () => {
                recognition.stop();
                microphoneBtn.classList.remove('listening');
                if (chatInput.value === "Listening...") { // If nothing was said
                    chatInput.value = "";
                    showMessageBox("No speech detected.", "info");
                }
            };

            recognition.onerror = (event) => {
                microphoneBtn.classList.remove('listening');
                console.error('Speech recognition error:', event.error);
                if (event.error === 'no-speech') {
                    showMessageBox("No speech detected. Please try again.", "info");
                } else if (event.error === 'not-allowed') {
                    showMessageBox("Microphone access denied. Please allow in browser settings.", "error");
                } else {
                    showMessageBox(`Speech recognition error: ${event.error}`, "error");
                }
                chatInput.value = chatInput.value === "Listening..." ? "" : chatInput.value; // Clear if still showing "Listening..."
            };
        } else {
            console.warn("Web Speech API not supported by this browser.");
            microphoneBtn.style.display = 'none'; // Hide microphone button if not supported
            showMessageBox("Your browser does not support Web Speech API. Voice input disabled.", "info");
        }

    </script>
</body>
</html>
"""

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Interactive 3D Zipper Reveal",
    page_icon="🔗"
)

# Embed the HTML content
# Use a key to ensure Streamlit re-renders the component if needed, though usually not for static HTML
components.html(html_content, height=800, scrolling=False) # Changed scrolling to False for full page control

# --- Custom CSS for Streamlit's internal elements to remove default padding ---
st.markdown("""
    <style>
        /* Hide Streamlit header/footer elements */
        .stApp > header {
            display: none !important;
        }
        #MainMenu {
            visibility: hidden !important;
        }
        footer {
            visibility: hidden !important;
        }

        /* Target Streamlit's main content block and remove all padding/margins */
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Target Streamlit's main page container */
        .stApp {
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden; /* Ensure no scrollbars from Streamlit's side */
        }

        /* Target the div that usually wraps `st.components.v1.html` */
        div[data-testid="stVerticalBlock"] > div {
            padding: 0 !important;
            margin: 0 !important;
        }
        div[data-testid="stHorizontalBlock"] {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Ensure the iframe itself takes up all available space and has no borders */
        iframe {
            display: block !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100vh !important; /* Make it fill the viewport height */
        }

        /* If there's an outer wrapper created by Streamlit for the component itself */
        .stComponent {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100vh !important;
        }

        /* Ensure no extra padding is added by general Streamlit styling */
        section[data-testid="stSidebar"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        section.main {
            padding: 0 !important;
            margin: 0 !important;
        }
    </style>
""", unsafe_allow_html=True)