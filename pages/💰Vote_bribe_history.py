from web3 import Web3
import time
import streamlit as st
from st_btn_select import st_btn_select
import yaml
import requests
from datetime import datetime
import pandas as pd
from veSolidfunctions import *
import json

# App
st.set_page_config(
    page_title="💰 Vote bribe history",
    page_icon="icons/solid.png",
    layout="wide",
)

# Params
params_path = "params.yaml"
config = read_params(params_path)

try:
    w3 = Web3(Web3.HTTPProvider(config["data"]["provider_url"]))
    contract_instance_veNFT = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_veNFT"]), abi=config["data"]["abi_veNFT"])
    contract_instance_Token = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_Token"]), abi=config["data"]["abi_Token"])
    contract_instance_Voter = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_Voter"]), abi=config["data"]["abi_Voter"])

except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

############################
# Page display
#############################
st.title("💰 Vote bribe history")

### Get pool list data
#pool_list = get_all_pools(contractinstance=contract_instance_Voter, web3=w3, abi_pool=config["data"]["abi_Token"], abi_gauge=config["data"]["abi_Gauge"])
# Save pool data
#save_pool_list_to_file(filename='pools.json', pools=pool_list)
# Read pool data
pool_list = load_pool_list(filename='pools.json')
try:
    w3 = Web3(Web3.HTTPProvider(config["data"]["provider_url"]))
    set_contracts_for_pools(pools=pool_list, web3=w3, abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"], abi_feedist=config["data"]["abi_Feedist"], abi_bribe=config["data"]["abi_Bribe"])
except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

first_period = first_solidly_vote_period_start
period = 1677110400
while period > first_period:
    st.caption("Vote bribes for epoch starting at " + datetime.utcfromtimestamp(period + 604800).strftime('%Y-%m-%d'))
    pooldata = []
    for pool in pool_list:
        bribe_tokens = pool["contract_bribe"].functions.periodRewardsList(period).call()

        for token_address in bribe_tokens:
            bribe_amount = pool["contract_bribe"].functions.periodRewardAmount(period, token_address).call()
            bribe_token_data = get_token_data(address=token_address, web3=w3, abi=config["data"]["abi_ERC20"])
            bribe_amount = bribe_amount / pow(10, bribe_token_data["decimals"])
            if (bribe_amount < 10):
                bribe_amount = round(bribe_amount, 2)
            else:
                bribe_amount = round(bribe_amount)

            bribe_usd = round(bribe_amount * get_token_price(token_address))

            pooldata.append(
                {
                    "🏊 Pool": pool["name"],
                    "🪙 Bribe token": bribe_token_data["symbol"],
                    "💰 Bribe token amount": str(bribe_amount),
                    "💰 Bribe value ($)": str(bribe_usd),
                }
            )

    if pooldata:
        bribes_df = pd.DataFrame(pooldata)
        # st.bar_chart(votes_df, x="epoch")
        st.dataframe(bribes_df)

    period = period - 604800



# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
