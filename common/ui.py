from pathlib import Path
import runpy
import streamlit as st
from common.contact import render_contact
ROOT = Path(__file__).resolve().parents[1]


def render_guide(app_id):
    st.info('Free demonstration • Synthetic example data only • No file uploads or live database connections')
    text = (ROOT / 'guides' / (app_id + '.md')).read_text(encoding='utf-8')
    with st.expander('Start here: a detailed explanation of this app', expanded=True):
        st.markdown(text)


class DemoStopped(Exception):
    """Pause analysis while keeping the shared contact form available."""


def run_demo(source, app_id, app_name):
    try:
        runpy.run_path(str(source), run_name='__main__')
    except DemoStopped:
        pass
    render_contact(app_id, app_name)
    st.divider()
    st.markdown("**Powered by Hertzler Systems**")
    st.image(str(ROOT / "assets" / "hertzler_logo.png"), width=360)
