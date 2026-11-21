"""Textos de la interfaz: explicaciones fijas e interpretaciones construidas con los números calculados.

Regla: ninguna cifra se escribe a mano; todas salen de los resultados del análisis.
"""

from typing import Dict, List

import pandas as pd

from src.config import (
    FEATURES_IF,
    IF_N_ESTIMATORS,
    PESO_R1_SOBRE_PARTICIPACION,
    PESO_R2_INCONSISTENCIA_ARITMETICA,
    PESO_R3_PARTICIPACION_EXTREMA,
    PESO_R4_VOTO_CONCENTRADO,
    PESO_R5_NULOS_EXCESIVOS,
    PESO_R6_NUMEROS_REDONDOS,
    UMBRAL_R3_PARTICIPACION,
    UMBRAL_R4_MIN_VOTOS_VALIDOS,
    UMBRAL_R4_PCT_MAX,
    UMBRAL_R5_PCT_NULOS,
)

from app.graficos import NOMBRES_TIPO

DESCARGO_ETICO = (
    "**Todos los votos son simulados.** Los departamentos y municipios son reales de Colombia, pero los "
    "resultados, las mesas y los candidatos son ficticios: **no representan ninguna elección real** ni hacen "
    "afirmaciones sobre ella. Una alerta indica una **inconsistencia que merece revisión**, no una prueba de fraude."
)


def pct(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f} %".replace(".", ",")


def num(x: float) -> str:
    return f"{int(x):,}".replace(",", ".")


# ------------------------------------------------------------------------------
# Catálogos fijos
# ------------------------------------------------------------------------------
CATALOGO_ANOMALIAS = pd.DataFrame([
    ("Sobreparticipación", "Más votos que ciudadanos habilitados para votar en la mesa", "Es imposible si el censo electoral de la mesa es correcto. En Colombia es causal de reclamación (Código Electoral, art. 192, num. 5)."),
    ("Relleno de urnas", "Votos extra agregados a un candidato hasta llevar la participación a 93–100 %", "Participación y apoyo a un candidato anormalmente altos a la vez."),
    ("Voto unánime", "Un candidato recibe ≥ 92 % de los votos válidos con participación alta", "Patrón típico de formularios E-14 diligenciados sin un conteo real de votos."),
    ("Inconsistencia aritmética", "El total escrito en el formulario E-14 no coincide con la suma de sus partes", "Error o alteración al diligenciar el E-14. En Colombia el error aritmético es causal de reclamación (art. 192, num. 11)."),
    ("Números redondos", "Todos los conteos de candidatos terminan en 0", "Las cifras inventadas tienden a ser redondas; con un conteo real es muy raro (≈ 1 de cada 10.000 mesas)."),
    ("Nulos excesivos", "15–35 % de los votos reclasificados como nulos, restados a la oposición", "Anulación selectiva de votos válidos durante el escrutinio de mesa."),
], columns=["Anomalía", "Qué simula", "Por qué es sospechosa"])

NOMBRES_REGLAS = {
    "R1_sobre_participacion": "R1 · Sobreparticipación",
    "R2_inconsistencia_aritmetica": "R2 · Inconsistencia aritmética",
    "R3_participacion_extrema": "R3 · Participación extrema",
    "R4_voto_concentrado": "R4 · Voto concentrado",
    "R5_nulos_excesivos": "R5 · Nulos excesivos",
    "R6_numeros_redondos": "R6 · Números redondos",
}

