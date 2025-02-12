import time
import streamlit as st
import json
import base64
import os
from pathlib import Path
import gettext
from google.cloud import secretmanager

# Function to access secrets from Google Secret Manager
def get_secret(secret_name):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/eth-psl-llm/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        st.error(f"Error with secret {secret_name} from Google Secret Manager: {e}")
        raise

# Function to get the absolute path to an image
def get_image_path(image_name):
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "images", image_name)

# Function to get API key
def get_api_key():
    return st.secrets["claude"]["claude_auth"]
    try:
        # Try to get from Google Secret Manager first
        return get_secret("claude_auth")
    except Exception:
        try:
            # Fall back to Streamlit secrets
            return st.secrets["claude"]["claude_auth"]
        except KeyError:
            # Lastly, try to get from environment variables
            if "claude_auth" in os.environ:
                return os.getenv("claude_auth")
            else:
                st.error("API key for 'claude_auth' not found in any source.")
                raise ValueError("API key not found.")

# Function to get the database URI
def get_db_uri():
    return st.secrets["neon_db"]["db_uri"]
    try:
        # Try to get from Google Secret Manager first
        return get_secret("db_uri")
    except Exception:
        try:
            # Fall back to Streamlit secrets
            return st.secrets["neon_db"]["db_uri"]
        except KeyError:
            # Lastly, try to get from environment variables
            if "db_uri" in os.environ:
                return os.getenv("db_uri")
            else:
                st.error("Database URI for 'db_uri' not found in any source.")
                raise ValueError("Database URI not found.")

    
def get_chatbot_config():
    """
    Loads and returns the chatbot configuration from a JSON file.
    """
    # Define the absolute path to the JSON file
    file_path = Path(__file__).parent / "chatbot_config.json"

    # Load the configuration
    with open(file_path, "r") as config_file:
        return json.load(config_file)

def stream_data(text):
    """
    Yields each word in the given text with a brief pause for streaming effect.
    """
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)

