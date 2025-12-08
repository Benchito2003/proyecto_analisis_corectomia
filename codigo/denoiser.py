import numpy as np
import scipy.signal
import soundfile as sf
import os
import subprocess
import sys

# --- CONFIGURACIÓN DE RUTAS RELATIVAS ---
# Obtenemos la ruta donde vive ESTE script (denoiser.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definimos las carpetas de entrada y salida RELATIVAS a este script
# Puedes cambiar "Input" y "Output" por los nombres que prefieras
INPUT_DIR = os.path.join(BASE_DIR, "Input")
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")


def load_audio(filepath):
    """Carga el audio directamente a un array de numpy usando soundfile."""
    try:
        data, samplerate = sf.read(filepath)
    except Exception as e:
        print(f"Error cargando archivo: {e}")
        return None, None

    # Si es estéreo, convertir a mono
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    return data, samplerate


def save_audio_wav(output_path, samples, sample_rate):
    """Guarda el array de numpy como WAV."""
    samples = np.clip(samples, -1.0, 1.0)
    print(f" -> Exportando WAV a {os.path.basename(output_path)}...")
    sf.write(output_path, samples, sample_rate)


def convert_to_mp3(wav_path, mp3_path):
    """Convierte WAV a MP3 usando el ffmpeg del sistema."""
    print(f" -> Exportando MP3 a {os.path.basename(mp3_path)}...")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", mp3_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print(" [ERROR] ffmpeg no encontrado. Instálalo con: sudo pacman -S ffmpeg")
    except Exception as e:
        print(f" [ERROR] Falló conversión MP3: {e}")


def denoise_audio(audio_data, sample_rate):
    """
    Algoritmo de reducción de ruido (Dos Pasos).
    """
    print(" -> Procesando: Analizando perfil de ruido y filtrando...")

    nperseg = 2048
    noverlap = 1536
    freqs, times, Zxx = scipy.signal.stft(
        audio_data, fs=sample_rate, nperseg=nperseg, noverlap=noverlap
    )

    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)

    # --- PASO 1: PERFILADO DE RUIDO ---
    frame_energy = np.sum(magnitude**2, axis=0)
    # Asumimos que el 10% con menos energía es ruido
    threshold = np.percentile(frame_energy, 10)
    noise_indices = np.where(frame_energy < threshold)[0]

    if len(noise_indices) == 0:
        noise_profile = np.mean(magnitude, axis=1, keepdims=True)
    else:
        noise_frames = magnitude[:, noise_indices]
        noise_profile = np.mean(noise_frames, axis=1, keepdims=True)

    # --- PASO 2: FILTRO WIENER ---
    psd_noise = noise_profile**2
    psd_signal_noisy = magnitude**2

    alpha = 2.0
    estimated_clean_psd = np.maximum(psd_signal_noisy - (alpha * psd_noise), 0)
    wiener_filter = estimated_clean_psd / (estimated_clean_psd + psd_noise + 1e-10)

    clean_magnitude = magnitude * wiener_filter
    Zxx_clean = clean_magnitude * np.exp(1j * phase)

    _, clean_signal = scipy.signal.istft(
        Zxx_clean, fs=sample_rate, nperseg=nperseg, noverlap=noverlap
    )

    return clean_signal


def main():
    # Asegurar que las carpetas existan
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f" [AVISO] Se creó la carpeta de entrada en: {INPUT_DIR}")
        print(" -> Por favor, coloca tus archivos .wav ahí y reinicia el programa.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f" [INFO] Carpeta de salida creada en: {OUTPUT_DIR}")

    print("--- Denoising Tool (Portable & Py3.13) ---")
    print(f"Directorio Entrada: {INPUT_DIR}")
    print(f"Directorio Salida:  {OUTPUT_DIR}")
    print("------------------------------------------")

    # Listar archivos disponibles automáticamente
    archivos = [
        f
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".wav", ".ogg", ".flac"))
    ]

    if not archivos:
        print(" [!] No hay archivos de audio en la carpeta 'Input'.")
        return

    print("Archivos disponibles:")
    for i, f in enumerate(archivos):
        print(f" {i + 1}. {f}")

    while True:
        user_input = input(
            "\nEscribe el nombre del archivo (o 'q' para salir): "
        ).strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            break

        if not user_input:
            continue

        # Permitir seleccionar por número o nombre
        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(archivos):
                user_input = archivos[idx]
            else:
                print("Número inválido.")
                continue

        input_path = os.path.join(INPUT_DIR, user_input)

        if not os.path.exists(input_path):
            # Intentar añadir extensión si falta
            if os.path.exists(input_path + ".wav"):
                input_path += ".wav"
                user_input += ".wav"
            else:
                print(f"Error: No se encuentra '{user_input}' en la carpeta Input.")
                continue

        # Cargar
        raw_data, rate = load_audio(input_path)
        if raw_data is None:
            continue

        # Procesar
        clean_data = denoise_audio(raw_data, rate)

        # Guardar
        base_name = os.path.splitext(user_input)[0]
        wav_out = os.path.join(OUTPUT_DIR, f"{base_name}_clean.wav")
        mp3_out = os.path.join(OUTPUT_DIR, f"{base_name}_clean.mp3")

        save_audio_wav(wav_out, clean_data, rate)
        convert_to_mp3(wav_out, mp3_out)

        print(f"¡Éxito! Procesado: {user_input}")


if __name__ == "__main__":
    main()
