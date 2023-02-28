from web3 import Web3
import time
import streamlit as st
from st_btn_select import st_btn_select
import yaml
import requests
from datetime import datetime
import pandas as pd
from veSolidfunctions import *


def display_voted_pools(voted_pools, total_votes, contract_instance_Voter):
    pooldata = []
    for pool in voted_pools:

        period_total_pool_votes = round(get_pool_votes_for_period(pooladdress=pool["address"], period=pool["period"], contract_instance_Voter=contract_instance_Voter))

        pooldata.append(
        {
            "🏊 Pool": pool["name"],
            "🧾 Votes": round(pool["votecount"]),
            "🧾 Votes (%)": round(pool["votecount"]/total_votes,2)*100,
            "🧾 Votes (% of pool)": round(pool["votecount"]/period_total_pool_votes,2)*100
            }
        )


    if pooldata:
            pool_df = pd.DataFrame(pooldata)
            pool_df.sort_values(by="🧾 Votes (%)", axis=0, ascending= False, inplace=True)

            # creating a single-element container
            placeholder = st.empty()

            # Empty Placeholder Filled
            with placeholder.container():
                st.dataframe(pool_df)

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
    w3 = Web3(Web3.HTTPProvider(config["data"]["provider_url"]))
    contract_instance_veNFT = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_veNFT"]), abi=config["data"]["abi_veNFT"])
    contract_instance_Token = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_Token"]), abi=config["data"]["abi_Token"])
    contract_instance_Voter = w3.eth.contract(address=Web3.toChecksumAddress(config["data"]["contract_address_Voter"]), abi=config["data"]["abi_Voter"])

except Exception as e:
    print(e)
    st.markdown("Error Please Try Again")

############################

# Title
st.title("🔍 veSOLID Checker")

# Select Button
selection = st_btn_select(("veSOLID NFT ID", "Wallet address"))

# Get SOLID Price
SOLID_price = get_solid_price()

# Get ETH Price
ETH_price = get_eth_price()

# Get total veSOLID supply
veSOLID_totalSupply = get_total_vesolid_supply(contract_instance_Token)

# Write basic info
st.write("🏛️ Total veSOLID supply: " + '{:,}'.format(round(veSOLID_totalSupply)))
st.markdown("💵 Current SOLID price: " + '{:,}'.format(round(SOLID_price, 2)))
# st.markdown("💵 Current ETH price: " + '{:,}'.format(round(ETH_price, 2)))

