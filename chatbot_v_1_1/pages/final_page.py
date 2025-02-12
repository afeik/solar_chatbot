import streamlit as st
from components.footnote import write_footnote
from components.utils import language_dropdown, get_api_key

if "page_set" not in st.session_state:
    # If not, set it to the main page and reload
    st.switch_page("energy_transition_chatbot_main.py")
st.set_page_config("Solar Energy Chatbot",":robot_face:")
lang = st.session_state.lang
_, col = language_dropdown(lang,ret_cols=True)
with col:
    if st.button(_("Try Again?")):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("energy_transition_chatbot_main.py")

st.markdown(_("<b>Thank you for your valuable contribution to our research project on solar energy!</b>"), unsafe_allow_html=True)
st.write(_("If you have further questions, contact us:"))
st.write("Dr. Mengshuo Jia (PSL - ETH Zürich) jia@eeh.ee.ethz.ch")
st.write("Benjamin Sawicki (NCCR Automation) bsawicki@ethz.ch")
st.write("Andreas Feik (ETH Zürich) anfeik@ethz.ch")

write_footnote(short_version=False)