@st.cache_resource()
def get_base64_of_bin_file(bin_file):
    """
    Reads a binary file, encodes it in base64, and returns the encoded string.
    """
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def set_png_as_page_bg(png_file):
    """
    Sets the given PNG file as the background image of the Streamlit app.
    """
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    body {{
    background-image: url("data:image/png;base64,{bin_str}");
    background-size: cover;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

def set_background_color(color):
    """
    Sets a solid background color for the Streamlit app.
    
    Parameters:
    color (str): The background color as a CSS color string (e.g., "#90CAF9" or "blue").
    """
    st.markdown(f"<style>.stApp {{background-color: {color};}}</style>", unsafe_allow_html=True)

def set_background_local(image_file):
    """
    Sets a local image file as the background of the Streamlit app.

    Parameters:
    image_file (str): Path to the image file to use as the background.
    """
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def language_dropdown(lang):
    # Directory for language files
    locale_dir = st.session_state.get("locale_dir", "locales")  # Default directory

    # Map language codes to display names
    languages = {
        "de": "Deutsch 🇨🇭",
        "en": "English 🇬🇧",
    }

    # Streamlit Layout: Use columns to place the dropdown on the right

    selected_language = st.selectbox(" ", list(languages.values()), index=list(languages.keys()).index(lang), label_visibility="collapsed")

    # Get the corresponding locale code
    current_lang = [code for code, name in languages.items() if name == selected_language][0]

    # Update the session state with the selected language
    if st.session_state.lang != current_lang:
        st.session_state.lang = current_lang
        st.rerun()  # Trigger a rerun to apply the new language immediately

    # Load the corresponding translation
    lang = gettext.translation("messages", localedir=locale_dir, languages=[current_lang], fallback=True)
    lang.install()
    _ = lang.gettext

    return _


def apply_main_chatbot_styling():
    """
    Consolidates all the CSS + JS snippets used for the layout, pinned chat input,
    pinned disclaimer text, and sidebar modifications.
    Specifically hides any element with data-testid="stSidebarCollapseButton".
    """
    # 1) Your existing styling for header, chat container, pinned input, etc.
    st.markdown(
        """
        <style>
        /* Keep your original styling for header & chat container */
        .header-container {
          width: 80% !important;
          margin: 0 auto;
        }
        .chat-container {
          width: 60% !important;
          margin: 0 auto;
        }
        .footer-container {
          display: block !important;
          width: 80% !important;
          margin-left: auto !important;
          margin-right: auto !important;
          margin-top: -10px !important;
          margin-bottom: 0 !important;
        }

        /* Typing animation keyframes */
        @keyframes typing {
          0% { opacity: 0.2; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1); }
          100% { opacity: 0.2; transform: scale(0.8); }
        }

        /* Pin chat input at the bottom of the page */
        div[data-testid="stChatInput"] {
           display: block !important;
           width: 80% !important;
           margin-left: auto !important;
           margin-right: auto !important;
           margin-top: -12px !important;
           margin-bottom: 0 !important;
        }

        /* Pinned text block below the chat input */
        #pinned-text-below {
           position: fixed;
           bottom: 30px; 
           left: 60%;
           transform: translateX(-60%);
           z-index: 9998; 
           background-color: white;
           text-align: center;
           width: 80%;
           padding: 0.2rem;
           font-size: 14px !important;
           color: #333;
           border-radius: 4px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # 2) Sidebar styling (remove scroll, fix width, etc.)
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] > div:first-child {
            height: 100vh !important;
            overflow-y: hidden !important;
        }
        [data-testid="stSidebar"] {
            width: 20vw !important;
        }
        div[data-testid="stSidebar"] {
            overflow-y: hidden !important;
            height: 100vh !important;
            transform: translateX(0px) !important;
            min-width: 300px !important;
            max-width: 300px !important;
        }
        div[data-testid="stSidebar"] > div {
            overflow-y: hidden !important;
            height: 100vh !important;
        }
        div[data-testid="stSidebar"] .stButton button {
            font-size: 10px !important;
            width: 100% !important; 
        }
        /* Pinned text block below the chat input */
        #pinned-text-below-sidebar {
           position: fixed;
           bottom: 0px; 
           z-index: 9998; 
           background-color: white;
           text-align: center;
           width: 80%;
           padding: 0.2rem;
           font-size: 10px !important;
           color: #333;
           border-radius: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 3) CSS selectors that hide the collapse button (including stSidebarCollapseButton)
    st.markdown(
        """
        <style>
        /* Attempt to hide it purely via CSS */
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 4) JavaScript approach: forcibly remove that element from the DOM
    # (in case the CSS alone does not catch it)
    st.components.v1.html(
        """
        <script>
        document.addEventListener("DOMContentLoaded", function() {
          // Try to remove anything with data-testid="stSidebarCollapseButton"
          const doc = window.parent.document;
          let toggleBtn = doc.querySelectorAll('[data-testid="stSidebarCollapseButton"]');
          toggleBtn.forEach(function(btn) {
            if (btn && btn.parentNode) {
              btn.parentNode.removeChild(btn);
            }
          });
        });
        </script>
        """,
        height=0,
    )


################################################################################
#  BUBBLE RENDERING FUNCTIONS
################################################################################
def display_bubble(role, content):
    """
    Renders a single chat bubble for either a user or an assistant.
    """
    if role == "user":
        html = f"""
        <div style="
            margin-bottom: 20px;
            width: 60% !important;
            max-width: 90%;
            padding: 12px 16px;
            border-radius: 15px;
            background-color: #DCF8C6;
            text-align: right !important;
            margin-left: auto;
        ">
            {content}
        </div>
        """
    else:  # assistant
        html = f"""
        <div style="
            margin-bottom: 20px;
            width: 60% !important;
            max-width: 90%;
            padding: 12px 16px;
            border-radius: 15px;
            background-color: #F1F0F0;
            text-align: left !important;
            margin-right: auto;
        ">
            {content}
        </div>
        """
    st.markdown(html, unsafe_allow_html=True)

def display_thinking_bubble():
    """
    Renders a left-aligned "thinking" animation with no background or border, 
    so that only the three animated dots are visible on the left.
    """
    thinking_html = """
    <div style="
        margin-bottom: 20px;
        margin-left: 0;
        margin-right: auto;
        display: flex;
        align-items: center;
        gap: 5px;
        background-color: transparent;
        border: none;
        padding: 0;
    ">
        <div style="
            height: 8px;
            width: 8px;
            background-color: #bbb;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        "></div>
        <div style="
            height: 8px;
            width: 8px;
            background-color: #bbb;
            border-radius: 50%;
            animation: typing 1.4s infinite;
            animation-delay: 0.2s;
        "></div>
        <div style="
            height: 8px;
            width: 8px;
            background-color: #bbb;
            border-radius: 50%;
            animation: typing 1.4s infinite;
            animation-delay: 0.4s;
        "></div>
    </div>
    """
    st.markdown(thinking_html, unsafe_allow_html=True)



def update_chat_container(chat_placeholder):
    """
    Renders all messages in st.session_state.messages into the placeholder container.
    """
    with chat_placeholder.container():
        left, mid, right = st.columns([1, 8, 1])
        with mid:
            for msg in st.session_state.messages:
                if msg["role"] == "assistant" and msg.get("pending", False):
                    display_thinking_bubble()
                else:
                    display_bubble(msg["role"], msg["content"])
