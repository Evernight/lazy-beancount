#!/usr/bin/env python3

import io
from math import isnan
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

import streamlit as st
import streamlit.components.v1 as components
import yaml
from beancount import loader
from beancount_importers import beancount_import_run
from streamlit_ace import st_ace
from streamlit_echarts import JsCode, st_echarts
from streamlit_option_menu import option_menu

import gen_accounts

ACCOUNT_TYPE_DESC = {
    "cash": "💶 Cash",
    "opaque_funds": "🏦 Fund",
    "opaque_funds_valuation": "🏦 Fund",
    "liabilities": "👥 Shared",
}
TOTALS_DIR = "totals"
PRICES_DIR = "prices"
ACCOUNTS_CONFIG_FILE = "accounts_config.yml"
GENERATED_ACCOUNTS_FILE = "accounts.gen.bean"
PRICES_CONFIG_FILE = "prices_config.yml"
MAIN_LEDGER_FILE = "main.bean"

hostname = os.environ.get("LAZY_BEANCOUNT_HOST", "localhost")
fava_port = os.environ.get("FAVA_PORT", 5003)
beancount_import_port = os.environ.get("BEANCOUNT_IMPORT_PORT", 8101)
lazy_beancount_port = os.environ.get("LAZY_BEANCOUNT_PORT", 8777)

