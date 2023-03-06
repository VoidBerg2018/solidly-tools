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
    page_title="💵 Pool fees history",
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
st.title("💸 Pool fees history")

### Get pool list data
pool_dict = {}
# Load pool data
pool_dict = load_pool_dict(filename='pools.json')
# Add if missing
pools_add_missing(pool_dict, contractinstance=contract_instance_Voter, web3=w3, abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"], abi_token=config["data"]["abi_Token"])
# Save pool data
#save_pool_dict_to_file(filename='pools.json', pools=pool_dict)



try:
    w3 = Web3(Web3.HTTPProvider(config["data"]["provider_url"]))
    set_contracts_for_pools(pool_dict=pool_dict, web3=w3, abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"], abi_feedist=config["data"]["abi_Feedist"], abi_bribe=config["data"]["abi_Bribe"])
except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")




for key in pool_dict:
    st.caption("Pool fees for " + pool_dict[key]["name"])
    first_period = first_solidly_vote_period_start
    period = get_active_period(contract_instance_Voter)
    pooldata = []
    while period > first_period:
        fees_token0 = pool_dict[key]["contract_feedist"].functions.periodRewardAmount(period, pool_dict[key]["token0_address"]).call()
        fees_token1 = pool_dict[key]["contract_feedist"].functions.periodRewardAmount(period, pool_dict[key]["token1_address"]).call()

        fees_token0 = round(fees_token0 / pow(10, pool_dict[key]["token0_decimals"]), 2)
        fees_token1 = round(fees_token1 / pow(10, pool_dict[key]["token1_decimals"]), 2)
        fees_token0_usd = fees_token0 * get_token_price(pool_dict[key]["token0_address"])
        fees_token1_usd = fees_token1 * get_token_price(pool_dict[key]["token1_address"])

        sum_fees_usd = round(fees_token0_usd + fees_token1_usd)
        pooldata.append(
            {
                "🕰️ Epoch": datetime.utcfromtimestamp(period).strftime('%Y-%m-%d'),
                "🪙 "+pool_dict[key]["token0_symbol"]: str(fees_token0),
                "🪙 "+pool_dict[key]["token1_symbol"]: str(fees_token1),
                "💵 Sum ($) ": str(sum_fees_usd)
            }
        )
        period = period - 604800

    if pooldata:
        fees_df = pd.DataFrame(pooldata)
        # st.bar_chart(votes_df, x="epoch")
        st.dataframe(fees_df)




# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
