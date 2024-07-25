#!/usr/bin/env python3

from typing import Optional

import datetime
import io

from dataclasses import dataclass, field
from collections import namedtuple
from datetime import datetime, timedelta

import click
import yaml

ACCOUNTS_OPENING_DATE = "1970-01-01"
ACCOUNTS_GEN_BY_TYPE = {
    'cash': [
        'Assets:@',
        'Equity:OpeningBalances:@',
        'Income:Unattributed:@',
        'Income:Uncategorized:@',
        'Expenses:Unattributed:@',
        'Expenses:Uncategorized:@'
    ],
    'opaque_funds': [
        'Assets:@',
        'Equity:OpeningBalances:@',
        'Income:@:PnL'
    ],
    'opaque_funds_valuation': [
        'Assets:@',
        'Equity:OpeningBalances:@',
        'Income:@:PnL'
    ],
    'investments': [
        'Assets:@',
        'Equity:OpeningBalances:@',
    ],
    'liabilities': [
        'Liabilities:@',
        'Equity:OpeningBalances:@',
        'Expenses:Unattributed:@'
    ]
}

ACCOUNT_TYPES = ACCOUNTS_GEN_BY_TYPE.keys()

@dataclass
class LeafConfig:
    type: str = field()
    name: str = field()
    currencies: list[str] = field()
    booking_method: Optional[str] = field()

@dataclass
class ParsedConfig:
    account_configs: list = field()
    opening_balances_date: datetime = field()

def generate_accounts_recursive(account_type, node, cur_name):
    # print(f'Gen {account_type}  {cur_name}')
    if isinstance(node, list):
        result = []
        for item in node:
            result.extend(generate_accounts_recursive(account_type, item, cur_name))
        return result
    elif isinstance(node, dict):
        results = []
        booking_method = None
        for key in node.keys():
            if key == 'currencies':
                results = [LeafConfig(account_type, cur_name, node[key], None)]
            elif key == 'leaf_currencies':
                for currency in node[key]:
                    results.append(
                        LeafConfig(account_type, f"{cur_name}:{currency}" if cur_name else currency, [currency], None)
                    )
            elif key == "booking_method":
                booking_method = node[key]
            else:  
                return generate_accounts_recursive(account_type, node[key], f"{cur_name}:{key}" if cur_name else key)
        for result in results:
            result.booking_method = booking_method
        return results
    else:
        return []
    
def parse_config(filename):
    with open(filename, 'r') as config:
        parsed_config = yaml.safe_load(config)
        # print(json.dumps(parsed_config, indent=4))
        configs = []
        for account_type in ACCOUNT_TYPES:
            if account_type in parsed_config:
                configs.extend(generate_accounts_recursive(account_type, parsed_config.get(account_type), ''))
        opening_balances_date = datetime.strptime(parsed_config['opening_balances_date'], '%Y-%m-%d')
        return ParsedConfig(
            account_configs=configs,
            opening_balances_date=opening_balances_date
        )

def gen_update_totals(config, date, values, initial_check=False, comment_accounts=set()):
    output = io.StringIO()

    pad_date = (date - timedelta(days=1)).strftime('%Y-%m-%d')
    balance_date = date.strftime('%Y-%m-%d')

    for cfg in config.account_configs:
        account_type = cfg.type
        name = cfg.name
        currencies = cfg.currencies
        if account_type in ['cash', 'opaque_funds', 'liabilities']:
            account_name = (f"Liabilities:{name}" if account_type == 'liabilities' else 
                f"Assets:{name}")
            if initial_check:
                pad_account = f'Equity:OpeningBalances:{name}'
            elif account_type == 'opaque_funds':
                pad_account = f"Income:{name}:PnL"
            else:
                pad_account = f"Expenses:Unattributed:{name}"
            if account_name in comment_accounts:
                output.write(f"; {pad_date} pad {account_name:65} {pad_account} \n")
            else:
                output.write(f"{pad_date} pad {account_name:65} {pad_account} \n")

    output.write('\n')
    for cfg in config.account_configs:
        account_type = cfg.type
        name = cfg.name
        currencies = cfg.currencies
        for currency in currencies:
            if (name, currency) in values:
                balance_statement = ''
                if account_type in ['cash', 'opaque_funds', 'liabilities']:
                    balance_statement = (f"{balance_date} balance Liabilities:{name}" if account_type == 'liabilities' else 
                        f"{balance_date} balance Assets:{name}")
                elif account_type == 'opaque_funds_valuation':
                    balance_statement = f"{balance_date} custom \"valuation\" Assets:{name}"
                output.write(f"{balance_statement:65} {values[(name, currency)]} {currency}\n")

    return output.getvalue()

