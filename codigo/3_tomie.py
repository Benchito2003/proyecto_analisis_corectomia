import os
import glob
import numpy as np
import pandas as pd
import scipy.io.wavfile as wav
from scipy import signal
from scipy.interpolate import interp1d
import sys

# Intentar importar pydub para MP3
try:
    from pydub import AudioSegment
except ImportError:
    print("Error: Falta la librería 'pydub'. Instálala con: pip install pydub")
    sys.exit(1)

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y PARÁMETROS
# ==========================================
BASE_DIR = "/home/yetmontero/Cordec/GFA"
PATH_CSV_PRE = os.path.join(BASE_DIR, "Datum/CSV/PRE")
PATH_CSV_POST = os.path.join(BASE_DIR, "Datum/CSV/POST")
PATH_AUDIO_IN = os.path.join(BASE_DIR, "Recursos/Clean")
PATH_AUDIO_OUT = os.path.join(BASE_DIR, "VoxAdj")

# Parámetros de suavizado (Savitzky-Golay)
WINDOW_LENGTH = 51
POLYORDER = 3

# Parámetros de procesamiento de Audio (STFT)
N_FFT = 2048
HOP_LENGTH = 512

os.makedirs(PATH_AUDIO_OUT, exist_ok=True)


# ==========================================
# 2. FUNCIONES DE UTILIDAD (Corrección de errores)
# ==========================================
def aplicar_filtro_seguro(columna_datos, window_len=51, polyorder=3):
    """
    Aplica savgol_filter con ajuste dinámico de ventana.
    """
    n_datos = len(columna_datos)
    min_len = polyorder + 2

    if n_datos < min_len:
        return columna_datos

    if window_len > n_datos:
        window_len = n_datos

    if window_len % 2 == 0:
        window_len -= 1

    if window_len <= polyorder:
        window_len = n_datos if n_datos % 2 != 0 else n_datos - 1
        if window_len <= polyorder:
            return columna_datos

    try:
        return signal.savgol_filter(columna_datos, window_len, polyorder)
    except:
        return columna_datos


# ==========================================
# 3. ANÁLISIS ESTADÍSTICO (Generación de Máscara)
# ==========================================
def obtener_perfil_promedio(ruta_carpeta, etiqueta):
    archivos = glob.glob(os.path.join(ruta_carpeta, "*.csv"))
    print(f"--- Analizando {etiqueta}: {len(archivos)} archivos encontrados ---")

    acumulador_magnitud = []
    eje_frecuencia_comun = None

    for archivo in archivos:
        try:
            df = pd.read_csv(archivo)
            if "Frecuencia_Hz" not in df.columns or "Magnitud_dB" not in df.columns:
                continue

            # Suavizar
            df["Smooth"] = aplicar_filtro_seguro(
                df["Magnitud_dB"], WINDOW_LENGTH, POLYORDER
            )

            if eje_frecuencia_comun is None:
                eje_frecuencia_comun = df["Frecuencia_Hz"].values
                acumulador_magnitud.append(df["Smooth"].values)
            else:
                f_interp = interp1d(
                    df["Frecuencia_Hz"],
                    df["Smooth"],
                    kind="linear",
                    fill_value="extrapolate",
                )
                magnitud_interpolada = f_interp(eje_frecuencia_comun)
                acumulador_magnitud.append(magnitud_interpolada)

        except Exception as e:
            print(f"   [Error] {os.path.basename(archivo)}: {e}")

    if not acumulador_magnitud:
        raise ValueError(f"No se pudieron procesar datos en {etiqueta}")

    promedio = np.mean(acumulador_magnitud, axis=0)
    return eje_frecuencia_comun, promedio


def calcular_mascara_transferencia():
    print("Calculando máscara de transferencia (PRE vs POST)...")
    freq_pre, mag_pre = obtener_perfil_promedio(PATH_CSV_PRE, "PRE-CORDECTOMÍA")
    freq_post, mag_post = obtener_perfil_promedio(PATH_CSV_POST, "POST-CORDECTOMÍA")

    # Alinear frecuencias
    f_interp_post = interp1d(
        freq_post, mag_post, kind="linear", fill_value="extrapolate"
    )
    mag_post_alineada = f_interp_post(freq_pre)

    # Calcular Máscara
    mascara_db = mag_pre - mag_post_alineada
    mascara_suave = aplicar_filtro_seguro(mascara_db, window_len=101, polyorder=3)

    print(
        f"[Mascara Generada] Rango de corrección: {min(mascara_suave):.2f}dB a {max(mascara_suave):.2f}dB"
    )
    return freq_pre, mascara_suave


