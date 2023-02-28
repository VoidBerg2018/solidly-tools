from web3 import Web3
import time
import streamlit as st
from st_btn_select import st_btn_select
import yaml
import requests
from datetime import datetime
import pandas as pd
from veSolidfunctions import *
#import altair as alt
import json

def show_total_votes_now(contract_instance_Token):
    veSOLID_totalSupply = get_total_vesolid_supply(contract_instance_Token)
    current_period = get_active_period(contract_instance_Voter)
    period = current_period
    datum = datetime.utcfromtimestamp(period).strftime('%Y-%m-%d')
    total_votes = get_total_votes_for_period(period, contract_instance_Voter)
    period_data = []
    period_data.append({"": "Maximum possible", "🧾 Votes": round(veSOLID_totalSupply), "🧾 Votes (%)": 100 })
    period_data.append({"": "Submitted", "🧾 Votes": round(total_votes), "🧾 Votes (%)": round(total_votes/veSOLID_totalSupply,2)*100})
    votes_df = pd.DataFrame(period_data)
    #st.bar_chart(votes_df, x="epoch")
    st.dataframe(votes_df)

def show_total_votes_over_time():
    current_period = get_active_period(contract_instance_Voter)
    first_period = first_solidly_vote_period_start + 604800
    period = current_period

    period_data = []
    while period > first_period:
        datum = datetime.utcfromtimestamp(period).strftime('%Y-%m-%d')
        period = period - 604800    # votes were submitted in the period before
        total_votes = get_total_votes_for_period(period, contract_instance_Voter)
        period_data.append({"epoch": datum, "total votes submitted": round(total_votes)})


    votes_df = pd.DataFrame(period_data)

   # chart = (
   #     alt.Chart(votes_df).mark_bar().encode(
   #         x='epoch',
   #         y='total votes submitted'
   #     )
   # )

    #st.altair_chart(chart)
    st.bar_chart(votes_df, x="epoch")


def show_votes_per_pool_over_time(pools, pools_votes_per_period, contract_instance_Voter):
    current_period = get_active_period(contract_instance_Voter)
    period_data = get_list_of_periods(contract_instance_Voter, current_period)

    pools_votes_per_period_df = pd.DataFrame(period_data)

    for pool in pools:
        pools_votes_per_period_df[pool["symbol"]] = pools_votes_per_period[pool["symbol"]]

    st.bar_chart(pools_votes_per_period_df, x="epoch")

    #create dataframe
    #pools_votes_per_period_df = pd.DataFrame(period_data, symbol_data, vote_data)
    #pools_votes_per_period_df.melt('epoch', var_name='symbol', value_name='votes')

    #st.line_chart(pools_votes_per_period_df)

  #  chart = (
  #      alt.Chart(pools_votes_per_period_df).mark_line().encode(
   #         x='epoch'
   #     )
   # )
    #st.altair_chart(chart)





# App
st.set_page_config(
    page_title="📊 Solidly voting statistics",
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
st.title("🗳️ Total votes for next epoch")
show_total_votes_now(contract_instance_Token=contract_instance_Token)

st.title("🗳️ Total votes over time")
show_total_votes_over_time()


if st.button('Lookup pool votes'):

    # Title
    st.title("🏊 Votes per pool for next epoch")

    ### Get pool list data
    pool_list = get_all_pools(contractinstance=contract_instance_Voter, web3=w3, abi=config["data"]["abi_Token"])
    # Save pool data
    # save_pool_list_to_file(filename='pools.json', pools=pool_list)
    # Read pool data
    #pool_list = load_pool_list(filename='pools.json')

    poolsvotes = get_pools_votes_for_next_epoch(pool_list, contract_instance_Voter)
    pools_to_display = []

    poolsvotes_df = pd.DataFrame(poolsvotes)
    st.dataframe(poolsvotes_df)
    st.bar_chart(poolsvotes_df)

    st.title("🏊 Votes per pool over time")


    ###Get historical vote data
    pools_votes_per_period = get_pools_votes_per_period(pool_list, contract_instance_Voter)
    #Save data
    #save_pools_votes_per_period(filename="pools_votes_per_period.json", pools_votes_per_period=pools_votes_per_period)
    #Load data
    #pools_votes_per_period = load_pools_votes_per_period(filename="pools_votes_per_period.json")


    show_votes_per_pool_over_time(pool_list, pools_votes_per_period, contract_instance_Voter)



# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
