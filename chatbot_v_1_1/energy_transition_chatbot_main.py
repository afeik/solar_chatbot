import streamlit as st
from components.footnote import write_footnote
from components.db_communication import update_proficiency, init_db_communication, insert_full_conversation_details, insert_usecase_specific_info
from components.utils import get_image_path, language_dropdown, get_chatbot_config
from PIL import Image
import anthropic
from pathlib import Path
from components.utils import language_dropdown, get_api_key
from streamlit_extras.stylable_container import stylable_container


# Check if the 'page' parameter exists
if "page_set" not in st.session_state:
    # If not, set it to the main page and reload
    st.session_state.page_set = "front_page"

st.set_page_config("Solar Energy Chatbot",":robot_face:")
# Initialize session state
if "lang" not in st.session_state:
    st.session_state.lang = "de"

if "locale_dir" not in st.session_state:
    st.session_state.locale_dir = Path(__file__).parent / "components" / "languages"

if "step" not in st.session_state:
    st.session_state.step = "select_proficiency"
    st.session_state.keywords = None

if "proficiency" not in st.session_state:
    st.session_state.proficiency = None

if "proficiency_selected" not in st.session_state:
    st.session_state.proficiency_selected = False

if "consent_given" not in st.session_state:
    st.session_state.consent_given = False

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None  # Or set a default value like ""


st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)
if "claude_client" not in st.session_state:
    st.session_state.conversation_id = None  # Or set a default value like ""
    # Initialize Claude client
    anthropic_api_key = get_api_key()

    if anthropic_api_key:
        st.session_state.claude_client = anthropic.Client(api_key=anthropic_api_key)
    else:
        st.error("Connection to Claude API failed.")

# Cache chatbot configuration to avoid repeated loading
@st.cache_resource
def get_cached_chatbot_config():
    return get_chatbot_config()

chatbot_config = get_cached_chatbot_config()

# Cache image loading to reduce latency
@st.cache_resource
def load_image(image_name):
    return Image.open(get_image_path(image_name))

def navigate_to_next_page():
    """
    Navigates to the conversation page.
    """
    st.switch_page("./pages/ai_conversation.py")

def select_proficiency_level():
    """
    Prompts the user to select their experience level with the energy transition
    and whether they already own a solar panel.
    """
    col1, col2 = st.columns([6,2])
    with col2: 
        lang = st.session_state.lang
        _ = language_dropdown(lang)


    # Load titles and text from the configuration file
    page_title = chatbot_config["titles"]["front_page"][lang]["page_title"]
    slider_title = chatbot_config["titles"]["front_page"][lang]["slider_title"]
    consent_text = chatbot_config["titles"]["front_page"][lang]["consent_text"]

    # Initialize session state variables
    if "proficiency" not in st.session_state:
        st.session_state.proficiency = None
    if "proficiency_selected" not in st.session_state:
        st.session_state.proficiency_selected = False
    if "step" not in st.session_state:
        st.session_state.step = "select_proficiency"
    if "consent_given" not in st.session_state:
        st.session_state.consent_given = False
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

    # Load and cache the image
    image = load_image("project_solar_stories.jpg")

    # Create a placeholder for dynamic content
    content_placeholder = st.empty()

    # Display the proficiency selection page
    with content_placeholder.container():
        st.markdown(f"<h3>{page_title}</h3>", unsafe_allow_html=True)
        st.image(image, use_column_width=True)

        # Consent checkbox comes first
        st.session_state.consent_given = st.checkbox(
            consent_text,
            value=st.session_state.get("consent_given", False),
            key="consent_checkbox"
        )

        if st.session_state.consent_given:
            # Slider for proficiency rating (only shown after consent)
            st.session_state.proficiency_rating = st.slider(
                slider_title,
                0, 100,
                value=st.session_state.get("proficiency_rating", 0),
                key="proficiency_slider"
            )

            # Determine proficiency level based on rating
            if 0 <= st.session_state.proficiency_rating <= 33:
                st.session_state.proficiency = "beginner"
            elif 34 <= st.session_state.proficiency_rating <= 66:
                st.session_state.proficiency = "intermediate"
            elif 67 <= st.session_state.proficiency_rating <= 100:
                st.session_state.proficiency = "expert"

            # Render buttons as Streamlit-native components with consistent styling
            col1, col2 = st.columns(2, gap="large")

            def handle_solar_selection(ownership):
                """
                Handles the selection and database interaction for solar panel ownership.
                Clears the page dynamically and navigates to the next step.
                """
                if not st.session_state.get("db_initialized", False):
                    init_db_communication()
                    st.session_state.db_initialized = True

                st.session_state.proficiency_selected = True
                st.session_state.solar_panel_ownership = ownership
                update_proficiency()
                insert_full_conversation_details(
                    None, None, None, st.session_state.consent_given
                )
                insert_usecase_specific_info({"solar_panel_ownership": ownership})

                # Clear the placeholder content
                content_placeholder.empty()

                # Navigate to the next page
                navigate_to_next_page()

            with col2:
                with stylable_container(
                "grey",
                css_styles="""
                    button {
                        background-color: #E0E0E0;
                        width: 100%;
                        display: block;
                    }
                """,
                ):
                    if st.button(_("I already own a Solar System"), key="own_solar_yes", use_container_width=True):
                        handle_solar_selection("yes")

            with col1:
                with stylable_container(
                "grey",
                css_styles="""
                    button {
                        background-color: #E0E0E0;
                        width: 100%;
                        display: block;
                    }
                """,
                ):
                    if st.button(_("I do not own a Solar System"), key="own_solar_no", use_container_width=True):
                        handle_solar_selection("no")

select_proficiency_level()
write_footnote(short_version=True)
