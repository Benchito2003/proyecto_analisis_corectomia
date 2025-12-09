### Versión 1.0

#### Generalidades.

	Para lograr el objetivo de nuestro proyecto, decidimos crear un algoritmo en python, elegimos especialementes este lenguaje debido a la diversidad de librerías creadas por la comunidad que facilitan el desarrollo de ciertos procesos al estar prediseñados por otros usuarios. 
	
	Se estructuró el algoritmo en dos fases principales. La primera, encargada del proceso de importación, optimización, creación y exportación de documentos de recursos adicionales. Y la segunda, destinada a la rehabilitación de la voz a un archivo de audio. 
	
	La versión post-cordectomía corresponde a una simulación del texto leída por el mismo paciente en un ambiente con bajo ruido estacionario y usando un microfono Razer Seiren Mini con las características (favor de añadir las características relevantes del micrófono). 
	
	La nomenclatura de los archivos se asigno de la siguiente manera: {código del paciente}-{Origen del archivo}{número identificador}.{formato del archivo}. 
	
	- Código del paciente: primeras iniciales del paciente.
	-  Identificador del archivo: Origen del archivo y número de identificación
		- Origen del archivo: A: audio pre-cordectoctomia, B: audio post-cordectomía.
		- Número identificador: En caso que se identifique un 0 antes del número, esto significa que no es una versión reciproca de un audio pre-cordectomía.
	- Formato; para audio: mp3, opus, ogg, wav, para bases de datos: .txt o .cvs, para gráficas: pdf.
	
	Por ejemplo: GFA-B1.ogg (Nombre: Gxxxxxx Fxxxxx Axxxxxx, primer audio de origen post-cordectomía y formato de audio ogg). 

#### Algortimos

- Algoritmo 1.1.0 (Importación y exporta los archivos paralelos): 
	
	La primera fase se encaga de importar la información desde cualquier tipo de formato de audio del paciente pre-cordectomía y su contraparte post-cordectomía. Se uso la librería Noisereduce para mejorar la calidad de los archivos, se crearon gráficas comparativas en el dominio de la frecuencia (post FFT) entre la versión original versus la versión posterior, y para visualizar el efecto del mejoramiento de la señal (es decir antes y después). Así mismo, se exportaron dos documentos (uno en .cvs y otro en .txt) con la información obtenida organizada en tablas de datos, separadas por bandas de frecuencia en la primera columna y valor de la magnitud en la segunda.

	Además se realizaron se añadieron los siguientes indicadores a la nomenclatura de los archivos para diferenciarlos con mayor facilidad:

	- Para audios.
		- Después de la reducción de ruido. Se agregó el prefijo "ENH-" (obtenido de la ingles "_Enhance_" que signifca potenciar la calidad)
		- Después de un procesamiento final de "rehabilitación" a un documento post-cordectomía, se agregó el prefijo "REH-".
	- Para las gráficas:
		- Cuando se realizó una comparación entre cualquiera de los documentos. Se añadieron los identificadores de los archivos despues del códido de paciente entre parentesis y separados por un guión medio "({identificador del archivo 1}-{identificador del archivo 1})".
		- Cuando solo se analizó un archivo, solo se agregó el prefijo "GRA-".
	- Para las tablas de datos:
		- Se les agregó el prefijo "DB-" (forma estandarizada de origen inglés que significa _Database_ o base de datos).

- Algoritmo 1.2.0 (Rehabilitación por amplificación espectral):
	
	Para la segunda fase, aca una de los bandas de frecuencia se calculo el factor por el cual se debía multiplicar cada categoría de frecuencia post-cordectomía para que esta tuviera los mismo valores pre-cordectomía. Al archivo post-cordectomía que se buscaba rehabilitar, en el dominio de la frecuencia se le amplificó por el factor antes obtenido y se aplicó una transformada inversa de fourier a los datos correspondientes. 

- Algoritmo 1.1.1 (Importación y exporta los archivos paralelos e individuales):
	
	Se mantuvo la primera fase del algoritmo, sin embargo, ahora permite aplicar el mismo algoritmo para las versiones pre-cordectomía aunque no tuvieran una contraparte post-cordectomía y exportarlo como una tabla de datos. 
	
	Se mantuvieron las mismas reglas de nomenclatura post-procesamiento.

