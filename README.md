# AIDiscordBot

Bot para discord implementado em python com comandos para testes nos mais populares modelos de IA generativa (RVC e Stable Diffusion)

#NVIDIA + CUDA

python -m venv venv
venv/scripts/activate

pip install -r requirements.txt
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124 
pip install -e git+https://github.com/JarodMica/rvc.git#egg=rvc
pip install -e git+https://github.com/tpnto/rvc-tts-pipeline.git@rvc-output-name#egg=rvc-tts-pipe
