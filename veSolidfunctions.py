from web3 import Web3
import time
import yaml
import requests
import json
from datetime import datetime

first_solidly_vote_period_start = 1671926400

####################
def read_params(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

####################
def read_nft_data(ntf_id, contract_instance):
    # Read Data
    NFT_data = {
        "balance": 0,
        "locked": 0,
        "lockend": 0,
        "voted" : False,
        "attached" : False,
    }

    try:
        # Balance veSOLID
        NFT_data["balance"] = round(
            contract_instance.functions.balanceOfNFT(ntf_id).call() / 1000000000000000000,
            4,
        )

        # Locked veSOLID
        NFT_data["locked"] = round(
            contract_instance.functions.locked(ntf_id).call()[0] / 1000000000000000000,
            4,
        )

        # Lock End Date
        NFT_data["lockend"] = time.strftime(
            "%Y-%m-%d",
            time.gmtime(int(contract_instance.functions.locked(ntf_id).call()[1])),
        )

        # Voted Last Epoch
        NFT_data["voted"] = contract_instance.functions.voted(ntf_id).call()

        # attached
        attachments = contract_instance.functions.attachments(ntf_id).call()
        if attachments == 0:
            NFT_data["attached"] = False
        else:
            NFT_data["attached"] = True

    except Exception as e:
        print(e)

    return NFT_data

#########################
def get_nft_votes(nftid, contract_instance):
    votes = []

    try:
        votes = contract_instance.functions.poolVote(nftid).call()
    except Exception as e:
        print(e)

    return votes


############################
# Get SOLID Price
def get_solid_price():
    SOLID_price = 0

    paramsSOLID = {
        "from": "0x777172D858dC1599914a1C4c6c9fC48c99a60990",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "amount": "1000000000000000000",
    }

    try:
        response = requests.get("https://router.firebird.finance/ethereum/route", params=paramsSOLID)
        SOLID_price = response.json()["maxReturn"]["tokens"]["0x777172d858dc1599914a1c4c6c9fc48c99a60990"]["price"]
    except Exception as e:
        print(e)

    return SOLID_price

####################
# Get ETH Price
def get_eth_price():
    ETH_price = 0

    paramsETH = {
        "from": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "amount": "1000000000000000000",
    }

    try:
       response = requests.get("https://router.firebird.finance/ethereum/route", params=paramsETH)
       ETH_price = response.json()["maxReturn"]["tokens"]["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"]["price"]
    except Exception as e:
        print(e)

    return ETH_price

##########################
# Get total veSOLID supply
def get_total_vesolid_supply(contract_instance):
    totalSupply = 0

    try:
        # Total veSOLID Supply
        totalSupply = contract_instance.functions.balanceOf(
            "0x77730ed992D286c53F3A0838232c3957dAeaaF73").call() / 1000000000000000000

        if totalSupply < 1.0:
            totalSupply = 1

    except Exception as e:
        print(e)

    return totalSupply


###################
def get_nfts_forwallet(wallet_address, contract_instance):
    tokenids = []

    try:
        # Checksum Address
        wallet_address = Web3.toChecksumAddress(wallet_address)

        # veSOLID Owner
        tokenids = []
        for index in range(100):
            veSOLID = contract_instance.functions.tokenOfOwnerByIndex(wallet_address, index).call()
            if veSOLID > 0:
                tokenids.append(veSOLID)
            else:
                break
    except Exception as e:
        print(e)

    return tokenids

######################
def get_pools_for_vote_addresses(nftid, vote_addresses, web3, contract_instance_voter, abi):
    pools = []
    current_period = get_active_period(contract_instance_voter)

    for vote_address in vote_addresses:
        # get instance
        contract_instance_proxy_pool = web3.eth.contract(address=Web3.toChecksumAddress(vote_address), abi=abi)

        symbol = get_pool_symbol(contract_instance_proxy_pool)

        name = get_pool_name(contract_instance_proxy_pool)

        # get vote count
        vote_count = contract_instance_voter.functions.votes(nftid, vote_address).call() / 1000000000000000000

        # add
        pools.append({"symbol":symbol, "name":name, "address":vote_address, "votecount":vote_count, "period":current_period, "poolcontract":contract_instance_proxy_pool })

    return pools



def get_pool_symbol(contractinstance):
    return contractinstance.functions.symbol().call()

def get_pool_name(contractinstance):
    return contractinstance.functions.name().call()

def get_nft_votes_for_pool(nftid, pooladdress, contractinstance):
    return contractinstance.functions.votes(nftid, pooladdress).call()


def get_pools_voted_at_period(nftid , period, web3, contractinstance, abi):
    go = True
    pools = []
    index = 0
    while go == True:
        try:
            # get instance
            pooladdress = contractinstance.functions.periodPoolVote(nftid, period, index).call()
            contract_instance_proxy_pool = web3.eth.contract(address=Web3.toChecksumAddress(pooladdress), abi=abi)

            symbol = get_pool_symbol(contract_instance_proxy_pool)

            name = get_pool_name(contract_instance_proxy_pool)

            # get vote count
            vote_count = contractinstance.functions.periodVotes(nftid, period, pooladdress).call() / 1000000000000000000

        except:
            go = False

        if go:
            pools.append({"symbol":symbol, "name":name, "address":pooladdress, "votecount":vote_count,  "period":period, "poolcontract":contract_instance_proxy_pool })
            index = index + 1
            if index == 100:
                go = False

    return pools

def get_nft_votes_at_period(nftid, period, contractinstance):
    return contractinstance.functions.periodUsedWeights(nftid, period).call() / 1000000000000000000

def get_active_period(contractinstance):
    return contractinstance.functions.activePeriod().call()

def get_all_pools(contractinstance, web3, abi):
    pools = []
    go = True
    index = 0
    while go == True:
        try:
            # get instance
            pooladdress = contractinstance.functions.pools(index).call()
            contract_instance_proxy_pool = web3.eth.contract(address=Web3.toChecksumAddress(pooladdress), abi=abi)

            symbol = get_pool_symbol(contract_instance_proxy_pool)

            name = get_pool_name(contract_instance_proxy_pool)

        except:
            go = False

        if go:
            #pools.append({"symbol": symbol, "name": name, "address":pooladdress, "poolcontract": contract_instance_proxy_pool})
            pools.append({"symbol": symbol, "name": name, "address": pooladdress})
            index = index + 1
            if index == 200:
                go = False

    return pools

def get_pool_votes_for_period(pooladdress, period, contract_instance_Voter):
    return contract_instance_Voter.functions.periodWeights(pooladdress, period ).call() / 1000000000000000000

def get_total_votes_for_period(period, contractinstance):
    answer = contractinstance.functions.periodTotalWeight(period).call() / 1000000000000000000
    return answer

def save_pool_list_to_file(filename, pools):
    with open(filename, 'w') as f:
        json.dump(pools, f, sort_keys=True, indent=4, ensure_ascii=False)
        print(filename +" saved!")

def load_pool_list(filename):
    with open(filename) as data_file:
        pools = json.load(data_file)
    return pools

def load_pools_votes_per_period(filename):
    with open(filename) as data_file:
        pools_votes_per_period = json.load(data_file)
    return pools_votes_per_period

def get_pools_votes_per_period(pools, contract_instance_Voter):
    pools_votes_per_period = {}
    current_period = get_active_period(contract_instance_Voter) - 604800
    period = current_period
    first_period = first_solidly_vote_period_start
    while period > first_period:
        try:
            # for each period
            total_votes = get_total_votes_for_period(period, contract_instance_Voter)

            for pool in pools:
                if period == current_period:
                    pools_votes_per_period[pool["symbol"]] = []

                pool_votes = round(get_pool_votes_for_period(pool["address"], period, contract_instance_Voter))
                perc_votes = round(pool_votes * 100 / total_votes, 2)
                pools_votes_per_period[pool["symbol"]].append(perc_votes)
                # st.caption( pool["symbol"]+ "   "  + datum + "      " + str(pool_votes) + "      " + str(perc_votes))

            period = period - 604800

        except Exception as e:
            print(e)

    return pools_votes_per_period

def get_pools_votes_for_next_epoch(pools, contract_instance_Voter):
    current_period = get_active_period(contract_instance_Voter)
    total_votes = get_total_votes_for_period(current_period, contract_instance_Voter)
    pools_votes_per_period = {}
    try:
        for pool in pools:
            pool_votes = round(get_pool_votes_for_period(pool["address"], current_period, contract_instance_Voter))
            perc_votes = round(pool_votes * 100 / total_votes, 2)
            pools_votes_per_period[pool["symbol"]] = []
            pools_votes_per_period[pool["symbol"]].append(perc_votes)

    except Exception as e:
        print(e)

    return pools_votes_per_period

def save_pools_votes_per_period(filename, pools_votes_per_period):
    # save data
    with open(filename, 'w') as f:
         json.dump(pools_votes_per_period, f, sort_keys=True, indent=4, ensure_ascii=False)
         print(filename +" saved!")


def get_list_of_periods(contract_instance_Voter, period_end):

    first_period = first_solidly_vote_period_start + 604800
    period = period_end

    period_data = []
    while period > first_period:
        datum = datetime.utcfromtimestamp(period).strftime('%Y-%m-%d')
        period = period - 604800 # votes were submitted in the period before
        total_votes = get_total_votes_for_period(period, contract_instance_Voter)
        period_data.append({"epoch": datum})


    return period_data