- Algoritmo 1.2.1 (Rehabilitación por suma espectral):
	
	Para la segunda fase, se obtuvo el promedio de las tablas datos precordectomía y postcordectomía y se le calculo la diferencia promedio. Al archivo post-cordectomía que se buscaba rehabilitar, en el dominio de la frecuencia se le sumó la diferencia promedio antes obtenida y se aplicó una transformada de fourier inversa. 

- Algoritmo 1.2.2 (Rehabilitación inyección. Desviación estándar):

	Para la segunda fase, se obtuvo la desviación estandar para cada banda de frecuencia cualculada, se calculo el limite superior de la desviación estandar del los datos post-cordectomía y el limite inferior de los datos pre-cordectomía para obtener una inyección proyectada de datos que virtualmente no superara el límite del promedio de los datos pre-cordectomía y de esta manera ayudar al algoritmo a amplificar de una manera más natural y no excediera el limite del promedio de los datos pre-cordectoía. Se calculó el factor de amplificación con la formula: datos de la frencuencia post-cordectomía más inyección proyectada dividida en entre el valor del promedio de los datos promedio pre-cordectomía.  Al archivo post-cordectomía que se buscaba rehabilitar, en el dominio de la frecuencia se amplificó por el factor antes obtenido y se aplicó una transformada inversa de fourier. 


### Versión 2.0

#### Generalidades

Se modificó el algoritmo de nomenclatura de la siguiente manera: 
Se agregó un indicador de **genero**, y el duplicó o triplicó la **cantidad de letras** correspondientes al origen del archivo de acuerdo a la evaluación previa cualitativa del la cantidad de ruido percibido del archivo original realizada en audifonos KZ ZSN Pro. Quedando de la siguiente manera: 

La nomenclatura de los archivos se asigno de la siguiente manera: {código del paciente}-{**Género**}{Origen y **calidad** del archivo}{número identificador}.{formato del archivo}. 

Estas es una descripción de los prefijos y sufijos empleados y su significado:

	- Código del paciente: creado a partir de las primeras iniciales del paciente.
	- Género del paciente: "M" para masculino, "F" para fenenino y "N" para neutro.
	- Origen y **calidad** del archivo: "A": audio pre-cordectoctomia, B: audio post-cordectomía. Entre mayor sea la iteración de este indicador, mayor es el nivel de ruido detectado cualitativamente, siendo el nivel 3 e nivel superior.
	- Número identificador: En caso que se identifique un 0 antes del número, esto significa que no es una versión reciproca de un audio pre-cordectomía.
	- Formato; para audio: mp3, opus, ogg, wav, para bases de datos: .txt o .cvs, para gráficas: pdf.

Por ejemplo: GFA-MAAA13.opus representaría los siguientes metadatos. Nombre: Gxxxxxx Fxxxxx Axxxxxx, treceavo audio de origen pre-cordectomía con un nivel alto (nivel 3) y formato de audio opus).

Para la fase dos, de acuerdo a la calidad de los archivos analizados. Se volvió a modular el proceso dividiendolo en una fase de análisis de los datos y otra fase de procesamiento final.

#### Algoritmos