def tabla_reglas(h: Dict[str, float]) -> pd.DataFrame:
    """Tabla de reglas. Los umbrales son fijos (decisión del proyecto); la referencia "típica" sale de los datos cargados."""
    return pd.DataFrame([
        ("R1 · Sobreparticipación", "Total de votos > ciudadanos habilitados en la mesa", PESO_R1_SOBRE_PARTICIPACION, "Crítica",
         "Imposible si el censo electoral de la mesa es correcto. Es causal de reclamación en Colombia (Código Electoral, art. 192, num. 5)."),
        ("R2 · Inconsistencia aritmética", "Total del E-14 ≠ suma de candidatos, blanco, nulos y no marcados", PESO_R2_INCONSISTENCIA_ARITMETICA, "Crítica",
         "Un E-14 correcto debe cuadrar exactamente. El error aritmético es causal de reclamación (art. 192, num. 11)."),
        ("R3 · Participación extrema", f"Participación ≥ {pct(UMBRAL_R3_PARTICIPACION, 0)}", PESO_R3_PARTICIPACION_EXTREMA, "Alta",
         f"Muy por encima de la participación típica de estos datos (mediana {pct(h['participacion_mediana'])}) y de la real en Colombia "
         f"(54,9 % en la primera vuelta presidencial de 2022): casi ningún ciudadano habilitado en la mesa se abstuvo."),
        ("R4 · Voto concentrado", f"Candidato más votado ≥ {pct(UMBRAL_R4_PCT_MAX, 0)} y ≥ {UMBRAL_R4_MIN_VOTOS_VALIDOS} votos válidos",
         PESO_R4_VOTO_CONCENTRADO, "Alta", "Concentración casi unánime; el mínimo de votos evita alertas en mesas diminutas."),
        ("R5 · Nulos excesivos", f"Nulos ≥ {pct(UMBRAL_R5_PCT_NULOS, 0)} del total", PESO_R5_NULOS_EXCESIVOS, "Media",
         f"Muy por encima de la tasa típica de nulos en estos datos (mediana {pct(h['pct_nulos_mediana'])}); en la primera vuelta "
         f"presidencial de 2022 en Colombia los nulos fueron cerca del 1,1 % del total."),
        ("R6 · Números redondos", "Los 4 conteos de candidatos son múltiplos de 10", PESO_R6_NUMEROS_REDONDOS, "Media",
         "Con un conteo real ocurre ≈ 1 vez de cada 10.000 mesas (probabilidad 0,1⁴)."),
    ], columns=["Regla", "Condición", "Peso", "Severidad", "Justificación"])

NOMBRES_FEATURES = {
    "participacion": "Participación",
    "desv_participacion_municipal": "Participación vs. mediana del municipio",
    "pct_cand_A": "% Candidato A",
    "pct_cand_B": "% Candidato B",
    "pct_cand_C": "% Candidato C",
    "pct_cand_D": "% Candidato D",
    "pct_max_candidato": "% del candidato más votado",
    "pct_nulos": "% de votos nulos",
    "pct_blanco": "% de votos en blanco",
    "diferencia_aritmetica": "Diferencia aritmética del E-14",
    "frac_multiplos_10": "Fracción de conteos redondos",
    "log_habilitados": "Tamaño de la mesa (logaritmo de habilitados)",
}

EXPLICACION_IF = (
    f"Isolation Forest construye {IF_N_ESTIMATORS} árboles que **parten los datos con cortes al azar**. "
    "Una mesa normal se parece a muchas otras y necesita muchos cortes para quedar sola; una mesa rara "
    "queda aislada con pocos cortes. El **puntaje de anomalía (score)** mide qué tan fácil fue aislarla: cuanto más alto, más rara. "
    "El modelo **no conoce las respuestas correctas**: aprende solo de cómo se ven los datos."
)

RIESGOS_LIMITACIONES: List[str] = [
    "**Datos sintéticos:** nosotros mismos diseñamos las anomalías; en un proceso real pueden ser más sutiles o de tipos no previstos.",
    "**Umbrales conocidos:** si alguien conoce las reglas, puede manipular quedándose justo debajo (por ejemplo, 94 % de participación).",
    "**Sesgo contra mesas pequeñas y rurales:** en mesas pequeñas los porcentajes varían más por azar e Isolation Forest las marca más; una comunidad homogénea puede parecer sospechosa sin serlo.",
    "**Dependencia del parámetro `contamination`:** fija cuántas mesas marca el modelo, y en la realidad no se conoce la tasa real de anomalías.",
    "**Sin dimensión temporal ni de proceso:** no se analizan la hora de transmisión del preconteo, la cadena de custodia de los documentos electorales ni las diferencias entre copias del E-14.",
    "**Nombres reales, datos simulados:** los resultados mencionan departamentos y municipios reales, pero sus votos son inventados; no deben citarse como información sobre esos lugares.",
    "**Riesgo de mal uso:** publicar alertas sin verificar puede usarse para desacreditar resultados legítimos. Una alerta solo prioriza qué E-14 revisar; la decisión corresponde a las comisiones escrutadoras.",
]


# ------------------------------------------------------------------------------
# Interpretaciones calculadas
# ------------------------------------------------------------------------------
def interpretar_datos(df: pd.DataFrame) -> str:
    return (
        f"Se cargaron **{num(len(df))} mesas** de **{df['departamento'].nunique()} departamentos** y "
        f"**{df['municipio'].nunique()} municipios**, con **{num(df['votantes_habilitados'].sum())} votantes habilitados** "
        f"y **{num(df['total_votos_reportado'].sum())} votos reportados**. "
        f"El {pct((df['zona'] == 'rural').mean(), 0)} de las mesas es rural."
    )


