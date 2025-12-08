import sys
import types
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import pandas as pd
import subprocess

# --- PARCHE DE SEGURIDAD PYTHON 3.13 ---
# Bloqueamos cualquier intento de librerías antiguas de buscar módulos eliminados
# (aifc, chunk, sunau, etc.)
modulos_eliminados = ["aifc", "chunk", "sunau"]
for mod in modulos_eliminados:
    try:
        __import__(mod)
    except ImportError:
        sys.modules[mod] = types.ModuleType(mod)
# ---------------------------------------

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = "/home/yetmontero/Cordec/GFA"

DIR_ESP = os.path.join(BASE_DIR, "Recursos/ESP")
DIR_GRA = os.path.join(BASE_DIR, "Recursos/GRA")
DIR_CSV = os.path.join(BASE_DIR, "Datum/CSV")
DIR_TXT = os.path.join(BASE_DIR, "Datum/TXT")

for d in [DIR_ESP, DIR_GRA, DIR_CSV, DIR_TXT]:
    os.makedirs(d, exist_ok=True)


def buscar_archivo_recursivo(nombre_archivo):
    print(f"   [?] Buscando '{nombre_archivo}'...")
    pattern = os.path.join(BASE_DIR, "**", nombre_archivo)
    files = glob.glob(pattern, recursive=True)
    if files:
        print(f"      [OK] Encontrado: {files[0]}")
        return files[0]
    return None


def convertir_a_wav_seguro(ruta_origen):
    """
    Convierte a WAV usando FFMPEG directamente en la shell.
    Esto evita que Python intente abrir formatos complejos con módulos viejos.
    """
    if ruta_origen.lower().endswith(".wav"):
        return ruta_origen, False

    nombre_base = os.path.basename(ruta_origen)
    ruta_temp = os.path.join(os.path.dirname(ruta_origen), f"temp_{nombre_base}.wav")

    # Si ya existe un temp de una ejecución fallida anterior, lo usamos/sobreescribimos
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", ruta_origen, "-ar", "44100", ruta_temp],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return ruta_temp, True
    except FileNotFoundError:
        print(
            "      [CRÍTICO] No se encontró el comando 'ffmpeg'. Instálalo con: sudo pacman -S ffmpeg"
        )
        return None, False
    except subprocess.CalledProcessError:
        print("      [ERROR] FFMPEG no pudo convertir el archivo (¿Archivo corrupto?).")
        return None, False


def procesar_fft(ruta_archivo, nombre_display):
    ruta_wav = None
    es_temporal = False

    try:
        # 1. Conversión externa (Bypassea errores de Python 3.13)
        ruta_wav, es_temporal = convertir_a_wav_seguro(ruta_archivo)

        if not ruta_wav:
            return None, None, None, None, None

        # 2. Cargar WAV (Nativo y seguro)
        y, sr = librosa.load(ruta_wav, sr=None)

        # 3. FFT
        D = librosa.stft(y)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        mag_promedio = np.mean(S_db, axis=1)
        freqs = librosa.fft_frequencies(sr=sr)

        return freqs, mag_promedio, S_db, sr, y

    except Exception as e:
        print(f"      [ERROR] Excepción inesperada: {e}")
        return None, None, None, None, None

    finally:
        # 4. Limpieza
        if es_temporal and ruta_wav and os.path.exists(ruta_wav):
            os.remove(ruta_wav)


def exportar_datos_clean(nombre_base, freqs, mag):
    df = pd.DataFrame({"Frecuencia_Hz": freqs, "Magnitud_dB": mag})
    nombre_salida = f"DB-{os.path.splitext(nombre_base)[0]}"

    # Exportar
    df.to_csv(os.path.join(DIR_CSV, f"{nombre_salida}.csv"), index=False)
    df.to_csv(os.path.join(DIR_TXT, f"{nombre_salida}.txt"), sep="\t", index=False)
    print(f"   -> Datos exportados en Datum/CSV y TXT")


