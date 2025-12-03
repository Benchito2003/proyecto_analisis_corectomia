import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import pandas as pd

# --- CONFIGURACIÓN DE RUTAS ---
# Usamos ruta absoluta para evitar ambigüedades
BASE_DIR = "/home/yetmontero/Cordec/GFA"

# Definimos carpetas de salida específicas
DIR_ESP = os.path.join(BASE_DIR, "Recursos/ESP")
DIR_GRA = os.path.join(BASE_DIR, "Recursos/GRA")
DIR_CSV = os.path.join(BASE_DIR, "Datum/CSV")
DIR_TXT = os.path.join(BASE_DIR, "Datum/TXT")

# Crear directorios de salida si no existen
for d in [DIR_ESP, DIR_GRA, DIR_CSV, DIR_TXT]:
    os.makedirs(d, exist_ok=True)


def buscar_archivo_recursivo(nombre_archivo):
    """
    Busca el archivo en TODA la carpeta BASE_DIR y sus subcarpetas.
    Equivalente a hacer un 'find' o 'ls -R'.
    """
    print(f"   [?] Buscando '{nombre_archivo}' en todo GFA...")

    # El patrón ** indica búsqueda recursiva
    pattern = os.path.join(BASE_DIR, "**", nombre_archivo)

    # recursive=True permite buscar en subdirectorios
    files = glob.glob(pattern, recursive=True)

    if files:
        # Retornamos el primero encontrado y mostramos dónde estaba
        print(f"      [OK] Encontrado: {files[0]}")
        return files[0]
    else:
        print(f"      [X] No encontrado en ninguna subcarpeta de GFA.")
        return None


def procesar_fft(ruta_archivo):
    """Carga audio y calcula la FFT (Magnitud en dB promedio)."""
    try:
        # Cargar audio (sr=None preserva el sampling rate original)
        y, sr = librosa.load(ruta_archivo, sr=None)

        # Calcular STFT
        D = librosa.stft(y)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

        # Promediar en el tiempo
        mag_promedio = np.mean(S_db, axis=1)
        freqs = librosa.fft_frequencies(sr=sr)

        return freqs, mag_promedio, S_db, sr, y
    except Exception as e:
        print(f"      [ERROR] Fallo al procesar audio: {e}")
        return None, None, None, None, None


def exportar_datos_clean(nombre_base, freqs, mag):
    """Exporta a CSV y TXT si es un archivo _clean."""
    df = pd.DataFrame({"Frecuencia_Hz": freqs, "Magnitud_dB": mag})

    nombre_salida = f"DB-{os.path.splitext(nombre_base)[0]}"

    # Exportar CSV
    csv_path = os.path.join(DIR_CSV, f"{nombre_salida}.csv")
    df.to_csv(csv_path, index=False)
    print(f"   -> Datos exportados a CSV: {csv_path}")

    # Exportar TXT
    txt_path = os.path.join(DIR_TXT, f"{nombre_salida}.txt")
    df.to_csv(txt_path, sep="\t", index=False)
    print(f"   -> Datos exportados a TXT: {txt_path}")


def generar_grafica_comparativa(lista_datos, nombres_archivos):
    """Genera la gráfica de líneas superpuestas y diferencias."""
    plt.figure(figsize=(14, 8))

    # --- SUBPLOT 1: Superposición ---
    ax1 = plt.subplot(2, 1, 1)
    colores = ["#77aadd", "#88cc88", "#ee8866", "#eedd88", "#aaaaff"]

    # Normalizar longitud de arrays para operaciones matemáticas
    min_len = min([d["mag"].shape[0] for d in lista_datos])
    freqs_comunes = lista_datos[0]["freqs"][:min_len]

    # Graficar señales
    for i, datos in enumerate(lista_datos):
        mag_recortada = datos["mag"][:min_len]
        ax1.plot(
            freqs_comunes,
            mag_recortada,
            label=nombres_archivos[i],
            color=colores[i % len(colores)],
            linewidth=2,
            alpha=0.9,
        )

    # Calcular diferencias (Target = primero en la lista)
    mag_ref = lista_datos[0]["mag"][:min_len]

    if len(lista_datos) == 2:
        mag_sec = lista_datos[1]["mag"][:min_len]
        diferencia = mag_ref - mag_sec
        ax1.plot(
            freqs_comunes,
            diferencia,
            label="Diferencia (Target)",
            color="#cc3333",
            linestyle="--",
            linewidth=2,
        )

    ax1.set_title("Análisis Espectral Comparativo")
    ax1.set_ylabel("Magnitud (dB)")
    ax1.set_xlim(0, 6000)
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend()

    # --- SUBPLOT 2: Diferencias Aisladas ---
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)

    if len(lista_datos) > 1:
        for i in range(1, len(lista_datos)):
            mag_actual = lista_datos[i]["mag"][:min_len]
            diff = mag_ref - mag_actual
            label_diff = f"Diff: {nombres_archivos[0]} - {nombres_archivos[i]}"
            ax2.plot(freqs_comunes, diff, label=label_diff, linewidth=1.5)

        ax2.axhline(0, color="black", linewidth=0.8, linestyle="-")

    ax2.set_xlabel("Frecuencia (Hz)")
    ax2.set_ylabel("Diferencia (dB)")
    ax2.grid(True, which="both", alpha=0.3)
    ax2.legend()

    # Nombre del archivo de salida
    nombre_join = "-".join([os.path.splitext(n)[0] for n in nombres_archivos])
    if len(nombre_join) > 60:
        nombre_join = nombre_join[:60] + "..."

    ruta_salida = os.path.join(DIR_GRA, f"Grafica({nombre_join}).png")
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150)
    plt.close()
    print(f"   -> Gráfica guardada en: {ruta_salida}")