- Algoritmo 2.1.0 (Importación y REGEX)

	Se empleó un algoritmo adaptativo basado en la "Referencia sintáctica de expresiones regulares" (REGEX por sus siglas en ingles de _Regular Expressions Syntax Reference_) donde se aplicaron los siguientes parémetros de acuerdo a los metadatos añadidos a la nomenclatura del archivo:

		- Filtro por Género (Pasa-Banda): Basado en las frecuencias comunes de acuerdo al género. 
		
			- "M" (Masculino): 70 - 7000 Hz. (Frecuencias más graves típicas del hombre). 
			- "F" (Femenino): 100 - 8000 Hz. (Corta más graves inútiles y permite más brillo agudo).
			- "N" (Neutro): 65 - 8000 Hz. (Rango de seguridad más amplio).
		
		- Filtro por Nivel de Ruido: Se ajustaron parámetros embebidos en la librería noisereduce. Esta es la configuración utilizada para cada uno de los niveles establecidos.
		
			- Nivel 1 (Archivos "A" - Ruido bajo) Para mantener la naturalidad y textura de la voz.
			
				- prop_decrease = 0.60: Elimina solo el 60% del ruido.
					- Deja un poco de "aire" de fondo para que la voz no suene robótica o cortada.
				- n_std_thresh = 2.0: Umbral de detección alto (Estricto).
					- Solo ataca lo que es _definitivamente_ ruido fuerte, ignorando los detalles sutiles de la voz.
				- time_constant = 0.5: Adaptación rápida.
					- El filtro se actualiza rápido, ideal para entornos controlados.
			- Nivel 2 (Archivos "AA" - Ruido medio) Elimina distracciones fuertes.
			
				- prop_decrease = 0.90: Elimina el 90% del ruido.
					- Limpieza agresiva necesaria para que la gráfica muestre la voz y no el ruido de fondo.
				- n_std_thresh = 1.5: **Umbral de detección bajo (Sensible).
					- Es más "paranoico"; ataca cualquier sonido que parezca mínimamente ruido estacionario.
				- time_constant = 2.0: **Adaptación lenta.
					- Asume que el ruido es constante (como un ventilador) y aplica una supresión estable y pesada a lo largo del tiempo.
			- Nivel 3 (Archivos "AAA" - Mucho ruido) Limpieza fuerte. Se asume que el ruido tan alto, por lo que se sacrifica bandas de la voz para salvar los datos.
			
				- prop_decrease = 0.90: Elimina el 90% del ruido detectado.
					- Es una sustracción casi total. Se acepta que la voz pueda sonar un poco más "delgada" o digital a cambio de eliminar casi todo el ruido de fondo (tráfico intenso, maquinaria).
				- n_std_thresh = 1.5: Umbral de detección bajo (Muy Sensible).
				    - El algoritmo se vuelve "intolerante" al ruido. Clasifica como ruido cualquier sonido que se parezca al perfil de fondo, incluso si se mezcla con la voz. Reduce el riesgo de que queden "manchas" de ruido en la gráfica.
				- time_constant = 1.0: Adaptación lenta y robusta.
					- Analiza ventanas de tiempo de 1 segundo para crear el perfil de ruido. Esto es ideal para ruidos pesados y constantes que no cambian rápido (zumbidos eléctricos fuertes o aire acondicionado industrial), asegurando una supresión estable.

- Algoritmo 2.2.0 (Entrenamiento) 2.1.0/(Procesamiento) 2.2.0
	
	Algoritmo 2.2.1.0 (Entrenamiento del modelo). Se asignó un valor de ponderación de acuerdo a la calidad original de los archivos:
	
			-"X": 10
			-"XX": 2
			-"XXX": 0.1
		
			"X" representa la letra asignada para el origen del archivo ("A"/"B"). De esta manera, los archivos con mayor calidad recibieron una mayor ponderación y se automatizó el proceso para que importara en su totalidad la carpeta que contiene los archivos correspondientes a la table de datos. Y calcula el perfil espectral ideal usando la fórmula:
			
			$$\text{Perfil}_{ideal} = \frac{\sum (\text{Datos}_i \times \text{Peso}_i)}{\sum \text{Pesos}_i}$$
			
			Esto significa que la voz se recontruye basándose fuertemente en los mejores audios, pero usará la información de los audios "sucios" para rellenar huecos o confirmar tendencias. 
	
	- Fase 2.2.2.0 (Algoritmo de reconstrucción)
	
		Se optó por un modelo donde nuevamente se inyectara material sonoro, para ello se aisló la banda media menos afectada (500-2500 Hz) de los valores del archivo post-cordectomía y se amplificaron para alcanzar la "octava artificial" más cercana a la voz objetivo, y de la banda de agudos más afectados (3500-4500 Hz) se extrajo el valor del promedio ponderado del arreglo correspondiente a los datos pre-cordectomía y se sustituyeron los datos en el dominio de la frecuencia en el archivo de voz objetivo y se le aplicó un filtro Savitzky-Golay para mejorar la calidad de los datos obtenidos. A estos datos en el dominio de la frecuenciaa se le aplicó una transformada inversa de fourier.
