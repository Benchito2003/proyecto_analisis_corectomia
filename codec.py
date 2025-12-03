import os
import re
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import soundfile as sf
import pandas as pd
import subprocess
import noisereduce as nr  # NECESARIO: pip install noisereduce
from scipy import signal
from matplotlib.backends.backend_pdf import PdfPages

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
ROOT_PATH = "/home/elchino/Escritorio/proyecto-analisis"


def configurar_rutas(codigo_paciente):
    base_paciente = os.path.join(ROOT_PATH, codigo_paciente)
    rutas = {
        "base": base_paciente,
        "wav": os.path.join(base_paciente, "Rex", "WAV"),
        "mp3": os.path.join(base_paciente, "Rex", "MP3"),
        "gra": os.path.join(base_paciente, "Rex", "GRA"),
        "txt": os.path.join(base_paciente, "Datum", "TXT"),
        "csv": os.path.join(base_paciente, "Datum", "CSV"),
        "pre_source": os.path.join(base_paciente, "OGFiles", "AAPre"),
        "post_source": os.path.join(base_paciente, "OGFiles", "BBPost"),
    }
    for key, path in rutas.items():
        if key not in ["pre_source", "post_source"]:
            os.makedirs(path, exist_ok=True)
    return rutas


# ==========================================
# 2. INTELIGENCIA DE METADATOS (Nomenclatura)
# ==========================================


def extraer_metadatos(nombre_archivo):
    """
    Analiza nombres como: GFA_MA3.opus o GFA_FAA16.opus
    Retorna:
    - Paciente: GFA
    - Genero: M, F o N
    - Categoria: Pre (A) o Post (B)
    - NivelRuido: 1 (Bajo, una letra) o 2 (Alto, dos letras AA/BB)
    - SufijoCompleto: MA3
    """
    base = os.path.splitext(nombre_archivo)[0]
    partes = base.split("_")

    if len(partes) < 2:
        return None  # Formato incorrecto

    paciente = partes[0]
    sufijo_raw = partes[1]  # Ej: MA3, FAA16

    # Regex para desglosar el sufijo:
    # Grupo 1: Genero (M, F, N)
    # Grupo 2: Tipo y Ruido (A, AA, B, BB...)
    # Grupo 3: Numero (3, 16...)
    patron = re.match(r"([MFN])([AB]+)(\d+)", sufijo_raw.upper())

    if not patron:
        return None

    genero = patron.group(1)
    letras_tipo = patron.group(2)  # Ej: A, AA, B, BBB
    numero = patron.group(3)

    # Lógica de Categoría (Pre/Post)
    if "A" in letras_tipo:
        categoria = "Pre"
    elif "B" in letras_tipo:
        categoria = "Post"
    else:
        categoria = "Unknown"

    # Lógica de Nivel de Ruido (Tamizaje empírico)
    # Si tiene más de 1 letra (AA, BB), es "Alto Ruido"
    nivel_ruido = "Alto" if len(letras_tipo) > 1 else "Bajo"

    return {
        "paciente": paciente,
        "genero": genero,
        "categoria": categoria,
        "nivel_ruido": nivel_ruido,
        "sufijo_completo": sufijo_raw,
        "identificador_unico": f"{paciente}({sufijo_raw})",
    }


def generar_nombres_salida(meta1, meta2=None):
    if meta2:
        # DB-GFA(MA3-MB1)
        id_str = f"{meta1['paciente']}({meta1['sufijo_completo']}-{meta2['sufijo_completo']})"
    else:
        # DB-GFA(MA3)
        id_str = meta1["identificador_unico"]

    return {
        "grafica": f"GRA-{id_str}.pdf",
        "tabla": f"DB-{id_str}",
        "audio_prefijo": "ENH",
    }


# ==========================================
# 3. PROCESAMIENTO DE SEÑAL AVANZADO
# ==========================================


def cargar_audio_ffmpeg(ruta_archivo, sr=44100):
    """Carga segura anti-fallos para Arch Linux"""
    if not os.path.exists(ruta_archivo):
        return None, None
    temp_wav = f"temp_{os.getpid()}_{np.random.randint(1000)}.wav"
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            ruta_archivo,
            "-ar",
            str(sr),
            "-ac",
            "1",
            "-loglevel",
            "quiet",
            temp_wav,
        ]
        subprocess.run(cmd, check=True)
        y, s_rate = sf.read(temp_wav)
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        return y, s_rate
    except Exception as e:
        print(f"   [ERROR CRÍTICO AUDIO]: {e}")
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        return None, None


