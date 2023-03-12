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
pool_dict = get_historical_pool_data(web3=w3, contract_instance_Voter=contract_instance_Voter, config=config)
set_contracts_for_pools(pool_dict=pool_dict, web3=w3, abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"], abi_feedist=config["data"]["abi_Feedist"], abi_bribe=config["data"]["abi_Bribe"])

##get bribe data
bribe_pool_data = get_historical_bribe_pool_data(web3=w3, pool_dict=pool_dict, contract_instance_Voter=contract_instance_Voter, config=config)

bribe_pool_data = dict(reversed(sorted(bribe_pool_data.items())))
for key in bribe_pool_data:
    epoch = round(((int(key)+604800 - 1672272000)/604800))
    st.caption("Vote bribes for epoch "+str(epoch)+" starting at " + datetime.utcfromtimestamp(int(key)+604800).strftime('%Y-%m-%d'))
    if bribe_pool_data[key]:
        bribes_df = pd.DataFrame(bribe_pool_data[key])
        # st.bar_chart(votes_df, x="epoch")
        st.dataframe(bribes_df)


# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

st.caption(note)