def gen_accounts(config):
    output = io.StringIO()
    for cfg in config.account_configs:
        account_type = cfg.type
        name = cfg.name
        booking_method = cfg.booking_method
        account_names = [
            account.replace('@', name)
            for account in ACCOUNTS_GEN_BY_TYPE[account_type]
        ]
        for account in account_names:
            if booking_method and account.startswith('Assets:'):
                output.write(f"{ACCOUNTS_OPENING_DATE} open {account} \"{booking_method}\"\n")
            else:
                output.write(f"{ACCOUNTS_OPENING_DATE} open {account}\n")
        output.write('\n')
    return output.getvalue()

@click.group()
@click.option("--config_file", type=click.Path(), default="accounts_config.yml")
@click.pass_context
def cli(ctx, config_file):
    ctx.obj['config'] = parse_config(config_file)

@cli.command()
@click.pass_context
def accounts(ctx):
    config = ctx.obj['config']
    for account_type, name, _ in config.account_configs:
        account_names = [
            account.replace('@', name)
            for account in ACCOUNTS_GEN_BY_TYPE[account_type]
        ]
        for account in account_names:
            print(f"{ACCOUNTS_OPENING_DATE} open {account}")
        print()

@cli.command()
@click.pass_context
def totals_init(ctx):
    config = ctx.obj['config']
    pad_date = (config.opening_balances_date - timedelta(days=1)).strftime('%Y-%m-%d')
    balance_date = config.opening_balances_date.strftime('%Y-%m-%d')

    for cfg in config.account_configs:
        account_type = cfg.type
        name = cfg.name
        currencies = cfg.currencies
        for currency in currencies:
            if account_type in ['cash', 'opaque_funds', 'liabilities']:
                pad_statement_left = (f"{pad_date} pad Liabilities:{name}" if account_type == 'liabilities' else 
                    f"{pad_date} pad Assets:{name}")
                print(f"{pad_statement_left:60} Equity:OpeningBalances:{name}")

    print()
    for cfg in config.account_configs:
        account_type = cfg.type
        name = cfg.name
        currencies = cfg.currencies
        for currency in currencies:
            if account_type in ['cash', 'opaque_funds', 'liabilities']:
                balance_statement = (f"{balance_date} balance Liabilities:{name}" if account_type == 'liabilities' else 
                    f"{balance_date} balance Assets:{name}")
                print(f"{balance_statement:60}" + f"0 {currency}")

@cli.command()
@click.argument("date")
@click.pass_context
def totals_update(ctx, date):
    config = ctx.obj['config']
    parsed_date = datetime.strptime(date, '%Y-%m-%d')

    pad_date = (parsed_date - timedelta(days=1)).strftime('%Y-%m-%d')
    balance_date = parsed_date.strftime('%Y-%m-%d')

    print('\n')
    for account_type, name, currencies in config.account_configs:
        if account_type in ['cash', 'opaque_funds', 'liabilities']:
            pad_statement_left = (f"{pad_date} pad Liabilities:{name}" if account_type == 'liabilities' else 
                f"{pad_date} pad Assets:{name}")
            pad_account = (f"Income:{name}:PnL" if account_type == 'opaque_funds' else 
                f"Expenses:Unattributed:{name}")
            print(f"{pad_statement_left:60}" + pad_account)

    print()
    for account_type, name, currencies in config.account_configs:
        for currency in currencies:
            if account_type in ['cash', 'opaque_funds', 'liabilities']:
                balance_statement = (f"{balance_date} balance Liabilities:{name}" if account_type == 'liabilities' else 
                    f"{balance_date} balance Assets:{name}")
                print(f"{balance_statement:60}" + f"0 {currency}")
            elif account_type == 'opaque_funds_valuation':
                balance_statement = f"{balance_date} custom \"valuation\" Assets:{name}"
                print(f"{balance_statement:60}" + f"0 {currency}")

if __name__ == '__main__':
    cli(obj={})