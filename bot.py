import discord
from Secret import CLIENT_ID,CLIENT_SECRET,BOT_TOKEN
import api_operations
import tools
import requests
from discord.ext import commands

AUTH_URL = 'https://eu.battle.net/oauth/token'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_access_token():
    response = requests.post(AUTH_URL, data={
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    return response.json().get('access_token')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def price(ctx, *, item_name):
    token = get_access_token()
    item_info = await api_operations.get_item_price(ctx, item_name.lower(), token)
    print('Done')

@bot.command()
async def addrealm(ctx, *, realm_name):
    token = get_access_token()
    try:

        await tools.update_realm_file(ctx, realm_name.lower(), token)
        print('Done')
    except Exception as e:
        
        await ctx.send(f"An error occurred: {str(e)}")

bot.run(BOT_TOKEN)
