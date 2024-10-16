import asyncio
import numpy as np
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
from util import to_thread
from openai import OpenAI
# import queue
# import sounddevice as sd

import discord
from discord import app_commands
from discord.ext import commands#, app_commands
from discord.ext import listening

from rvc_infer import rvc_convert
from audio_separator.separator import Separator # type: ignore
from scipy.io.wavfile import write as write_wav

#=============================================#
OPENAI_API_KEY=''
client = OpenAI(
  #base_url="http://localhost:11434/v1", #Se for rodar via ollama
  api_key=OPENAI_API_KEY,
)

TIPO_TTS = 'edge' #or edge-tts #bark
#=============================================#
class Bot(discord.Client):
    GUILD = discord.Object(id=1171625791948324944)

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.GUILD)
        await self.tree.sync()

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = Bot(intents=intents)
#=============================================#

@bot.event
async def on_ready():
    print(f'{bot.user} está rodando!') 
    activity = discord.Game(name="FFXIV")
    await bot.change_presence(activity=activity) 

@bot.tree.command(name = "listarvozes")
async def listarVozes(ctx):
    ctx.response.send_message(os.listdir('weights/'))


async def getCanal(interaction: discord.Interaction):
    if interaction.guild.voice_client is not None:
        if interaction.guild.voice_client.channel != interaction.user.voice.channel:
            await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
        return interaction.guild.voice_client
    if interaction.user.voice is not None:
        return await interaction.user.voice.channel.connect()


# @to_thread
# @bot.tree.command(name = "tts")
# async def tts(ctx, user_response: str, voice: typing.Optional[str] = '', pitch: typing.Optional[int] = 0, TTSVoice: typing.Optional[str] = 'pt-BR-FranciscaNeural'):
#     global vc
#     flag = 1
#     print("tts", voice, pitch, user_response, TTSVoice)

#     msg = await ctx.send("Gerando audio... :froggohappy:")

#     if voice != '' and voice not in os.listdir('weights/'):
#         await msg.edit(content="Modelo " + voice + " não existe")
#         return

#     pos = random.randint(0, 999)
#     output_original = f"say_{pos}.mp3"

#     if TIPO_TTS == 'bark':
#         # tts.tts_to_file(text=user_response, language="en", file_path=output_original)
#         audio_array = generate_audio(user_response)
#         write_wav(output_original, SAMPLE_RATE, audio_array)
#     else:
#         command = ["edge-tts", "--voice", TTSVoice, "--text", user_response, "--write-media", output_original]
#         subprocess.run(command)

#     await msg.edit(content="Convertendo voz para o modelo")

#     if voice != '':        
#         rvc_convert(model_path='weights/' + voice + '/' + voice + '.pth',
#                 file_index='weights/' + voice + '/' + voice + '.index',
#                 index_rate=.7,
#                 f0_up_key=pitch,
#                 input_path=output_original,
#                 output_file_name=f"out{pos}.wav"
#         )
#         output_saida = f"output/out{pos}.wav"
#     else:
#         output_saida = output_original

#     await msg.delete()

#     audio_file = discord.File(output_saida)

#     if flag == 0:
#         await ctx.send(file=audio_file)
#     else:
#         await ctx.send(file=audio_file)

#         if not vc:
#             vc = await ctx.author.voice.channel.connect()
#         audio = discord.FFmpegPCMAudio(output_saida)
#         if not vc.is_playing():
#             vc.play(audio, after=None)

#     os.remove(output_original)
#     # os.remove(output_saida)

@bot.tree.command(name = "diff", description="Gera imagem usando stablediff webui")
async def diff(ctx, *, user_response: str):
    resolucao = 1024
    modo = "turbo"

    response = requests.post(url=f'http://127.0.0.1:7860/sdapi/v1/txt2img', json={
        "prompt": user_response,
        "steps": 8 if modo == "turbo" else 20,
        "sampler_name": 'DPM++ SDE Karras', #'DPM++ 3M SDE' 'UniPC'
        "cfg_scale": 2 if modo == "turbo" else 7,
        "width": resolucao, "height": resolucao,
        "negative_prompt" : '(octane render, render, drawing, anime, bad photo, bad photography:1.3), (worst quality, low quality, blurry:1.2), (bad teeth, deformed teeth, deformed lips), (bad anatomy, bad proportions:1.1), (deformed iris, deformed pupils), (deformed eyes, bad eyes), (deformed face, ugly face, bad face), (deformed hands, bad hands, fused fingers), morbid, mutilated, mutation, disfigured'
    })

    if('images' not in response.json()):
        await ctx.send("Stable diff disabled")
    
    # print(response.json())

    image = Image.open(io.BytesIO(base64.b64decode(response.json()['images'][0])))
    image.save('output.png')
    await ctx.response.send_message(file=discord.File('output.png'))

