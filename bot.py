from time import sleep
import time
from PIL import Image
import os
import subprocess
import typing
import requests
import io
import base64
import random

import discord
from discord import app_commands
from discord.ext import commands

from rvc_infer import rvc_convert

from audio_separator.separator import Separator

DISCORD_TOKEN = open("token.txt", "r").read()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
# bot= discord.Client(command_prefix='!',intents=intents)
# tree= app_commands.CommandTree(bot)

vc = 0

@bot.event
async def on_ready():
    print(f'{bot.user} está rodando!') 
    activity = discord.Game(name="FFXIV")
    # await tree.sync()
    await bot.change_presence(activity=activity) 

@bot.command(name = "listarvozes")
async def listarVozes(ctx):
    ctx.send(os.listdir('weights/'))

    
@bot.command(name = "tts")
async def tts(ctx, user_response: str, voice: typing.Optional[str] = 'bruno', pitch: typing.Optional[int] = 0, TTSVoice: typing.Optional[str] = 'uk-UA-OstapNeural'):
    flag = 1
    print(voice, pitch, user_response, TTSVoice)

    msg = await ctx.send("Gerando audio... :froggohappy:")

    pos = random.randint(0, 999)

    outputedgetts = f"say_{pos}.mp3"
    command = ["edge-tts", "--voice", TTSVoice, "--text", user_response, "--write-media", outputedgetts]
    subprocess.run(command)

    rvc_convert(model_path='weights/' + voice + '/' + voice + '.pth',
                file_index='weights/' + voice + '/' + voice + '.index',
                index_rate=0.7,
                f0_up_key=pitch,
                input_path=outputedgetts,
                output_file_name=f"out{pos}.wav"
                )

    await msg.delete()

    outputpath = f"output/out{pos}.wav"
    audio_file = discord.File(outputpath)

    # Send the audio file to discord
    if flag == 0:
        await ctx.send(file=audio_file)
    else:
        vc = 0
        try:
            vc = await ctx.author.voice.channel.connect() #voice = await channel.connect()
        except:
            #await vc.disconnect()
            vc = ctx.voice_client
        
        vc.play(discord.FFmpegPCMAudio(outputpath))
        while vc.is_playing():
            sleep(.1)
        #await ctx.voice_client.disconnect()

    # clean up!
    os.remove(outputedgetts)
    os.remove(outputpath)

@bot.command(name = "entrar")
async def entrar(ctx, args):
    global vc
    vc = await ctx.author.voice.channel.connect()


bot.run(DISCORD_TOKEN)
