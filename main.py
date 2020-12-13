import discord
import os
import datetime
import pickle
from discord.ext import commands
from dotenv import load_dotenv
from hololivedata import HololiveData
load_dotenv()

bot = commands.Bot(command_prefix=".")


@bot.event
async def on_ready() :
	print(f"Discord.py Version : {discord.__version__}")
	print(f"Bot Username : {bot.user.name}")
	print(f"Bot ID : {bot.user.id}")
	print(f"Started At : {datetime.datetime.now().strftime('%d %B %Y // %H:%M:%S')}")

@bot.event
async def on_message(msg) : 
	pass

if __name__ == "__main__" :
	data = HololiveData(
		api_yt_key=os.getenv("API_YT_KEY"),
		token_discord=os.getenv("TOKEN_BOT")
	)

	# Add Channel Alert
	data.add_channel("CHANNEL_ID")

	# Start Data
	data.deamon = True
	data.start()

	bot.run(os.getenv("TOKEN_BOT"))
