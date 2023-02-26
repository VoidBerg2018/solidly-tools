from web3 import Web3
import time
import yaml
import requests

####################
def read_params(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

####################
def read_NFT_data(ntf_id, contract_instance):
    # Read Data
    NFT_data = {
        "balance": 0,
        "locked": 0,
        "lockend": 0,
        "voted" : False,
        "attached" : False
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


############################
# Get SOLID Price
def Get_Solid_Price():
    SOLID_price = 0

    paramsSOLID = {
        "from": "0x777172D858dC1599914a1C4c6c9fC48c99a60990",
        "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "amount": "1000000000000000000",
    }

    try:
        response = requests.get("https://router.firebird.finance/ethereum/route", params=paramsSOLID)
       # st.write(response.json())
        SOLID_price = response.json()["maxReturn"]["tokens"]["0x777172d858dc1599914a1c4c6c9fc48c99a60990"]["price"]
    except Exception as e:
        print(e)

    return SOLID_price

####################
# Get ETH Price
def Get_ETH_Price():
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
def Get_Total_veSOLID_Supply(contract_instance):
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
def Get_NFTs_forWallet_Price(wallet_address, contract_instance):
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