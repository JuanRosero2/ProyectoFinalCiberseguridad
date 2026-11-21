"""Configuración global, rutas, parámetros de simulación y umbrales justificados.

Todas las constantes del proyecto residen en este módulo con sus justificaciones
técnicas y operativas correspondientes, garantizando reproducibilidad y ausencia
de 'números mágicos' dispersos en el código.
"""

from pathlib import Path
from typing import Dict, List

# ==============================================================================
# 1. REPRODUCIBILIDAD
# ==============================================================================
# Semilla maestra obligatoria para generadores pseudoaleatorios (numpy y sklearn)
SEED: int = 42

# ==============================================================================
# 2. RUTAS DEL PROYECTO
# ==============================================================================
ROOT_DIR: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = ROOT_DIR / "data"
DATA_RAW_DIR: Path = DATA_DIR / "raw"
DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"

OUTPUTS_DIR: Path = ROOT_DIR / "outputs"
OUTPUTS_FIG_DIR: Path = OUTPUTS_DIR / "figures"
OUTPUTS_TAB_DIR: Path = OUTPUTS_DIR / "tables"

REPORTS_DIR: Path = ROOT_DIR / "reports"
DOCS_DIR: Path = ROOT_DIR / "docs"
TESTS_DIR: Path = ROOT_DIR / "tests"
NOTEBOOKS_DIR: Path = ROOT_DIR / "notebooks"

# Archivos de datos clave
DATA_RAW_CSV: Path = DATA_RAW_DIR / "mesas_simuladas.csv"
DATA_PROCESSED_CSV: Path = DATA_PROCESSED_DIR / "resultados_mesas.csv"
DATA_FEATURES_CSV: Path = DATA_PROCESSED_DIR / "features_mesas.csv"

# ==============================================================================
# 3. PARÁMETROS DEL ESCENARIO ELECTORAL SIMULADO (Colombia: geografía real, datos 100 % simulados)
# ==============================================================================
NUM_MESAS: int = 5000

# División territorial: 8 departamentos reales de Colombia y 6 municipios reales de cada uno
# (el primero es la capital departamental). Los nombres son reales; TODOS los votos son simulados
# y no representan resultados de ninguna elección real.
MUNICIPIOS_POR_DEPARTAMENTO: Dict[str, List[str]] = {
    "Antioquia": ["Medellín", "Bello", "Envigado", "Itagüí", "Rionegro", "Apartadó"],
    "Atlántico": ["Barranquilla", "Soledad", "Malambo", "Sabanalarga", "Puerto Colombia", "Baranoa"],
    "Bolívar": ["Cartagena", "Magangué", "Turbaco", "Arjona", "El Carmen de Bolívar", "Mompox"],
    "Boyacá": ["Tunja", "Duitama", "Sogamoso", "Chiquinquirá", "Paipa", "Puerto Boyacá"],
    "Cundinamarca": ["Soacha", "Facatativá", "Zipaquirá", "Girardot", "Fusagasugá", "Chía"],
    "Nariño": ["Pasto", "Tumaco", "Ipiales", "Túquerres", "La Unión", "Samaniego"],
    "Santander": ["Bucaramanga", "Floridablanca", "Girón", "Piedecuesta", "Barrancabermeja", "San Gil"],
    "Valle del Cauca": ["Cali", "Palmira", "Buenaventura", "Tuluá", "Cartago", "Buga"],
}
DEPARTAMENTOS: List[str] = list(MUNICIPIOS_POR_DEPARTAMENTO.keys())

# Población aproximada (miles de habitantes, cifras redondeadas) usada SOLO como peso para
# repartir las 5.000 mesas simuladas: así una capital grande tiene más mesas que un municipio pequeño.
POBLACION_APROX_MILES: Dict[str, int] = {
    "Medellín": 2600, "Bello": 560, "Envigado": 240, "Itagüí": 290, "Rionegro": 140, "Apartadó": 120,
    "Barranquilla": 1300, "Soledad": 680, "Malambo": 130, "Sabanalarga": 100, "Puerto Colombia": 50, "Baranoa": 65,
    "Cartagena": 1050, "Magangué": 140, "Turbaco": 90, "Arjona": 80, "El Carmen de Bolívar": 75, "Mompox": 45,
    "Tunja": 180, "Duitama": 120, "Sogamoso": 120, "Chiquinquirá": 65, "Paipa": 32, "Puerto Boyacá": 60,
    "Soacha": 800, "Facatativá": 160, "Zipaquirá": 150, "Girardot": 110, "Fusagasugá": 150, "Chía": 150,
    "Pasto": 400, "Tumaco": 260, "Ipiales": 140, "Túquerres": 45, "La Unión": 30, "Samaniego": 50,
    "Bucaramanga": 620, "Floridablanca": 320, "Girón": 200, "Piedecuesta": 180, "Barrancabermeja": 220, "San Gil": 65,
    "Cali": 2280, "Palmira": 360, "Buenaventura": 320, "Tuluá": 220, "Cartago": 140, "Buga": 130,
}
NUM_MUNICIPIOS_POR_DEPTO: int = 6
NUM_MUNICIPIOS_TOTAL: int = len(DEPARTAMENTOS) * NUM_MUNICIPIOS_POR_DEPTO  # 48
MIN_MESAS_POR_MUNICIPIO: int = 20  # Garantiza tamaño muestral mínimo por municipio
MESAS_POR_PUESTO: int = 20  # Agrupación estándar de mesas consecutivas por puesto de votación

