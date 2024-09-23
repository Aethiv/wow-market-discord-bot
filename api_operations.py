import requests
from tools import xml_to_json, load_realm_data,get_region_auction_data,get_realm_auction_data,EMOJI_MAP
import json
import re
from discord.ext import commands
import discord

ITEM_SEARCH_URL = 'https://eu.api.blizzard.com/data/wow/search/item?namespace=static-eu'


async def get_item_price(ctx, item_name, token):
    print(item_name)
    search_response = requests.get(f'https://eu.api.blizzard.com/data/wow/search/item?namespace=static-eu&name.en_US={item_name}&access_token={token}')
    results_data = search_response.json()

    matched_items = perfect_match_check(results_data, item_name)
    matched_items_dict = get_item_tier(matched_items)

    print(matched_items_dict)
    
    # Iterate over each matched item and check auction house
    for item_id, item_tier in matched_items_dict.items():
        # Use item_name and item_tier for the Discord message
        await check_auction_house(ctx, item_id, item_name, item_tier, token)
    

def get_realm_ID(realm_name,token):
    pattern = r"connected-realm/(\d+)"  # Matches "connected-realm/" followed by one or more digits

    realm_api_url = f'https://eu.api.blizzard.com/data/wow/realm/{realm_name}?namespace=dynamic-eu&locale=en_US&access_token={token}'
    realm_response = requests.get(realm_api_url)

    if realm_response.status_code == 200:
        realm_data = realm_response.json()
        
        connected_realm_url = realm_data["connected_realm"]["href"]
        match = re.search(pattern, connected_realm_url)

        if match:
            connected_realm_id = match.group(1)
            print(f"Connected Realm ID: {connected_realm_id}")
        else:
            print("Connected Realm ID not found in the response.")
        return connected_realm_id
    else:
        print(f"Failed to retrieve realm data: {realm_response.status_code}")
        return 0

async def check_auction_house(ctx, item_id, item_name, item_tier, token):
    print(f"Checking item ID: {item_id}")

    # Load realm data
    realmDict = load_realm_data()
    realm_lowest_prices = {}
    found_any_auction = False

    # Process each realm
    for realm in realmDict:
        for realm_name, realm_id in realm.items():
            print(f"Checking connected realm ID: {realm_id}")

            # Load auction data from file or download if expired
            auction_data = await get_realm_auction_data(ctx, realm_id, token)
            if auction_data:
                # Filter auctions for the item
                auctions = [auction for auction in auction_data['auctions'] if auction['item']['id'] == int(item_id)]
                
                if auctions:
                    # Find the lowest price, checking for both unit_price and buyout
                    lowest_price = min(
                        auction.get('unit_price', auction.get('buyout')) for auction in auctions if 'unit_price' in auction or 'buyout' in auction
                    )
                    if lowest_price:
                        realm_lowest_prices[realm_name] = lowest_price
                        found_any_auction = True
            else:
                print(f"Failed to retrieve or load auction data for realm ID: {realm_id}")

    # Prepare message for lowest prices by realm
    if realm_lowest_prices:
        message = f"Item: {item_name} {EMOJI_MAP.get(item_tier, '<:amogus:1285386395275493376>')}\nLowest prices by realm:\n"
        for realm_name, lowest_price in realm_lowest_prices.items():
            message += f"Realm: {realm_name} | Lowest Price: {lowest_price / 10000}g\n"
        await ctx.send(message)
    
    # Check the region-wide commodities auction house
    print(f"Checking region-wide commodities auction house for item ID: {item_id}")
    region_auction_data = await get_region_auction_data(ctx, token)

    if region_auction_data:
        # Filter auctions for the item
        auctions = [auction for auction in region_auction_data['auctions'] if auction['item']['id'] == int(item_id)]
        
        if auctions:
            # Find the lowest price, checking for both unit_price and buyout
            lowest_price = min(
                auction.get('unit_price', auction.get('buyout')) for auction in auctions if 'unit_price' in auction or 'buyout' in auction
            )
            
            if lowest_price:
                # Send the result to Discord
                await ctx.send(f"Item: {item_name} {EMOJI_MAP.get(item_tier, ':default:')}\nLowest price region-wide: {lowest_price / 10000}g")
        else:
            # Only send a message if no auctions were found region-wide and also no local auctions
            if not found_any_auction:
                await ctx.send(f"Item: {item_name} {EMOJI_MAP.get(item_tier, ':default:')}\nNo auctions found for item ID {item_id} region-wide.")
    else:
        await ctx.send(f"Failed to retrieve or load region-wide auction data.")



def perfect_match_check(results_data, item_name):
    item_ids = []
    for result in results_data['results']:
        item_ids.append(result['data']['media']['id'])
    print(item_ids)

    #Get wowhead json
    wowhead_data_dicts = []
    for item_id in item_ids:
        wowhead_json = xml_to_json(item_id)
        wowhead_data_dicts.append(json.loads(wowhead_json))

    verified_items = []
    for item_data in wowhead_data_dicts:
        if item_data["wowhead"]["item"]["name"].lower() == item_name.lower():
            verified_items.append(item_data)
        
    return verified_items

def get_item_tier(verified_items):
    item_tier_dict = {}
    for item in verified_items:
        item_id = item['wowhead']['item']['@id']
        #xml from wowhead converted to json
        html_tooltip = item['wowhead']['item']['htmlTooltip']

        match = re.search(r'quality-tier(\d+)\.png', html_tooltip)
        if match:
            tier = match.group(1)
            # Add item id and tier to the dictionary
            item_tier_dict[item_id] = f"tier{tier}"
        else:
            # If no tier is found, set the value to None or some default
            item_tier_dict[item_id] = None

    return item_tier_dict









#def get_item_price(item_id, token):
 #   item_info_url = f'https://eu.api.blizzard.com/data/wow/item/{item_id}?namespace=static-eu&access_token={token}'
  #  item_info_response = requests.get(item_info_url)
   # item_info = item_info_response.json()
    #return item_info.get('vendor_price', 'Price not available')