def limpieza_avanzada(y, sr, genero, nivel_ruido):
    """
    ALGORITMO DE FASE 1 MEJORADO:
    1. Filtro Pasa-Banda según Género (Aísla la voz humana).
    2. Reducción de Ruido Estacionario Adaptativa (Según nivel AA/A).
    """

    # --- PASO 1: DEFINIR RANGOS DE FRECUENCIA POR GÉNERO ---
    # Los hombres tienen fundamentales más graves, las mujeres/niños más agudas.
    # Recortamos lo que está fuera para quitar "rumble" de carros y silbidos.
    if genero == "M":
        freq_min, freq_max = 70, 7000  # Rango amplio voz masculina
    elif genero == "F":
        freq_min, freq_max = 100, 8000  # Rango voz femenina
    else:  # Neutro
        freq_min, freq_max = 65, 8000  # Rango conservador

    # Filtro Butterworth Pasa-Banda (Band-Pass)
    sos = signal.butter(10, [freq_min, freq_max], "bp", fs=sr, output="sos")
    y_bandpass = signal.sosfilt(sos, y)

    # --- PASO 2: REDUCCIÓN DE RUIDO INTELIGENTE (NOISEREDUCE) ---
    # Utilizamos Stationary Noise Reduction.
    # Si el archivo es 'Alto' (AA), somos más agresivos.

    if nivel_ruido == "Alto":
        # Configuración agresiva para salvar audios sucios (AA)
        prop_decrease = 0.90  # Eliminar el 90% del ruido detectado
        n_std_thresh = 1.5  # Umbral más estricto
        time_constant = 2.0  # Tiempo de suavizado
    else:
        # Configuración suave para audios limpios (A)
        prop_decrease = 0.60  # Eliminar solo el 60% (preserva aire natural)
        n_std_thresh = 2.0  # Umbral estándar
        time_constant = 0.5

    # Aplicamos reducción de ruido sobre la señal ya filtrada por banda
    # Usamos n_jobs=1 para evitar conflictos en scripts simples
    try:
        y_clean = nr.reduce_noise(
            y=y_bandpass,
            sr=sr,
            prop_decrease=prop_decrease,
            stationary=True,  # Asume ruido constante (ventiladores, motores lejanos)
            n_std_thresh_stationary=n_std_thresh,
            time_constant_s=time_constant,
        )
    except Exception as e:
        print(
            f"   [ADVERTENCIA] Falló noisereduce, usando solo filtro banda. Error: {e}"
        )
        y_clean = y_bandpass

    # --- PASO 3: NORMALIZACIÓN ---
    # Importante para que todos los audios tengan el mismo "volumen" relativo en la DB
    max_val = np.max(np.abs(y_clean))
    if max_val > 0:
        y_final = y_clean / max_val * 0.95
    else:
        y_final = y_clean

    return y_final


def exportar_audios(y, sr, nombre_original, rutas):
    """Guarda ENH-{nombre}"""
    nombre_salida = f"ENH-{os.path.splitext(nombre_original)[0]}"
    ruta_wav = os.path.join(rutas["wav"], f"{nombre_salida}.wav")
    ruta_mp3 = os.path.join(rutas["mp3"], f"{nombre_salida}.mp3")
    sf.write(ruta_wav, y, sr)
    cmd = f"ffmpeg -y -i '{ruta_wav}' -codec:a libmp3lame -qscale:a 2 '{ruta_mp3}' -loglevel quiet"
    os.system(cmd)


def obtener_espectro(y, sr, n_fft=4096):
    D = librosa.stft(y, n_fft=n_fft)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    return librosa.fft_frequencies(sr=sr, n_fft=n_fft), np.mean(S_db, axis=1)


# ==========================================
# 4. MOTOR PRINCIPAL
# ==========================================