# Zona de cada mesa (en Colombia los puestos rurales están en corregimientos e inspecciones):
# en las capitales casi todas las mesas son urbanas; en los demás municipios hay más mesas rurales.
FRACCION_RURAL_CAPITAL: float = 0.08
FRACCION_RURAL_OTROS: float = 0.40

# Rango de votantes habilitados por mesa (censo de mesa)
# En zonas urbanas las mesas suelen ser más densas; en rurales son más pequeñas y dispersas
HABILITADOS_URBANO_MIN: int = 250
HABILITADOS_URBANO_MAX: int = 600  # Intervalo cerrado [250, 600]
HABILITADOS_RURAL_MIN: int = 80
HABILITADOS_RURAL_MAX: int = 300   # Intervalo cerrado [80, 300]

# Participación electoral típica (turnout)
# Media municipal modelada como Normal(0.55, 0.07) acotada a [0.35, 0.80].
# Referencia: la participación en la primera vuelta presidencial de Colombia en 2022 fue del 54,9 %.
TURNOUT_MU_MEDIA: float = 0.55
TURNOUT_MU_STD: float = 0.07
TURNOUT_MU_MIN: float = 0.35
TURNOUT_MU_MAX: float = 0.80

# Parámetro de concentración de la distribución Beta para participación por mesa
# Un valor de 60 asegura dispersión realista alrededor de la media del municipio
TURNOUT_BETA_K: float = 60.0
TURNOUT_P_MIN: float = 0.20
TURNOUT_P_MAX: float = 0.92

# Candidatos y preferencias políticas nacionales de referencia
CANDIDATOS: List[str] = ["Candidato A", "Candidato B", "Candidato C", "Candidato D"]
PREFERENCIAS_BASE: List[float] = [0.38, 0.32, 0.18, 0.12]

# Concentraciones para modelo jerárquico Dirichlet (Depto -> Municipio -> Mesa)
CONCENTRACION_DEPTO: float = 40.0
CONCENTRACION_MUNI: float = 80.0
CONCENTRACION_MESA: float = 150.0

# Composición esperada de votos no dirigidos a candidatos, calibrada con la primera vuelta
# presidencial de Colombia en 2022: voto en blanco ≈ 1,7 %, nulos ≈ 1,1 %, no marcados ≈ 0,14 %.
PROB_BLANCO: float = 0.017
PROB_NULOS: float = 0.011
PROB_NO_MARCADOS: float = 0.0015
PROB_CANDIDATOS: float = 1.0 - (PROB_BLANCO + PROB_NULOS + PROB_NO_MARCADOS)

# Jornada electoral colombiana: domingo de 8:00 a. m. a 4:00 p. m.; al cierre los jurados hacen el
# escrutinio de mesa y diligencian el formulario E-14. La fecha es ficticia (no coincide con
# ninguna elección real).
FECHA_HORA_CIERRE: str = "2026-09-13T16:00:00"
# Parámetros LogNormal para retraso de reporte (minutos después del cierre)
RETRASO_URBANA_MU_LOG: float = 4.09434456  # ln(60)
RETRASO_URBANA_SIGMA: float = 0.5
RETRASO_RURAL_MU_LOG: float = 4.78749174   # ln(120)
RETRASO_RURAL_SIGMA: float = 0.5
RETRASO_MAX_MINUTOS: int = 479  # 7 horas y 59 minutos

# ==============================================================================
# 4. CATÁLOGO DE ANOMALÍAS INYECTADAS Y CASOS EXTREMOS
# ==============================================================================
NUM_EXTREMOS_LEGITIMOS: int = 40

