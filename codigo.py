import os
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import soundfile as sf
import noisereduce as nr
import pandas as pd
from pydub import AudioSegment
from matplotlib.backends.backend_pdf import PdfPages

# --- CONFIGURACIÓN DE RUTAS ---
BASE_PATH = "/home/elchino/Escritorio/proyecto-analisis"
PATH_INFO = os.path.join(BASE_PATH, "Información")
PATH_DATOS = os.path.join(BASE_PATH, "Datos")

# Crear carpetas si no existen
os.makedirs(PATH_INFO, exist_ok=True)
os.makedirs(PATH_DATOS, exist_ok=True)


def cargar_y_convertir(ruta_archivo, sr=44100):
    """Carga audio usando librosa. Si falla, intenta con pydub (para formatos raros)."""
    try:
        # Librosa carga y remuestrea automáticamente
        y, s_rate = librosa.load(ruta_archivo, sr=sr)
        return y, s_rate
    except Exception as e:
        print(f"Librosa falló, intentando con Pydub... Error: {e}")
        # Fallback para formatos que librosa a veces pelea (aunque con ffmpeg instalado debería ir bien)
        audio = AudioSegment.from_file(ruta_archivo)
        audio = audio.set_frame_rate(sr).set_channels(1)  # Convertir a mono
        y = (
            np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
        )  # Normalizar
        return y, sr


def exportar_audios(y, sr, nombre_base, carpeta):
    """Exporta en WAV y MP3"""
    nombre_salida = f"mejorado_{nombre_base}"
    ruta_wav = os.path.join(carpeta, f"{nombre_salida}.wav")
    ruta_mp3 = os.path.join(carpeta, f"{nombre_salida}.mp3")

    # Guardar WAV
    sf.write(ruta_wav, y, sr)

    # Guardar MP3 (usando pydub porque soundfile no escribe mp3 directamente)
    # Convertimos numpy array de vuelta a AudioSegment
    audio_segment = AudioSegment(
        (y * 32767).astype("int16").tobytes(), frame_rate=sr, sample_width=2, channels=1
    )
    audio_segment.export(ruta_mp3, format="mp3", bitrate="192k")
    print(f"Audios guardados: {nombre_salida}")


def obtener_espectro(y, sr, n_fft=2048):
    """
    Calcula la magnitud del espectro promedio.
    Usamos STFT y promediamos en el tiempo para obtener una curva de frecuencia consistente
    independientemente de la duración del audio.
    """
    # Short-Time Fourier Transform
    D = librosa.stft(y, n_fft=n_fft)
    # Magnitud
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    # Promedio en el eje del tiempo (axis 1) para obtener un perfil de frecuencia
    promedio_frecuencias = np.mean(S_db, axis=1)
    # Generar eje de frecuencias
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    return freqs, promedio_frecuencias


