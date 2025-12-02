# Módulo para descomprimir ogg en wav EN MASA
from pydub import AudioSegment
import glob

# Variables de rutas
ruta = "../audios/ogg/"
nombres_nuevos = "audio_ruidoso"

# audio = AudioSegment.from_file("./assets/audios/antes_cordectomia.ogg")
archivos = glob.glob(ruta + "*ogg")


def normalizar():
    """
    Función que convierte y normaliza automáticamente los audios que se ubiquen en el directorio /audios/ogg
    """
    contador = 0
    for i in archivos:
        audio = AudioSegment.from_file(i)
        audio.export(
            "audios/wav/" + nombres_nuevos + f"{contador + 1}.wav", format="wav"
        )
        contador += 1


if __name__ == "__main__":
    normalizar()