def interpretar_eda(h: Dict[str, float], res_nac: pd.DataFrame) -> str:
    cand = res_nac[res_nac["opcion"].str.startswith("Candidato")].sort_values("pct_validos", ascending=False)
    primero, segundo = cand.iloc[0], cand.iloc[1]
    return (
        f"La participación típica es de **{pct(h['participacion_media'])}** (mediana {pct(h['participacion_mediana'])}); "
        f"la mitad central de las mesas está entre {pct(h['participacion_p25'])} y {pct(h['participacion_p75'])}. "
        f"Sin embargo, **{h['n_part_95']} mesas superan el 95 %** y **{h['n_sobre_100']} superan el 100 %** "
        f"(máximo {pct(h['participacion_max'])}), algo imposible si el censo electoral de la mesa es correcto. "
        f"Además, **{h['n_dif_arit']} formularios E-14 no cuadran** aritméticamente, **{h['n_conc_90']}** tienen un candidato con ≥ 90 % "
        f"y **{h['n_nulos_12']}** tienen ≥ 12 % de nulos (la mediana es {pct(h['pct_nulos_mediana'])}). "
        f"Estas colas son las que justifican los umbrales de las reglas.\n\n"
        f"A nivel nacional, {primero['opcion']} obtiene {pct(primero['pct_validos'] / 100)} de los votos válidos y "
        f"{segundo['opcion']} {pct(segundo['pct_validos'] / 100)}. Recuerda que son datos ficticios."
    )


def interpretar_reglas(df: pd.DataFrame) -> str:
    n = int(df["alerta_reglas"].sum())
    sev = df["severidad_reglas"].value_counts()
    cerca = int(((df["participacion"] >= 0.90) & (df["participacion"] < UMBRAL_R3_PARTICIPACION) & ~df["alerta_reglas"]).sum())
    return (
        f"Las reglas marcan **{n} mesas ({pct(n / len(df))})**: {sev.get('critica', 0)} críticas, "
        f"{sev.get('alta', 0)} altas y {sev.get('media', 0)} medias. "
        "Su fortaleza es que cada alerta se explica sola (\"el E-14 no cuadra\", \"hay más votos que ciudadanos habilitados\"). "
        f"Su debilidad es que **no ven lo que queda justo debajo del umbral**: hay {cerca} mesas sin alerta con "
        f"participación entre 90 % y 95 %, que una manipulación cuidadosa podría aprovechar."
    )


def interpretar_if(df: pd.DataFrame, perfil: pd.DataFrame, umbral: float, contamination: float) -> str:
    n = int(df["alerta_if"].sum())
    alertadas = df[df["alerta_if"]]
    top = perfil.head(3)
    rasgos = ", ".join(
        f"{NOMBRES_FEATURES[f].lower()} ({'más alta' if d > 0 else 'más baja'})"
        for f, d in zip(top["feature"], top["diferencia"])
    )
    tam_alert = alertadas["votantes_habilitados"].mean() if n else float("nan")
    tam_total = df["votantes_habilitados"].mean()
    solo_if = int((df["alerta_if"] & ~df["alerta_reglas"]).sum())
    texto = (
        f"Con `contamination = {contamination:.2f}`, Isolation Forest marca **{n} mesas** (score ≥ {umbral:.3f}). "
        f"Lo que más las diferencia del resto es: {rasgos}. "
        f"**{solo_if} de ellas no las marca ninguna regla**: es lo que aporta esta técnica, combinaciones raras que no cruzan un umbral individual."
    )
    if n and tam_alert < tam_total * 0.85:
        texto += (
            f"\n\n⚠️ Las mesas marcadas son más pequeñas que el promedio ({tam_alert:.0f} frente a {tam_total:.0f} ciudadanos "
            "habilitados): en mesas pequeñas los porcentajes varían más por azar, así que el modelo tiende a señalarlas. "
            "Es un **sesgo** a tener en cuenta."
        )
    return texto


