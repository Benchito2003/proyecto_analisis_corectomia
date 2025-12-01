import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft, fftfreq
from scipy.signal import butter, filtfilt
from pydub import AudioSegment
import os


def load_audio(file_path):
    """Load audio file (mp3, wav, etc.) and convert to numpy array"""
    # Convert mp3 to wav if necessary
    if file_path.lower().endswith(".mp3"):
        audio = AudioSegment.from_mp3(file_path)
        wav_path = file_path.rsplit(".", 1)[0] + "_temp.wav"
        audio.export(wav_path, format="wav")
        sample_rate, data = wavfile.read(wav_path)
        os.remove(wav_path)  # Clean up temp file
    else:
        sample_rate, data = wavfile.read(file_path)

    # Convert stereo to mono if necessary
    if len(data.shape) > 1:
        data = data.mean(axis=1)

    # Normalize to [-1, 1]
    data = data.astype(float) / np.max(np.abs(data))

    return sample_rate, data


def perform_fft(data, sample_rate):
    """Perform FFT on audio data"""
    n = len(data)
    fft_vals = fft(data)
    fft_freq = fftfreq(n, 1 / sample_rate)

    # Only return positive frequencies
    positive_freq_idx = fft_freq > 0
    fft_freq = fft_freq[positive_freq_idx]
    fft_vals = np.abs(fft_vals[positive_freq_idx])

    return fft_freq, fft_vals


def noise_cancelling_filter(
    data, sample_rate, cutoff_low=100, cutoff_high=3000, order=5
):
    """
    Apply a bandpass filter to reduce noise
    cutoff_low: lower frequency bound (Hz)
    cutoff_high: upper frequency bound (Hz)
    """
    nyquist = 0.5 * sample_rate
    low = cutoff_low / nyquist
    high = cutoff_high / nyquist

    # Design Butterworth bandpass filter
    b, a = butter(order, [low, high], btype="band")

    # Apply filter
    filtered_data = filtfilt(b, a, data)

    return filtered_data


def save_audio(file_path, sample_rate, data):
    """Save filtered audio to file"""
    # Denormalize and convert to int16
    data_int = np.int16(data * 32767)
    wavfile.write(file_path, sample_rate, data_int)
    print(f"Filtered audio saved to: {file_path}")


def plot_fft_comparison(freq_orig, fft_orig, freq_filtered, fft_filtered):
    """Plot FFT results side by side"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # Original signal FFT
    ax1.plot(freq_orig, fft_orig, linewidth=0.5)
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Magnitude")
    ax1.set_title("Original Signal FFT")
    ax1.set_xlim(0, 5000)  # Focus on relevant frequency range
    ax1.grid(True, alpha=0.3)

    # Filtered signal FFT
    ax2.plot(freq_filtered, fft_filtered, linewidth=0.5, color="green")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("After Noise Cancelling Filter FFT")
    ax2.set_xlim(0, 5000)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def main(audio_file_path):
    """Main function to process audio"""
    print(f"Loading audio file: {audio_file_path}")

    # Step 1: Import audio file
    sample_rate, original_data = load_audio(audio_file_path)
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Duration: {len(original_data) / sample_rate:.2f} seconds")

    # Step 2: Perform FFT on original audio
    print("\nPerforming FFT on original signal...")
    freq_orig, fft_orig = perform_fft(original_data, sample_rate)

    # Step 3: Apply noise cancelling filter
    print("Applying noise cancelling filter...")
    filtered_data = noise_cancelling_filter(
        original_data, sample_rate, cutoff_low=100, cutoff_high=3000
    )

    # Save filtered audio
    output_path = audio_file_path.rsplit(".", 1)[0] + "_filtered.wav"
    save_audio(output_path, sample_rate, filtered_data)

    # Step 4: Perform FFT on filtered audio
    print("Performing FFT on filtered signal...")
    freq_filtered, fft_filtered = perform_fft(filtered_data, sample_rate)

    # Step 5: Plot comparison
    print("\nGenerating comparison plot...")
    plot_fft_comparison(freq_orig, fft_orig, freq_filtered, fft_filtered)


# Example usage
if __name__ == "__main__":
    # Replace with your audio file path
    audio_file = "your_audio_file.mp3"  # or .wav, .m4a, etc.

    # Check if file exists
    if os.path.exists(audio_file):
        main(audio_file)
    else:
        print(f"Error: File '{audio_file}' not found!")
        print("\nPlease update the 'audio_file' variable with your audio file path.")
