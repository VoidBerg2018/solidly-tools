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


def display_pool_rewards(pool):
    if pool:
        st.caption("Voter rewards for " + pool["name"])
        first_period = first_solidly_vote_period_start
        period = get_active_period(contract_instance_Voter)
        pooldata = []
        index = 0
        while period > first_period:
            fees_token0 = pool["contract_feedist"].functions.periodRewardAmount(period, pool["token0_address"]).call()
            fees_token1 = pool["contract_feedist"].functions.periodRewardAmount(period, pool["token1_address"]).call()

            fees_token0 = round(fees_token0 / pow(10, pool["token0_decimals"]), 2)
            fees_token1 = round(fees_token1 / pow(10, pool["token1_decimals"]), 2)
            fees_token0_usd = fees_token0 * get_token_price(pool["token0_address"])
            fees_token1_usd = fees_token1 * get_token_price(pool["token1_address"])

            sum_fees_usd = round(fees_token0_usd + fees_token1_usd)

            sum_bribes_usd = 0
            bribe_string = ""
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

                bribe_string = bribe_string + str(bribe_amount) + " " + bribe_token_data["symbol"] + " "
                sum_bribes_usd = sum_bribes_usd + bribe_usd

            pool_votes = round(get_pool_votes_for_period(pool["address"], period, contract_instance_Voter))
            sum_sum = round(sum_fees_usd + sum_bribes_usd)
            rewards_per_votes = 0
            if (pool_votes > 0):
                rewards_per_votes = round((sum_sum / pool_votes) * 10000)

            if (rewards_per_votes > sum_sum):
                rewards_per_votes = sum_sum

            apr_per_votes = round(((rewards_per_votes * 52) / (get_solid_price() * 10000)) * 100, 2)

            epochstart = datetime.utcfromtimestamp(period + 604800).strftime('%Y-%m-%d')
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
            period = period - 604800
            index = index + 1

        if pooldata:
            fees_df = pd.DataFrame(pooldata)
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

    display_pool_rewards(get_pool_from_dict("vAMM-SOLID/WETH", pool_dict))
    display_pool_rewards(get_pool_from_dict("sAMM-FRAX/USDT", pool_dict))
    display_pool_rewards(get_pool_from_dict("sAMM-FRAX/USDC", pool_dict))
    display_pool_rewards(get_pool_from_dict("sAMM-frxETH/WETH", pool_dict))
    display_pool_rewards(get_pool_from_dict("vAMM-FXS/frxETH", pool_dict))
    display_pool_rewards(get_pool_from_dict("vAMM-BLUR/WETH", pool_dict))

except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

if st.button('Lookup all pools'):
    try:
        for key in pool_dict:
            display_pool_rewards(pool_dict[key])
    except Exception as e:
        print(e)
        st.markdown("Error Please Try Again")



# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
