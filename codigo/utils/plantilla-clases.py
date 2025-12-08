# ==============================================================================
# PLANTILLA DE PROGRAMACIÓN ORIENTADA A OBJETOS (POO)
# Autor: El Arquitecto (Tú)
# Propósito: Enseñar Clases, Herencia y Polimorfismo
# ==============================================================================


class ComponenteBase:
    """
    CLASE PADRE (SUPERCLASE)
    Esta clase define los atributos y comportamientos genéricos que
    todo componente tendrá, evitando repetir código.
    """

    def __init__(self, nombre, id_componente):
        """
        CONSTRUCTOR: Se ejecuta automáticamente al crear un objeto.
        Aquí inicializamos los atributos (variables) del objeto.
        """
        # Atributos de instancia (propios de cada objeto)
        self.nombre = nombre
        self.id = id_componente
        self._activo = False  # El guion bajo (_) indica que es una variable "protegida" (uso interno)

    def encender(self):
        """Método (función) para cambiar el estado del componente"""
        self._activo = True
        print(f"✅ [SISTEMA] El componente '{self.nombre}' ha sido ENCENDIDO.")

    def apagar(self):
        """Método para apagar"""
        self._activo = False
        print(f"🛑 [SISTEMA] El componente '{self.nombre}' ha sido APAGADO.")

    def estado(self):
        """Retorna el estado actual para consultarlo"""
        return "Activo" if self._activo else "Inactivo"


# ==============================================================================
# HERENCIA
# ==============================================================================


class SensorBiomedico(ComponenteBase):
    """
    CLASE HIJA (SUBCLASE)
    Hereda todo de 'ComponenteBase' (nombre, id, encender, apagar)
    y añade funcionalidades específicas para sensores.
    """

    def __init__(self, nombre, id_componente, tipo_medicion, unidad):
        # super() llama al constructor del Padre para no repetir la lógica de inicialización
        super().__init__(nombre, id_componente)

        # Nuevos atributos exclusivos de esta clase hija
        self.tipo_medicion = tipo_medicion
        self.unidad = unidad
        self.valor_actual = 0.0

    def leer_datos(self, valor_simulado):
        """
        Método exclusivo del Sensor.
        Simula la lectura de un dato físico.
        """
        if self._activo:
            self.valor_actual = valor_simulado
            print(
                f"📊 [LECTURA] {self.nombre} ({self.tipo_medicion}): {self.valor_actual} {self.unidad}"
            )
            self._analizar_riesgo()  # Llamada a un método interno
        else:
            print(
                f"⚠️ [ERROR] No se puede leer: El sensor '{self.nombre}' está apagado."
            )

    def _analizar_riesgo(self):
        """Método interno para procesar el dato (Lógica de negocio)"""
        # Ejemplo simple de lógica
        if self.valor_actual > 100:
            print(f"   🚨 ALERTA: Valor crítico detectado en {self.nombre}!")
        else:
            print(f"   👍 Estado normal.")


# ==============================================================================
# EJECUCIÓN (MAIN)
# ==============================================================================

if __name__ == "__main__":
    print("--- INICIANDO SISTEMA DE MONITORIZACIÓN ---\n")

    # 1. Instanciación: Creando objetos a partir de las clases
    # Nota como no tenemos que reescribir la lógica de "encender" para cada uno.
    sensor_cardiaco = SensorBiomedico(
        "ECG Lead I", "SENS-001", "Frecuencia Cardíaca", "BPM"
    )
    sensor_oxigeno = SensorBiomedico("Oxímetro Dedo", "SENS-002", "Saturación O2", "%")

    # 2. Uso de métodos heredados (del Padre)
    sensor_cardiaco.encender()

    # 3. Intento de uso de un sensor apagado (Lógica de la Hija)
    sensor_oxigeno.leer_datos(98.5)  # Esto dará error porque no lo encendimos

    # 4. Uso correcto
    sensor_oxigeno.encender()
    print(f"\nEstado actual del oxímetro: {sensor_oxigeno.estado()}\n")

    # 5. Simulando lecturas
    sensor_cardiaco.leer_datos(80)  # Normal
    sensor_cardiaco.leer_datos(120)  # Crítico (dispara la alerta interna)
    sensor_oxigeno.leer_datos(99)

    print("\n--- FIN DE LA SIMULACIÓN ---")
