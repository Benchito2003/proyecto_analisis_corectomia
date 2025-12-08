import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import soundfile as sf

# --- CONFIGURACIÓN DE RUTAS RELATIVAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Entrada: Los WAVs normalizados
DIR_INPUT = os.path.join(BASE_DIR, "..", "data", "1_input")

# Salida: Directamente a la carpeta de imágenes del reporte
DIR_IMG_OUT = os.path.join(BASE_DIR, "..", "docs", "reporte", "imagenes")
# Salida de datos (CSV) por si los necesitas
DIR_DATA_OUT = os.path.join(BASE_DIR, "..", "data", "3_analysis")

# --- ESTILO VISUAL (Dark Theme) ---
plt.style.use("dark_background")
COLOR_PRE = "#61afef"  # Azul OneDark
COLOR_POST = "#e06c75"  # Rojo OneDark
COLOR_GRID = "#4b5263"


def cargar_audio(ruta):
    try:
        data, samplerate = sf.read(ruta)
        # Asegurar Mono
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        return data, samplerate
    except Exception as e:
        print(f"Error cargando {ruta}: {e}")
        return None, None


def calcular_espectro_medio(data, fs):
    """
    Calcula la Transformada de Fourier (PSD) promediada en el tiempo.
    Nos dice QUÉ frecuencias están presentes globalmente.
    """
    freqs, psd = scipy.signal.welch(data, fs, nperseg=4096)
    # Convertir a dB
    psd_db = 10 * np.log10(psd + 1e-10)  # +epsilon para evitar log(0)
    return freqs, psd_db


def plot_espectrograma_banda_estrecha(ax, data, fs, titulo):
    """
    Configuración específica para ver ARMÓNICOS (La 'Escalera').
    Ventana grande (NFFT alto) = Mejor resolución de frecuencia.
    """
    Pxx, freqs, bins, im = ax.specgram(
        data,
        NFFT=4096,  # Ventana grande para ver las rayitas
        Fs=fs,
        noverlap=3000,
        cmap="inferno",
    )
    ax.set_title(titulo, color="white", fontsize=10)
    ax.set_ylabel("Frecuencia (Hz)")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylim(0, 5000)  # Enfocamos en la voz humana (0-5kHz)


def generar_analisis(archivo_pre, archivo_post):
    print(
        f" -> Analizando: \n    A) {os.path.basename(archivo_pre)}\n    B) {os.path.basename(archivo_post)}"
    )

    # 1. Cargar
    y_pre, sr_pre = cargar_audio(archivo_pre)
    y_post, sr_post = cargar_audio(archivo_post)

    if y_pre is None or y_post is None:
        return

    # 2. Calcular Espectros Medios (PSD)
    f_pre, mag_pre = calcular_espectro_medio(y_pre, sr_pre)
    f_post, mag_post = calcular_espectro_medio(y_post, sr_post)

    # --- GRÁFICA 1: COMPARATIVA DE ESPECTROS (Cuantitativa) ---
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Plot Superpuesto
    ax1.plot(
        f_pre,
        mag_pre,
        label="Pre-Cordectomía (Sano)",
        color=COLOR_PRE,
        linewidth=1.5,
        alpha=0.9,
    )
    ax1.plot(
        f_post,
        mag_post,
        label="Post-Cordectomía (Patológico)",
        color=COLOR_POST,
        linewidth=1.2,
        alpha=0.8,
    )

    ax1.set_xlim(0, 5000)  # Zoom a la zona de voz
    ax1.set_title("Comparativa de Densidad Espectral de Potencia (PSD)", fontsize=14)
    ax1.set_ylabel("Magnitud (dB)")
    ax1.legend()
    ax1.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)

    # Plot Diferencial (La "Mascara")
    # Interpolamos para restar (por si tienen longitudes levemente distintas)
    min_len = min(len(mag_pre), len(mag_post))
    diff = mag_pre[:min_len] - mag_post[:min_len]
    f_common = f_pre[:min_len]

    ax2.fill_between(
        f_common,
        diff,
        0,
        where=(diff > 0),
        color="#98c379",
        alpha=0.3,
        label="Pérdida de Energía",
    )
    ax2.plot(f_common, diff, color="white", linewidth=1)
    ax2.set_xlim(0, 5000)
    ax2.set_title("Diferencia Espectral (Lo que se perdió)", fontsize=12)
    ax2.set_xlabel("Frecuencia (Hz)")
    ax2.set_ylabel("Diferencia (dB)")
    ax2.legend()
    ax2.grid(color=COLOR_GRID, linestyle=":", alpha=0.5)

    plt.tight_layout()
    ruta_fig1 = os.path.join(DIR_IMG_OUT, "analisis_espectral_comparativo.png")
    plt.savefig(ruta_fig1, dpi=150)
    print(f" [IMG] Guardada comparativa espectral en: {ruta_fig1}")
    plt.close()

    # --- GRÁFICA 2: ESPECTROGRAMA BANDA ESTRECHA (Cualitativa / Visual) ---
    # Esta es la imagen "Escalera vs Niebla" para tu diapo
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    plot_espectrograma_banda_estrecha(
        ax3, y_pre, sr_pre, "PRE: Estructura Armónica (Líneas definidas)"
    )
    plot_espectrograma_banda_estrecha(
        ax4, y_post, sr_post, "POST: Ruido de Banda Ancha (Difuso/Niebla)"
    )

    plt.tight_layout()
    ruta_fig2 = os.path.join(DIR_IMG_OUT, "evidencia_visual_armonicos.png")
    plt.savefig(ruta_fig2, dpi=150)
    print(f" [IMG] Guardada evidencia visual en: {ruta_fig2}")
    plt.close()


def main():
    # Crear directorios si no existen
    for d in [DIR_IMG_OUT, DIR_DATA_OUT]:
        if not os.path.exists(d):
            os.makedirs(d)

    print("--- 2_CORDIE.PY: Análisis Espectral ---")
    print(f"Buscando archivos en: {DIR_INPUT}")

    # Listar WAVs
    wavs = sorted(glob.glob(os.path.join(DIR_INPUT, "*.wav")))

    if len(wavs) < 2:
        print(
            "[ERROR] Necesito al menos 2 archivos .wav en 'data/1_input' para comparar."
        )
        return

    print("\nArchivos disponibles:")
    for i, w in enumerate(wavs):
        print(f" [{i}] {os.path.basename(w)}")

    # Selección interactiva sencilla
    try:
        idx_pre = int(input("\nSelecciona el número del audio PRE (Sano): "))
        idx_post = int(input("Selecciona el número del audio POST (Enfermo): "))

        generar_analisis(wavs[idx_pre], wavs[idx_post])

        print("\n--- ¡Análisis Terminado! ---")
        print("Revisa la carpeta 'docs/reporte/imagenes' para ver tus gráficas.")

    except (ValueError, IndexError):
        print("[ERROR] Selección inválida.")


import glob  # Import tardío para glob

if __name__ == "__main__":
    main()
