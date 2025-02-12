import streamlit as st
from components.footnote import write_footnote
from components.utils import language_dropdown, get_chatbot_config
from components.db_communication import insert_final_rating, insert_initial_rating
st.set_page_config("Solar Energy Chatbot",":robot_face:")

# Obtain Config
chatbot_config = get_chatbot_config() 


def get_initial_rating():
    """
    Collects the user's initial confidence rating on the summarized statement.

    Displays a slider for the user to rate their confidence in the truth of a 
    summarized statement based on their initial input. Submits the rating to 
    the database and advances the conversation step.
    """
    lang = st.session_state.lang
    _ = language_dropdown(lang)

    placeholder = st.empty()

    if st.session_state.step == "initial_rating":
        with placeholder.container():
            st.markdown(_("<h4>AI Summary of your concern:</h4>"),unsafe_allow_html=True)
            st.markdown(f"> *{st.session_state.summary}*")
            #st.divider()

            # Ensure rating state is properly initialized
            if "initial_rating_submitted" not in st.session_state:
                st.session_state["initial_rating_submitted"] = False

            if not st.session_state["initial_rating_submitted"]:
                if st.session_state.lang == "de":
                    disclaimer = chatbot_config["disclaimer_de"]
                else:
                    disclaimer = chatbot_config["disclaimer_en"]
                st.markdown(
                        f"""
                        <div style='color: gray; font-size: 13px; margin: 0; padding: 0; text-align: left;'>
                            {disclaimer}
                        </div>
                        """,
                        unsafe_allow_html=True
                )
                st.slider(
                    "",
                    0, 100,
                    key="initial_rating_slider"
                )
                # Create two columns
                col1, col2 = st.columns([1, 1])  # Adjust proportions as necessary

                with col1:
                    st.write(_("How confident are you that this statement is correct?"))

                with col2:
                    pass

                if st.button(_("Submit Initial Rating"), key="submit_initial_rating"):
                    #send_ga_event("initial_rating")
                    insert_initial_rating(st.session_state.initial_rating_slider)
                    st.session_state["initial_rating_submitted"] = True
                    st.session_state.initial_rating = st.session_state.initial_rating_slider
                    st.session_state.step = "conversation"
                    #st.switch_page("./pages/final_page.py")
                    placeholder.empty()
                    st.rerun()

            write_footnote()
    else:
        placeholder.empty()

def get_final_rating():
    """
    Collects the user's final confidence rating after the conversation.

    Displays the initial statement summary and provides a slider for the 
    user to rate their confidence after discussing it. Submits the rating 
    to the database and completes the conversation.
    """
    if "page_set" not in st.session_state:
    # If not, set it to the main page and reload
        st.switch_page("energy_transition_chatbot_main.py")

    lang = st.session_state.lang
    _ = language_dropdown(lang)
    
    #st.markdown(_("<b>How helpful was this conversation regarding your questions or your general understanding of solar energy technologies?</b>"),unsafe_allow_html=True)
    st.markdown(chatbot_config['solar_ownership'][st.session_state.solar_panel_ownership]['final_rating'][st.session_state.lang],unsafe_allow_html=True)
    #st.markdown(f"> *{st.session_state.summary}*")
    #st.divider()

    # Ensure rating state is properly initialized
    if "final_rating_submitted" not in st.session_state:
        st.session_state["final_rating_submitted"] = False

    if not st.session_state["final_rating_submitted"]:
        st.slider(
            "",
            0, 100,
            key="final_rating_slider"
        )
        #st.write(_("How helpful was this conversation regarding your questions or your general understanding of solar energy technologies?"))
        if st.button(_("Submit Final Rating"), key="submit_final_rating"):
            #send_ga_event("final_rating")
            insert_final_rating(st.session_state.final_rating_slider)
            st.session_state["final_rating_submitted"] = True
            st.session_state.final_rating = st.session_state.final_rating_slider
            #st.session_state.step = "completed"
            st.switch_page("./pages/final_page.py")
            st.rerun()

    write_footnote(short_version=False)

get_final_rating()