def generar_pdf_espectrograma(datos1, datos2, nombre1, nombre2):
    """Genera PDF con espectrogramas."""
    plt.figure(figsize=(10, 12))

    # Plot 1
    plt.subplot(3, 1, 1)
    librosa.display.specshow(
        datos1["S_db"], sr=datos1["sr"], x_axis="time", y_axis="hz"
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title(f"Espectrograma: {nombre1}")
    plt.ylim(0, 8000)

    # Plot 2
    plt.subplot(3, 1, 2)
    librosa.display.specshow(
        datos2["S_db"], sr=datos2["sr"], x_axis="time", y_axis="hz"
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title(f"Espectrograma: {nombre2}")
    plt.ylim(0, 8000)

    # Plot Diferencia
    len_t = min(datos1["S_db"].shape[1], datos2["S_db"].shape[1])
    len_f = min(datos1["S_db"].shape[0], datos2["S_db"].shape[0])

    spec1 = datos1["S_db"][:len_f, :len_t]
    spec2 = datos2["S_db"][:len_f, :len_t]
    diff_spec = spec1 - spec2

    plt.subplot(3, 1, 3)
    librosa.display.specshow(
        diff_spec, sr=datos1["sr"], x_axis="time", y_axis="hz", cmap="coolwarm"
    )
    plt.colorbar(format="%+2.0f dB")
    plt.title(f"Diferencial ({nombre1} - {nombre2})")
    plt.ylim(0, 8000)

    n1_clean = os.path.splitext(nombre1)[0]
    n2_clean = os.path.splitext(nombre2)[0]
    ruta_pdf = os.path.join(DIR_ESP, f"Espectro({n1_clean}-{n2_clean}).pdf")

    plt.tight_layout()
    plt.savefig(ruta_pdf)
    plt.close()
    print(f"   -> PDF Espectral guardado en: {ruta_pdf}")


def main():
    print("=== Herramienta de Análisis Cordec (Búsqueda Recursiva) ===")
    print(f"Directorio Base: {BASE_DIR}")

    while True:
        entrada = input("\nIntroduce archivos (sep. por coma) o 'Q' para salir: ")
        if entrada.strip().upper() == "Q":
            break

        nombres = [n.strip() for n in entrada.split(",")]
        if len(nombres) < 2:
            print("Error: Se requieren al menos dos archivos para comparar.")
            continue

        datos_procesados = []
        archivos_validos = []

        for nombre in nombres:
            # USAR NUEVA FUNCIÓN DE BÚSQUEDA RECURSIVA
            ruta = buscar_archivo_recursivo(nombre)

            if ruta:
                freqs, mag, S_db, sr, y = procesar_fft(ruta)

                if freqs is not None:
                    datos_procesados.append(
                        {
                            "freqs": freqs,
                            "mag": mag,
                            "S_db": S_db,
                            "sr": sr,
                            "nombre": nombre,
                        }
                    )
                    archivos_validos.append(nombre)

                    # Detectar _clean para exportar
                    if "_clean" in nombre:
                        exportar_datos_clean(nombre, freqs, mag)
            else:
                pass  # El mensaje de error ya se imprime en buscar_archivo

        if len(datos_procesados) >= 2:
            generar_grafica_comparativa(datos_procesados, archivos_validos)
            if len(datos_procesados) == 2:
                generar_pdf_espectrograma(
                    datos_procesados[0],
                    datos_procesados[1],
                    archivos_validos[0],
                    archivos_validos[1],
                )
        else:
            print("No se encontraron suficientes archivos válidos.")


if __name__ == "__main__":
    main()
