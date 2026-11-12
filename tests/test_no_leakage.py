"""Pruebas de verificación de integridad: prevención de fuga de información (No Data Leakage).

Garantiza que las columnas de ground truth (es_anomalia, tipo_anomalia, nota_simulacion)
jamás sean accesibles ni utilizadas por los detectores en sus algoritmos.
"""

from pathlib import Path
import pytest

from src.config import FEATURES_IF, ROOT_DIR

COLUMNAS_GROUND_TRUTH = ["es_anomalia", "tipo_anomalia", "nota_simulacion"]


def test_features_if_no_leakage() -> None:
    """Verifica que la lista de features de Isolation Forest no contenga columnas de ground truth."""
    for col_gt in COLUMNAS_GROUND_TRUTH:
        assert (
            col_gt not in FEATURES_IF
        ), f"Fuga de información detectada: '{col_gt}' está presente en FEATURES_IF"


def test_codigo_fuente_detectores_no_leakage() -> None:
    """Inspecciona el código fuente de rules.py e isolation_forest.py verificando que no nombren columnas prohibidas."""
    archivos_detectores = [
        ROOT_DIR / "src" / "rules.py",
        ROOT_DIR / "src" / "isolation_forest.py",
    ]

    for archivo in archivos_detectores:
        assert archivo.exists(), f"El archivo {archivo} no existe"
        contenido = archivo.read_text(encoding="utf-8")

        for col_gt in COLUMNAS_GROUND_TRUTH:
            assert (
                col_gt not in contenido
            ), f"Fuga de información en {archivo.name}: se encontró referencia a '{col_gt}'"

