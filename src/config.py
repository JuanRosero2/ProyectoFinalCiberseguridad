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
# 3. PARÁMETROS DEL ESCENARIO ELECTORAL SIMULADO (República de Simulandia)
# ==============================================================================
NUM_MESAS: int = 5000

# División territorial ficticia
DEPARTAMENTOS: List[str] = [
    "Aurora", "Bruma", "Cumbre", "Delta",
    "Estela", "Fénix", "Granito", "Horizonte"
]
NUM_MUNICIPIOS_POR_DEPTO: int = 6
NUM_MUNICIPIOS_TOTAL: int = len(DEPARTAMENTOS) * NUM_MUNICIPIOS_POR_DEPTO  # 48
MIN_MESAS_POR_MUNICIPIO: int = 20  # Garantiza tamaño muestral mínimo por municipio

# Clasificación geográfica: probabilidad de que un municipio sea catalogado como urbano
PROB_ZONA_URBANA: float = 0.60

# Rango de votantes habilitados por mesa (censo de mesa)
# En zonas urbanas las mesas suelen ser más densas; en rurales son más pequeñas y dispersas
HABILITADOS_URBANO_MIN: int = 250
HABILITADOS_URBANO_MAX: int = 600  # Intervalo cerrado [250, 600]
HABILITADOS_RURAL_MIN: int = 80
HABILITADOS_RURAL_MAX: int = 300   # Intervalo cerrado [80, 300]

# Participación electoral típica (turnout)
# Media municipal modelada como Normal(0.58, 0.07) acotada a [0.35, 0.80]
TURNOUT_MU_MEDIA: float = 0.58
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

# Composición esperada de votos no dirigidos a candidatos
PROB_BLANCO: float = 0.02
PROB_NULOS: float = 0.03
PROB_NO_MARCADOS: float = 0.01

# Horario de votación y transmisión
FECHA_HORA_CIERRE: str = "2026-03-08T16:00:00"
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

# R5: Votos nulos excesivos (>= 12 % del total). Cuadruplica la tasa base esperada (~3 %).
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
# Contaminación supuesta coherente con la capacidad operativa de auditoría (~4 %)
IF_CONTAMINATION: float = 0.04
IF_N_ESTIMATORS: int = 300
IF_MAX_SAMPLES: str = "auto"

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
COLOR_SOLO_IF: str = "#4E79A7"      # Azul: detectado solo por Isolation Forest
COLOR_AMBAS: str = "#E15759"        # Rojo: detectado por ambas técnicas (concordancia crítica)

DPI_FIGURAS: int = 200
FIGSIZE_DEFAULT: tuple = (9, 6)