CANTIDADES_ANOMALIAS: Dict[str, int] = {
    "sobre_participacion": 30,
    "relleno_urnas": 45,
    "voto_unanime": 35,
    "inconsistencia_aritmetica": 35,
    "numeros_redondos": 25,
    "nulos_excesivos": 30,
}
NUM_TOTAL_ANOMALIAS: int = sum(CANTIDADES_ANOMALIAS.values())  # 200 (4.0 % del total)

# ==============================================================================
# 5. UMBRALES Y PESOS DE LA TÉCNICA 1: REGLAS SIMPLES
# ==============================================================================
# R1: Participación física imposible (> 100 % del censo electoral)
PESO_R1_SOBRE_PARTICIPACION: int = 3  # Severidad crítica

# R2: Inconsistencia aritmética (total reportado no coincide con la suma de votos)
PESO_R2_INCONSISTENCIA_ARITMETICA: int = 3  # Severidad crítica

# R3: Participación extrema (>= 95 % del censo). En elecciones generales voluntarias
# una asistencia de 95 %+ es estadísticamente improbable y amerita revisión prioritaria.
UMBRAL_R3_PARTICIPACION: float = 0.95
PESO_R3_PARTICIPACION_EXTREMA: int = 2  # Severidad alta

# R4: Voto unánime o ultra-concentrado (>= 90 % a un candidato con al menos 50 votos válidos).
# El mínimo de 50 votos previene falsos positivos en mesas diminutas.
UMBRAL_R4_PCT_MAX: float = 0.90
UMBRAL_R4_MIN_VOTOS_VALIDOS: int = 50
PESO_R4_VOTO_CONCENTRADO: int = 2  # Severidad alta

# R5: Votos nulos excesivos (>= 12 % del total). Es más de diez veces la tasa nacional de
# referencia (≈ 1,1 % en la primera vuelta presidencial de 2022) y deja margen para mesas pequeñas.
UMBRAL_R5_PCT_NULOS: float = 0.12
PESO_R5_NULOS_EXCESIVOS: int = 1  # Severidad media

# R6: Números redondos (los 4 candidatos reciben votos múltiplos de 10).
# Probabilidad estocástica natural p ≈ 0.1^4 = 0.0001; fuerte heurística de datos inventados.
UMBRAL_R6_FRAC_MULTIPLOS_10: float = 1.0
PESO_R6_NUMEROS_REDONDOS: int = 1  # Severidad media

# Categorías de severidad por reglas simples
PUNTAJE_CRITICA: int = 3
PUNTAJE_ALTA: int = 2
PUNTAJE_MEDIA: int = 1

# ==============================================================================
# 6. PARÁMETROS DE LA TÉCNICA 2: ISOLATION FOREST
# ==============================================================================
# Contaminación supuesta: revisar ≈ 4 % de los E-14, una carga razonable para las comisiones escrutadoras
IF_CONTAMINATION: float = 0.04
IF_N_ESTIMATORS: int = 300
IF_MAX_SAMPLES: str = "auto"
NIVELES_CONTAMINACION_SENSIBILIDAD: List[float] = [0.02, 0.04, 0.06, 0.08]

# Lista canónica de features de entrada para Isolation Forest.
# IMPORTANTE (Regla 2): JAMÁS incluir columnas de ground truth (es_anomalia, tipo_anomalia, nota_simulacion)
FEATURES_IF: List[str] = [
    "participacion",
    "desv_participacion_municipal",
    "pct_cand_A",
    "pct_cand_B",
    "pct_cand_C",
    "pct_cand_D",
    "pct_max_candidato",
    "pct_nulos",
    "pct_blanco",
    "diferencia_aritmetica",
    "frac_multiplos_10",
    "log_habilitados",
]

# ==============================================================================
# 7. ESTILOS Y COLORES PARA VISUALIZACIÓN (Paleta consistente obligatoria)
# ==============================================================================
COLOR_NORMAL: str = "#9E9E9E"       # Gris: sin alertas
COLOR_SOLO_REGLAS: str = "#F28E2B"  # Naranja: detectado solo por reglas
COLOR_SOLO_IF: str = "#2E6FD0"      # Azul: detectado solo por Isolation Forest (validado: croma y separación para daltonismo)
COLOR_AMBAS: str = "#E15759"        # Rojo: detectado por ambas técnicas (concordancia crítica)

DPI_FIGURAS: int = 200
FIGSIZE_DEFAULT: tuple = (9, 6)
HIST_BINS_FIG1: int = 60  # Resolución de histograma para distinguir la cola > 95 %

