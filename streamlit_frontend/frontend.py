import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
import subprocess
from datetime import datetime
import gen_accounts
import os
import re
import io
from decimal import Decimal
import yaml
from streamlit_ace import st_ace

ACCOUNT_TYPE_DESC = {
    'cash': '💶 Cash',
    'opaque_funds': '🏦 Fund',
    'opaque_funds_valuation': '🏦 Fund',
    'liabilities': '👥 Shared'
}
TOTALS_DIR = 'totals'
PRICES_DIR = 'prices'
ACCOUNTS_CONFIG_FILE = 'accounts_config.yml'
GENERATED_ACCOUNTS_FILE = 'accounts.gen.bean'
PRICES_CONFIG_FILE = 'prices_config.yml'

st.set_page_config(
    layout="wide",
    page_title="Lazy Beancount",
    page_icon=":abacus:",
    menu_items=None,
    initial_sidebar_state='collapsed'
)

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    [data-testid="collapsedControl"] {
        display: none
    }
    </style>
    """
st.markdown(hide_st_style, unsafe_allow_html=True)

def fava_page():
    components.iframe("http://localhost:5000", height=640)
    st.page_link('http://localhost:5000', label='open in new tab', icon=':material/arrow_outward:')

@st.experimental_dialog("File already exists. Overwrite?")
def write_file_dialog(filename, file_contents):
    st.text(f'Overwrite file {filename}?')
    if st.button('Yes'):
        with open(filename, 'w') as file:
            file.write(file_contents)
            st.text('Saved!')
            st.rerun()
    if st.button('Cancel'):
        st.rerun()

def file_editor_with_save(filename, additional_editor_params={}):
    with open(filename, 'r') as f:
        file_contents = f.read()
    editor_params = {
        'language':'yaml',
        'theme': 'nord_dark',
        'height': 560,
        **additional_editor_params
    }
    result = st_ace(file_contents, **editor_params)
    st.text("Don't forget to apply changes (cmd+enter) before clicking the button below")
    if st.button('Save', type='primary'):
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                file.write(result)
                st.text('File created!')
                st.rerun()
        else:
            write_file_dialog(filename, result)

def totals_page():
    col1, col2, col3 = st.columns([1, 2, 3])
    with col1:
        totals_files = sorted(os.listdir(TOTALS_DIR))
        totals_dates = []
        for filename in totals_files: 
            res = re.search(r"update-(\d+)-(\d+)-(\d+)\.gen\.bean", filename)
            if res:
                totals_dates.append(res.group(1) + '/' + res.group(2) + '/' + res.group(3))
        selected_file = option_menu(
            None, 
            ['New', 'Initial'] + totals_dates, 
            icons=['calendar-plus', 'calendar-minus'] + ['calendar'] * len(totals_dates)
        )
        
    with col2:
        config = gen_accounts.parse_config(ACCOUNTS_CONFIG_FILE)
        cur_date = None
        if selected_file == 'New':
            cur_date = datetime.today().date()
        elif selected_file == 'Initial':
            cur_date = config.opening_balances_date
        else:
            cur_date = datetime.strptime(selected_file, '%Y/%m/%d')
        date = st.date_input(
            "Select date", 
            cur_date, 
            max_value=datetime.today().date(), 
            min_value=config.opening_balances_date,
            disabled=(selected_file == 'Initial')
        )
        filename = None
        values = {}
        if selected_file == 'Initial':
            filename = os.path.join(TOTALS_DIR, 'initial.gen.bean')
            values = {}
        else:
            filename = os.path.join(TOTALS_DIR, 'update-' + date.strftime('%Y-%m-%d') + '.gen.bean')
            if os.path.exists(filename):
                values = {}
                with open(filename, 'r') as f:
                    for line in f:
                        res = re.search(r".+\s+balance\s+\w+\:([\w\:]+)\s+([\d\.]+)\s+(\w+).*", line)
                        if res:
                            values[(res.group(1), res.group(3))] = float(res.group(2))
                        res_val = re.search(r".+\s+\"valuation\"\s+\w+\:([\w\:]+)\s+([\d\.]+)\s+(\w+).*", line)
                        if res_val:
                            values[(res_val.group(1), res_val.group(3))] = float(res_val.group(2))
            else:
                if selected_file == 'New':
                    values = {}
                else:
                    values = st.session_state.get('totals_values', {})

        rows = []
        for account_type, name, currencies in config.account_configs:
            if account_type not in ['cash', 'opaque_funds', 'opaque_funds_valuation', 'liabilities']:
                continue
            for currency in currencies:
                rows.append({
                    'type': ACCOUNT_TYPE_DESC.get(account_type, '-'),
                    'name': name,
                    'currency': currency,
                    'value': values.get((name, currency), None)
                })
        st.session_state['totals_values'] = values

        edited_rows = st.data_editor(
            rows,
            column_config=
            {
                'type': 'Type',
                'name': 'Name',
                'currency': 'Currency',
                'value': st.column_config.NumberColumn('Value')
            },
            disabled=['type', 'name', 'currency'],
            use_container_width=True,
            height=560
        )
    
    with col3:
        if not os.path.exists(filename):
            st.subheader(f':green[{filename} (new)]')
        else:
            st.subheader(filename)
        values = {(row['name'], row['currency']): row['value'] for row in edited_rows if row['value'] is not None}
        file_contents = gen_accounts.gen_update_totals(config, date, values, initial_check=(selected_file == 'Initial'))
        st.code(file_contents)
        
        @st.experimental_dialog("Remove the file?")
        def delete_file_dialog():
            if st.button('Yes'):
                os.remove(filename)
                st.rerun()
            if st.button('Cancel'):
                st.rerun()

        if st.button('Save', type='primary'):
            if not os.path.exists(filename):
                with open(filename, 'w') as file:
                    file.write(file_contents)
                    st.text('File created!')
                    st.rerun()
            else:
                write_file_dialog(filename, file_contents)
        if os.path.exists(filename):
            if st.button('Delete'):
                delete_file_dialog()

def prices_page():
    prices_config = None
    with open(PRICES_CONFIG_FILE, 'r') as config:
        prices_config = yaml.safe_load(config)
    commodities_map = {}
    for c in prices_config.get('commodities') or []:
        for ind, val in c.items():
            commodities_map[ind] = val

    date = st.date_input("Select date", datetime.today().date(), max_value=datetime.today().date())
    with st.spinner('Fetching prices...'):
        command = ["bean-price", "main.bean" ,"-i", "-c", f"--date={date.strftime('%Y-%m-%d')}"]
        st.code(' '.join(command), language='shell')
        st.text('Processed output:')
        beanprice_output = subprocess.check_output(command)
        processed_output = io.StringIO()
        for line in beanprice_output.decode('utf-8').split('\n'):
            res = re.search(r"^([\d-]+)\s+price\s+([\w-]+)\s+([\d\\.]+)\s+([\w-]+)", line)
            if res:
                price_date = res.group(1)
                commodity = res.group(2)
                value = res.group(3)
                currency = res.group(4)

                updated_value = Decimal(value)
                if commodity in commodities_map and 'multiplier' in commodities_map[commodity]:
                    updated_value *= Decimal(commodities_map[commodity]['multiplier'])

                # Ignore zero values
                if updated_value > 0:
                    processed_output.write(f'{price_date} price {commodity:20} {updated_value:.8f} {currency}\n')
        st.code(processed_output.getvalue())

        filename = os.path.join(PRICES_DIR, 'prices-' + date.strftime('%Y-%m-%d') + '.gen.bean') 
        st.text(f'Save to {filename}?')
        if st.button('Save', type='primary'):
            with open(filename, "w") as f:
                f.write(processed_output.getvalue())
                st.text(f'Successfully saved into {filename}')

def import_page():
    components.iframe("http://localhost:8101", height=640)
    st.page_link('http://localhost:8101', label='open in new tab', icon=':material/arrow_outward:')

def config_page():
    selected_config = st.selectbox(
        'File', 
        options=[
            'accounts_config.yml', 
            'prices_config.yml', 
            'importers_config.yml',
            'main.bean', 
            'accounts.bean', 
            'commodities.bean', 
            'manual_transactions.bean'
        ],
        label_visibility="collapsed"
    )
    if selected_config == 'accounts_config.yml':
        col1, col2 = st.columns([2, 1])
        config = gen_accounts.parse_config(ACCOUNTS_CONFIG_FILE)
        with col1:
            with open(ACCOUNTS_CONFIG_FILE, 'r') as f:
                accounts_config = f.read()
            result = st_ace(accounts_config, language='yaml', theme='nord_dark', height=600)
            with open(ACCOUNTS_CONFIG_FILE, 'w') as f:
                f.write(result)
        
        with col2:
            st.subheader(GENERATED_ACCOUNTS_FILE)
            accounts_definitions = gen_accounts.gen_accounts(config)
            with st.container(height=500, border=False):
                st.code(accounts_definitions)
            if st.button('Save', type='primary'):
                with open(GENERATED_ACCOUNTS_FILE, 'w') as f:
                    f.write(accounts_definitions)
                st.text(f'Saved {GENERATED_ACCOUNTS_FILE}')
    elif selected_config == 'prices_config.yml':
        file_editor_with_save('prices_config.yml', {'height':460})
    elif selected_config == 'importers_config.yml':
        file_editor_with_save('importers_config.yml', {'height':460})
    elif selected_config == 'main.bean':
        file_editor_with_save('main.bean', {'language':'lisp', 'height':460})
    elif selected_config == 'accounts.bean':
        file_editor_with_save('accounts.bean', {'language':'lisp', 'height':460})
    elif selected_config == 'commodities.bean':
        file_editor_with_save('commodities.bean', {'language':'lisp', 'height':460})
    elif selected_config == 'manual_transactions.bean':
        file_editor_with_save('manual_transactions.bean', {'language':'lisp', 'height':460})

pages = [
    st.Page(fava_page, title="Fava", url_path='fava'),
    st.Page(totals_page, title="Totals", url_path='totals'),
    st.Page(import_page, title="Import", url_path='import'),
    st.Page(prices_page, title="Prices", url_path='prices'),
    st.Page(config_page, title="Config", url_path='config'),
]
pg = st.navigation(pages)

selected_page_index = 0
for p in pages:
    if pg.title == p.title:
        break
    selected_page_index += 1
selected_page = option_menu(None, 
    [page.title for page in pages],
    icons=['coin', 'pencil', 'upload', "graph-up", 'gear'],
    default_index=selected_page_index,
    orientation="horizontal"
)
pg.run()
if selected_page != pg.title:
    for p in pages:
        if p.title == selected_page:
            st.switch_page(p)