def procesar_paciente(ruta_audio1, ruta_audio2):
    # Obtener nombres de archivo sin extensión
    nombre1 = os.path.splitext(os.path.basename(ruta_audio1))[0]
    nombre2 = os.path.splitext(os.path.basename(ruta_audio2))[0]
    nombre_conjunto = f"{nombre1}_vs_{nombre2}"

    print(f"--- Procesando: {nombre1} (Pre) y {nombre2} (Post) ---")

    # 1. Cargar Audios (Remuestrear a 44.1kHz para consistencia)
    sr_comun = 44100
    y1, sr1 = cargar_y_convertir(ruta_audio1, sr=sr_comun)
    y2, sr2 = cargar_y_convertir(ruta_audio2, sr=sr_comun)

    # 2. Reducción de Ruido y Mejora
    # Usamos reducción de ruido estacionario. prop_decrease=0.8 es suave para no dañar la voz
    print("Aplicando reducción de ruido...")
    y1_clean = nr.reduce_noise(y=y1, sr=sr1, prop_decrease=0.85, stationary=True)
    y2_clean = nr.reduce_noise(y=y2, sr=sr2, prop_decrease=0.85, stationary=True)

    # 3. Exportar Audios Mejorados
    exportar_audios(y1_clean, sr1, nombre1, PATH_INFO)
    exportar_audios(y2_clean, sr2, nombre2, PATH_INFO)

    # 4. Calcular FFT (Espectros)
    # Usamos n_fft fijo para que los bins de frecuencia sean idénticos
    freqs, mag1_orig = obtener_espectro(y1, sr1)
    _, mag1_clean = obtener_espectro(y1_clean, sr1)

    _, mag2_orig = obtener_espectro(y2, sr2)
    _, mag2_clean = obtener_espectro(y2_clean, sr2)

    # Calcular diferencia (Post - Pre mejorados, o simplemente magnitud de diferencia)
    # Asumimos que queremos ver cómo cambió el espectro
    diferencia = mag2_clean - mag1_clean

    # 5. Generar PDF con Gráficas
    ruta_pdf = os.path.join(PATH_INFO, f"grafica_{nombre_conjunto}.pdf")

    with PdfPages(ruta_pdf) as pdf:
        fig = plt.figure(figsize=(14, 18))

        # Diseño de la cuadrícula: 4 filas.
        # Fila 0: Audio 1 Orig vs Mejorado
        # Fila 1: Audio 2 Orig vs Mejorado
        # Fila 2: Comparativa (3 columnas)

        # --- Gráfica 1: Audio 1 (Pre) ---
        ax1 = plt.subplot2grid((4, 3), (0, 0), colspan=3)
        ax1.plot(freqs, mag1_orig, label="Original (Pre)", alpha=0.5, color="gray")
        ax1.plot(freqs, mag1_clean, label="Mejorado (Pre)", color="blue")
        ax1.set_title(f"Audio 1 (Pre-Cordectomía): {nombre1}")
        ax1.set_ylabel("Amplitud (dB)")
        ax1.set_xlabel("Frecuencia (Hz)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # --- Gráfica 2: Audio 2 (Post) ---
        ax2 = plt.subplot2grid((4, 3), (1, 0), colspan=3)
        ax2.plot(freqs, mag2_orig, label="Original (Post)", alpha=0.5, color="gray")
        ax2.plot(freqs, mag2_clean, label="Mejorado (Post)", color="green")
        ax2.set_title(f"Audio 2 (Post-Cordectomía): {nombre2}")
        ax2.set_ylabel("Amplitud (dB)")
        ax2.set_xlabel("Frecuencia (Hz)")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # --- Fila Inferior: Comparativas ---
        # Izquierda: Audio 1 Mejorado
        ax3 = plt.subplot2grid((4, 3), (2, 0))
        ax3.plot(freqs, mag1_clean, color="blue")
        ax3.set_title("Pre-Op Mejorado")
        ax3.set_xlabel("Hz")
        ax3.grid(True, alpha=0.3)

        # Centro: Audio 2 Mejorado
        ax4 = plt.subplot2grid((4, 3), (2, 1), sharey=ax3)
        ax4.plot(freqs, mag2_clean, color="green")
        ax4.set_title("Post-Op Mejorado")
        ax4.set_xlabel("Hz")
        ax4.grid(True, alpha=0.3)

        # Derecha: Diferencia
        ax5 = plt.subplot2grid((4, 3), (2, 2))
        ax5.plot(freqs, diferencia, color="red")
        ax5.set_title("Diferencia (Post - Pre)")
        ax5.set_xlabel("Hz")
        ax5.set_ylabel("Delta dB")
        ax5.grid(True, alpha=0.3)
        # Línea cero para referencia
        ax5.axhline(0, color="black", linewidth=0.8, linestyle="--")

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    print(f"Gráficas guardadas en: {ruta_pdf}")

    # 6. Exportar Datos (CSV y TXT)
    data = {
        "Frecuencia_Hz": freqs,
        f"{nombre1}_Mejorado_dB": mag1_clean,
        f"{nombre2}_Mejorado_dB": mag2_clean,
        "Diferencia_dB": diferencia,
    }

    df = pd.DataFrame(data)

    ruta_csv = os.path.join(PATH_DATOS, f"tabla_{nombre_conjunto}.csv")
    ruta_txt = os.path.join(PATH_DATOS, f"tabla_{nombre_conjunto}.txt")

    df.to_csv(ruta_csv, index=False)
    df.to_csv(ruta_txt, sep="\t", index=False)

    print(f"Tablas de datos guardadas en: {PATH_DATOS}")


# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    # AQUÍ DEBES PONER LAS RUTAS DE TUS ARCHIVOS DE ENTRADA
    # Ejemplo:
    # audio_pre = "ruta/a/tu/archivo_pre.opus"
    # audio_post = "ruta/a/tu/archivo_post.opus"

    print("Por favor, introduce la ruta completa del primer archivo (Pre-Cordectomía):")
    archivo1 = (
        input().strip().replace("'", "")
    )  # Limpia comillas si se arrastra el archivo

    print(
        "Por favor, introduce la ruta completa del segundo archivo (Post-Cordectomía):"
    )
    archivo2 = input().strip().replace("'", "")

    if os.path.exists(archivo1) and os.path.exists(archivo2):
        procesar_paciente(archivo1, archivo2)
        print("\n--- Proceso Finalizado con Éxito ---")
    else:
        print("Error: Uno o ambos archivos no fueron encontrados. Verifica las rutas.")
