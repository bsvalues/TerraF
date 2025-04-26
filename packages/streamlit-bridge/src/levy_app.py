from tf_bridge import call_api
import streamlit as st

st.title("Levy Calculator POC")
prop_id = st.text_input("Property ID", "123")
if st.button("Calculate"):
    with st.spinner("Fetching…"):
        data = call_api(f"/api/v1/levy?propertyId={prop_id}")
    st.json(data)