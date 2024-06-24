import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import subprocess
from datetime import datetime

st.set_page_config(
    layout="wide",
    page_title="Lazy Beancount",
    page_icon=":material/paid:"
)

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}

    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)

selected_page = option_menu(None, 
    ["Fava", "Import", "Price", 'Accounts'],
    icons=['coin', 'pencil', "graph-up", 'gear'],
    default_index=0,
    orientation="horizontal")

if selected_page == "Fava":
    components.iframe("http://localhost:5000", height=640)
elif selected_page == "Import":
    components.iframe("http://localhost:8101", height=640)
elif selected_page == "Price":
    date = st.date_input("Select date", datetime.today().date(), max_value=datetime.today().date())
    with st.spinner('Loading prices...'):
        beanprice_output = subprocess.check_output(
            ["bean-price", "../main.bean" ,"-i", f"--date={date.strftime('%Y-%m-%d')}"]
        )
        st.code(beanprice_output.decode('utf-8'))
elif selected_page == "Accounts":
    date = st.date_input("Select date", datetime.today().date())
    with st.spinner('Generating boilerplate...'):
        totals_update_code = subprocess.check_output(
            ["python3", "../gen_accounts.py", "--config_file", "../accounts_config.yml", "totals-update", date.strftime('%Y-%m-%d')]
        )
        totals_init_code = subprocess.check_output(
            ["python3", "../gen_accounts.py", "--config_file", "../accounts_config.yml", "totals-init"]
        )
        accounts_code = subprocess.check_output(
            ["python3", "../gen_accounts.py", "--config_file", "../accounts_config.yml", "accounts"]
        )
        st.subheader(f"Totals update for {date.strftime('%Y-%m-%d')}")
        st.code(totals_update_code.decode('utf-8'))
        st.subheader(f"Totals init")
        st.code(totals_init_code.decode('utf-8'))
        st.subheader(f"Accounts definition")
        st.code(accounts_code.decode('utf-8'))