@to_thread
@bot.tree.command(name = "rvc")
async def rvc(ctx, musica: str, voz: typing.Optional[str] = 'brunov5', pitch: typing.Optional[int] = 0, start: typing.Optional[int] = 0, time: typing.Optional[int] = 15):
    vc = await getCanal(ctx)
    if vc is None:
        await ctx.response.send_message("Não está em nenhum canal de voz")
        return

    flag = 1
    print(voz, pitch, musica)

    await ctx.response.send_message("Processando")

    #msg = await ctx.send("Baixando música")
    pos = random.randint(0, 999)
    output_original = f"say_{pos}.mp3"
    audio = output_original

    commandyt = ["yt-dlp", '--extract-audio', '--audio-format', 'mp3', musica, "-o", output_original]
    subprocess.run(commandyt)

    if flag == 1: #Recorta audio
        subprocess.run(" ".join(["ffmpeg", "-i", output_original, '-ss', str(start), '-t', str(time), f"cortado_{pos}.mp3", "-y"]))
        output_original = f"cortado_{pos}.mp3"

    #await msg.edit(content="Separando vocal do instrumental")

    separator = Separator()
    separator.load_model("UVR-MDX-NET-Inst_HQ_3.onnx")
    separado  = separator.separate(output_original)
    
    #await msg.edit(content="Convertendo voz")

    rvc_convert(model_path='weights/' + voz + '/' + voz + '.pth',
                file_index='weights/' + voz + '/' + voz + '.index',
                index_rate=0.8,
                f0_up_key=pitch,
                input_path=separado[0],
                output_file_name=f"out{pos}.wav"
                )

    #await msg.delete()

    output_saida = f"output/mus{pos}.mp3"
    commandff2 = ["ffmpeg", "-i", f"output/out{pos}.wav", "-i", separado[1], '-filter_complex', 'amerge=inputs=2', '-ac', '2', '-b:a', '192K',  f"output/mus{pos}.mp3", "-y"]
    subprocess.run(commandff2)

    audio_file = discord.File(output_saida)

    if flag == 0:       
        await ctx.channel.send(file=audio_file)
    else:
        await ctx.channel.send(file=audio_file)

        audio = discord.FFmpegPCMAudio(output_saida)

        #if not vc.is_playing():
        vc.play(audio, after=None)


    # clean up!
    os.remove(f"output/out{pos}.wav")
    os.remove(output_original)
    # os.remove(output_saida)
    os.remove(separado[0])
    os.remove(separado[1])


@to_thread
@bot.tree.command(name = "gpt")
async def gpt(ctx, *, texto: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente"},
            {"role": "user", "content": texto}
        ]
    )

    await ctx.response.send_message(completion.choices[0].message.content[:1999])

@to_thread
@bot.tree.command(name = "yt", description="Toca música do Yt no voice")
async def yt(ctx, musica: str, flag: int = 1):
    vc = getCanal(ctx)

    #msg = await ctx.response.send_message("Baixando música")
    pos = random.randint(0, 9999)
    output_original = f"yt_{pos}.mp3"
    audio = output_original

    commandyt = ["yt-dlp", '--extract-audio', '--audio-format', 'mp3', musica, "-o", output_original]
    subprocess.run(commandyt)

    #await msg.delete()

    if flag == 0:       
        audio_file = discord.File(output_original)
        await ctx.channel.send(file=audio_file)
    else:
        audio_file = discord.File(output_original)
        await ctx.channel.send(file=audio_file)

        audio = discord.FFmpegPCMAudio(output_original)

        #if not vc.is_playing():
        vc.play(audio, after=None)

    os.remove(output_original)

if __name__ == "__main__":
    bot.run(open("token.txt", "r").read())