st.set_page_config(
    layout="wide",
    page_title="Lazy Beancount",
    page_icon=f"http://{hostname}:{lazy_beancount_port}/app/static/favicon-32x32.png",
    menu_items=None,
    initial_sidebar_state="collapsed",
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


def trigger_fava_reload():
    command = ["touch", MAIN_LEDGER_FILE]
    subprocess.check_output(command)
    print("Triggered Fava reload")


def fava_page():
    components.iframe(f"http://{hostname}:{fava_port}", height=640)
    st.page_link(
        f"http://{hostname}:{fava_port}",
        label="open in new tab",
        icon=":material/arrow_outward:",
    )


@st.dialog("File already exists. Overwrite?")
def write_file_dialog(filename, file_contents, on_confirm=None):
    st.text(f"Overwrite file {filename}?")
    if st.button("Yes"):
        with open(filename, "w") as file:
            file.write(file_contents)
        if on_confirm:
            with st.spinner("Saving..."):
                on_confirm()
        st.text("Saved!")
        st.rerun()
    if st.button("Cancel"):
        st.rerun()


def file_editor_with_save(filename, additional_editor_params={}):
    with open(filename, "r") as f:
        file_contents = f.read()
    editor_params = {
        "language": "yaml",
        "theme": "nord_dark",
        "height": 560,
        **additional_editor_params,
    }
    result = st_ace(file_contents, **editor_params)
    st.text(
        "Don't forget to apply changes (cmd+enter) before clicking the button below"
    )
    if st.button("Save", type="primary"):
        if not os.path.exists(filename):
            with open(filename, "w") as file:
                file.write(result)
                st.text("File created!")
                st.rerun()
        else:
            write_file_dialog(filename, result)


def totals_page():
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        totals_files = sorted(os.listdir(TOTALS_DIR))
        totals_dates = []
        for filename in totals_files:
            res = re.search(r"update-(\d+)-(\d+)-(\d+)\.gen\.bean", filename)
            if res:
                totals_dates.append(
                    res.group(1) + "/" + res.group(2) + "/" + res.group(3)
                )
        selected_file = option_menu(
            None,
            ["New", "Initial"] + totals_dates,
            icons=["calendar-plus", "calendar-minus"]
            + ["calendar"] * len(totals_dates),
        )

    with col2:
        config = gen_accounts.parse_config(ACCOUNTS_CONFIG_FILE)
        cur_date = None
        if selected_file == "New":
            cur_date = datetime.today().date()
        elif selected_file == "Initial":
            cur_date = config.opening_balances_date
        else:
            cur_date = datetime.strptime(selected_file, "%Y/%m/%d")
        date = st.date_input(
            "Select date",
            cur_date,
            max_value=(datetime.today() + timedelta(days=7)).date(),
            min_value=config.opening_balances_date,
            disabled=(selected_file == "Initial"),
        )
        filename = None
        values = {}
        if selected_file == "Initial":
            filename = os.path.join(TOTALS_DIR, "initial.gen.bean")
        else:
            filename = os.path.join(
                TOTALS_DIR, "update-" + date.strftime("%Y-%m-%d") + ".gen.bean"
            )

        if os.path.exists(filename):
            values = {}
            with open(filename, "r") as f:
                for line in f:
                    res = re.search(
                        r".+\s+balance\s+\w+\:([\w\:]+)\s+([-\d\.]+)\s+(\w+).*", line
                    )
                    if res:
                        values[(res.group(1), res.group(3))] = float(res.group(2))
                    res_val = re.search(
                        r".+\s+\"valuation\"\s+\w+\:([\w\:]+)\s+([-\d\.]+)\s+(\w+).*",
                        line,
                    )
                    if res_val:
                        values[(res_val.group(1), res_val.group(3))] = float(
                            res_val.group(2)
                        )
        else:
            if selected_file == "New":
                values = {}
            else:
                values = st.session_state.get("totals_values", {})

        rows = []
        all_currencies = set()

        for cfg in config.account_configs:
            account_type = cfg.type
            name = cfg.name
            currencies = cfg.currencies
            if account_type not in [
                "cash",
                "opaque_funds",
                "opaque_funds_valuation",
                "liabilities",
            ]:
                continue
            for currency in currencies:
                rows.append(
                    {
                        "type": ACCOUNT_TYPE_DESC.get(account_type, "-"),
                        "name": name,
                        "currency": currency,
                        "value": values.get((name, currency), None),
                    }
                )
                all_currencies.add(currency)
        st.session_state["totals_values"] = values


        edited_rows = st.data_editor(
            rows,
            column_config={
                "type": "Type",
                "name": "Name",
                "currency": st.column_config.MultiselectColumn(
                    "Currency", 
                    color=["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc"],
                    options=all_currencies
                ),
                "value": st.column_config.NumberColumn("Value", format="accounting"),
            },
            disabled=["type", "name", "currency"],
            width='stretch',
            height=560,
        )

    with col3:
        if not os.path.exists(filename):
            st.subheader(f":green[{filename} (new)]")
        else:
            st.subheader(filename)

        st.markdown(
            "Don't forget to save the file after editing. This may take few seconds for a large ledger since it will "
            + "check which ```pad``` operations are necessary and which should be commented out."
        )

        values = {
            (str(row["name"]), str(row["currency"])): Decimal(str(row["value"]))
            for row in edited_rows
            if row["value"] is not None and not isnan(row["value"])
        }
        file_contents = gen_accounts.gen_update_totals(
            config, date, values, is_initial_check=(selected_file == "Initial")
        )
        st.code(file_contents)

        @st.dialog("Remove the file?")
        def delete_file_dialog():
            if st.button("Yes"):
                os.remove(filename)
                trigger_fava_reload()
                st.rerun()
            if st.button("Cancel"):
                st.rerun()

        if st.button("Save", type="primary"):

            def comment_out_unused_pads():
                entries, errors, options_map = loader.load_file(MAIN_LEDGER_FILE)
                comment_pad_accounts = set()
                for error in errors:
                    if (
                        error.message == "Unused Pad entry"
                        and filename in error.source["filename"]
                    ):
                        comment_pad_accounts.add(error.entry.account)
                file_contents_pad_commented = gen_accounts.gen_update_totals(
                    config,
                    date,
                    values,
                    is_initial_check=(selected_file == "Initial"),
                    comment_accounts=comment_pad_accounts,
                )
                with open(filename, "w") as file:
                    file.write(file_contents_pad_commented)
                trigger_fava_reload()

            if not os.path.exists(filename):
                with st.spinner("Saving..."):
                    with open(filename, "w") as file:
                        file.write(file_contents)
                    comment_out_unused_pads()
                    st.text("File created!")
            else:
                write_file_dialog(
                    filename, file_contents, on_confirm=comment_out_unused_pads
                )
        if os.path.exists(filename):
            if st.button("Delete"):
                delete_file_dialog()


def prices_page():
    col1, col2 = st.columns([1, 4])

    date = None
    prices_for_dates = st.session_state.get("prices_for_dates", defaultdict(str))
    with col2:
        prices_config = None
        with open(PRICES_CONFIG_FILE, "r") as config:
            prices_config = yaml.safe_load(config)
        commodities_map = {}
        for c in prices_config.get("commodities") or []:
            for ind, val in c.items():
                commodities_map[ind] = val

        date = st.date_input(
            "Select date", datetime.today().date(), max_value=datetime.today().date()
        )
        date_str = str(date)
        if st.button("Fetch", type="primary"):
            with st.spinner("Fetching prices..."):
                try:
                    command = [
                        "bean-price",
                        MAIN_LEDGER_FILE,
                        "-i",
                        "-c",
                        f"--date={date.strftime('%Y-%m-%d')}",
                    ]
                    st.code(" ".join(command), language="shell")

                    beanprice_output = subprocess.check_output(command)
                    processed_output = io.StringIO()
                    for line in beanprice_output.decode("utf-8").split("\n"):
                        res = re.search(
                            r"^([\d-]+)\s+price\s+([\w-]+)\s+([\d\\.]+)\s+([\w-]+)",
                            line,
                        )
                        if res:
                            price_date = res.group(1)
                            commodity = res.group(2)
                            value = res.group(3)
                            currency = res.group(4)

                            updated_value = Decimal(value)
                            if (
                                commodity in commodities_map
                                and "multiplier" in commodities_map[commodity]
                            ):
                                updated_value *= Decimal(
                                    commodities_map[commodity]["multiplier"]
                                )

                            # Ignore zero values
                            if updated_value > 0:
                                processed_output.write(
                                    f"{price_date} price {commodity:20} {updated_value:.8f} {currency}\n"
                                )

                    prices_for_dates[date_str] = processed_output.getvalue()
                    st.session_state["prices_for_dates"] = prices_for_dates

                except Exception as e:
                    st.code(str(e))

        st.subheader("Processed output:")
        st.code(prices_for_dates[date_str])

        filename = os.path.join(
            PRICES_DIR, "prices-" + date.strftime("%Y-%m-%d") + ".gen.bean"
        )
        st.markdown(f"Save to ```{filename}```?")
        if st.button(
            "Save", type="primary", disabled=(prices_for_dates[date_str] == "")
        ):
            print("saving")
            print(prices_for_dates[date_str])
            with open(filename, "w") as f:
                f.write(prices_for_dates[date_str])
                st.markdown(f"Successfully saved into ```{filename}```")
                trigger_fava_reload()

    with col1:
        prices_files = sorted(os.listdir(PRICES_DIR))
        prices_dates = []
        for filename in prices_files:
            res = re.search(r"prices-(\d+)-(\d+)-(\d+)\.gen\.bean", filename)
            if res and res.group(1) == str(date.year):
                # prices_dates.append(res.group(1) + '/' + res.group(2) + '/' + res.group(3))
                prices_dates.append(
                    (
                        res.group(1) + "-" + res.group(2) + "-" + res.group(3),
                        int(res.group(3)),
                    )
                )
        heatmap = {
            "tooltip": {
                "position": "top",
            },
            "calendar": [
                {
                    "orient": "vertical",
                    "range": str(date.year),
                    "cellSize": [20, "auto"],
                    "dayLabel": {"show": True, "firstDay": 1, "color": "#ddd"},
                    "monthLabel": {"show": True, "color": "#ddd"},
                    # 'itemStyle': {'color' : '#333'}
                    # 'yearLabel': { 'show': False }
                }
            ],
            "series": {
                "type": "heatmap",
                "coordinateSystem": "calendar",
                "symbolSize": 0,
                "label": {
                    "show": True,
                    "formatter": JsCode("function(p) {return p.data[1];}").js_code,
                    "fontSize": 8,
                },
                "data": prices_dates,
            },
        }
        st_echarts(options=heatmap, height=640)


def import_page():
    selected_import_page = option_menu(
        None,
        ["Review data", "Upload files"],
        icons=["view-list", "file-earmark-arrow-up-fill"],
        orientation="horizontal",
    )
    if selected_import_page == "Review data":
        components.iframe(f"http://{hostname}:{beancount_import_port}", height=540)
        st.page_link(
            f"http://{hostname}:{beancount_import_port}",
            label="open in new tab",
            icon=":material/arrow_outward:",
        )
    else:
        st.markdown(
            "Define configuration of importers in `importers_config.yml` under Config tab first. "
            + "Then upload statement files (for example, ```csv```) here."
        )
        importers_config = beancount_import_run.load_import_config_from_file(
            "importers_config.yml", "beancount_import_data", "beancount_import_output"
        )
        columns = st.columns(3)
        col_ind = 0
        all_types = dict.fromkeys(
            c.get("type", "?") for c in importers_config["all"]["data_sources"]
        )
        type_markers = "🔴🟣🟠🟢🟡🔵🟤"
        type_marker = {}
        for i, type in enumerate(all_types):
            type_marker[type] = type_markers[i % len(type_markers)]

        for config in importers_config["all"]["data_sources"]:
            with columns[col_ind].container(border=True):
                uploaded_file = st.file_uploader(
                    f"{config.get('emoji', '📄')} **{config['account']}**\n\n"
                    + f"{type_marker[config.get('type', '?')]} 💱 **{config.get('currency', '?')}**\n\n"
                    + f"{config['directory']}",
                    help=config.get("description"),
                )
                if uploaded_file is not None:
                    bytes_data = uploaded_file.getvalue()
                    available_file_name = uploaded_file.name
                    ind = 0
                    while os.path.exists(
                        os.path.join(config["directory"], available_file_name)
                    ):
                        ind += 1
                        filename_and_ext = os.path.splitext(uploaded_file.name)
                        available_file_name = (
                            f"{filename_and_ext[0]}_{ind}{filename_and_ext[1]}"
                        )
                    with open(
                        os.path.join(config["directory"], available_file_name), "wb"
                    ) as f:
                        f.write(bytes_data)

                    @st.dialog("File uploaded")
                    def file_uploaded():
                        st.write(
                            f"Uploaded to ```{os.path.join(config['directory'], available_file_name)}```"
                        )
                        if st.button("Great!"):
                            st.rerun()

                    file_uploaded()
            col_ind = (col_ind + 1) % 3


def config_page():
    selected_config = st.selectbox(
        "File",
        options=[
            "accounts_config.yml",
            "prices_config.yml",
            "importers_config.yml",
            "main.bean",
            "accounts.bean",
            "commodities.bean",
            "manual_transactions.bean",
        ],
        label_visibility="collapsed",
    )
    if selected_config == ACCOUNTS_CONFIG_FILE:
        col1, col2 = st.columns([1, 1])
        # config = gen_accounts.parse_config(ACCOUNTS_CONFIG_FILE)
        with col1:
            with open(ACCOUNTS_CONFIG_FILE, "r") as f:
                accounts_config = f.read()
            text_edit_content = st_ace(
                accounts_config,
                auto_update=True,
                language="yaml",
                theme="nord_dark",
                height=600,
                tab_size=2,
                font_size=12,
            )

        with col2:
            st.subheader(GENERATED_ACCOUNTS_FILE)
            st.markdown(
                "This editor is experimental, please save periodically / back up content / "
                + "don't type a lot at once or use an external editor in addition"
            )

            result_content = ""
            error = False
            try:
                parsed_config = gen_accounts.parse_config_from_string(text_edit_content)
                result_content = gen_accounts.gen_accounts(parsed_config)
            except Exception as e:
                result_content = str(e)
                error = True

            with st.container(height=480, border=False):
                st.code(result_content, line_numbers=True)
            if st.button(
                f"Save file and update {GENERATED_ACCOUNTS_FILE}",
                type="primary",
                disabled=error,
            ):
                with open(ACCOUNTS_CONFIG_FILE, "w") as f:
                    f.write(text_edit_content)
                with open(GENERATED_ACCOUNTS_FILE, "w") as f:
                    f.write(result_content)
                st.text(
                    f"Saved {ACCOUNTS_CONFIG_FILE} and updated {GENERATED_ACCOUNTS_FILE}"
                )

    elif selected_config == "prices_config.yml":
        file_editor_with_save("prices_config.yml", {"height": 460})
    elif selected_config == "importers_config.yml":
        file_editor_with_save("importers_config.yml", {"height": 460})
    elif selected_config == "main.bean":
        file_editor_with_save("main.bean", {"language": "lisp", "height": 460})
    elif selected_config == "accounts.bean":
        file_editor_with_save("accounts.bean", {"language": "lisp", "height": 460})
    elif selected_config == "commodities.bean":
        file_editor_with_save("commodities.bean", {"language": "lisp", "height": 460})
    elif selected_config == "manual_transactions.bean":
        file_editor_with_save(
            "manual_transactions.bean", {"language": "lisp", "height": 460}
        )


def logs_page():
    if st.button("Trigger Fava reload", type="primary"):
        trigger_fava_reload()
    if st.button("Catch up with logs", type="primary"):
        # Don't do anything in particular but this will update the st.code element on the page
        pass
    st.code(open("lazy-beancount.log", "r").read(), line_numbers=True)


pages = [
    st.Page(fava_page, title="Fava", url_path="fava"),
    st.Page(totals_page, title="Totals", url_path="totals"),
    st.Page(import_page, title="Import", url_path="import"),
    st.Page(prices_page, title="Prices", url_path="prices"),
    st.Page(logs_page, title="Logs", url_path="logs"),
    st.Page(config_page, title="Config", url_path="config"),
]
pg = st.navigation(pages)

selected_page_index = 0
for p in pages:
    if pg.title == p.title:
        break
    selected_page_index += 1
selected_page = option_menu(
    None,
    [page.title for page in pages],
    icons=["coin", "pencil", "file-earmark-arrow-up", "graph-up", "file-text", "gear"],
    default_index=selected_page_index,
    orientation="horizontal",
)
with st.sidebar:
    st.page_link(
        f"http://{hostname}:{fava_port}", label="Fava", icon=":material/arrow_outward:"
    )
    st.page_link(
        f"http://{hostname}:{beancount_import_port}",
        label="Beancount Import",
        icon=":material/arrow_outward:",
    )
pg.run()
if selected_page != pg.title:
    for p in pages:
        if p.title == selected_page:
            st.switch_page(p)
