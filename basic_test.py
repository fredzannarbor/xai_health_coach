import streamlit as st

st.set_page_config(page_title="Basic Test")

st.title("Basic Test Page")
st.write("If you can see this, basic Streamlit is working")

st.divider()

st.write("Query Parameters:", dict(st.query_params))
st.write("Session State:", dict(st.session_state))

if st.button("Click Me"):
    st.write("Button clicked!")