def interpretar_patrones(df: pd.DataFrame, riesgo_muni: pd.DataFrame) -> str:
    cuenta = df["nivel_riesgo"].value_counts()
    alto = int(cuenta.get("alto", 0))
    medio = int(cuenta.get("medio", 0))
    det = df["deteccion"].value_counts()
    patrones = (
        df[df["nivel_riesgo"] == "alto"]["reglas_activadas"].str.split(", ").explode()
        .replace("", pd.NA).dropna().value_counts()
    )
    sin_alerta = df[df["deteccion"] == "Sin alerta"]
    alto_df = df[df["nivel_riesgo"] == "alto"]
    patron_txt = ", ".join(f"{r} ({c})" for r, c in patrones.head(3).items()) if len(patrones) else "ninguna regla"
    texto = (
        f"**{alto} mesas quedan en riesgo alto** y {medio} en riesgo medio, de {num(len(df))}. "
        f"Ambas técnicas coinciden en {det.get('Ambas técnicas', 0)} mesas; solo las reglas marcan {det.get('Solo reglas', 0)} "
        f"y solo Isolation Forest {det.get('Solo Isolation Forest', 0)}. "
        f"Las reglas más frecuentes en el riesgo alto son: {patron_txt}.\n\n"
        f"En la huella electoral (Figura 2) las mesas sin alerta forman una nube central (mediana: participación "
        f"{pct(sin_alerta['participacion'].median())}, candidato más votado {pct(sin_alerta['pct_max_candidato'].median())}); "
        f"las mesas en riesgo alto se alejan de ella (mediana: participación {pct(alto_df['participacion'].median())}, "
        f"candidato más votado {pct(alto_df['pct_max_candidato'].median())})."
    ) if alto else (
        f"**No hay mesas en riesgo alto** y {medio} en riesgo medio, de {num(len(df))}."
    )
    if len(riesgo_muni):
        m = riesgo_muni.iloc[0]
        texto += (
            f"\n\nEn estos datos simulados, **{m['municipio']}** encabeza la lista con {pct(m['pct_riesgo_alto'] / 100)} de sus mesas "
            f"en riesgo alto ({m['mesas_riesgo_alto']} de {m['total_mesas']}): sería el primer municipio donde solicitar la revisión de los E-14."
        )
    return texto


def explicar_mesa(fila: pd.Series, umbral_if: float, nulos_tipico: float) -> List[str]:
    """Frases en lenguaje sencillo sobre por qué una mesa es (o no) sospechosa."""
    frases = []
    if fila["R1_sobre_participacion"]:
        frases.append(f"Reporta **{num(fila['total_votos_reportado'])} votos con solo {num(fila['votantes_habilitados'])} ciudadanos habilitados** (participación de {pct(fila['participacion'])}).")
    if fila["R2_inconsistencia_aritmetica"]:
        frases.append(f"El total escrito en el E-14 **difiere en {num(fila['diferencia_aritmetica'])} votos** de la suma de sus partes.")
    if fila["R3_participacion_extrema"] and not fila["R1_sobre_participacion"]:
        frases.append(f"Participación de **{pct(fila['participacion'])}**, por encima del umbral de {pct(UMBRAL_R3_PARTICIPACION, 0)}.")
    if fila["R4_voto_concentrado"]:
        frases.append(f"Un solo candidato recibe **{pct(fila['pct_max_candidato'])}** de los votos válidos.")
    if fila["R5_nulos_excesivos"]:
        frases.append(f"El **{pct(fila['pct_nulos'])} de los votos son nulos** (lo típico en estos datos es {pct(nulos_tipico)}).")
    if fila["R6_numeros_redondos"]:
        frases.append("**Todos los conteos de candidatos terminan en 0**, algo muy improbable por azar.")
    if fila["alerta_if"]:
        frases.append(
            f"Isolation Forest la considera rara: puntaje {fila['score_if']:.3f} (umbral {umbral_if:.3f}), "
            f"más rara que el {fila['percentil_score_if']:.0f} % de las mesas."
        )
    desv = fila["participacion"] - fila["mediana_participacion_municipio"]
    if abs(desv) >= 0.15:
        frases.append(
            f"Su participación está {pct(abs(desv))} {'por encima' if desv > 0 else 'por debajo'} de la mediana de su municipio "
            f"({pct(fila['mediana_participacion_municipio'])})."
        )
    if not frases:
        frases.append("No activa ninguna regla y su puntaje de Isolation Forest está por debajo del umbral: no hay motivo para priorizarla.")
    return frases


