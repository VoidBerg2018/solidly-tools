from web3 import Web3
import time
import yaml
import requests
import json
from datetime import datetime

first_solidly_vote_period_start = 1672272000

token_prices = {
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48":1,  #USDC
        "0xde1e704dae0b4051e80dabb26ab6ad6c12262da0":1, #DEI ;)
        "0xdac17f958d2ee523a2206206994597c13d831ec7":1, #USDT
        "0x5f98805a4e8be255a32880fdec7f6728c6568ba0":1, #LUSD
        "0x853d955acef822db058eb8505911ed77f175b99e":1, #FRAX
        "0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3":1, #MIM
        "0x8d6cebd76f18e1558d4db88138e2defb3909fad6":1, #MAI
                }

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
    SOLID_price = get_token_price("0x777172d858dc1599914a1c4c6c9fc48c99a60990")

    return SOLID_price

# Get ETH Price
def get_eth_price():
    ETH_price = get_token_price("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")

    return ETH_price

def get_token_price_firebird(token_address):
    price = 0
    token_address = str(token_address).lower()
    params = {
        "from": token_address,
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "amount": "1000000000000000000",
    }

    try:
        response = requests.get("https://router.firebird.finance/ethereum/route", params=params)
        price = response.json()["maxReturn"]["tokens"][token_address]["price"]
    except Exception as e:
        print(e)

    return price

def get_token_price(token_address):
    price = 0
    if str(token_address) in token_prices:
        price = token_prices[str(token_address)]
    else:
        price = get_token_price_firebird(token_address)
        token_prices[str(token_address)] = price
    return price


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


        except Exception as e:

            print(e)
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


def pools_add_missing(pools_dict, contractinstance, web3, abi_pool, abi_gauge, abi_token):
    go = True
    index = len(pools_dict)
    while go == True:
        try:
            # get instance
            pooladdress = contractinstance.functions.pools(index).call()
            if not (pooladdress in pools_dict):
                contract_instance_proxy_pool = web3.eth.contract(address=Web3.toChecksumAddress(pooladdress), abi=abi_pool)

                symbol = get_pool_symbol(contract_instance_proxy_pool)
                name = get_pool_name(contract_instance_proxy_pool)
                token0_address = contract_instance_proxy_pool.functions.token0().call()
                token1_address = contract_instance_proxy_pool.functions.token1().call()

                token0_symbol = get_token_symbol(address=token0_address, web3=web3, abi=abi_token)
                token1_symbol = get_token_symbol(address=token1_address, web3=web3, abi=abi_token)

                token0_decimals = get_token_decimals(address=token0_address, web3=web3, abi=abi_token)
                token1_decimals = get_token_decimals(address=token1_address, web3=web3, abi=abi_token)

                gauge_address = contractinstance.functions.gauges(pooladdress).call()
                feedist_address = contractinstance.functions.feeDists(pooladdress).call()

                contract_instance_proxy_gauge = web3.eth.contract(address=Web3.toChecksumAddress(gauge_address), abi=abi_gauge)
                bribe_address = contract_instance_proxy_gauge.functions.bribe().call()

                pools_dict[pooladdress] = {"symbol": symbol, "name": name,
                          "address": pooladdress, "gauge_address":gauge_address,"feedist_address":feedist_address,"bribe_address":bribe_address,
                          "token0_address": token0_address,"token1_address": token1_address,"token0_symbol":token0_symbol,"token1_symbol":token1_symbol,
                          "token0_decimals":token0_decimals,"token1_decimals":token1_decimals
                          }

        except Exception as e:

            print(e)
            go = False

        if go:

            index = index + 1
            if index == 2000:
                go = False

    return pools_dict


def get_pool_votes_for_period(pooladdress, period, contract_instance_Voter):
    return contract_instance_Voter.functions.periodWeights(pooladdress, period ).call() / 1000000000000000000

def get_total_votes_for_period(period, contractinstance):
    answer = contractinstance.functions.periodTotalWeight(period).call() / 1000000000000000000
    return answer

def save_pool_dict_to_file(filename, pools):
    with open(filename, 'w') as f:
        json.dump(pools, f, sort_keys=True, indent=4, ensure_ascii=False)
        print(filename +" saved!")

def load_pool_dict(filename):
    with open(filename) as data_file:
        pools = json.load(data_file)
    return pools

