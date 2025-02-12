import streamlit as st
from components.footnote import write_footnote
from components.db_communication import insert_db_message, insert_full_conversation_details
from components.utils import get_chatbot_config, language_dropdown

st.set_page_config("Solar Energy Chatbot",":robot_face:")
chatbot_config = get_chatbot_config()

def get_user_statement_and_summary(client):
    """
    Collects a user statement, generates a summary using the Claude API,
    and displays the summary for user confirmation, along with additional mandatory user details.
    """
    lang = st.session_state.lang
    _ = language_dropdown(lang)
    lang = st.session_state.lang

    # Load titles and concerns from the configuration file
    page_title = chatbot_config["titles"]["concerns_page"][lang]["page_title"]
    text_area_title = chatbot_config["titles"]["concerns_page"][lang]["text_area_title"]
    example_concerns = chatbot_config["concerns"][lang]

    # Initialize session state variables
    default_states = {
        #"age_group": "Select",
        #"gender": "Select",
        #"highest_degree": "Select",
        "lang": lang,
        "summary": None,
        "statement": None,
        "step": None,
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Page title
    st.markdown(f"<h4>{page_title}</h4>", unsafe_allow_html=True)

    # # Dropdown options
    # age_group_label = _("Age Group:")
    # gender_label = _("Gender:")
    # degree_label = _("Highest Degree Achieved:")
    # age_groups = [
    #     _("Select"), _("Under 18"), _("18-24"), _("25-34"),
    #     _("35-44"), _("45-54"), _("55-64"), _("65 and older"), _("Prefer not to say")
    # ]
    # genders = [_("Select"), _("Male"), _("Female"), _("Other"), _("Prefer not to say")]
    # degrees = [_("Select"), _("High School"), _("Bachelor's"), _("Master's"), _("PhD"), _("Other")]

    # st.session_state.age_group = st.selectbox(age_group_label, age_groups, key="age_group_selectbox")
    # st.session_state.gender = st.selectbox(gender_label, genders, key="gender_selectbox")
    # st.session_state.highest_degree = st.selectbox(degree_label, degrees, key="degree_selectbox")
    
    if "age_group" not in st.session_state:
        st.session_state.age_group = None

    if "gender" not in st.session_state:
        st.session_state.gender = None
        
    if "highest_degree" not in st.session_state: 
        st.session_state.highest_degree = None

    # Text area for the user statement
    statement = st.text_area(
        f"{text_area_title}",
        height=200,
        key="user_statement_textarea"
    )

    # Columns for submit button and error placeholder
    col1, col2 = st.columns([1.5, 3.6])
    with col1:
        submit_button = st.button(_("Submit Statement"), key="submit_button")
    with col2:
        error_placeholder = st.empty()

    # Expandable section for example concerns
    with st.expander(_("Need inspiration? Click here to see example concerns.")):
        for concern in example_concerns:
            st.markdown(f"<p style='font-size:14px;color:grey;margin-bottom:10px;'>- {concern}</p>", unsafe_allow_html=True)

    # Validation
    min_char_count = 30
    char_count = len(statement)
    fields_filled = (
        #st.session_state.age_group != _("Select")
        #and st.session_state.gender != _("Select")
        #and st.session_state.highest_degree != _("Select") and
        char_count >= min_char_count
    )

    if submit_button:
        if not fields_filled:
            # Error message for incomplete fields
            with col2:
                error_message = "<div style='color: red; font-size: 13px;'>"
                # if st.session_state.age_group == _("Select"):
                #     error_message += _("Please select your age group.")
                # elif st.session_state.gender == _("Select"):
                #     error_message += _("Please select your gender.")
                # elif st.session_state.highest_degree == _("Select"):
                #     error_message += _("Please select your highest degree.")
                if char_count < min_char_count:
                    error_message += (
                        _("Please enter at least ") +
                        str(min_char_count) +
                        _(" characters. You currently have: ") +
                        str(char_count) +
                        _(" characters.")
                    )
                error_message += "</div>"
                error_placeholder.markdown(error_message, unsafe_allow_html=True)
        else:
            # Clear error placeholder
            error_placeholder.empty()

            # Language prompt
            lang_prompt = "Use the English Language." if lang == "en" else "Verwende die Deutsche Sprache."

            # Call to the Claude API
            try:
                summary_response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=chatbot_config["general"]["summary_max_tokens"],
                    system=lang_prompt + chatbot_config["general"]["summary_role"],
                    messages=[
                        {"role": "user", "content": [{"type": "text", "text": statement}]}
                    ],
                    temperature=chatbot_config["general"]["summary_temperature"],
                )
                summary = summary_response.content[0].text.strip()
            except Exception as e:
                st.error(f"Failed to generate a summary. Error: {e}")
                return

            # Store data in session state
            st.session_state.summary = summary
            st.session_state.statement = statement

            # Save details to the database
            try:
                insert_db_message(statement, role="user", message_type="initial_statement")
                insert_db_message(summary, role="assistant", message_type="initial_statement_summary")
                insert_full_conversation_details(
                    st.session_state.age_group,
                    st.session_state.gender,
                    st.session_state.highest_degree,
                    st.session_state.consent_given,
                )
            except Exception as e:
                st.error(f"Failed to save data to the database. Error: {e}")
                return

            # Move to the next step
            st.session_state.step = "initial_rating"
            st.rerun()

    # Footer
    write_footnote()



