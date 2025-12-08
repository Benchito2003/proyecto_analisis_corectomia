import matplotlib.pyplot as plt
from scipy.io import wavfile
import numpy as np

# Rutas a tus archivos (asegúrate de que sean WAV)
archivo_antes = "audios/wav/audio_ruidoso1.wav"
archivo_despues = "audios/wav/audio_ruidoso2.wav"


def plot_narrowband(ax, filename, title):
    fs, data = wavfile.read(filename)

    # Si es estéreo, pasamos a mono
    if len(data.shape) > 1:
        data = data[:, 0]

    # Normalizar para que se vean parecidos en volumen visual
    data = data / np.max(np.abs(data))

    # --- CONFIGURACIÓN MÁGICA ---
    # NFFT alto = Alta resolución de frecuencia (Banda Estrecha)
    # Esto es lo que crea el efecto de "Líneas"
    Pxx, freqs, bins, im = ax.specgram(
        data, NFFT=4096, Fs=fs, noverlap=3500, cmap="inferno"
    )

    ax.set_title(title, fontsize=14, color="white")
    ax.set_ylabel("Frecuencia (Hz)", color="white")
    ax.set_xlabel("Tiempo (s)", color="white")

    # Limitamos la frecuencia a 5000Hz (donde está la voz humana principal)
    ax.set_ylim(0, 5000)

    # Estilizado para fondo oscuro (estilo One Dark)
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")


# Configurar la figura (Fondo oscuro para resaltar colores)
plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

# Generar gráficos
try:
    plot_narrowband(
        ax1,
        archivo_antes,
        "ANTES: Cuerdas Vocales Sanas\n(Estructura armónica visible = Líneas)",
    )
    plot_narrowband(
        ax2,
        archivo_despues,
        "DESPUÉS: Post-Cordectomía\n(Pérdida de armónicos = Niebla/Ruido)",
    )

    plt.tight_layout()
    plt.show()
except FileNotFoundError:
    print(
        "¡Ojo! No encontré los archivos. Edita las variables 'archivo_antes' y 'archivo_despues'."
    )