def load_pool_fees(filename):
    with open(filename) as data_file:
        pools = json.load(data_file)
    return pools



def save_bribe_pool_dict_to_file(filename, pools):
    with open(filename, 'w',encoding="utf-8") as f:
        json.dump(pools, f, sort_keys=True, indent=4, ensure_ascii=False)
        print(filename +" saved!")

def save_pool_fees_to_file(filename, pools):
    with open(filename, 'w') as f:
        json.dump(pools, f, sort_keys=True, indent=4, ensure_ascii=False)
        print(filename +" saved!")

def load_bribe_pool_dict(filename):
    with open(filename,encoding="utf-8") as data_file:
        pools = json.load(data_file)
    return pools



def get_pool_from_dict(symbol, pool_dict):
    for key in pool_dict:
        if pool_dict[key]["symbol"] == symbol:
            return pool_dict[key]

def load_pools_votes_per_period(filename):
    with open(filename) as data_file:
        pools_votes_per_period = json.load(data_file)
    return pools_votes_per_period

def pools_votes_per_period_add_missing(pool_dict, pools_votes_per_period, contract_instance_Voter):
    current_period = get_active_period(contract_instance_Voter) - 604800
    period = current_period
    first_period = first_solidly_vote_period_start
    while period > first_period:
        try:
            # for each period
            if not (str(period) in pools_votes_per_period):
                total_votes = get_total_votes_for_period(period, contract_instance_Voter)
                pools_votes_per_period[str(period)] = {}
                for key in pool_dict:

                    pool_votes = round(get_pool_votes_for_period(pool_dict[key]["address"], period, contract_instance_Voter))
                    perc_votes = round(pool_votes * 100 / total_votes, 2)
                    pools_votes_per_period[str(period)][pool_dict[key]["symbol"]] = perc_votes
                    # st.caption( pool["symbol"]+ "   "  + datum + "      " + str(pool_votes) + "      " + str(perc_votes))

            period = period - 604800

        except Exception as e:
            print(e)




def get_pools_votes_for_next_epoch(pool_dict, contract_instance_Voter):
    current_period = get_active_period(contract_instance_Voter)
    total_votes = get_total_votes_for_period(current_period, contract_instance_Voter)
    pools_votes_per_period = {}
    try:
        for key in pool_dict:
            pool_votes = round(get_pool_votes_for_period(pool_dict[key]["address"], current_period, contract_instance_Voter))
            perc_votes = round(pool_votes * 100 / total_votes, 2)
            pools_votes_per_period[pool_dict[key]["symbol"]] = []
            pools_votes_per_period[pool_dict[key]["symbol"]].append(perc_votes)

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
        #total_votes = get_total_votes_for_period(period, contract_instance_Voter)
        period_data.append({"epoch": datum})

    return period_data



def set_contracts_for_pools(pool_dict, web3, abi_pool, abi_gauge, abi_feedist, abi_bribe):
    for key in pool_dict:
        try:
            contract_instance_proxy_pool = web3.eth.contract(address=Web3.toChecksumAddress(pool_dict[key]["address"]), abi=abi_pool)
            contract_instance_gauge = web3.eth.contract(address=Web3.toChecksumAddress(pool_dict[key]["gauge_address"]),  abi=abi_gauge)
            contract_instance_feedist = web3.eth.contract(address=Web3.toChecksumAddress(pool_dict[key]["feedist_address"]),  abi=abi_feedist)
            contract_instance_bribe = web3.eth.contract(address=Web3.toChecksumAddress(pool_dict[key]["bribe_address"]), abi=abi_bribe)
            pool_dict[key]["contract_pool"] = contract_instance_proxy_pool
            pool_dict[key]["contract_gauge"] = contract_instance_gauge
            pool_dict[key]["contract_feedist"] = contract_instance_feedist
            pool_dict[key]["contract_bribe"] = contract_instance_bribe
        except Exception as e:
            print(e)

def get_token_symbol(address, web3, abi):
    contract_instance = web3.eth.contract(address=Web3.toChecksumAddress(address), abi=abi)
    return contract_instance.functions.symbol().call()

def get_token_decimals(address, web3, abi):
    contract_instance = web3.eth.contract(address=Web3.toChecksumAddress(address), abi=abi)
    return contract_instance.functions.decimals().call()

