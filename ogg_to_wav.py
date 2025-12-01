# Módulo para descomprimir ogg en wav
from pydub import AudioSegment

# Cargar audio whatsapp
audio = AudioSegment.from_file("./assets/audios/antes_cordectomia.ogg")


# Lo exporta como audio puro (WAV)
audio.export("audio_puro.wav", format="wav")