# ==========================================
# 4. PROCESAMIENTO DE AUDIO (Aplicación de Máscara)
# ==========================================
def aplicar_mascara_a_audio(ruta_archivo_completa, freq_mascara, ganancia_db_mascara):
    nombre_base = os.path.basename(ruta_archivo_completa)
    nombre_sin_ext = os.path.splitext(nombre_base)[0]

    print(f"   Procesando: {nombre_base} ...")

    # Cargar Audio
    try:
        fs, audio = wav.read(ruta_archivo_completa)
    except Exception as e:
        print(f"   [Error] No se pudo leer el audio: {e}")
        return

    if audio.dtype == np.int16:
        audio = audio / 32768.0

    if len(audio.shape) > 1:
        audio = audio[:, 0]  # Mono

    # STFT
    f_stft, t_stft, Zxx = signal.stft(audio, fs, nperseg=N_FFT)

    # Interpolar Máscara
    interpolador_mascara = interp1d(
        freq_mascara, ganancia_db_mascara, kind="linear", fill_value="extrapolate"
    )
    mascara_interpolada = interpolador_mascara(f_stft)

    # Aplicar ganancia
    ganancia_lineal = 10 ** (mascara_interpolada / 20.0)
    Zxx_modificado = Zxx * ganancia_lineal[:, np.newaxis]

    # ISTFT
    _, audio_recuperado = signal.istft(Zxx_modificado, fs)

    # Normalizar
    max_val = np.max(np.abs(audio_recuperado))
    if max_val > 0:
        audio_recuperado = audio_recuperado / max_val * 0.9

    # Convertir a int16 para guardar
    audio_int16 = (audio_recuperado * 32767).astype(np.int16)

    # --- GUARDAR WAV ---
    ruta_salida_wav = os.path.join(PATH_AUDIO_OUT, f"MOD_{nombre_sin_ext}.wav")
    wav.write(ruta_salida_wav, fs, audio_int16)
    print(f"   [WAV] Guardado en: {ruta_salida_wav}")

    # --- CONVERTIR Y GUARDAR MP3 ---
    try:
        ruta_salida_mp3 = os.path.join(PATH_AUDIO_OUT, f"MOD_{nombre_sin_ext}.mp3")
        # Cargamos el WAV que acabamos de crear para convertirlo
        audio_segment = AudioSegment.from_wav(ruta_salida_wav)
        audio_segment.export(ruta_salida_mp3, format="mp3", bitrate="192k")
        print(f"   [MP3] Guardado en: {ruta_salida_mp3}")
    except Exception as e:
        print(f"   [!] Error al generar MP3 (Verifica ffmpeg): {e}")


# ==========================================
# 5. MENÚ INTERACTIVO
# ==========================================
def main():
    print("=== SISTEMA DE RESTAURACIÓN VOCAL (WAV + MP3) ===")

    # 1. Preparación de Máscara
    try:
        freq_ref, mascara_db = calcular_mascara_transferencia()
    except Exception as e:
        print(f"Error crítico: {e}")
        return

    print("\n" + "=" * 50)
    print(f"Carpeta de audios origen: {PATH_AUDIO_IN}")
    print("Salida: Archivos .wav y .mp3 en carpeta VoxAdj")
    print("=" * 50)

    # 2. Bucle Interactivo
    while True:
        try:
            entrada = input("\n>> Ingrese nombre del audio (.wav): ").strip()
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break

        if entrada.lower() in ["salir", "exit", "quit", "q"]:
            print("Cerrando programa.")
            break

        if entrada.lower() in ["ls", "lista", "list", "dir"]:
            print("\n--- Archivos disponibles en Recursos/Clean ---")
            wavs = [f for f in os.listdir(PATH_AUDIO_IN) if f.endswith(".wav")]
            if not wavs:
                print("(Carpeta vacía)")
            else:
                for w in wavs:
                    print(f" - {w}")
            continue

        if not entrada:
            continue

        # Manejo inteligente del nombre
        nombre_archivo = entrada
        if not nombre_archivo.lower().endswith(".wav"):
            nombre_archivo += ".wav"

        ruta_completa = os.path.join(PATH_AUDIO_IN, nombre_archivo)

        if os.path.exists(ruta_completa):
            aplicar_mascara_a_audio(ruta_completa, freq_ref, mascara_db)
        else:
            print(f"   [!] El archivo '{nombre_archivo}' no existe.")


if __name__ == "__main__":
    main()