def hallazgos(res, riesgo_muni: pd.DataFrame) -> List[str]:
    """Hallazgos principales calculados (pestaña 8)."""
    df = res.df
    h = res.eda["hallazgos"]
    cuenta = df["nivel_riesgo"].value_counts()
    alto = int(cuenta.get("alto", 0))
    lista = [
        f"De {num(len(df))} mesas, **{alto} ({pct(alto / len(df))}) quedan en riesgo alto**: es la lista de E-14 que conviene revisar primero.",
        f"Hay **{h['n_sobre_100']} mesas con más votos que ciudadanos habilitados** y **{h['n_dif_arit']} formularios E-14 que no cuadran**: inconsistencias sin explicación legítima que, en Colombia, son causales de reclamación (art. 192, num. 5 y 11).",
        f"Isolation Forest marca {int(df['alerta_if'].sum())} mesas, de las cuales **{int((df['alerta_if'] & ~df['alerta_reglas']).sum())} no las detecta ninguna regla**: aporta cobertura sobre combinaciones raras.",
    ]
    if res.evaluacion is not None:
        m = res.evaluacion["metricas"].set_index("detector")
        r, i, u = m.loc["Reglas simples"], m.loc["Isolation Forest"], m.loc["Unión (Cualquiera)"]
        alto_df = df[df["nivel_riesgo"] == "alto"]
        lista += [
            f"**Reglas:** precisión {pct(r['precision'])} y recall {pct(r['recall'])}. **Isolation Forest:** precisión {pct(i['precision'])} y recall {pct(i['recall'])}. Las reglas son mucho más precisas; IF genera más falsas alarmas.",
            f"**Combinadas (unión)** detectan el {pct(u['recall'])} de las anomalías ({int(u['VP'])} de {int(u['VP'] + u['FN'])}). En el riesgo alto, **{pct(alto_df['es_anomalia'].mean())} son anomalías reales**.",
        ]
        ext = res.evaluacion["fp_extremos"].set_index("detector")
        if ext.loc["Isolation Forest", "total_extremos"] > 0:
            lista.append(
                f"De las {int(ext.loc['Isolation Forest', 'total_extremos'])} mesas **atípicas pero legítimas**, Isolation Forest marca "
                f"{int(ext.loc['Isolation Forest', 'falsos_positivos'])} y las reglas {int(ext.loc['Reglas simples', 'falsos_positivos'])}: "
                "**una alerta no es una prueba de fraude**."
            )
        fn = res.evaluacion["falsos_negativos"]
        if len(fn):
            tipos = fn["tipo_anomalia"].map(NOMBRES_TIPO).value_counts()
            detalle = ", ".join(f"{t}: {c}" for t, c in tipos.items())
            if len(fn) == 1:
                rango = f"con una participación de {pct(fn['participacion'].iloc[0])}"
                inicio = f"Se escapa **1 anomalía** ({detalle}), {rango}"
            else:
                rango = f"con participación entre {pct(fn['participacion'].min())} y {pct(fn['participacion'].max())}"
                inicio = f"Se escapan **{len(fn)} anomalías** ({detalle}), {rango}"
            lista.append(inicio + ": quien conoce los umbrales puede quedarse justo debajo de ellos.")
    if len(riesgo_muni):
        top = riesgo_muni.head(3)
        lista.append(
            "En la simulación, los municipios con mayor proporción de riesgo alto son "
            + ", ".join(f"**{r.municipio}** ({pct(r.pct_riesgo_alto / 100)})" for r in top.itertuples())
            + ": la revisión puede focalizarse geográficamente."
        )
    return lista


def conclusion() -> str:
    return (
        "Las dos técnicas son **complementarias**: las reglas son precisas y fáciles de explicar para lo que es "
        "imposible o improbable; Isolation Forest amplía la cobertura sobre combinaciones raras a costa de más "
        "falsas alarmas. Juntas permiten **priorizar qué formularios E-14 revisar**, pero ninguna alerta, por sí sola, "
        "demuestra fraude."
    )


FEATURES_IF_TABLA = pd.DataFrame({
    "Variable": [NOMBRES_FEATURES[f] for f in FEATURES_IF],
    "Columna": FEATURES_IF,
})


