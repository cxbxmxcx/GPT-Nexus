import streamlit as st

from gpt_nexus.nexus_base.nexus import Nexus


@st.cache_resource
def get_nexus():
    return Nexus()
