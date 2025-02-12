import streamlit as st
from .utils import get_chatbot_config, language_dropdown
from pathlib import Path
from .db_communication import insert_feedback
import time 

chatbot_config = get_chatbot_config() 

@st.dialog("Impressum", width="large")
def show_impressum():
    """
    Displays the Impressum content in a dialog box by loading 
    and rendering markdown from a file.
    """
    # Display logos side by side
    # col1, col2 = st.columns(2)
    # with col1:
    #     img1_path = get_image_path("eth_logo.png")
    #     img1 = Image.open(img1_path).resize((150, 35))
    #     st.image(img1)
    # with col2:
    #     img2_path = get_image_path("nccr_logo.png")
    #     img2 = Image.open(img2_path).resize((150, 35))
    #     st.image(img2)

    if st.session_state.lang == "de":
        file_path = Path(__file__).parent / "impressum_chatbot_de.md"
    else: 
        file_path = Path(__file__).parent / "impressum_chatbot_en.md"

    with open(file_path, "r") as file:
        markdown_content = file.read()
    st.markdown(markdown_content)

@st.dialog("💬 Feedback", width="large")
def show_feedback_popup():
    """
    Displays a feedback form with a star rating and text feedback input.
    """ 
    # Initialize session state for feedback inputs
    if "feedback_rating" not in st.session_state:
        st.session_state["feedback_rating"] = None
    if "feedback_text" not in st.session_state:
        st.session_state["feedback_text"] = ""

    # Star rating using st.slider (adjust for demonstration)
    feedback_rating = st.feedback(options="stars") 
    if feedback_rating == None: 
        feedback_rating = 0
    st.session_state["feedback_rating"] = feedback_rating + 1
    # Text area for detailed feedback
    st.session_state["feedback_text"] = st.text_area(_("Please let us know what we can improve:"), key="feedback_text_area")

    # Submit feedback button
    if st.button(_("Submit Feedback")):
        if st.session_state["feedback_text"]:
            # Insert feedback into the database
            insert_feedback(st.session_state["feedback_text"], st.session_state["feedback_rating"])
            # Reset feedback inputs
            st.session_state["feedback_rating"] = None
            st.session_state["feedback_text"] = ""
            time.sleep(2)
            st.rerun()
            
        else:
            st.error(_("Please enter your feedback."))
        

def write_footnote(short_version=False):
    """
    Displays a footer with a disclaimer and version information,
    along with Impressum and Feedback buttons and partner logos.
    
    Parameters:
    -----------
    short_version : bool, optional
        If True, displays a simplified version of the disclaimer.
    """

    # Define a container for the footer
    disclaimer_placeholder = st.container()

    with disclaimer_placeholder:
        col1, col2, col3 = st.columns([0.2,0.2,0.6], vertical_alignment="top")  # Two columns for alignment

        # Left column: Impressum button
        with col1:
            # CSS styling for Impressum and Feedback buttons
            st.markdown(
                """
                <style>
                /* Hide specific elements */
                .element-container:has(style) {
                    display: none;
                }
                #button-impressum {
                    display: none;
                }
                #button-feedback {
                    display: none;
                }
                .element-container:has(#button-impressum) + div button {
                    background-color: transparent;
                    color: gray;
                    border: none;
                    padding: 0;
                    font-size: 10px;
                    text-decoration: underline;
                    cursor: pointer;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Invisible spans to target buttons
            st.markdown('<span id="button-impressum"> </span>', unsafe_allow_html=True)

            # Visible Impressum button
            current_version = chatbot_config["version"]
            if st.button("V" + current_version + ", Impressum"):
                show_impressum()

        if short_version == False: 
            # Right column: Feedback button
            with col2:
                            # CSS styling for Impressum and Feedback buttons
                st.markdown(
                    """
                    <style>
                    /* Hide specific elements */
                    .element-container:has(style) {
                        display: none;
                    }
                    #button-impressum {
                        display: none;
                    }
                    #button-feedback {
                        display: none;
                    }
                    .element-container:has(#button-feedback) + div button {
                        background-color: transparent;
                        color: gray;
                        border: none;
                        padding: 0;
                        font-size: 10px;
                        text-decoration: underline;
                        cursor: pointer;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                # Invisible spans to target buttons
                st.markdown('<span id="button-feedback"> </span>', unsafe_allow_html=True)

                # Visible Impressum button
                if st.button("💬 Feedback"):
                    show_feedback_popup()

        