def get_token_data(address, web3, abi):
    token_data = {}
    try:
        contract_instance = web3.eth.contract(address=Web3.toChecksumAddress(address), abi=abi)
        token_data["decimals"] = contract_instance.functions.decimals().call()
        token_data["symbol"] = contract_instance.functions.symbol().call()

    except Exception as e:
        print(e)

    return token_data

def avoid_0_str(number):
    if number>0:
        return '{:,}'.format(number)
    else:
        return ""

def bribe_pool_add_missing(bribe_pool_data, pool_dict, period, w3, abiERC20):
    start_period = first_solidly_vote_period_start
    while period >= start_period:
        if not (str(period) in bribe_pool_data):
            pooldata = []
            for key in pool_dict:
                bribe_tokens = pool_dict[key]["contract_bribe"].functions.periodRewardsList(period).call()

                for token_address in bribe_tokens:
                    bribe_amount = pool_dict[key]["contract_bribe"].functions.periodRewardAmount(period, token_address).call()
                    bribe_token_data = get_token_data(address=token_address, web3=w3, abi=abiERC20)
                    bribe_amount = bribe_amount / pow(10, bribe_token_data["decimals"])
                    if (bribe_amount < 10):
                        bribe_amount = round(bribe_amount, 2)
                    else:
                        bribe_amount = round(bribe_amount)

                    bribe_usd = round(bribe_amount * get_token_price(token_address))

                    pooldata.append(
                        {
                            "🏊 Pool": pool_dict[key]["name"],
                            "🪙 Bribe token": bribe_token_data["symbol"],
                            "💰 Bribe token amount": str(bribe_amount),
                            "💰 Bribe value ($)": str(bribe_usd),
                        }
                    )

            if pooldata:
                bribe_pool_data[str(period)] = pooldata

        period = period - 604800


def pool_fees_add_missing(pool_dict, pool_fees, contract_instance_Voter):
    current_period = get_active_period(contract_instance_Voter)
    first_period = first_solidly_vote_period_start
    for key in pool_dict:
        period = current_period
        if not key in pool_fees:
            pool_fees[key] = {}
        while period >= first_period:
            try:
                # for each period
                if not str(period) in pool_fees[key]:
                    pool_fees[key][str(period)] = {}

                    fees_token0 = pool_dict[key]["contract_feedist"].functions.periodRewardAmount(period, pool_dict[key]["token0_address"]).call()
                    fees_token1 = pool_dict[key]["contract_feedist"].functions.periodRewardAmount(period, pool_dict[key]["token1_address"]).call()
                    fees_token0 = round(fees_token0 / pow(10, pool_dict[key]["token0_decimals"]), 2)
                    fees_token1 = round(fees_token1 / pow(10, pool_dict[key]["token1_decimals"]), 2)

                    pool_fees[key][str(period)] = {"fees_token0":fees_token0,"fees_token1":fees_token1}

                period = period - 604800

            except Exception as e:
                print(e)



def get_historical_pool_data(web3, contract_instance_Voter, config):
    pool_dict = {}
    # Load pool data
    pool_dict = load_pool_dict(filename='pools.json')
    # Add if missing
    pools_add_missing(pool_dict, contractinstance=contract_instance_Voter, web3=web3,
                      abi_pool=config["data"]["abi_Pool"], abi_gauge=config["data"]["abi_Gauge"],
                      abi_token=config["data"]["abi_Token"])
    # Save pool data
    # save_pool_dict_to_file(filename='pools.json', pools=pool_dict)
    return pool_dict

def get_historical_bribe_pool_data(web3, pool_dict, contract_instance_Voter, config):
    bribe_pool_data = {}
    bribe_pool_data = load_bribe_pool_dict(filename='bribe_pool_data.json')
    # Add missing
    current_period = get_active_period(contract_instance_Voter)
    bribe_pool_add_missing(bribe_pool_data=bribe_pool_data, pool_dict=pool_dict, period=current_period, w3=web3,
                           abiERC20=config["data"]["abi_ERC20"])
    # save_bribe_pool_dict_to_file(filename='bribe_pool_data.json', pools=bribe_pool_data)
    return bribe_pool_data

def get_historical_pool_fees_data(pool_dict, contract_instance_Voter):
    pool_fees = {}
    pool_fees = load_pool_fees(filename='pool_fees.json')
    pool_fees_add_missing(pool_dict, pool_fees, contract_instance_Voter)
    # save_pool_fees_to_file(filename='pool_fees.json', pools=pool_fees)
    return pool_fees