def explicar_falsos_negativos(fn: pd.DataFrame, umbral_if: float) -> str:
    """Explica, con los valores reales, por qué se escaparon las anomalías no detectadas."""
    debajo_r3 = int(((fn["participacion"] < UMBRAL_R3_PARTICIPACION) & (fn["participacion"] >= 0.85)).sum())
    def num3(x: float) -> str:
        return f"{x:.3f}".replace(".", ",")

    if len(fn) == 1:
        f = fn.iloc[0]
        texto = (
            f"Esta mesa no activó ninguna regla y su puntaje de Isolation Forest ({num3(f['score_if'])}) quedó por debajo "
            f"del umbral ({num3(umbral_if)}). Tiene una participación de {pct(f['participacion'])} y el candidato más "
            f"votado obtuvo {pct(f['pct_max_candidato'])}."
        )
    else:
        texto = (
            f"Ninguna de estas {len(fn)} mesas activó una regla y todas tienen un puntaje de Isolation Forest menor al umbral "
            f"({num3(fn['score_if'].min())}–{num3(fn['score_if'].max())} frente a {num3(umbral_if)}). "
            f"Su participación va de {pct(fn['participacion'].min())} a {pct(fn['participacion'].max())} y el candidato más "
            f"votado, de {pct(fn['pct_max_candidato'].min())} a {pct(fn['pct_max_candidato'].max())}."
        )
    if debajo_r3:
        texto += (
            f" **{'Quedó' if len(fn) == 1 else f'{debajo_r3} quedaron'} entre 85 % y {pct(UMBRAL_R3_PARTICIPACION, 0)} de participación, justo debajo del umbral de R3**: "
            "una manipulación moderada y cuidadosa puede pasar ambos filtros."
        )
    return texto


# ------------------------------------------------------------------------------
# Explicación de los controles deslizables (barras)
# ------------------------------------------------------------------------------
def explicar_contamination(contamination: float, n_mesas: int | None = None) -> str:
    """Qué pasa al mover la barra de contamination de Isolation Forest."""
    if n_mesas:
        cuantas = f"Con **{contamination:.2f}** y {num(n_mesas)} mesas, el modelo marcará **≈ {num(round(contamination * n_mesas))} mesas** como raras."
    else:
        cuantas = f"Con **{contamination:.2f}**, el modelo marcará como raras ≈ el {pct(contamination, 0)} de las mesas del archivo."
    return (
        f"**¿Qué controla esta barra?** El porcentaje de mesas que Isolation Forest marcará como raras. {cuantas}\n\n"
        "- **Si la subes (hacia 0,10):** marca más mesas. Detecta más anomalías, pero también aumentan las "
        "**falsas alarmas** (mesas normales que habría que revisar sin necesidad).\n"
        "- **Si la bajas (hacia 0,02):** marca menos mesas. Sus alertas son más seguras, pero se **escapan más** anomalías.\n"
        "- **Valor recomendado: 0,04.** Equivale a revisar ≈ 4 % de las mesas, una carga de trabajo razonable para las "
        "comisiones escrutadoras.\n\n"
        "Esta barra **no cambia las reglas simples**: sus umbrales son fijos. Con el archivo con etiquetas, la pestaña "
        "*Evaluación* muestra cómo cambian los aciertos y las falsas alarmas con cada valor."
    )


def explicar_min_mesas(min_mesas: int, riesgo_todos: pd.DataFrame) -> str:
    """Qué pasa al mover la barra de mínimo de mesas por municipio (Figura 5)."""
    total = len(riesgo_todos)
    excluidos = riesgo_todos[riesgo_todos["total_mesas"] < min_mesas]
    texto = (
        "**¿Qué controla esta barra?** Solo incluye en la Figura 5 los municipios con **al menos esa cantidad de mesas**. "
        "En un municipio con pocas mesas, una o dos alertas disparan el porcentaje (2 de 20 mesas = 10 %), y puede "
        "aparecer arriba sin ser realmente el más problemático.\n\n"
        "- **Si la subes:** el ranking es más confiable, pero quedan fuera los municipios pequeños.\n"
        "- **Si la bajas a 0:** aparecen todos los municipios, incluidos los pequeños con porcentajes inflados.\n\n"
    )
    if min_mesas == 0 or excluidos.empty:
        texto += f"Ahora se muestran **los {total} municipios**."
    else:
        con_alto = excluidos[excluidos["mesas_riesgo_alto"] > 0]
        texto += f"Con **{min_mesas}** se muestran **{total - len(excluidos)} de {total} municipios**; se excluyen {len(excluidos)} por tener menos mesas"
        if len(con_alto):
            texto += (
                ", entre ellos " + ", ".join(f"{r.municipio} ({r.mesas_riesgo_alto} de {r.total_mesas})" for r in con_alto.head(4).itertuples())
                + " con mesas en riesgo alto. Revísalos en la tabla de priorización."
            )
        else:
            texto += ", y ninguno de ellos tiene mesas en riesgo alto."
    return texto