# Token ID Search
if selection == "veSOLID NFT ID":
    try:
        tokenid = st.number_input("veSOLID NFT ID:", min_value=1, format="%d")

        # get NFT data
        NFT_data = read_nft_data(tokenid, contract_instance_veNFT)
        # get votes addresses
        vote_addresses = get_nft_votes(nftid=tokenid, contract_instance=contract_instance_Voter)
        # get pool data
        voted_pools = get_pools_for_vote_addresses(nftid=tokenid, vote_addresses=vote_addresses, web3=w3,contract_instance_voter=contract_instance_Voter, abi=config["data"]["abi_Pool"])

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
                st.markdown("🗄️ Attached: " + ["Yes" if NFT_data["attached"] == True else "No"][0])
                st.markdown("✔️ Voted: " + ["Yes" if NFT_data["voted"] == True else "No"][0])

                display_voted_pools(voted_pools, NFT_data["balance"], contract_instance_Voter=contract_instance_Voter)

        if st.button('Lookup historical votes'):
            current_period = get_active_period(contract_instance_Voter)
            first_period = 1672531200
            period = current_period

            while period > first_period:
            # for each period

                st.caption("Votes for epoch "+datetime.utcfromtimestamp(period).strftime('%Y-%m-%d'))
                period = period - 604800
                period_voted_pools = get_pools_voted_at_period(nftid=tokenid, period=period, web3=w3, contractinstance=contract_instance_Voter, abi=config["data"]["abi_Pool"])
                period_total_votes = get_nft_votes_at_period(nftid=tokenid, period=period, contractinstance=contract_instance_Voter)
                display_voted_pools(period_voted_pools, period_total_votes, contract_instance_Voter=contract_instance_Voter)

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
            tokenids = get_nfts_forwallet(wallet_address, contract_instance_veNFT)

            # veSOLID DF
            tokendata = []
            votedata = []
            for tokenid in tokenids:

                #read NFT data
                NFT_data = read_nft_data(tokenid, contract_instance_veNFT)
                # get votes addresses
                vote_addresses = get_nft_votes(nftid=tokenid, contract_instance=contract_instance_Voter)
                # get pool data
                voted_pools = get_pools_for_vote_addresses(nftid=tokenid, vote_addresses=vote_addresses, web3=w3,
                                                           contract_instance_voter=contract_instance_Voter,
                                                           abi=config["data"]["abi_Pool"])

                if NFT_data["voted"]:
                    display_VoteNote = True

                if NFT_data["attached"]:
                    display_AttachedNote = True

                tokendata.append(
                    {
                        "🔢 NFT ID": tokenid,
                        "🔒 Locked SOLID": round(NFT_data["locked"]),
                        "🧾 veSOLID Balance": round(NFT_data["balance"]),
                        "💰 Estimated USD Value": round(SOLID_price * NFT_data["locked"]),
                        "📈 Estimated ETH Value": round((SOLID_price * NFT_data["locked"]) / ETH_price, 3),
                        "⏲️ Lock End Date": NFT_data["lockend"],
                        "🗳️ Vote Share %": round(NFT_data["balance"] / veSOLID_totalSupply * 100,4),
                        "🗄️ Attached": ["Yes" if NFT_data["attached"] == True else "No"][0],
                        "✔️ Voted": ["Yes" if NFT_data["voted"] == True else "No"][0]
                    }
                )

                if NFT_data["voted"]:
                    pooldata = []
                    for pool in voted_pools:
                        period_total_pool_votes = round(get_pool_votes_for_period(pooladdress=pool["address"], period=pool["period"],contract_instance_Voter=contract_instance_Voter))

                        pooldata.append(
                            {
                                "🏊 Pool": pool["name"],
                                "🧾 Votes": round(pool["votecount"]),
                                "🧾 Votes (%)": round(pool["votecount"] / NFT_data["balance"], 2) * 100,
                                "🧾 Votes (% of pool)": round(pool["votecount"] / period_total_pool_votes, 2) * 100
                            }
                        )

                    votedata.append(
                        {"id":tokenid,"pooldata":pooldata}
                    )

            if tokendata:
                veSOLID_df = pd.DataFrame(tokendata)
                veSOLID_df.sort_values(by="🔢 NFT ID", axis=0, inplace=True)

                # creating a single-element container
                placeholder = st.empty()

                # Empty Placeholder Filled
                with placeholder.container():
                    if wallet_address:
                        st.dataframe(veSOLID_df)

                if votedata:
                    for votenft in votedata:
                        st.caption("✔️ Voted for next epoch NFT ID: " + str(votenft["id"]))
                        pool_df = pd.DataFrame(votenft["pooldata"])
                        pool_df.sort_values(by="🧾 Votes (%)", axis=0, ascending=False, inplace=True)

                        # creating a single-element container
                        placeholder = st.empty()

                        # Empty Placeholder Filled
                        with placeholder.container():
                            st.dataframe(pool_df)


                if st.button('Lookup historical votes'):
                    current_period = get_active_period(contract_instance_Voter)
                    first_period = 1672531200
                    period = current_period

                    while period > first_period:
                        # for each period

                        st.caption("Votes for epoch " + datetime.utcfromtimestamp(period).strftime('%Y-%m-%d'))
                        period = period - 604800
                        for tokenid in tokenids:

                            period_voted_pools = get_pools_voted_at_period(nftid=tokenid, period=period, web3=w3,
                                                                          contractinstance=contract_instance_Voter,
                                                                          abi=config["data"]["abi_Pool"])
                            period_total_votes = get_nft_votes_at_period(nftid=tokenid, period=period,
                                                                         contractinstance=contract_instance_Voter)


                            if (period_voted_pools):
                                st.caption("NFT ID: " + str(tokenid))
                                display_voted_pools(period_voted_pools, period_total_votes, contract_instance_Voter=contract_instance_Voter)

            else:
                st.markdown(":red[No veSOLID NFTs found]")

        except Exception as e:
            print(e)
            st.markdown("Error Please Try Again")




        # get pools voted for period - periodPoolVote (index until return nix)
            #get vote for pool at period - periodVotes


# Note
note = """NFA, DYOR -- This web app is in beta, I am not responsible for any information on this page. USD Values are just an estimate of prices pulled from Firebird API.   \n"""

if display_VoteNote:
    note += """:red[If Voted is Yes you cannot sell/move your veSOLID NFT this epoch unless you reset your vote.]   \n"""
if display_AttachedNote:
    note += """:red[If Attached is Yes you cannot sell/move your veSOLID NFT unless you detach it.]   \n"""

note += """Thanks to ALMIGHTYABE for creating the original veTHE-Checker!"""
st.caption(note)
