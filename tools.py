import requests
import xmltodict
import json
import os
import importlib
import time

REALM_AUCTION_FILE = 'realm_auctions.json'
REGION_AUCTION_FILE = 'region_auctions.json'
AUCTION_EXPIRATION_TIME = 3600
file_path = 'realm_ids.json'

EMOJI_MAP = {
    "tier1": "<:tier1:1285359155854573668>",
    "tier2": "<:tier2:1285359290932269077>",
    "tier3": "<:tier3:1285359300134305822>",
    "default": "<:amogus:1285386395275493376>"
    # Add more emojis as needed
}

def xml_to_json(item_id):
    response = requests.get(f"https://www.wowhead.com/item={item_id}&xml")

    if response.status_code == 200:
        xml_data = response.content
        data = xmltodict.parse(xml_data)
        json_data = json.dumps(data)
        return json_data
    else:
        print(f"XD error code: {response.status_code}")


def load_realm_data():
    """Load realm data from the file. Returns an empty list if the file doesn't exist or is empty."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_realm_data(realm_data):
    """Save the realm data to the file."""
    with open(file_path, 'w') as file:
        json.dump(realm_data, file, indent=4)

def save_auction_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def load_auction_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None

def is_data_expired(file_path):
    if os.path.exists(file_path):
        last_modified = os.path.getmtime(file_path)
        current_time = time.time()
        return (current_time - last_modified) > AUCTION_EXPIRATION_TIME
    return True

async def get_realm_auction_data(ctx, realm_id, token):
    file_path = f"{realm_id}_REALM_AUCTION_FILE"
    if is_data_expired(file_path):
        print("Downloading new realm auction data...")
        await ctx.send("Downloading new realm auction data...")
        auction_url = f'https://eu.api.blizzard.com/data/wow/connected-realm/{realm_id}/auctions?namespace=dynamic-eu&locale=en_US&access_token={token}'
        auction_response = requests.get(auction_url)

        if auction_response.status_code == 200:
            auction_data = auction_response.json()
            save_auction_data(file_path, auction_data)
            return auction_data
        else:
            print(f"Failed to retrieve connected realm auction data: {auction_response.status_code}")
            return None
    else:
        print("Loading realm auction data from file...")
        auction_data = load_auction_data(file_path)
        if auction_data is None:
            print(f"Corrupted or invalid data in {file_path}. Redownloading...")
            return get_realm_auction_data(ctx, realm_id, token)  # Redownload if corrupted
        return auction_data

async def get_region_auction_data(ctx, token):
    file_path = REGION_AUCTION_FILE
    if is_data_expired(file_path):
        await ctx.send("Downloading region AH data...")
        print("Downloading new region-wide auction data...")
        region_auction_url = f'https://eu.api.blizzard.com/data/wow/auctions/commodities?namespace=dynamic-eu&locale=en_US&access_token={token}'
        region_auction_response = requests.get(region_auction_url)

        if region_auction_response.status_code == 200:
            region_auction_data = region_auction_response.json()
            save_auction_data(file_path, region_auction_data)
            return region_auction_data
        else:
            print(f"Failed to retrieve region-wide auction data: {region_auction_response.status_code}")
            return None
    else:
        print("Loading region-wide auction data from file...")
        auction_data = load_auction_data(file_path)
        if auction_data is None:
            print(f"Corrupted or invalid data in {file_path}. Redownloading...")
            return get_region_auction_data(ctx, token)  # Redownload if corrupted
        return auction_data

async def update_realm_file(ctx, realm_name, token):
    try:
        api_operations = importlib.import_module('api_operations')
        get_realm_ID = getattr(api_operations, 'get_realm_ID')

        # Load existing data
        realm_data = load_realm_data()
        
        # Fetch new realm ID
        new_realm = get_realm_ID(realm_name, token)
        print(new_realm)
        if new_realm == 0:
            await ctx.send("Incorrect realm name")
            return

        # Check if the realm name already exists in the data
        existing_realm = next((item for item in realm_data if realm_name in item), None)
        
        if existing_realm:
            await ctx.send(f"{realm_name} is already on the list")
        else:
            # Add new entry
            realm_data.append({realm_name: new_realm})
            save_realm_data(realm_data)
            await ctx.send(f"Added new realm '{realm_name}' with ID {new_realm}.")
        
    except Exception as e:
        # Send error message to Discord
        await ctx.send(f"Failed to update realm data: {str(e)}")
        raise  # Re-raise the exception to be caught by the bot