def procesar_archivos(archivos_input, rutas):
    datos = []

    # --- FASE A: PROCESAMIENTO ---
    for nombre in archivos_input:
        meta = extraer_metadatos(nombre)
        if not meta:
            print(f"   [ERROR] Formato de nombre inválido: {nombre}")
            return

        # Buscar archivo
        rutas_posibles = [
            os.path.join(rutas["pre_source"], nombre),
            os.path.join(rutas["post_source"], nombre),
            os.path.join(rutas["base"], nombre),
        ]
        ruta_final = next((r for r in rutas_posibles if os.path.exists(r)), None)

        if not ruta_final:
            print(f"   [ERROR] No encontrado: {nombre}")
            return

        print(f"   -> Procesando: {nombre}")
        print(
            f"      [Metadatos] Género: {meta['genero']} | Ruido: {meta['nivel_ruido']} | Tipo: {meta['categoria']}"
        )

        # 1. Cargar
        y, sr = cargar_audio_ffmpeg(ruta_final)
        if y is None:
            return

        # 2. LIMPIEZA AVANZADA (Aquí ocurre la magia)
        y_clean = limpieza_avanzada(y, sr, meta["genero"], meta["nivel_ruido"])

        # 3. Exportar Audio
        exportar_audios(y_clean, sr, nombre, rutas)

        # 4. Obtener Datos Espectrales
        freqs, mag_orig = obtener_espectro(y, sr)

        # CRUCIAL: Estos son los datos que irán a la DB.
        # Estamos asegurando que la DB contenga la señal FILTRADA.
        _, mag_clean = obtener_espectro(y_clean, sr)

        datos.append(
            {
                "meta": meta,
                "nombre": nombre,
                "freqs": freqs,
                "mag_orig": mag_orig,
                "mag_clean": mag_clean,  # Esta es la señal limpia
            }
        )

    # --- FASE B: RESULTADOS (Gráficas y Tablas) ---
    if len(datos) == 2:
        info = generar_nombres_salida(datos[0]["meta"], datos[1]["meta"])
    else:
        info = generar_nombres_salida(datos[0]["meta"])

    # 1. Generar PDF
    ruta_pdf = os.path.join(rutas["gra"], info["grafica"])
    with PdfPages(ruta_pdf) as pdf:
        fig = plt.figure(figsize=(12, 16))
        plt.rcParams.update({"font.size": 9})

        # Gráficas individuales
        for i, d in enumerate(datos):
            ax = plt.subplot2grid((3, 1), (i, 0))
            ax.plot(
                d["freqs"],
                d["mag_orig"],
                color="gray",
                alpha=0.3,
                label="Original (Sucio)",
            )
            color = "#1f77b4" if d["meta"]["categoria"] == "Pre" else "#2ca02c"
            ax.plot(d["freqs"], d["mag_clean"], color=color, label="Filtrado (Limpio)")
            ax.set_title(f"{d['nombre']} ({d['meta']['nivel_ruido']} Ruido)")
            ax.set_ylabel("dB")
            ax.set_xlim(0, 6000)
            ax.legend()
            ax.grid(True, alpha=0.3)

        # Comparativa
        ax_fus = plt.subplot2grid((3, 1), (2, 0))
        if len(datos) == 2:
            d1, d2 = datos[0], datos[1]
            # Diferencia usando SOLO las señales limpias
            diferencia = d2["mag_clean"] - d1["mag_clean"]

            ax_fus.plot(
                d1["freqs"],
                d1["mag_clean"],
                color="#1f77b4",
                label=f"{d1['meta']['categoria']} Limpio",
                alpha=0.7,
            )
            ax_fus.plot(
                d2["freqs"],
                d2["mag_clean"],
                color="#2ca02c",
                label=f"{d2['meta']['categoria']} Limpio",
                alpha=0.7,
            )
            ax_fus.plot(
                d1["freqs"],
                diferencia,
                color="#d62728",
                label="Diferencia (Target)",
                linestyle="--",
            )

            df_data = {
                "Frecuencia_Hz": d1["freqs"],
                f"{d1['nombre']}_Clean_dB": d1[
                    "mag_clean"
                ],  # Explicitamente marcado Clean
                f"{d2['nombre']}_Clean_dB": d2["mag_clean"],
                "Diferencia_dB": diferencia,
            }
        else:
            d1 = datos[0]
            ax_fus.plot(d1["freqs"], d1["mag_clean"], color="#1f77b4")
            df_data = {
                "Frecuencia_Hz": d1["freqs"],
                f"{d1['nombre']}_Clean_dB": d1["mag_clean"],
            }

        ax_fus.set_xlim(0, 6000)
        ax_fus.legend()
        ax_fus.grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close()

    print(f"   -> Gráfica: {info['grafica']}")

    # 2. Exportar Tablas (DB)
    df = pd.DataFrame(df_data)
    ruta_csv = os.path.join(rutas["csv"], f"{info['tabla']}.csv")
    ruta_txt = os.path.join(rutas["txt"], f"{info['tabla']}.txt")
    df.to_csv(ruta_csv, index=False)
    df.to_csv(ruta_txt, sep="\t", index=False)
    print(f"   -> DB Actualizada: {info['tabla']} (Datos Filtrados)")


# ==========================================
# 5. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    print("=== ANÁLISIS DE VOZ AVANZADO (GFA Phase 1.5) ===")
    rutas = configurar_rutas("GFA")  # Default GFA

    while True:
        entrada = input(
            "\nArchivos (ej: GFA_MA3.opus GFA_MB1.ogg) [q salir]: \n>> "
        ).strip()
        if entrada.lower() == "q":
            break
        if not entrada:
            continue

        archivos = [
            os.path.basename(f.replace("'", "").replace('"', ""))
            for f in entrada.split()
        ]
        if len(archivos) > 2:
            print("Máximo 2 archivos.")
            continue

        procesar_archivos(archivos, rutas)
