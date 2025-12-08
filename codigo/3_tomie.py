import os
import glob
import numpy as np
import scipy.signal
import soundfile as sf
from scipy.interpolate import interp1d

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Leemos de Input (WAVs limpios)
DIR_INPUT = os.path.join(BASE_DIR, "..", "data", "1_input")
# Guardamos en Output (Resultados finales)
DIR_OUTPUT = os.path.join(BASE_DIR, "..", "data", "2_output")

# Parámetros de Procesamiento de Señal
FS_TARGET = 44100  # Frecuencia de muestreo estándar
N_FFT = 2048  # Tamaño de ventana para STFT
HOP_LEN = 512  # Salto entre ventanas


def cargar_audio(ruta):
    try:
        data, samplerate = sf.read(ruta)
        # Forzar mono y resampling simple si no coincide (aunque normalizar.py ya lo hizo)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        return data, samplerate
    except Exception as e:
        print(f"[ERROR] No se pudo leer {ruta}: {e}")
        return None, None


def calcular_perfil_espectral(data, fs):
    """
    Calcula el perfil de energía promedio (PSD) de un audio.
    Nos dice 'cuánta energía hay en cada frecuencia' en promedio.
    """
    freqs, psd = scipy.signal.welch(data, fs, nperseg=N_FFT)
    # Convertir a dB, con protección contra log(0)
    psd_db = 10 * np.log10(psd + 1e-12)
    return freqs, psd_db


def suavizar_curva(curva):
    """
    Aplica filtro Savitzky-Golay para evitar picos bruscos que suenen robóticos.
    """
    window_length = 51  # Debe ser impar
    polyorder = 3
    if len(curva) < window_length:
        window_length = len(curva) // 2 * 2 + 1
    return scipy.signal.savgol_filter(curva, window_length, polyorder)


def aplicar_restauracion(archivo_sano, archivo_enfermo):
    print(f"\n--- Iniciando Restauración ---")
    print(f"Ref (Sano):    {os.path.basename(archivo_sano)}")
    print(f"Target (Post): {os.path.basename(archivo_enfermo)}")

    # 1. Cargar Audios
    y_ref, sr_ref = cargar_audio(archivo_sano)
    y_tgt, sr_tgt = cargar_audio(archivo_enfermo)

    if y_ref is None or y_tgt is None:
        return

    # 2. Calcular la Máscara de Transferencia (La "Diferencia")
    print(" -> Calculando perfiles espectrales...")
    f_ref, psd_ref = calcular_perfil_espectral(y_ref, sr_ref)
    f_tgt, psd_tgt = calcular_perfil_espectral(y_tgt, sr_tgt)

    # Interpolar para asegurar que las frecuencias coincidan exáctamente
    interp_func = interp1d(f_tgt, psd_tgt, kind="linear", fill_value="extrapolate")
    psd_tgt_aligned = interp_func(f_ref)

    # Calcular diferencia (Sano - Enfermo)
    # Si es positivo, falta energía en el enfermo. Si es negativo, sobra.
    raw_mask_db = psd_ref - psd_tgt_aligned

    # Suavizar la máscara (Clave para sonido natural)
    smooth_mask_db = suavizar_curva(raw_mask_db)

    # Limitar la ganancia máxima (Para no romper los tímpanos ni saturar)
    smooth_mask_db = np.clip(smooth_mask_db, -10, 20)  # Máx 20dB de boost

    print(" -> Aplicando corrección espectral (STFT)...")

    # 3. Aplicar al audio enfermo usando STFT
    # Convertimos audio a frecuencias (Tiempo x Frecuencia)
    f_stft, t_stft, Zxx = scipy.signal.stft(
        y_tgt, fs=sr_tgt, nperseg=N_FFT, noverlap=N_FFT - HOP_LEN
    )

    # Crear interpolador para mapear nuestra máscara a las frecuencias de la STFT
    mask_interpolator = interp1d(
        f_ref, smooth_mask_db, kind="linear", fill_value="extrapolate"
    )
    gain_db_per_freq = mask_interpolator(f_stft)

    # Convertir dB a Ganancia Lineal (Amplitud)
    # Gain = 10 ^ (dB / 20)
    gain_linear = 10 ** (gain_db_per_freq / 20.0)

    # Expandir dimensiones para multiplicar la matriz STFT
    # Zxx tiene forma (Frecuencias, Tiempo). Gain es (Frecuencias).
    # Necesitamos multiplicar cada columna de tiempo por el vector de ganancia.
    Zxx_restored = Zxx * gain_linear[:, np.newaxis]

    # 4. Reconstruir audio (ISTFT)
    _, y_restored = scipy.signal.istft(
        Zxx_restored, fs=sr_tgt, nperseg=N_FFT, noverlap=N_FFT - HOP_LEN
    )

    # 5. Guardar
    nombre_base = os.path.splitext(os.path.basename(archivo_enfermo))[0]
    ruta_salida = os.path.join(DIR_OUTPUT, f"{nombre_base}_RESTAURADO.wav")

    sf.write(ruta_salida, y_restored, sr_tgt)
    print(f" [EXITO] Audio restaurado guardado en:\n    {ruta_salida}")


def main():
    if not os.path.exists(DIR_OUTPUT):
        os.makedirs(DIR_OUTPUT)

    print("--- 3_TOMIE.PY: Restauración Espectral ---")
    wavs = sorted(glob.glob(os.path.join(DIR_INPUT, "*.wav")))

    if len(wavs) < 2:
        print("[ERROR] Necesito al menos 2 audios en 'data/1_input'.")
        return

    print("Selecciona los archivos:")
    for i, w in enumerate(wavs):
        print(f" [{i}] {os.path.basename(w)}")

    try:
        idx_ref = int(input("\n1. Selecciona el audio SANO (Referencia): "))
        idx_tgt = int(input("2. Selecciona el audio ENFERMO (A restaurar): "))

        aplicar_restauracion(wavs[idx_ref], wavs[idx_tgt])

    except (ValueError, IndexError):
        print("[ERROR] Selección inválida.")


if __name__ == "__main__":
    main()
