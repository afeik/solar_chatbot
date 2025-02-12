import time
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# 1) IMPORTS FROM YOUR MODULES
from components.utils import (
    apply_main_chatbot_styling,
    get_chatbot_config,
    language_dropdown,
    display_bubble,
    display_thinking_bubble,
    update_chat_container
)
from components.footnote import write_footnote  # if needed elsewhere
from components.db_communication import (
    insert_db_message,
    insert_feedback,
    insert_final_rating,
    insert_initial_rating,
)
from streamlit_extras.stylable_container import stylable_container

###############################################################################
# PAGE CONFIG & SESSION STATE INITIALIZATION
###############################################################################
st.set_page_config(
    page_title="Solar Energy Chatbot",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------
# Hide all possible collapse/expand controls in the sidebar:
st.markdown(
    """
    <style>
    /* Hide the typical "collapse sidebar" control in recent Streamlit versions */
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Hide buttons in older versions that used these titles */
    button[title="Expand"], button[title="Collapse"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Some builds label it with this aria-label */
    button[aria-label="Hide sidebar"] {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ------------------------------------------------------------------

apply_main_chatbot_styling()
chatbot_config = get_chatbot_config()

if "page_set" not in st.session_state:
    st.switch_page("energy_transition_chatbot_main.py")
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "conversation_turns" not in st.session_state:
    st.session_state.conversation_turns = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

###############################################################################
# DIALOGS: IMPRESSUM AND FEEDBACK
###############################################################################
@st.dialog("Impressum", width="large")
def show_impressum():
    if st.session_state.lang == "de":
        file_path = Path(__file__).parent.parent / "components" /"impressum_chatbot_de.md"
    else:
        file_path = Path(__file__).parent.parent /"components" / "impressum_chatbot_en.md"
    with open(file_path, "r") as file:
        markdown_content = file.read()
    st.markdown(markdown_content)


@st.dialog("💬 Feedback", width="large")
def show_feedback_popup():
    if "feedback_rating" not in st.session_state:
        st.session_state["feedback_rating"] = None
    if "feedback_text" not in st.session_state:
        st.session_state["feedback_text"] = ""

    feedback_rating = st.feedback(options="stars")
    if feedback_rating is None:
        feedback_rating = 0
    st.session_state["feedback_rating"] = feedback_rating + 1

    st.session_state["feedback_text"] = st.text_area(
        _("Please let us know what we can improve:"), key="feedback_text_area"
    )

    if st.button(_("Submit Feedback")):
        if st.session_state["feedback_text"]:
            insert_feedback(
                st.session_state["feedback_text"],
                st.session_state["feedback_rating"]
            )
            st.session_state["feedback_rating"] = None
            st.session_state["feedback_text"] = ""
            time.sleep(2)
            st.rerun()
        else:
            st.error(_("Please enter your feedback."))

@st.dialog(_("We value your feedback!"), width="large")
def show_feedback_dialog():
    if not st.session_state.feedback_submitted:
        st.markdown(
            chatbot_config["solar_ownership"][st.session_state.solar_panel_ownership]["q1"][st.session_state.lang],
            unsafe_allow_html=True
        )
        st.slider("", 0, 100, key="q1")
        
        st.divider()

        st.markdown(
            chatbot_config["solar_ownership"][st.session_state.solar_panel_ownership]["q2"][st.session_state.lang],
            unsafe_allow_html=True
        )
        st.slider("", 0, 100, key="q2")
        st.divider()
        # Feedback text area is left outside of the bordered question containers.
        st.session_state["feedback_text"] = st.text_area(
            _("Please let us know what we can improve:"), key="feedback_text_area"
        )
        
        
        
        # Custom container to style the submit button.
        with stylable_container(
            "grey",
            css_styles="""
                button {
                    background-color: #E0E0E0;
                    width: 100%;
                    display: block;
                }
            """
        ):
            if st.button(_("Submit Feedback")):
                insert_initial_rating(st.session_state.q1)
                insert_final_rating(st.session_state.q2)
                if st.session_state["feedback_text"].strip():
                    insert_feedback(st.session_state["feedback_text"])
                st.session_state.feedback_submitted = True
                time.sleep(1)
                if st.session_state.lang == "de":
                    thanks_msg = (
                        "Ich danke Ihnen für das Feedback - "
                        "Gerne stehe ich noch für weitere Fragen zur Verfügung!"
                    )
                else:
                    thanks_msg = (
                        "Thank you for your feedback - "
                        "I am happy to answer any further questions you might have!"
                    )
                st.session_state.messages.append({"role": "assistant", "content": thanks_msg})
                insert_db_message(thanks_msg, "assistant", "conversation")
                st.rerun()
    else:
        # Thank-you message area.
        with stylable_container(
            "green",
            css_styles="""
                .thank-you {
                    padding: 20px;
                    border-radius: 10px;
                    background-color: #f0fff0;
                    border: 1px solid #ccc;
                }
            """
        ):
            st.markdown('<div class="thank-you">', unsafe_allow_html=True)
            st.markdown(
                _("<b>Thank you for your valuable contribution to our research project on solar energy!</b>"),
                unsafe_allow_html=True
            )
            st.write(_("If you have further questions, contact us:"))
            st.write("Dr. Mengshuo Jia (PSL - ETH Zürich) jia@eeh.ee.ethz.ch")
            st.write("Benjamin Sawicki (NCCR Automation) bsawicki@ethz.ch")
            st.write("Andreas Feik (ETH Zürich) anfeik@ethz.ch")
            st.markdown("</div>", unsafe_allow_html=True)



###############################################################################
# MAIN CHAT FUNCTION
###############################################################################
def claude_conversation(client):
    with st.sidebar:
        # Place title, language selector, and conversation button at the top.
        lang = st.session_state.lang
        title = chatbot_config["titles"]["front_page"][lang]["name"]
        st.markdown(f"<h2 style='text-align: center;'>{title}</h2>", unsafe_allow_html=True)
        _= language_dropdown(lang)

        # Main conversation button (large button)
        if not st.session_state.feedback_submitted:
            with stylable_container(
                "grey",
                css_styles="""
                    button {
                        background-color: #E0E0E0;
                        width: 100%;
                        display: block;
                    }
                """
            ):
                if st.button(_("Done? Click here to continue."), key="end_conversation"):
                    show_feedback_dialog()
        else:
            with stylable_container(
                "grey",
                css_styles="""
                    button {
                        background-color: #E0E0E0;
                        width: 100%;
                        display: block;
                    }
                """
            ):
                if st.button(_("Start a new conversation?"), key="start_new"):
                    for k in list(st.session_state.keys()):
                        del st.session_state[k]
                    st.switch_page("energy_transition_chatbot_main.py")

        # A small spacer (adjust height as desired)
        #st.markdown("<div style='height:57vh;'></div>", unsafe_allow_html=True)

        # Directly below, place the Impressum and Feedback buttons in two columns.
        impressum, feedback = st.columns(2)

        # ----- IMPRESSUM BUTTON (Left Column) -----
        with impressum:
            st.markdown(
                """
                <style>
                /* Hide the invisible marker */
                #button-impressum { display: none; }
                /* Style the button immediately following the marker */
                .element-container:has(#button-impressum) + div button {
                    background-color: transparent;
                    color: gray;
                    border: none;
                    font-size: 8px !important;
                    text-decoration: underline;
                    position: bottom;
                    bottom: 0;
                }
                /* Remove any hover effects by matching the default styling */
                .element-container:has(#button-impressum) + div button:hover {
                    background-color: transparent;
                    color: gray;
                    border: none;
                    font-size: 8px !important;
                    text-decoration: underline;
                    position: bottom;
                    bottom: 0;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<span id="button-impressum"></span>', unsafe_allow_html=True)
            if st.button("Impressum", key="impressum_sidebar", help="Impressum"):
                show_impressum()

        # ----- FEEDBACK BUTTON (Right Column) -----
        with feedback:
            st.markdown(
                """
                <style>
                #button-feedback { display: none; }
                .element-container:has(#button-feedback) + div button {
                    background-color: transparent;
                    color: gray;
                    border: none;
                    font-size: 8px !important;
                    text-decoration: underline;
                    position: relative;
                    bottom: 0;
                }
                /* Remove any hover effects by matching the default styling */
                .element-container:has(#button-feedback) + div button:hover {
                    background-color: transparent;
                    color: gray;
                    border: none;
                    font-size: 8px !important;
                    text-decoration: underline;
                    position: relative;
                    bottom: 0;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown('<span id="button-feedback"></span>', unsafe_allow_html=True)
            if st.button("💬 Feedback", key="feedback_sidebar", help="Feedback"):
                show_feedback_popup()

    # --- MAIN CHAT INTERFACE ---
    if st.session_state.conversation_turns == 0 and "initial_clarification_sent" not in st.session_state:
        with st.spinner(_("Preparing your conversation ...")):
            lang_prompt = (
                "Verwende die Deutsche Sprache." if st.session_state.lang == "de" else "Use the English Language."
            )
            solar_prompt = (
                f"Solar Ownership: {st.session_state.solar_panel_ownership}. "
                f"Based on this, emphasize these questions (concise and not all at once): "
                f"{chatbot_config['solar_ownership'][st.session_state.solar_panel_ownership]['questions']} "
                f"User Proficiency Level: {st.session_state.proficiency}"
            )
            init_resp = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=chatbot_config[st.session_state.proficiency]["conversation_max_tokens"],
                temperature=chatbot_config[st.session_state.proficiency]["conversation_temperature"],
                system=(
                    f"{lang_prompt} If German, you can use a typical Swiss Greeting "
                    f"{chatbot_config['general']['general_role']} "
                    f"{chatbot_config[st.session_state.proficiency]['conversation_role']}"
                ),
                messages=[{"role": "user", "content": solar_prompt}],
            )
            init_text = init_resp.content[0].text.strip()
            st.session_state.messages.append({"role": "assistant", "content": init_text})
            st.session_state.initial_clarification_sent = True
            insert_db_message(init_text, "assistant", "conversation")

    chat_placeholder = st.empty()
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    with st.container():
        update_chat_container(chat_placeholder)
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = st.chat_input(placeholder=_("Your response:"), key="main_chat_input")
    disclaimer = (
        chatbot_config["disclaimer_en"] if st.session_state.lang == "en" else chatbot_config["disclaimer_de"]
    )
    # Add CSS to ensure the disclaimer is centered.
    st.markdown(
        """
        <style>
        #pinned-text-below {
            text-align: center;
            width: 100%;
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(f'<div id="pinned-text-below">{disclaimer}</div>', unsafe_allow_html=True)

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        insert_db_message(user_input, "user", "conversation")

        st.session_state.messages.append({"role": "assistant", "content": "", "pending": True})
        update_chat_container(chat_placeholder)

        context_str = "\n".join(
            f"{m['role']}: {m['content']}" for m in st.session_state.messages if not m.get("pending", False)
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.7,
            system="Some system prompt...",
            messages=[
                {"role": "assistant", "content": context_str},
                {"role": "user", "content": user_input},
            ],
        )
        assistant_text = response.content[0].text.strip()

        st.session_state.messages[-1] = {"role": "assistant", "content": assistant_text}
        insert_db_message(assistant_text, "assistant", "conversation")
        st.session_state.conversation_turns += 1

        update_chat_container(chat_placeholder)
        st.rerun()


###############################################################################
# LAUNCH THE CHAT
###############################################################################
claude_conversation(st.session_state.claude_client)
