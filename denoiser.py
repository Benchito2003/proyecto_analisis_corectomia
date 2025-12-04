import numpy as np
import scipy.signal
from pydub import AudioSegment
import os
import sys

# --- CONFIGURATION PATHS ---
INPUT_DIR = "/home/yetmontero/Cordec/GFA/OGFiles/AAPre"
OUTPUT_DIR = "/home/yetmontero/Cordec/GFA/VoxAdj"


def load_audio(filepath):
    """Loads audio file and converts to numpy float array."""
    try:
        audio = AudioSegment.from_file(filepath)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None, None, None

    # Convert to mono for processing
    audio_mono = audio.set_channels(1)

    # Get raw data and normalize
    samples = np.array(audio_mono.get_array_of_samples())

    if audio.sample_width == 2:
        samples = samples.astype(np.float32) / 32768.0
    elif audio.sample_width == 4:
        samples = samples.astype(np.float32) / 2147483648.0
    else:
        # Fallback for 8-bit or other widths if necessary
        samples = samples.astype(np.float32) / (2 ** (8 * audio.sample_width - 1))

    return samples, audio.frame_rate, audio


def save_audio(output_path, samples, original_audio):
    """Converts numpy array back to audio file."""
    # Clip to avoid distortion
    samples = np.clip(samples, -1.0, 1.0)

    # Convert back to correct integer format
    if original_audio.sample_width == 2:
        samples_int = (samples * 32767).astype(np.int16)
    elif original_audio.sample_width == 4:
        samples_int = (samples * 2147483647).astype(np.int32)
    else:
        samples_int = (
            samples * (2 ** (8 * original_audio.sample_width - 1) - 1)
        ).astype(np.int32)

    # Create pydub segment
    processed_audio = AudioSegment(
        samples_int.tobytes(),
        frame_rate=original_audio.frame_rate,
        sample_width=original_audio.sample_width,
        channels=1,
    )

    print(f" -> Exporting to {os.path.basename(output_path)}...")
    format_type = output_path.split(".")[-1]
    processed_audio.export(output_path, format=format_type)


def denoise_audio(audio_data, sample_rate):
    """
    Two-Pass Denoising:
    1. Identify noise profile from low-energy segments (VAD).
    2. Apply Statistical Wiener Filter.
    """
    print(" -> Processing: Analyzing noise profile & applying filter...")

    # STFT configuration
    nperseg = 2048
    noverlap = 1536
    freqs, times, Zxx = scipy.signal.stft(
        audio_data, fs=sample_rate, nperseg=nperseg, noverlap=noverlap
    )

    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)

    # --- PASS 1: STATISTICAL NOISE PROFILING ---
    frame_energy = np.sum(magnitude**2, axis=0)

    # Assume bottom 10% is silence/noise
    threshold = np.percentile(frame_energy, 10)
    noise_indices = np.where(frame_energy < threshold)[0]

    if len(noise_indices) == 0:
        noise_profile = np.mean(magnitude, axis=1, keepdims=True)
    else:
        noise_frames = magnitude[:, noise_indices]
        noise_profile = np.mean(noise_frames, axis=1, keepdims=True)

    # --- PASS 2: WIENER FILTERING ---
    psd_noise = noise_profile**2
    psd_signal_noisy = magnitude**2

    alpha = 2.0  # Aggression factor
    estimated_clean_psd = np.maximum(psd_signal_noisy - (alpha * psd_noise), 0)
    wiener_filter = estimated_clean_psd / (estimated_clean_psd + psd_noise + 1e-10)

    clean_magnitude = magnitude * wiener_filter
    Zxx_clean = clean_magnitude * np.exp(1j * phase)

    _, clean_signal = scipy.signal.istft(
        Zxx_clean, fs=sample_rate, nperseg=nperseg, noverlap=noverlap
    )

    return clean_signal


def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating output directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("--- Denoising Tool Initialized ---")
    print(f"Input Directory: {INPUT_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("----------------------------------")

    while True:
        user_input = input(
            "\nEnter filename (e.g., GFA_A1.wav) or 'q' to quit: "
        ).strip()

        if user_input.lower() in ["q", "quit", "exit"]:
            print("Exiting program.")
            break

        if not user_input:
            continue

        # Construct full path
        input_path = os.path.join(INPUT_DIR, user_input)

        if not os.path.exists(input_path):
            print(f"Error: File not found at {input_path}")
            print(
                "Please check the name and extension (e.g., did you forget .wav or .ogg?)"
            )
            continue

        # Load
        raw_data, rate, audio_obj = load_audio(input_path)

        if raw_data is None:
            continue  # Skip loop if load failed

        # Process
        clean_data = denoise_audio(raw_data, rate)

        # Prepare output filenames
        base_name = os.path.splitext(user_input)[0]
        wav_out = os.path.join(OUTPUT_DIR, f"{base_name}_clean.wav")
        mp3_out = os.path.join(OUTPUT_DIR, f"{base_name}_clean.mp3")

        # Export
        save_audio(wav_out, clean_data, audio_obj)
        save_audio(mp3_out, clean_data, audio_obj)

        print(f"Success! {user_input} processed.")


if __name__ == "__main__":
    main()
