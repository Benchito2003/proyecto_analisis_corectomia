import os
import glob
import subprocess

# --- CONFIGURACIÓN DE RUTAS RELATIVAS ---
# Base: Donde está este script (carpeta 'codigo')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas relativas a la estructura del proyecto
# data/0_raw/ogg -> Es donde están tus originales
DIR_ORIGEN = os.path.join(BASE_DIR, "..", "data", "0_raw", "ogg")
# data/1_input -> Es donde pondremos los WAVs limpios
DIR_DESTINO = os.path.join(BASE_DIR, "..", "data", "1_input")

PREFIX_NOMBRE = "paciente_A"  # Ejemplo: paciente_A_1.wav


def normalizar():
    """
    Convierte OGG a WAV usando FFMPEG directamente.
    Evita errores de pydub/audioop en Python 3.13.
    """
    # 1. Crear carpeta de destino si no existe
    if not os.path.exists(DIR_DESTINO):
        os.makedirs(DIR_DESTINO)
        print(f"Carpeta creada: {DIR_DESTINO}")

    # 2. Buscar archivos OGG
    patron = os.path.join(DIR_ORIGEN, "*.ogg")
    archivos = glob.glob(patron)

    if not archivos:
        print(f"No encontré archivos .ogg en: {DIR_ORIGEN}")
        return

    print(f"Procesando {len(archivos)} archivos...")

    contador = 1
    for archivo_ogg in archivos:
        # Construir nombre de salida: ../data/1_input/paciente_A_1.wav
        nombre_salida = f"{PREFIX_NOMBRE}_{contador}.wav"
        ruta_salida = os.path.join(DIR_DESTINO, nombre_salida)

        print(f" -> Convirtiendo: {os.path.basename(archivo_ogg)} ...")

        # Llamada al sistema (FFmpeg)
        # -i: entrada, -ac 1: mono, -ar 44100: sample rate
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",  # -y para sobreescribir sin preguntar
                    "-i",
                    archivo_ogg,  # Archivo original
                    "-ac",
                    "1",  # Convertir a MONO (Importante para análisis)
                    "-ar",
                    "44100",  # Estandarizar frecuencia
                    ruta_salida,  # Archivo final
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            print(f"    [OK] Guardado en: {nombre_salida}")
            contador += 1

        except FileNotFoundError:
            print(
                "    [ERROR] No tienes ffmpeg instalado. Ejecuta: sudo pacman -S ffmpeg"
            )
            break
        except Exception as e:
            print(f"    [ERROR] Falló la conversión: {e}")


if __name__ == "__main__":
    print("--- INICIO DE NORMALIZACIÓN (ETAPA 0) ---")
    normalizar()
    print("--- FIN ---")
