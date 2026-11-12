"""Generador sintético de mesas electorales con inyección de anomalías y casos extremos.

Genera 5.000 mesas de votación simuladas de la República de Simulandia,
garantizando reproducibilidad estricta bajo SEED = 42 y el cumplimiento del
esquema de datos canónico.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from src.config import (
    CANDIDATOS,
    CANTIDADES_ANOMALIAS,
    CONCENTRACION_DEPTO,
    CONCENTRACION_MESA,
    CONCENTRACION_MUNI,
    DATA_RAW_CSV,
    DATA_RAW_DIR,
    DEPARTAMENTOS,
    FECHA_HORA_CIERRE,
    HABILITADOS_RURAL_MAX,
    HABILITADOS_RURAL_MIN,
    HABILITADOS_URBANO_MAX,
    HABILITADOS_URBANO_MIN,
    MIN_MESAS_POR_MUNICIPIO,
    NUM_EXTREMOS_LEGITIMOS,
    NUM_MESAS,
    NUM_MUNICIPIOS_POR_DEPTO,
    PREFERENCIAS_BASE,
    PROB_BLANCO,
    PROB_NO_MARCADOS,
    PROB_NULOS,
    PROB_ZONA_URBANA,
    RETRASO_MAX_MINUTOS,
    RETRASO_RURAL_MU_LOG,
    RETRASO_RURAL_SIGMA,
    RETRASO_URBANA_MU_LOG,
    RETRASO_URBANA_SIGMA,
    SEED,
    TURNOUT_BETA_K,
    TURNOUT_MU_MAX,
    TURNOUT_MU_MEDIA,
    TURNOUT_MU_MIN,
    TURNOUT_MU_STD,
    TURNOUT_P_MAX,
    TURNOUT_P_MIN,
)

COLUMNAS_ESQUEMA: List[str] = [
    "mesa_id",
    "departamento",
    "municipio",
    "zona",
    "puesto",
    "votantes_habilitados",
    "votos_cand_A",
    "votos_cand_B",
    "votos_cand_C",
    "votos_cand_D",
    "votos_blanco",
    "votos_nulos",
    "votos_no_marcados",
    "total_votos_reportado",
    "hora_reporte",
    "es_anomalia",
    "tipo_anomalia",
    "nota_simulacion",
]


def _crear_estructura_territorial(rng: np.random.Generator) -> Tuple[List[str], List[str], List[str], np.ndarray]:
    """Crea la lista de 48 municipios con sus departamentos, asigna zona y mesas."""
    deptos: List[str] = []
    municipios: List[str] = []
    zonas_muni: List[str] = []

    for dep in DEPARTAMENTOS:
        for m in range(1, NUM_MUNICIPIOS_POR_DEPTO + 1):
            deptos.append(dep)
            muni_nombre = f"{dep}-Mun{m:02d}"
            municipios.append(muni_nombre)
            es_urbano = rng.random() < PROB_ZONA_URBANA
            zonas_muni.append("urbana" if es_urbano else "rural")

    num_m = len(municipios)  # 48
    pesos = rng.dirichlet(np.ones(num_m) * 2.0)
    mesas_por_muni = rng.multinomial(NUM_MESAS, pesos)

    # Asegurar que ningún municipio quede con menos de MIN_MESAS_POR_MUNICIPIO (20)
    while np.any(mesas_por_muni < MIN_MESAS_POR_MUNICIPIO):
        idx_def = np.where(mesas_por_muni < MIN_MESAS_POR_MUNICIPIO)[0][0]
        idx_max = np.argmax(mesas_por_muni)
        mesas_por_muni[idx_def] += 1
        mesas_por_muni[idx_max] -= 1

    return deptos, municipios, zonas_muni, mesas_por_muni


def generar_dataset(seed: int = SEED) -> pd.DataFrame:
    """Genera el DataFrame completo con 5.000 mesas normales, casos extremos y anomalías inyectadas."""
    rng = np.random.default_rng(seed)

    deptos_lista, muni_lista, zonas_muni, mesas_por_muni = _crear_estructura_territorial(rng)

    # 1. Preferencias departamentales y municipales
    pref_base = np.array(PREFERENCIAS_BASE)
    pref_deptos = {dep: rng.dirichlet(pref_base * CONCENTRACION_DEPTO) for dep in DEPARTAMENTOS}
    pref_munis = {}
    turnout_munis = {}

    for idx, muni in enumerate(muni_lista):
        dep = deptos_lista[idx]
        pref_munis[muni] = rng.dirichlet(pref_deptos[dep] * CONCENTRACION_MUNI)
        # Turnout municipal
        mu_m = float(np.clip(rng.normal(TURNOUT_MU_MEDIA, TURNOUT_MU_STD), TURNOUT_MU_MIN, TURNOUT_MU_MAX))
        turnout_munis[muni] = mu_m

    # 2. Generar mesas base
    registros = []
    mesa_global_idx = 1
    cierre_dt = datetime.fromisoformat(FECHA_HORA_CIERRE)

    for m_idx, muni in enumerate(muni_lista):
        dep = deptos_lista[m_idx]
        zona = zonas_muni[m_idx]
        cant_mesas = mesas_por_muni[m_idx]
        mu_m = turnout_munis[muni]
        pref_m = pref_munis[muni]

        for idx_en_muni in range(cant_mesas):
            mesa_id = f"M{mesa_global_idx:05d}"
            mesa_global_idx += 1

            puesto_num = (idx_en_muni // 20) + 1
            puesto = f"{muni}-P{puesto_num:02d}"

            # Votantes habilitados
            if zona == "urbana":
                habilitados = int(rng.integers(HABILITADOS_URBANO_MIN, HABILITADOS_URBANO_MAX + 1))
            else:
                habilitados = int(rng.integers(HABILITADOS_RURAL_MIN, HABILITADOS_RURAL_MAX + 1))

            # Participación
            alpha_b = mu_m * TURNOUT_BETA_K
            beta_b = (1.0 - mu_m) * TURNOUT_BETA_K
            p_mesa = float(np.clip(rng.beta(alpha_b, beta_b), TURNOUT_P_MIN, TURNOUT_P_MAX))
            total_votos = int(round(p_mesa * habilitados))
            total_votos = max(total_votos, 1)

            # Preferencias de la mesa
            pref_mesa = rng.dirichlet(pref_m * CONCENTRACION_MESA)
            # Distribución multinomial con 7 categorías
            # [cand_A, cand_B, cand_C, cand_D, blanco, nulos, no_marcados]
            p_candidatos = pref_mesa * 0.94
            probs_mesa = np.array([
                p_candidatos[0], p_candidatos[1], p_candidatos[2], p_candidatos[3],
                PROB_BLANCO, PROB_NULOS, PROB_NO_MARCADOS
            ])
            probs_mesa = probs_mesa / probs_mesa.sum()

            conteos = rng.multinomial(total_votos, probs_mesa)

            # Hora de reporte
            if zona == "urbana":
                retraso = float(rng.lognormal(mean=RETRASO_URBANA_MU_LOG, sigma=RETRASO_URBANA_SIGMA))
            else:
                retraso = float(rng.lognormal(mean=RETRASO_RURAL_MU_LOG, sigma=RETRASO_RURAL_SIGMA))
            retraso = min(retraso, float(RETRASO_MAX_MINUTOS))
            hora_rep = (cierre_dt + timedelta(minutes=int(round(retraso)))).isoformat()

            total_rep = int(np.sum(conteos))

            registros.append({
                "mesa_id": mesa_id,
                "departamento": dep,
                "municipio": muni,
                "zona": zona,
                "puesto": puesto,
                "votantes_habilitados": habilitados,
                "votos_cand_A": int(conteos[0]),
                "votos_cand_B": int(conteos[1]),
                "votos_cand_C": int(conteos[2]),
                "votos_cand_D": int(conteos[3]),
                "votos_blanco": int(conteos[4]),
                "votos_nulos": int(conteos[5]),
                "votos_no_marcados": int(conteos[6]),
                "total_votos_reportado": total_rep,
                "hora_reporte": hora_rep,
                "es_anomalia": 0,
                "tipo_anomalia": "ninguna",
                "nota_simulacion": "",
            })

    df = pd.DataFrame(registros)

    # 3. Casos extremos legítimos (40 mesas rurales pequeñas)
    candidatas_rurales = df[
        (df["zona"] == "rural") & (df["votantes_habilitados"] <= 200)
    ].index.to_numpy()

    if len(candidatas_rurales) < NUM_EXTREMOS_LEGITIMOS:
        # En el caso improbable de < 40, ordenar rurales por habilitados
        candidatas_rurales = df[df["zona"] == "rural"].sort_values("votantes_habilitados").index.to_numpy()

    idx_extremos = rng.choice(candidatas_rurales, size=NUM_EXTREMOS_LEGITIMOS, replace=False)

    for idx in idx_extremos:
        hab = int(df.at[idx, "votantes_habilitados"])
        p_alta = float(rng.uniform(0.85, 0.94))
        tot_extremo = int(round(p_alta * hab))
        tot_extremo = max(tot_extremo, 1)

        candidato_fav = int(rng.integers(0, 4))
        fav_share = float(rng.uniform(0.75, 0.88))
        resto_dir = rng.dirichlet(np.ones(3)) * (1.0 - fav_share)

        pref_cands = np.zeros(4)
        pref_cands[candidato_fav] = fav_share
        otros_idx = [i for i in range(4) if i != candidato_fav]
        for oi, r_val in zip(otros_idx, resto_dir):
            pref_cands[oi] = r_val

        p_cands = pref_cands * 0.94
        probs_extremo = np.array([
            p_cands[0], p_cands[1], p_cands[2], p_cands[3],
            PROB_BLANCO, PROB_NULOS, PROB_NO_MARCADOS
        ])
        probs_extremo = probs_extremo / probs_extremo.sum()
        conteos_ext = rng.multinomial(tot_extremo, probs_extremo)

        df.at[idx, "votos_cand_A"] = int(conteos_ext[0])
        df.at[idx, "votos_cand_B"] = int(conteos_ext[1])
        df.at[idx, "votos_cand_C"] = int(conteos_ext[2])
        df.at[idx, "votos_cand_D"] = int(conteos_ext[3])
        df.at[idx, "votos_blanco"] = int(conteos_ext[4])
        df.at[idx, "votos_nulos"] = int(conteos_ext[5])
        df.at[idx, "votos_no_marcados"] = int(conteos_ext[6])
        df.at[idx, "total_votos_reportado"] = int(np.sum(conteos_ext))
        df.at[idx, "nota_simulacion"] = "extremo_legitimo"
        df.at[idx, "es_anomalia"] = 0
        df.at[idx, "tipo_anomalia"] = "ninguna"

    # 4. Inyección de anomalías (200 mesas sin reemplazo y excluyendo extremos legítimos)
    indices_disponibles = set(df.index) - set(idx_extremos)

    # 4.1 sobre_participacion (30 mesas)
    cant_sp = CANTIDADES_ANOMALIAS["sobre_participacion"]
    elegidas_sp = rng.choice(list(indices_disponibles), size=cant_sp, replace=False)
    indices_disponibles -= set(elegidas_sp)

    for idx in elegidas_sp:
        hab = int(df.at[idx, "votantes_habilitados"])
        factor = float(rng.uniform(1.02, 1.30))
        nuevo_total = int(round(hab * factor))
        v_A = int(df.at[idx, "votos_cand_A"])
        v_B = int(df.at[idx, "votos_cand_B"])
        v_C = int(df.at[idx, "votos_cand_C"])
        v_D = int(df.at[idx, "votos_cand_D"])
        v_bl = int(df.at[idx, "votos_blanco"])
        v_nu = int(df.at[idx, "votos_nulos"])
        v_nm = int(df.at[idx, "votos_no_marcados"])
        conteos = np.array([v_A, v_B, v_C, v_D, v_bl, v_nu, v_nm])
        tot_act = max(int(np.sum(conteos)), 1)
        scale = nuevo_total / tot_act
        nuevos = np.round(conteos * scale).astype(int)
        # Ajustar diferencia de redondeo en A
        diff = nuevo_total - int(np.sum(nuevos))
        nuevos[0] = max(nuevos[0] + diff, 0)

        df.at[idx, "votos_cand_A"] = int(nuevos[0])
        df.at[idx, "votos_cand_B"] = int(nuevos[1])
        df.at[idx, "votos_cand_C"] = int(nuevos[2])
        df.at[idx, "votos_cand_D"] = int(nuevos[3])
        df.at[idx, "votos_blanco"] = int(nuevos[4])
        df.at[idx, "votos_nulos"] = int(nuevos[5])
        df.at[idx, "votos_no_marcados"] = int(nuevos[6])
        df.at[idx, "total_votos_reportado"] = int(np.sum(nuevos))
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "sobre_participacion"

    # 4.2 relleno_urnas (45 mesas en 3 municipios seleccionados al azar)
    cant_ru = CANTIDADES_ANOMALIAS["relleno_urnas"]
    munis_todos = list(df["municipio"].unique())
    munis_ru = rng.choice(munis_todos, size=3, replace=False)

    elegidas_ru = []
    for m in munis_ru:
        cand_muni = [i for i in df[df["municipio"] == m].index if i in indices_disponibles]
        elegidas_m = rng.choice(cand_muni, size=15, replace=False)
        elegidas_ru.extend(elegidas_m)
        indices_disponibles -= set(elegidas_m)

    for idx in elegidas_ru:
        hab = int(df.at[idx, "votantes_habilitados"])
        obj_p = float(rng.uniform(0.93, 1.00))
        objetivo = int(np.floor(hab * obj_p))
        tot_act = (
            int(df.at[idx, "votos_cand_A"])
            + int(df.at[idx, "votos_cand_B"])
            + int(df.at[idx, "votos_cand_C"])
            + int(df.at[idx, "votos_cand_D"])
            + int(df.at[idx, "votos_blanco"])
            + int(df.at[idx, "votos_nulos"])
            + int(df.at[idx, "votos_no_marcados"])
        )
        extra = max(objetivo - tot_act, 0)
        df.at[idx, "votos_cand_A"] = int(df.at[idx, "votos_cand_A"]) + extra
        nuevo_tot = tot_act + extra
        df.at[idx, "total_votos_reportado"] = nuevo_tot
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "relleno_urnas"

    # 4.3 voto_unanime (35 mesas)
    cant_vu = CANTIDADES_ANOMALIAS["voto_unanime"]
    elegidas_vu = rng.choice(list(indices_disponibles), size=cant_vu, replace=False)
    indices_disponibles -= set(elegidas_vu)

    for idx in elegidas_vu:
        hab = int(df.at[idx, "votantes_habilitados"])
        p_vu = float(rng.uniform(0.85, 0.99))
        nuevo_total = max(int(round(hab * p_vu)), 10)
        ganador_idx = int(rng.integers(0, 4))
        pct_ganador = float(rng.uniform(0.92, 1.00))

        blanco = int(round(nuevo_total * rng.uniform(0.002, 0.006)))
        nulo = int(round(nuevo_total * rng.uniform(0.002, 0.006)))
        no_marcado = int(round(nuevo_total * rng.uniform(0.002, 0.006)))
        no_cands = blanco + nulo + no_marcado
        validos = max(nuevo_total - no_cands, 4)

        votos_ganador = int(round(validos * pct_ganador))
        resto_validos = max(validos - votos_ganador, 0)
        otros_reparto = rng.multinomial(resto_validos, np.ones(3) / 3.0)

        conteos_cands = np.zeros(4, dtype=int)
        conteos_cands[ganador_idx] = votos_ganador
        oi_list = [i for i in range(4) if i != ganador_idx]
        for k, oi in enumerate(oi_list):
            conteos_cands[oi] = int(otros_reparto[k])

        df.at[idx, "votos_cand_A"] = int(conteos_cands[0])
        df.at[idx, "votos_cand_B"] = int(conteos_cands[1])
        df.at[idx, "votos_cand_C"] = int(conteos_cands[2])
        df.at[idx, "votos_cand_D"] = int(conteos_cands[3])
        df.at[idx, "votos_blanco"] = blanco
        df.at[idx, "votos_nulos"] = nulo
        df.at[idx, "votos_no_marcados"] = no_marcado
        tot_final = int(np.sum(conteos_cands)) + no_cands
        df.at[idx, "total_votos_reportado"] = tot_final
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "voto_unanime"

    # 4.4 inconsistencia_aritmetica (35 mesas)
    cant_ia = CANTIDADES_ANOMALIAS["inconsistencia_aritmetica"]
    elegidas_ia = rng.choice(list(indices_disponibles), size=cant_ia, replace=False)
    indices_disponibles -= set(elegidas_ia)

    deltas_posibles = np.concatenate([np.arange(-60, -4), np.arange(5, 61)])
    for idx in elegidas_ia:
        suma_actual = (
            int(df.at[idx, "votos_cand_A"])
            + int(df.at[idx, "votos_cand_B"])
            + int(df.at[idx, "votos_cand_C"])
            + int(df.at[idx, "votos_cand_D"])
            + int(df.at[idx, "votos_blanco"])
            + int(df.at[idx, "votos_nulos"])
            + int(df.at[idx, "votos_no_marcados"])
        )
        delta = int(rng.choice(deltas_posibles))
        if suma_actual + delta < 0:
            delta = abs(delta)
        df.at[idx, "total_votos_reportado"] = suma_actual + delta
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "inconsistencia_aritmetica"

    # 4.5 numeros_redondos (25 mesas con total >= 100)
    cant_nr = CANTIDADES_ANOMALIAS["numeros_redondos"]
    disp_nr = [
        i for i in indices_disponibles
        if (
            int(df.at[i, "votos_cand_A"])
            + int(df.at[i, "votos_cand_B"])
            + int(df.at[i, "votos_cand_C"])
            + int(df.at[i, "votos_cand_D"])
            + int(df.at[i, "votos_blanco"])
            + int(df.at[i, "votos_nulos"])
            + int(df.at[i, "votos_no_marcados"])
        ) >= 100
    ]
    elegidas_nr = rng.choice(disp_nr, size=cant_nr, replace=False)
    indices_disponibles -= set(elegidas_nr)

    for idx in elegidas_nr:
        for c_col in ["votos_cand_A", "votos_cand_B", "votos_cand_C", "votos_cand_D"]:
            val = int(df.at[idx, c_col])
            redondeado = max(10, int(round(val / 10.0) * 10))
            df.at[idx, c_col] = redondeado

        suma_nr = (
            int(df.at[idx, "votos_cand_A"])
            + int(df.at[idx, "votos_cand_B"])
            + int(df.at[idx, "votos_cand_C"])
            + int(df.at[idx, "votos_cand_D"])
            + int(df.at[idx, "votos_blanco"])
            + int(df.at[idx, "votos_nulos"])
            + int(df.at[idx, "votos_no_marcados"])
        )
        df.at[idx, "total_votos_reportado"] = suma_nr
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "numeros_redondos"

    # 4.6 nulos_excesivos (30 mesas)
    cant_ne = CANTIDADES_ANOMALIAS["nulos_excesivos"]
    elegidas_ne = rng.choice(list(indices_disponibles), size=cant_ne, replace=False)
    indices_disponibles -= set(elegidas_ne)

    for idx in elegidas_ne:
        v_A = int(df.at[idx, "votos_cand_A"])
        v_B = int(df.at[idx, "votos_cand_B"])
        v_C = int(df.at[idx, "votos_cand_C"])
        v_D = int(df.at[idx, "votos_cand_D"])
        v_bl = int(df.at[idx, "votos_blanco"])
        v_nu = int(df.at[idx, "votos_nulos"])
        v_nm = int(df.at[idx, "votos_no_marcados"])

        tot_act = v_A + v_B + v_C + v_D + v_bl + v_nu + v_nm
        pct_nulos_target = float(rng.uniform(0.15, 0.35))
        k = int(round(tot_act * pct_nulos_target))

        # Restar votos de oposición (B, C, D)
        suma_bcd = v_B + v_C + v_D
        if suma_bcd > 0:
            k_efectivo = min(k, suma_bcd)
            # Descontar proporcionalmente
            rB = v_B / suma_bcd
            rC = v_C / suma_bcd
            rD = v_D / suma_bcd

            dB = min(v_B, int(round(k_efectivo * rB)))
            dC = min(v_C, int(round(k_efectivo * rC)))
            dD = min(v_D, int(round(k_efectivo * rD)))

            diff_k = k_efectivo - (dB + dC + dD)
            # Ajustar diferencia residual sin dejar negativos
            if diff_k > 0:
                if v_B - dB >= diff_k:
                    dB += diff_k
                elif v_C - dC >= diff_k:
                    dC += diff_k
                elif v_D - dD >= diff_k:
                    dD += diff_k
            elif diff_k < 0:
                # Quitar exceso
                alivio = -diff_k
                if dB >= alivio:
                    dB -= alivio
                elif dC >= alivio:
                    dC -= alivio
                elif dD >= alivio:
                    dD -= alivio

            total_restado = dB + dC + dD
            df.at[idx, "votos_cand_B"] = v_B - dB
            df.at[idx, "votos_cand_C"] = v_C - dC
            df.at[idx, "votos_cand_D"] = v_D - dD
            df.at[idx, "votos_nulos"] = v_nu + total_restado

        df.at[idx, "total_votos_reportado"] = (
            int(df.at[idx, "votos_cand_A"])
            + int(df.at[idx, "votos_cand_B"])
            + int(df.at[idx, "votos_cand_C"])
            + int(df.at[idx, "votos_cand_D"])
            + int(df.at[idx, "votos_blanco"])
            + int(df.at[idx, "votos_nulos"])
            + int(df.at[idx, "votos_no_marcados"])
        )
        df.at[idx, "es_anomalia"] = 1
        df.at[idx, "tipo_anomalia"] = "nulos_excesivos"

    # Ordenar columnas según el esquema oficial
    df = df[COLUMNAS_ESQUEMA]
    return df


def main() -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    df = generar_dataset(seed=SEED)
    df.to_csv(DATA_RAW_CSV, index=False)

    print(f"Dataset generado exitosamente en: {DATA_RAW_CSV}")
    print(f"Total de mesas: {len(df)}")
    print("\nDistribución por tipo de anomalía:")
    print(df["tipo_anomalia"].value_counts())
    print("\nDistribución por nota de simulación:")
    print(df["nota_simulacion"].value_counts())
    print(f"\nMesas normales limpias (ninguna y sin nota): {len(df[(df['tipo_anomalia'] == 'ninguna') & (df['nota_simulacion'] == '')])}")


if __name__ == "__main__":
    main()

