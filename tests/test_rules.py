"""Pruebas unitarias para la Técnica 1: Reglas simples."""

import pandas as pd
import pytest

from src.rules import aplicar_reglas


@pytest.fixture
def df_casos_control() -> pd.DataFrame:
    """Crea un DataFrame sintético con filas diseñadas para activar cada regla por separado."""
    filas = [
        # 0: Mesa normal (no activa ninguna regla)
        {
            "mesa_id": "T0",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 102,
            "votos_cand_B": 85,
            "votos_cand_C": 31,
            "votos_cand_D": 14,
            "votos_blanco": 5,
            "votos_nulos": 6,
            "votos_no_marcados": 2,
            "total_votos_reportado": 245,
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 1: R1 sobre_participacion (450 reportados > 400 habilitados)
        {
            "mesa_id": "T1",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 190,
            "votos_cand_B": 150,
            "votos_cand_C": 60,
            "votos_cand_D": 30,
            "votos_blanco": 5,
            "votos_nulos": 10,
            "votos_no_marcados": 5,
            "total_votos_reportado": 450,
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 2: R2 inconsistencia_aritmetica (suma es 245, pero reportan 270)
        {
            "mesa_id": "T2",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 102,
            "votos_cand_B": 85,
            "votos_cand_C": 31,
            "votos_cand_D": 14,
            "votos_blanco": 5,
            "votos_nulos": 6,
            "votos_no_marcados": 2,
            "total_votos_reportado": 270,  # 245 + 25
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 3: R3 participacion_extrema (385 / 400 = 96.25 %)
        {
            "mesa_id": "T3",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 150,
            "votos_cand_B": 130,
            "votos_cand_C": 60,
            "votos_cand_D": 30,
            "votos_blanco": 5,
            "votos_nulos": 8,
            "votos_no_marcados": 2,
            "total_votos_reportado": 385,
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 4: R4 voto_concentrado (Candidato A con 95 votos de 100 validos = 95 %)
        {
            "mesa_id": "T4",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 95,
            "votos_cand_B": 3,
            "votos_cand_C": 1,
            "votos_cand_D": 1,
            "votos_blanco": 2,
            "votos_nulos": 2,
            "votos_no_marcados": 1,
            "total_votos_reportado": 105,
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 5: R5 nulos_excesivos (50 nulos de 250 votos = 20.0 %)
        {
            "mesa_id": "T5",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 90,
            "votos_cand_B": 60,
            "votos_cand_C": 30,
            "votos_cand_D": 15,
            "votos_blanco": 5,
            "votos_nulos": 50,
            "votos_no_marcados": 0,
            "total_votos_reportado": 250,
            "hora_reporte": "2026-03-08T17:00:00",
        },
        # 6: R6 numeros_redondos (40, 30, 20, 10 todos múltiplos de 10)
        {
            "mesa_id": "T6",
            "departamento": "Antioquia",
            "municipio": "Medellín",
            "zona": "urbana",
            "puesto": "P01",
            "votantes_habilitados": 400,
            "votos_cand_A": 70,
            "votos_cand_B": 40,
            "votos_cand_C": 20,
            "votos_cand_D": 10,
            "votos_blanco": 3,
            "votos_nulos": 4,
            "votos_no_marcados": 1,
            "total_votos_reportado": 148,
            "hora_reporte": "2026-03-08T17:00:00",
        },
    ]
    return pd.DataFrame(filas)


def test_activacion_individual_reglas(df_casos_control: pd.DataFrame) -> None:
    """Verifica que cada fila active exactamente la regla prevista."""
    resultado = aplicar_reglas(df_casos_control)

    # Fila 0: Normal -> ninguna alerta
    assert not resultado.loc[0, "alerta_reglas"]
    assert resultado.loc[0, "puntaje_reglas"] == 0
    assert resultado.loc[0, "severidad_reglas"] == "sin alerta"

    # Fila 1: R1 activa
    assert resultado.loc[1, "R1_sobre_participacion"]
    assert resultado.loc[1, "puntaje_reglas"] >= 3
    assert resultado.loc[1, "severidad_reglas"] == "critica"

    # Fila 2: R2 activa
    assert resultado.loc[2, "R2_inconsistencia_aritmetica"]
    assert resultado.loc[2, "puntaje_reglas"] >= 3
    assert resultado.loc[2, "severidad_reglas"] == "critica"

    # Fila 3: R3 activa
    assert resultado.loc[3, "R3_participacion_extrema"]
    assert not resultado.loc[3, "R1_sobre_participacion"]
    assert resultado.loc[3, "severidad_reglas"] in ["alta", "critica"]

    # Fila 4: R4 activa
    assert resultado.loc[4, "R4_voto_concentrado"]
    assert resultado.loc[4, "severidad_reglas"] in ["alta", "critica"]

    # Fila 5: R5 activa
    assert resultado.loc[5, "R5_nulos_excesivos"]
    assert resultado.loc[5, "puntaje_reglas"] >= 1

    # Fila 6: R6 activa
    assert resultado.loc[6, "R6_numeros_redondos"]
    assert resultado.loc[6, "puntaje_reglas"] >= 1

