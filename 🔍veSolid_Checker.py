from web3 import Web3
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta, TH
import time
import streamlit as st
from st_btn_select import st_btn_select
import yaml
import requests
import pandas as pd

# App
st.set_page_config(
    page_title="🔍 veSOLID Checker",
    page_icon="icons/solid.png",
    layout="wide",
)

# Params
params_path = "params.yaml"


def read_params(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config


config = read_params(params_path)

# Title
st.title("🔍 veSOLID Checker")

# Select Button
selection = st_btn_select(("Token ID", "Address"))
#DEus dao 0x83b285e802d76055169b1c5e3bf21702b85b89cb

# Get SOLID Price
params = {
    "from": "0x777172D858dC1599914a1C4c6c9fC48c99a60990",
    "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "amount": "1000000000000000000",
}

try:
    response = requests.get("https://router.firebird.finance/ethereum/route", params=params)
   # st.write(response.json())
    SOLID_price = response.json()["maxReturn"]["tokens"]["0x777172d858dc1599914a1c4c6c9fc48c99a60990"]["price"]
except Exception as e:
    print(e)

# Get total veSOLID supply
try:
    provider_url = config["data"]["provider_url"]
    w3 = Web3(Web3.HTTPProvider(provider_url))

    abi_veNFT = config["data"]["abi_veNFT"]
    contract_address_veNFT = config["data"]["contract_veNFT_address"]
    contract_instance_veNFT = w3.eth.contract(address=contract_address_veNFT, abi=abi_veNFT)

    abi_Token = config["data"]["abi_Token"]
    contract_address_Token = config["data"]["contract_Token_address"]
    contract_instance_Token = w3.eth.contract(address=Web3.toChecksumAddress(contract_address_Token), abi=abi_Token)

    # Total veSOLID Supply
    totalSupply = contract_instance_Token.functions.balanceOf(
        "0x77730ed992D286c53F3A0838232c3957dAeaaF73").call() / 1000000000000000000

    st.write("Total veSOLID supply: " + '{:,}'.format(round(totalSupply)))
    st.markdown("💵 Current SOLID price: " + '{:,}'.format(round(SOLID_price, 2)))

    if totalSupply < 1.0:
        totalSupply = 1


except Exception as e:
    print(e)

# Token ID Search
if selection == "Token ID":
    tokenid = st.number_input("veSOLID Token ID:", min_value=1, format="%d")

    # Read Data
    try:
        # Balance veSOLID
        bal = round(
            contract_instance_veNFT.functions.balanceOfNFT(tokenid).call() / 1000000000000000000,
            4,
        )

        # Locked veSOLID
        locked = round(
            contract_instance_veNFT.functions.locked(tokenid).call()[0] / 1000000000000000000,
            4,
        )

        # Lock End Date
        lockend = time.strftime(
            "%Y-%m-%d",
            time.gmtime(int(contract_instance_veNFT.functions.locked(tokenid).call()[1])),
        )

        # Voted Last Epoch
        voted = contract_instance_veNFT.functions.voted(tokenid).call()

        # creating a single-element container
        placeholder = st.empty()

        # Empty Placeholder Filled
        with placeholder.container():
            if tokenid:
                st.markdown("🔒 Locked SOLID: " + '{:,}'.format(round(locked)))
                st.markdown("🧾 veSOLID Balance: " + '{:,}'.format(round(bal)))
                st.markdown("🤑 Estimated USD Value: $" + '{:,}'.format(round(SOLID_price * locked)))
                st.markdown("⏲️ Lock End Date: " + str(lockend))
                st.markdown("🗳️ Vote Share: " + str(round(bal / totalSupply * 100, 4)) + "%")
                st.markdown("✔️ Voted: " + ["Yes" if voted == True else "No"][0])
                # st.markdown(
                #     "⚡ Voted Current Epoch: "
                #     + ["No" if votedcurrentepoch == False else "Yes"][0]
                # )

    except Exception as e:
        print(e)
        st.markdown("Error Please Try Again")

# Address Search
if selection == "Address":
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
            tokenids = []
            for index in range(100):
                veSOLID = contract_instance_veNFT.functions.tokenOfOwnerByIndex(wallet_address, index).call()
                if veSOLID > 0:
                    tokenids.append(veSOLID)
                else:
                    break

            # veSOLID DF
            tokendata = []
            for tokenid in tokenids:
                # Balance veSOLID
                bal = round(
                    contract_instance_veNFT.functions.balanceOfNFT(tokenid).call() / 1000000000000000000,
                    4,
                )

                # Locked veSOLID
                locked = round(
                    contract_instance_veNFT.functions.locked(tokenid).call()[0] / 1000000000000000000,
                    4,
                )

                # Lock End Date
                lockend = time.strftime(
                    "%Y-%m-%d",
                    time.gmtime(int(contract_instance_veNFT.functions.locked(tokenid).call()[1])),
                )

                # Voted Last Epoch
                voted = contract_instance_veNFT.functions.voted(tokenid).call()

                # # Voted Current Epoch
                # votedcurrentepoch = (
                #     contract_instance2.functions.lastVoted(tokenid).call()
                #     > currentepoch
                # )

                tokendata.append(
                    {
                        "🔢 Token ID": tokenid,
                        "🔒 Locked SOLID": round(locked),
                        "🧾 veSOLID Balance": round(bal),
                        "🤑 Estimated USD Value": round(SOLID_price * locked),
                        "⏲️ Lock End Date": lockend,
                        "🗳️ Vote Share %": round(bal / totalSupply * 100,4),
                        "✔️ Voted": ["Yes" if voted == True else "No"][0],
                        # "⚡ Voted Current Epoch": [
                        #     "No" if votedcurrentepoch == False else "Yes"
                        # ][0],
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
st.markdown("#")
st.markdown("#")
st.caption(
 """
NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page.

USD Value is just an estimate of SOLID Price pulled from Firebird API.

:red[If "Voted" is Yes you cannot sell your veSOLID this epoch unless you reset your vote.]

Thanks to ALMIGHTYABE for creating the original veTHE-Checker!
"""
 )