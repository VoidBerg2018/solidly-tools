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


def display_pool_rewards(pool, pool_fees, bribe_pool_data, current_period):
    if pool:
        st.caption("Voter rewards for " + pool["name"])
        start_period = first_solidly_vote_period_start

        pooldata = []
        index = 0
        while start_period <= current_period:
            key = pool["address"]
            fees_token0 = pool_fees[key][str(start_period)]["fees_token0"]
            fees_token1 = pool_fees[key][str(start_period)]["fees_token1"]

            fees_token0_usd = fees_token0 * get_token_price(pool_dict[key]["token0_address"])
            fees_token1_usd = fees_token1 * get_token_price(pool_dict[key]["token1_address"])

            sum_fees_usd = round(fees_token0_usd + fees_token1_usd)

            sum_bribes_usd = 0
            bribe_string = ""

            bribe_period = str(start_period - 604800)
            if bribe_period in bribe_pool_data:
                for entry in bribe_pool_data[bribe_period]:
                    if entry["🏊 Pool"] == pool["name"]:
                        bribe_string = bribe_string + entry["💰 Bribe token amount"] + " " + entry["🪙 Bribe token"] + " "
                        sum_bribes_usd = sum_bribes_usd + int(entry["💰 Bribe value ($)"])


            pool_votes = round(get_pool_votes_for_period(pool["address"], start_period- 604800, contract_instance_Voter))
            sum_sum = round(sum_fees_usd + sum_bribes_usd)
            rewards_per_votes = 0
            if (pool_votes > 0):
                rewards_per_votes = round((sum_sum / pool_votes) * 10000)

            if (rewards_per_votes > sum_sum):
                rewards_per_votes = sum_sum

            apr_per_votes = round(((rewards_per_votes * 52) / (get_solid_price() * 10000)) * 100, 2)

            epochstart = datetime.utcfromtimestamp(start_period ).strftime('%Y-%m-%d')
           # if index == 0:
            #    epochstart = datetime.utcfromtimestamp(period + 604800).strftime('%Y-%m-%d') + " (upcoming)"
           # if index == 1:
           #     epochstart = datetime.utcfromtimestamp(period + 604800).strftime('%Y-%m-%d') + " (current)"

            pooldata.append(
                {
                    "🕰️ Epoch starting at": epochstart,
                    "🪙 " + pool["token0_symbol"] + " fees": avoid_0_str(fees_token0),
                    "🪙 " + pool["token1_symbol"] + " fees": avoid_0_str(fees_token1),
                    "💵 Sum fees ($) ": avoid_0_str(sum_fees_usd),
                    "💰 Bribes": bribe_string,
                    "💵 Sum bribes ($) ": avoid_0_str(sum_bribes_usd),
                    "💵 Total rewards ($) ": avoid_0_str(sum_sum),
                    "🧾 Votes": avoid_0_str(pool_votes),
                    "🐠 Reward ($) for 10k votes": avoid_0_str(rewards_per_votes),
                    "✨ APR (%) for 10k votes ": avoid_0_str(apr_per_votes)
                }
            )
            start_period = start_period + 604800
            index = index + 1

        if pooldata:
            fees_df = pd.DataFrame(pooldata)
            fees_df.sort_values(by="🕰️ Epoch starting at", axis=0, ascending=False, inplace=True)
            # st.bar_chart(votes_df, x="epoch")
            st.dataframe(fees_df)

# App
st.set_page_config(
    page_title="💸 Pool voter rewards history",
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
st.title("💸 Pool voter rewards history")

# Get SOLID Price
SOLID_price = get_solid_price()
st.markdown("💵 Current SOLID price: " + '{:,}'.format(round(SOLID_price, 2)))

### Get pool data
pool_dict = get_historical_pool_data(web3=w3, contract_instance_Voter=contract_instance_Voter, config=config)
set_contracts_for_pools(pool_dict=pool_dict, web3=w3, abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"], abi_feedist=config["data"]["abi_Feedist"], abi_bribe=config["data"]["abi_Bribe"])
##get bribe and fee data
bribe_pool_data = get_historical_bribe_pool_data(web3=w3, pool_dict=pool_dict, contract_instance_Voter=contract_instance_Voter, config=config)
pool_fees = get_historical_pool_fees_data(pool_dict=pool_dict, contract_instance_Voter=contract_instance_Voter)

try:
    current_period = get_active_period(contract_instance_Voter)
    display_pool_rewards(pool=get_pool_from_dict("vAMM-SOLID/WETH", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    display_pool_rewards(pool=get_pool_from_dict("sAMM-FRAX/USDT", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    display_pool_rewards(pool=get_pool_from_dict("sAMM-FRAX/USDC", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    display_pool_rewards(pool=get_pool_from_dict("sAMM-frxETH/WETH", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    display_pool_rewards(pool=get_pool_from_dict("vAMM-FXS/frxETH", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    display_pool_rewards(pool=get_pool_from_dict("vAMM-BLUR/WETH", pool_dict), pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)

except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

if st.button('Lookup all pools'):
    try:
        for key in pool_dict:
            display_pool_rewards(pool_dict[key],  pool_fees=pool_fees, bribe_pool_data=bribe_pool_data, current_period=current_period)
    except Exception as e:
        print(e)
        st.markdown("Error Please Try Again")



# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
