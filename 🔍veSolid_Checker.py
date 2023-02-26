from web3 import Web3
import time
import streamlit as st
from st_btn_select import st_btn_select
import yaml
import requests
import pandas as pd
from veSolidfunctions import *

# App
st.set_page_config(
    page_title="🔍 veSOLID Checker",
    page_icon="icons/solid.png",
    layout="wide",
)

# Params
params_path = "params.yaml"
display_VoteNote = False
display_AttachedNote = False

config = read_params(params_path)

try:
    provider_url = config["data"]["provider_url"]
    w3 = Web3(Web3.HTTPProvider(provider_url))

    abi_veNFT = config["data"]["abi_veNFT"]
    contract_address_veNFT = config["data"]["contract_veNFT_address"]
    contract_instance_veNFT = w3.eth.contract(address=contract_address_veNFT, abi=abi_veNFT)

    abi_Token = config["data"]["abi_Token"]
    contract_address_Token = config["data"]["contract_Token_address"]
    contract_instance_Token = w3.eth.contract(address=Web3.toChecksumAddress(contract_address_Token), abi=abi_Token)

except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

############################

# Title
st.title("🔍 veSOLID Checker")

# Select Button
selection = st_btn_select(("veSOLID NFT ID", "Wallet address"))

# Get SOLID Price
SOLID_price = Get_Solid_Price()

# Get ETH Price
ETH_price = Get_ETH_Price()

# Get total veSOLID supply
veSOLID_totalSupply = Get_Total_veSOLID_Supply(contract_instance_Token)


st.write("🏛️ Total veSOLID supply: " + '{:,}'.format(round(veSOLID_totalSupply)))
st.markdown("💵 Current SOLID price: " + '{:,}'.format(round(SOLID_price, 2)))
# st.markdown("💵 Current ETH price: " + '{:,}'.format(round(ETH_price, 2)))


# Token ID Search
if selection == "veSOLID NFT ID":
    try:
        tokenid = st.number_input("veSOLID NFT ID:", min_value=1, format="%d")

        NFT_data = read_NFT_data(tokenid, contract_instance_veNFT)

        # creating a single-element container
        placeholder = st.empty()

        # Empty Placeholder Filled
        with placeholder.container():
            if tokenid:
                st.markdown("🔒 Locked SOLID: " + '{:,}'.format(round(NFT_data["locked"])))
                st.markdown("🧾 veSOLID Balance: " + '{:,}'.format(round(NFT_data["balance"])))
                st.markdown("💰 Estimated USD Value: $" + '{:,}'.format(round(SOLID_price * NFT_data["locked"])))
                st.markdown("📈 Estimated ETH Value: " + '{:,}'.format(round((SOLID_price * NFT_data["locked"])/ETH_price, 3)))
                st.markdown("⏲️ Lock End Date: " + str(NFT_data["lockend"]))
                st.markdown("🗳️ Vote Share: " + str(round(NFT_data["balance"] / veSOLID_totalSupply * 100, 4)) + "%")
                st.markdown("✔️ Voted: " + ["Yes" if NFT_data["voted"] == True else "No"][0])
                st.markdown("🗄️ Attached: " + ["Yes" if NFT_data["attached"] == True else "No"][0])

    except Exception as e:
        print(e)
        st.markdown("Error Please Try Again")


# Address Search
if selection == "Wallet address":
    wallet_address = st.text_input(
        label="Wallet address:",
        placeholder="Enter your wallet address",
        max_chars=42,
    )

    if wallet_address:
        # Read Data
        try:
            # Checksum Address
            wallet_address = Web3.toChecksumAddress(wallet_address)

            # veSOLID Owner
            tokenids = Get_NFTs_forWallet_Price(wallet_address, contract_instance_veNFT)

            # veSOLID DF
            tokendata = []
            for tokenid in tokenids:

                NFT_data = read_NFT_data(tokenid, contract_instance_veNFT)

                if NFT_data["voted"]:
                    display_VoteNote = True

                if NFT_data["attached"]:
                    display_AttachedNote = True

                tokendata.append(
                    {
                        "🔢 Token ID": tokenid,
                        "🔒 Locked SOLID": round(NFT_data["locked"]),
                        "🧾 veSOLID Balance": round(NFT_data["balance"]),
                        "💰 Estimated USD Value": round(SOLID_price * NFT_data["locked"]),
                        "📈 Estimated ETH Value": round((SOLID_price * NFT_data["locked"]) / ETH_price, 3),
                        "⏲️ Lock End Date": NFT_data["lockend"],
                        "🗳️ Vote Share %": round(NFT_data["balance"] / veSOLID_totalSupply * 100,4),
                        "✔️ Voted": ["Yes" if NFT_data["voted"] == True else "No"][0],
                        "🗄️ Attached": ["Yes" if NFT_data["attached"] == True else "No"][0]

                    }
                )

            if tokendata:
                veSOLID_df = pd.DataFrame(tokendata)
                veSOLID_df.sort_values(by="🔢 Token ID", axis=0, inplace=True)

                # creating a single-element container
                placeholder = st.empty()

                # Empty Placeholder Filled
                with placeholder.container():
                    if wallet_address:
                        st.dataframe(veSOLID_df)
            else:
                st.markdown(":red[No veSOLID NFTs found]")

        except Exception as e:
            print(e)
            st.markdown("Error Please Try Again")


# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

if display_VoteNote:
    note += """:red[If Voted is Yes you cannot sell/move your veSOLID NFT this epoch unless you reset your vote.]   \n"""
if display_AttachedNote:
     note += """:red[If Attached is Yes you cannot sell/move your veSOLID NFT unless you detach it.]   \n"""

note += """Thanks to ALMIGHTYABE for creating the original veTHE-Checker!"""
st.caption(note)