def generar_grafica_comparativa(lista_datos, nombres_archivos):
    plt.figure(figsize=(14, 8))

    # Subplot 1
    ax1 = plt.subplot(2, 1, 1)
    colores = ["#77aadd", "#88cc88", "#ee8866", "#eedd88", "#aaaaff"]
    min_len = min([d["mag"].shape[0] for d in lista_datos])
    freqs = lista_datos[0]["freqs"][:min_len]

    for i, d in enumerate(lista_datos):
        ax1.plot(
            freqs,
            d["mag"][:min_len],
            label=nombres_archivos[i],
            color=colores[i % 5],
            linewidth=2,
            alpha=0.9,
        )

    # Diferencia
    if len(lista_datos) == 2:
        diff = lista_datos[0]["mag"][:min_len] - lista_datos[1]["mag"][:min_len]
        ax1.plot(
            freqs,
            diff,
            label="Diferencia (Target)",
            color="#cc3333",
            linestyle="--",
            linewidth=2,
        )

    ax1.set_title("Análisis Espectral Comparativo")
    ax1.set_ylabel("Magnitud (dB)")
    ax1.set_xlim(0, 6000)
    ax1.legend()
    ax1.grid(alpha=0.3)

    # Subplot 2
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    if len(lista_datos) > 1:
        for i in range(1, len(lista_datos)):
            diff = lista_datos[0]["mag"][:min_len] - lista_datos[i]["mag"][:min_len]
            ax2.plot(
                freqs,
                diff,
                label=f"Diff: {nombres_archivos[0]} - {nombres_archivos[i]}",
            )
        ax2.axhline(0, color="k", linewidth=0.8)

    ax2.set_xlabel("Frecuencia (Hz)")
    ax2.set_ylabel("Dif (dB)")
    ax2.legend()
    ax2.grid(alpha=0.3)

    nombre_out = "-".join([os.path.splitext(n)[0] for n in nombres_archivos])
    if len(nombre_out) > 50:
        nombre_out = nombre_out[:50]

    plt.tight_layout()
    plt.savefig(os.path.join(DIR_GRA, f"Grafica({nombre_out}).png"), dpi=150)
    plt.close()
    print(f"   -> Gráfica guardada.")


def generar_pdf(d1, d2, n1, n2):
    plt.figure(figsize=(10, 12))

    for i, (d, n) in enumerate([(d1, n1), (d2, n2)]):
        plt.subplot(3, 1, i + 1)
        librosa.display.specshow(d["S_db"], sr=d["sr"], x_axis="time", y_axis="hz")
        plt.colorbar(format="%+2.0f dB")
        plt.title(f"Espectrograma: {n}")
        plt.ylim(0, 8000)

    # Diferencial
    h = min(d1["S_db"].shape[0], d2["S_db"].shape[0])
    w = min(d1["S_db"].shape[1], d2["S_db"].shape[1])
    diff = d1["S_db"][:h, :w] - d2["S_db"][:h, :w]

    plt.subplot(3, 1, 3)
    librosa.display.specshow(
        diff, sr=d1["sr"], x_axis="time", y_axis="hz", cmap="coolwarm"
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title(f"Diferencial ({n1} - {n2})")
    plt.ylim(0, 8000)

    n1c = os.path.splitext(n1)[0]
    n2c = os.path.splitext(n2)[0]
    plt.tight_layout()
    plt.savefig(os.path.join(DIR_ESP, f"Espectro({n1c}-{n2c}).pdf"))
    plt.close()
    print(f"   -> PDF guardado.")


def main():
    print(f"=== Cordec Analyzer (ULTIMATE - Py3.13 Fix) ===\nBase: {BASE_DIR}")
    while True:
        entrada = input("\nArchivos (sep. por coma) o 'Q': ")
        if entrada.strip().upper() == "Q":
            break

        nombres = [n.strip() for n in entrada.split(",")]
        if len(nombres) < 2:
            print("Se requieren 2+ archivos.")
            continue

        datos = []
        nombres_validos = []

        for n in nombres:
            ruta = buscar_archivo_recursivo(n)
            if ruta:
                f, m, s, sr, y = procesar_fft(ruta, n)
                if f is not None:
                    datos.append(
                        {"freqs": f, "mag": m, "S_db": s, "sr": sr, "nombre": n}
                    )
                    nombres_validos.append(n)
                    if "_clean" in n:
                        exportar_datos_clean(n, f, m)

        if len(datos) >= 2:
            generar_grafica_comparativa(datos, nombres_validos)
            if len(datos) == 2:
                generar_pdf(datos[0], datos[1], nombres_validos[0], nombres_validos[1])
        else:
            print("Insuficientes archivos procesados.")


if __name__ == "__main__":
    main()

