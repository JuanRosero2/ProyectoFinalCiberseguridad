"""Panel de integridad electoral (datos simulados).

Ejecutar desde la raíz del proyecto:  streamlit run app/app.py
"""

import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.config import IF_CONTAMINATION  # noqa: E402
from src.generate_demo_excel import DEMO_CON_ETIQUETAS, DEMO_SIN_ETIQUETAS, generar_excels_demo  # noqa: E402

from app import graficos, textos  # noqa: E402
from app.analisis import COLUMNAS_REGLAS, analizar, riesgo_municipal  # noqa: E402
from app.carga import COLUMNAS_ETIQUETA, leer_archivo, validar_y_preparar  # noqa: E402
from app.exportar import construir_excel  # noqa: E402

st.set_page_config(page_title="Integridad electoral · datos simulados", page_icon="🗳️", layout="wide")



def _pct_col(etiqueta: str):
    return st.column_config.NumberColumn(etiqueta, format="%.1f %%")


# Nombres legibles para las columnas de las tablas
CFG = {
    "prioridad": st.column_config.NumberColumn("Prioridad"),
    "mesa_id": "Mesa",
    "departamento": "Departamento",
    "municipio": "Municipio",
    "zona": "Zona",
    "votantes_habilitados": st.column_config.NumberColumn("Ciudadanos habilitados"),
    "votos_cand_A": "Candidato A", "votos_cand_B": "Candidato B",
    "votos_cand_C": "Candidato C", "votos_cand_D": "Candidato D",
    "votos_blanco": "Voto en blanco", "votos_nulos": "Nulos", "votos_no_marcados": "No marcados",
    "total_votos_reportado": st.column_config.NumberColumn("Total del E-14"),
    "nivel_riesgo": "Nivel de riesgo",
    "reglas_activadas": "Reglas activadas",
    "puntaje_reglas": st.column_config.NumberColumn("Puntaje de reglas"),
    "severidad_reglas": "Severidad",
    "score_if": st.column_config.NumberColumn("Puntaje IF", format="%.3f"),
    "participacion": _pct_col("Participación"),
    "pct_max_candidato": _pct_col("Candidato más votado"),
    "pct_nulos": _pct_col("Nulos"),
    "diferencia_aritmetica": st.column_config.NumberColumn("Diferencia en el E-14"),
    "deteccion": "Detectada por",
    "tipo_anomalia": "Tipo (respuesta de la simulación)",
    "detector": "Técnica",
    "mesas_alertadas": st.column_config.NumberColumn("Mesas alertadas"),
    "VP": st.column_config.NumberColumn("Aciertos (VP)"),
    "FP": st.column_config.NumberColumn("Falsas alarmas (FP)"),
    "FN": st.column_config.NumberColumn("No detectadas (FN)"),
    "VN": st.column_config.NumberColumn("Normales descartadas (VN)"),
    "precision": _pct_col("Precisión"),
    "recall": _pct_col("Recall (detectadas)"),
    "f1": _pct_col("F1"),
    "total_extremos": st.column_config.NumberColumn("Mesas legítimas atípicas"),
    "falsos_positivos": st.column_config.NumberColumn("Falsas alarmas"),
    "tasa_fp_extremos": _pct_col("% de falsas alarmas"),
    "media": _pct_col("Media"), "desv": _pct_col("Desviación"), "mediana": _pct_col("Mediana"),
    "min": _pct_col("Mínimo"), "max": _pct_col("Máximo"), "mesas": st.column_config.NumberColumn("Mesas"),
}

MODO_CON = "Con etiquetas"
MODO_SIN = "Sin etiquetas"

# ------------------------------------------------------------------------------
# Estilo (tema oscuro definido en .streamlit/config.toml; aquí solo detalles)
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 3.2rem; max-width: 1400px;}
    [data-testid="stMetric"] {
        background: #161D27; border: 1px solid #243042; border-radius: 12px; padding: 14px 16px;
    }
    [data-testid="stMetricLabel"] p {color: #9AA6B8; font-size: 0.9rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 4px; flex-wrap: wrap;}
    .stTabs [data-baseweb="tab"] {
        background: #161D27; border-radius: 10px 10px 0 0; padding: 8px 14px; font-size: 0.95rem;
    }
    .stTabs [aria-selected="true"] {background: #1E2A3B;}
    [data-testid="stSidebar"] {border-right: 1px solid #1F2937;}
    .hero {
        background: linear-gradient(135deg, #16233A 0%, #121925 100%); border: 1px solid #243042;
        border-radius: 16px; padding: 22px 26px; margin-bottom: 18px;
    }
    .hero h1 {font-size: 1.75rem; margin: 0 0 6px 0; color: #E8EDF5;}
    .hero p {color: #A8B3C4; margin: 0; font-size: 1rem;}
    .pasos {display: flex; gap: 10px; margin: 4px 0 18px 0; flex-wrap: wrap;}
    .paso {
        flex: 1; min-width: 180px; border-radius: 12px; padding: 10px 14px; font-size: 0.92rem;
        background: #161D27; border: 1px solid #243042; color: #7E8A9C;
    }
    .paso b {display: block; font-size: 0.78rem; letter-spacing: .04em; text-transform: uppercase;}
    .paso.activo {border-color: #4C8DF0; color: #DDE3EC; background: #17243A;}
    .paso.hecho {border-color: #2F7D5B; color: #B9E4CF; background: #132620;}
    .estado {border-radius: 12px; padding: 12px 14px; margin: 6px 0 10px 0; font-size: 0.9rem; line-height: 1.5;}
    .estado.ok {background: #132620; border: 1px solid #2F7D5B; color: #CDEBDD;}
    .estado.pendiente {background: #2A2214; border: 1px solid #8A6A2A; color: #F0DDB4;}
    .modo {border-radius: 12px; padding: 12px 14px; border: 1px solid #243042; background: #161D27;
           color: #A8B3C4; height: 100%; font-size: 0.92rem;}
    .modo.elegido {border-color: #4C8DF0; background: #17243A; color: #DDE3EC;}
    .modo h4 {margin: 0 0 6px 0; font-size: 1rem; color: #E8EDF5;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cargar(contenido: bytes, nombre: str):
    df = leer_archivo(BytesIO(contenido), nombre)
    return validar_y_preparar(df)


def _bytes_demo(ruta: Path) -> bytes:
    if not ruta.exists():
        generar_excels_demo()
    return ruta.read_bytes()


def _a_porcentaje(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    df = df.copy()
    for c in columnas:
        df[c] = df[c] * 100
    return df



SEVERIDAD_LEGIBLE = {"critica": "Crítica", "alta": "Alta", "media": "Media", "sin alerta": "Sin alerta"}
DETECTOR_LEGIBLE = {
    "Reglas simples": "Reglas simples",
    "Isolation Forest": "Isolation Forest",
    "Unión (Cualquiera)": "Unión (cualquiera de las dos)",
    "Intersección (Ambas)": "Intersección (ambas)",
}


def _legible(df: pd.DataFrame) -> pd.DataFrame:
    """Solo para mostrar: tildes y mayúsculas correctas en valores internos."""
    df = df.copy()
    if "severidad_reglas" in df.columns:
        df["severidad_reglas"] = df["severidad_reglas"].map(SEVERIDAD_LEGIBLE).fillna(df["severidad_reglas"])
    if "detector" in df.columns:
        df["detector"] = df["detector"].map(DETECTOR_LEGIBLE).fillna(df["detector"])
    return df


def _ejecutar(contenido: bytes, nombre: str, modo: str, contamination: float) -> None:
    """Corre el análisis y guarda el resultado en la sesión."""
    df, val = cargar(contenido, nombre)
    usar_etiquetas = modo == MODO_CON and val.tiene_etiquetas
    if not usar_etiquetas:
        df = df.drop(columns=[c for c in COLUMNAS_ETIQUETA if c in df.columns])
    with st.spinner("Analizando los formularios E-14: variables derivadas → reglas → Isolation Forest → nivel de riesgo…"):
        res = analizar(df, contamination, usar_etiquetas)
    st.session_state["analisis"] = {
        "res": res, "val": val, "nombre": nombre, "modo": modo, "contenido": contenido,
        "contamination": contamination, "hora": datetime.now().strftime("%H:%M:%S"),
    }


def _reiniciar() -> None:
    for k in ["analisis", "archivo_subido"]:
        st.session_state.pop(k, None)


EXPLICACION_MODOS = {
    MODO_CON: (
        "🏷️ Con etiquetas",
        "El archivo trae las columnas <b>es_anomalia</b> y <b>tipo_anomalia</b>: la <b>respuesta correcta</b> de la "
        "simulación (qué mesas manipulamos). Permite <b>medir qué tan bien detectan</b> las técnicas (pestaña Evaluación). "
        "Las etiquetas <b>nunca</b> se usan para detectar, solo para comparar al final.",
    ),
    MODO_SIN: (
        "📄 Sin etiquetas",
        "Como en la <b>vida real</b>: no se sabe qué mesas fueron manipuladas. Las técnicas detectan igual, pero "
        "<b>no se puede medir su precisión</b> y la pestaña Evaluación queda desactivada. Si el archivo trae etiquetas, "
        "se ignoran.",
    ),
}


def _pasos(actual: int) -> None:
    nombres = ["Elegir tipo de archivo", "Subir y validar", "Analizar"]
    html = '<div class="pasos">'
    for i, n in enumerate(nombres, start=1):
        clase = "hecho" if i < actual else ("activo" if i == actual else "")
        marca = "✓ " if i < actual else ""
        html += f'<div class="paso {clase}"><b>Paso {i}</b>{marca}{n}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


analisis = st.session_state.get("analisis")

# ------------------------------------------------------------------------------
# Barra lateral: aviso ético + estado del análisis
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🗳️ Integridad electoral")
    st.caption("Detección de anomalías en un proceso electoral simulado")

    st.markdown("#### Estado")
    if analisis is None:
        st.markdown(
            '<div class="estado pendiente">⏳ <b>Sin analizar</b><br>Sigue los pasos de la pantalla principal: '
            "elige el tipo de archivo, súbelo y pulsa <b>Analizar</b>.</div>",
            unsafe_allow_html=True,
        )
    else:
        r = analisis["res"]
        st.markdown(
            f'<div class="estado ok">✅ <b>Análisis completado</b> ({analisis["hora"]})<br>'
            f'📁 {analisis["nombre"]}<br>'
            f'{EXPLICACION_MODOS[analisis["modo"]][0]}<br>'
            f'🧮 {textos.num(len(r.df))} mesas · contamination {analisis["contamination"]:.2f}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "📥 Descargar resultados (Excel)", data=construir_excel(r, riesgo_municipal(r, 0)),
            file_name="resultados_integridad_electoral.xlsx", width="stretch", type="primary",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        with st.form("reanalizar"):
            st.markdown("**Sensibilidad de Isolation Forest**")
            nuevo_c = st.slider(
                "Porcentaje de mesas que marcará como raras (contamination)", 0.02, 0.10, float(analisis["contamination"]), 0.01,
                help="Más alto: marca más mesas (detecta más, pero con más falsas alarmas). Más bajo: marca menos (alertas más seguras, pero se escapan más). Recomendado: 0,04.",
            )
            st.caption(f"Con {nuevo_c:.2f} se marcarán ≈ {textos.num(round(nuevo_c * len(r.df)))} de {textos.num(len(r.df))} mesas. "
                       "No cambia las reglas. Los resultados solo se actualizan al pulsar el botón.")
            if st.form_submit_button("🔁 Volver a analizar con este valor", width="stretch"):
                _ejecutar(analisis["contenido"], analisis["nombre"], analisis["modo"], nuevo_c)
                st.rerun()
        if st.button("📂 Cargar otro archivo", width="stretch", on_click=_reiniciar):
            st.rerun()

    with st.expander("⚖️ Aviso ético", expanded=analisis is None):
        st.markdown(textos.DESCARGO_ETICO)


# ------------------------------------------------------------------------------
# Pantalla de carga (obligatoria antes de ver resultados)
# ------------------------------------------------------------------------------
if analisis is None:
    st.markdown(
        '<div class="hero"><h1>Detección de anomalías en un proceso electoral simulado</h1>'
        "<p>Elige si tu archivo trae etiquetas, súbelo y pulsa <b>Analizar</b>. "
        "Verás qué mesas tienen patrones sospechosos que podrían afectar la integridad del sistema, y por qué.</p></div>",
        unsafe_allow_html=True,
    )

    subido = st.session_state.get("archivo_subido")
    val = None
    error_lectura = None
    if subido is not None:
        try:
            _, val = cargar(subido.getvalue(), subido.name)
        except Exception as exc:  # archivo ilegible
            error_lectura = str(exc)

    modo_elegido = st.session_state.get("modo", MODO_CON)
    modo_ok = val is not None and val.ok and not (modo_elegido == MODO_CON and not val.tiene_etiquetas)
    _pasos(3 if modo_ok else (2 if "modo" in st.session_state else 1))

    # Paso 1 ----------------------------------------------------------------
    with st.container(border=True):
        st.markdown("### 1 · ¿Tu archivo trae etiquetas?")
        modo = st.radio(
            "Tipo de archivo", [MODO_CON, MODO_SIN], key="modo", horizontal=True, label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        for col, m in zip((c1, c2), (MODO_CON, MODO_SIN)):
            titulo, texto = EXPLICACION_MODOS[m]
            col.markdown(
                f'<div class="modo {"elegido" if m == modo else ""}"><h4>{titulo}</h4>{texto}</div>',
                unsafe_allow_html=True,
            )

    # Paso 2 ----------------------------------------------------------------
    with st.container(border=True):
        st.markdown("### 2 · Sube tu archivo de mesas (resultados de los E-14)")
        st.file_uploader(
            "Excel (.xlsx) o CSV con una fila por mesa", type=["xlsx", "csv"], key="archivo_subido",
            help="Debe tener las columnas del formato del proyecto (ver hoja 'diccionario' del Excel de ejemplo).",
        )
        with st.expander("¿No tienes un archivo? Descarga un Excel de ejemplo y luego súbelo aquí"):
            d1, d2 = st.columns(2)
            d1.download_button("⬇️ Ejemplo con etiquetas", _bytes_demo(DEMO_CON_ETIQUETAS),
                               file_name=DEMO_CON_ETIQUETAS.name, width="stretch")
            d2.download_button("⬇️ Ejemplo sin etiquetas", _bytes_demo(DEMO_SIN_ETIQUETAS),
                               file_name=DEMO_SIN_ETIQUETAS.name, width="stretch")
            st.caption("Ambos son datos 100 % simulados (5.000 mesas). Incluyen las hojas `mesas`, `diccionario` y `leeme`.")

        if error_lectura:
            st.error(f"No se pudo leer el archivo: {error_lectura}")
        elif val is not None:
            st.markdown(f"**Validación de `{subido.name}`**")
            v1, v2 = st.columns(2)
            for i, (descripcion, aprobado) in enumerate(val.chequeos):
                (v1 if i % 2 == 0 else v2).markdown(f"{'✅' if aprobado else '❌'} {descripcion}")
            for error in val.errores:
                st.error(error)
            if val.ok:
                if modo == MODO_CON and not val.tiene_etiquetas:
                    st.error(
                        "Elegiste **Con etiquetas**, pero el archivo no tiene las columnas `es_anomalia` y `tipo_anomalia`. "
                        "Cambia a **Sin etiquetas** en el paso 1 o sube un archivo con etiquetas."
                    )
                elif modo == MODO_SIN and val.tiene_etiquetas:
                    st.info("El archivo trae etiquetas, pero elegiste **Sin etiquetas**: se ignorarán por completo.")
                else:
                    st.success("Archivo válido y coherente con el tipo elegido. Ya puedes analizarlo.")
        else:
            st.caption("Aún no has subido ningún archivo.")

    # Paso 3 ----------------------------------------------------------------
    with st.container(border=True):
        st.markdown("### 3 · Analizar")
        a, b = st.columns([2, 1], vertical_alignment="bottom")
        contamination = a.slider(
            "Sensibilidad de Isolation Forest: porcentaje de mesas que marcará como raras (contamination)",
            0.02, 0.10, IF_CONTAMINATION, 0.01,
        )
        if b.button("🔍 Analizar datos", type="primary", width="stretch", disabled=not modo_ok):
            _ejecutar(subido.getvalue(), subido.name, modo, contamination)
            st.rerun()
        if not modo_ok:
            st.caption("El botón se habilita cuando el archivo es válido y coincide con el tipo elegido.")
        st.info(textos.explicar_contamination(contamination, len(cargar(subido.getvalue(), subido.name)[0]) if val is not None and val.ok else None))

    with st.expander("ℹ️ ¿Qué hace este panel?"):
        st.markdown(
            "En una elección se diligencian miles de formularios E-14 y revisarlos todos a mano es inviable. Este panel "
            "aplica **análisis de datos** para encontrar mesas con comportamientos inusuales que podrían indicar "
            "**inconsistencias**, y así **priorizar qué E-14 revisar**. No detecta fraude real: trabaja con datos "
            "**100 % simulados**."
        )
        st.table(textos.CATALOGO_ANOMALIAS.set_index("Anomalía"))
    st.stop()


# ------------------------------------------------------------------------------
# Resultados (solo después de pulsar Analizar)
# ------------------------------------------------------------------------------
res = analisis["res"]
val = analisis["val"]
df = res.df

st.markdown(
    f'<div class="hero"><h1>Resultados del análisis</h1><p>📁 <b>{analisis["nombre"]}</b> · '
    f'{EXPLICACION_MODOS[analisis["modo"]][0]} · {textos.num(len(df))} mesas · analizado a las {analisis["hora"]}</p>'
    '<p style="margin-top:6px;font-size:0.9rem;">⚠️ Municipios reales, votos simulados: estos resultados no corresponden a ninguna elección real.</p></div>',
    unsafe_allow_html=True,
)

NOMBRES_PESTANAS = [
    "🏠 Inicio", "📁 Datos cargados", "📊 Análisis exploratorio", "📏 Reglas simples",
    "🌲 Isolation Forest", "🚩 Patrones sospechosos", "🎯 Evaluación", "📝 Hallazgos",
]
pestanas = st.tabs(NOMBRES_PESTANAS)


# 1 · Inicio ---------------------------------------------------------------------
with pestanas[0]:
    st.markdown(
        "En una elección se diligencian miles de formularios E-14 y revisarlos todos a mano es inviable. Este panel aplica "
        "**análisis de datos** para encontrar las mesas con comportamientos inusuales que podrían indicar "
        "**inconsistencias que afectan la integridad del sistema**, y así **priorizar qué E-14 revisar**. "
        "Cada fila del archivo es el **formulario E-14** de una mesa: los votos por candidato, el voto en blanco, "
        "los nulos y las tarjetas no marcadas que anotan los jurados al cerrar la votación a las 4:00 p. m., junto con "
        "los **ciudadanos habilitados** para votar en esa mesa según el censo electoral. Las alertas sirven para "
        "decidir qué E-14 revisar o qué recuentos solicitar ante las **comisiones escrutadoras**.\n\n"
        "Los departamentos y municipios son reales de Colombia, pero **todos los votos son simulados**: el objetivo "
        "no es detectar fraude real, sino mostrar cómo el análisis de datos encuentra patrones sospechosos."
    )
    st.subheader("¿Qué anomalías buscamos?")
    st.table(textos.CATALOGO_ANOMALIAS.set_index("Anomalía"))
    st.subheader("¿Con qué técnicas?")
    a, b = st.columns(2)
    with a.container(border=True):
        st.markdown("**📏 Técnica 1 · Reglas simples**\n\nSeis validaciones con umbrales justificados (el E-14 debe cuadrar, no puede haber más votos que ciudadanos habilitados, etc.). Precisas y fáciles de explicar.")
    with b.container(border=True):
        st.markdown("**🌲 Técnica 2 · Isolation Forest**\n\nModelo no supervisado que encuentra mesas cuya *combinación* de valores es rara, aunque ningún valor por sí solo cruce un umbral.")
    st.subheader("Cómo leer los resultados")
    st.markdown(
        "1. Recorre las pestañas en orden: datos → análisis exploratorio → técnicas → patrones sospechosos.\n"
        "2. En **Patrones sospechosos**, elige una mesa para ver **por qué** es sospechosa.\n"
        "3. Revisa la **Evaluación** (solo con etiquetas) y los **Hallazgos**.\n"
        "4. Descarga los resultados o cambia la sensibilidad de Isolation Forest desde la barra lateral."
    )


# 2 · Datos cargados -------------------------------------------------------------
with pestanas[1]:
    st.header("Datos cargados")
    st.subheader("Validación del archivo")
    for descripcion, aprobado in val.chequeos:
        st.markdown(f"{'✅' if aprobado else '❌'} {descripcion}")
    for error in val.errores:
        st.error(error)
    for aviso in val.avisos:
        if "etiquetas" in aviso and analisis["modo"] == MODO_SIN:
            continue
        st.info(aviso)
    if analisis["modo"] == MODO_SIN and val.tiene_etiquetas:
        st.info("El archivo traía etiquetas, pero se eligió **Sin etiquetas**: se descartaron antes del análisis.")

    st.subheader("Resumen")
    k = st.columns(6)
    k[0].metric("Mesas", textos.num(len(df)))
    k[1].metric("Departamentos", df["departamento"].nunique())
    k[2].metric("Municipios", df["municipio"].nunique())
    k[3].metric("Ciudadanos habilitados", textos.num(df["votantes_habilitados"].sum()))
    k[4].metric("Votos en los E-14", textos.num(df["total_votos_reportado"].sum()))
    k[5].metric("Participación media", textos.pct(df["participacion"].mean()))
    st.info(textos.interpretar_datos(df))

    st.subheader("Vista previa")
    buscar = st.text_input("Buscar una mesa por su código", placeholder="Ej.: M01854")
    cols_orig = ["mesa_id", "departamento", "municipio", "zona", "votantes_habilitados",
                 "votos_cand_A", "votos_cand_B", "votos_cand_C", "votos_cand_D",
                 "votos_blanco", "votos_nulos", "votos_no_marcados", "total_votos_reportado"]
    vista = df.sort_values("mesa_id")[cols_orig]
    if buscar:
        vista = vista[vista["mesa_id"].str.contains(buscar.strip(), case=False)]
    st.dataframe(vista.head(100), hide_index=True, width="stretch", column_config=CFG)
    st.caption(f"Se muestran hasta 100 filas de {textos.num(len(vista))}.")

# 3 · EDA --------------------------------------------------------------------
with pestanas[2]:
    st.header("Análisis exploratorio")
    st.markdown("Antes de detectar, entendemos **cómo se ve una mesa normal**. Así los umbrales se justifican con los datos.")
    st.plotly_chart(graficos.figura_1_participacion(df), width="stretch")
    a, b = st.columns([2, 3])
    a.plotly_chart(graficos.apoyo_resultados_nacionales(res.eda["resultados_nacionales"]), width="stretch")
    b.plotly_chart(graficos.apoyo_participacion_departamento(df), width="stretch")
    st.info(textos.interpretar_eda(res.eda["hallazgos"], res.eda["resultados_nacionales"]))
    with st.expander("Estadísticas descriptivas de las variables"):
        st.dataframe(res.eda["resumen"].round(3), width="stretch")
    with st.expander("Participación por departamento y zona (tabla)"):
        tabla = _a_porcentaje(res.eda["participacion_depto"], ["media", "desv", "mediana", "min", "max"])
        st.dataframe(tabla, hide_index=True, width="stretch",
                     column_config=CFG)

# 4 · Reglas -----------------------------------------------------------------
with pestanas[3]:
    st.header("Técnica 1 · Reglas simples")
    st.markdown("Cada regla es una verificación que haría un jurado o una comisión escrutadora al revisar un E-14. El **puntaje** suma los pesos de las reglas que se activan y define la severidad. R1 y R2 corresponden a causales de reclamación del Código Electoral colombiano (art. 192, num. 5 y 11).")
    st.table(textos.tabla_reglas(res.eda["hallazgos"]).set_index("Regla"))
    sev = df["severidad_reglas"].value_counts()
    k = st.columns(4)
    k[0].metric("🔴 Crítica (≥ 3)", int(sev.get("critica", 0)))
    k[1].metric("🟠 Alta (2)", int(sev.get("alta", 0)))
    k[2].metric("🟡 Media (1)", int(sev.get("media", 0)))
    k[3].metric("⚪ Sin alerta", textos.num(sev.get("sin alerta", 0)))
    st.plotly_chart(graficos.apoyo_mesas_por_regla(df, COLUMNAS_REGLAS, textos.NOMBRES_REGLAS), width="stretch")
    st.info(textos.interpretar_reglas(df))
    st.subheader("Mesas alertadas por las reglas")
    alertadas = df[df["alerta_reglas"]][["mesa_id", "municipio", "participacion", "pct_max_candidato", "pct_nulos",
                                         "diferencia_aritmetica", "reglas_activadas", "puntaje_reglas", "severidad_reglas"]]
    st.dataframe(_legible(_a_porcentaje(alertadas, ["participacion", "pct_max_candidato", "pct_nulos"])), hide_index=True,
                 width="stretch",
                 column_config=CFG)

# 5 · Isolation Forest -------------------------------------------------------
with pestanas[4]:
    st.header("Técnica 2 · Isolation Forest")
    st.markdown(textos.EXPLICACION_IF)
    a, b = st.columns([1, 2])
    with a:
        st.markdown("**Variables que usa el modelo** (no usa las etiquetas ni los códigos de mesa):")
        st.dataframe(textos.FEATURES_IF_TABLA, hide_index=True, width="stretch")
    with b:
        st.plotly_chart(graficos.figura_3_score_if(df, res.umbral_if, res.tiene_etiquetas), width="stretch")
    st.plotly_chart(graficos.apoyo_perfil_if(res.perfil_if, textos.NOMBRES_FEATURES), width="stretch")
    st.info(textos.interpretar_if(df, res.perfil_if, res.umbral_if, res.contamination))

# 6 · Patrones sospechosos ---------------------------------------------------
with pestanas[5]:
    st.header("Patrones sospechosos y mesas a revisar")
    st.markdown(
        "**Nivel de riesgo:** 🔴 **alto** = ambas técnicas coinciden o una regla crítica (R1/R2) · "
        "🟠 **medio** = una sola técnica · ⚪ **bajo** = sin alertas."
    )
    cuenta = df["nivel_riesgo"].value_counts()
    k = st.columns(3)
    k[0].metric("🔴 Riesgo alto", int(cuenta.get("alto", 0)))
    k[1].metric("🟠 Riesgo medio", int(cuenta.get("medio", 0)))
    k[2].metric("⚪ Riesgo bajo", textos.num(cuenta.get("bajo", 0)))

    st.plotly_chart(graficos.figura_2_huella(df), width="stretch")

    min_mesas = st.slider("Figura 5 · mostrar solo municipios con al menos esta cantidad de mesas", 0, 100, 20, 5)
    st.info(textos.explicar_min_mesas(min_mesas, riesgo_municipal(res, 0)))
    riesgo = riesgo_municipal(res, min_mesas)
    st.plotly_chart(graficos.figura_5_riesgo_municipio(riesgo), width="stretch")
    st.info(textos.interpretar_patrones(df, riesgo))

    st.subheader("Tabla de priorización")
    f1, f2, f3 = st.columns(3)
    niveles = f1.multiselect("Nivel de riesgo", ["alto", "medio", "bajo"], default=["alto", "medio"], placeholder="Todos los niveles")
    deptos = f2.multiselect("Departamento", sorted(df["departamento"].unique()), placeholder="Todos los departamentos")
    munis_disp = sorted(df[df["departamento"].isin(deptos)]["municipio"].unique()) if deptos else sorted(df["municipio"].unique())
    munis = f3.multiselect("Municipio", munis_disp, placeholder="Todos los municipios")
    tabla = df[df["nivel_riesgo"].isin(niveles)]
    if deptos:
        tabla = tabla[tabla["departamento"].isin(deptos)]
    if munis:
        tabla = tabla[tabla["municipio"].isin(munis)]
    cols = ["prioridad", "mesa_id", "departamento", "municipio", "zona", "nivel_riesgo", "reglas_activadas",
            "puntaje_reglas", "score_if", "participacion", "pct_max_candidato", "pct_nulos", "deteccion"]
    st.dataframe(_a_porcentaje(tabla[cols], ["participacion", "pct_max_candidato", "pct_nulos"]),
                 hide_index=True, width="stretch",
                 column_config=CFG)
    st.caption(f"{textos.num(len(tabla))} mesas con los filtros actuales, ordenadas por prioridad de revisión.")

    st.subheader("Ficha de mesa: ¿por qué es sospechosa?")
    opciones = tabla["mesa_id"].tolist() or df["mesa_id"].tolist()
    mesa = st.selectbox("Elige una mesa", opciones, index=0)
    fila = df[df["mesa_id"] == mesa].iloc[0]
    icono = {"alto": "🔴", "medio": "🟠", "bajo": "⚪"}[fila["nivel_riesgo"]]
    st.markdown(f"### {icono} {fila['mesa_id']} · {fila['municipio']} ({fila['zona']}) — riesgo **{fila['nivel_riesgo']}**")
    a, b = st.columns([2, 3])
    with a:
        conteos = pd.DataFrame({
            "Concepto": ["Ciudadanos habilitados", "Candidato A", "Candidato B", "Candidato C", "Candidato D",
                         "Voto en blanco", "Nulos", "No marcados", "Suma de conteos", "Total escrito en el E-14"],
            "Valor": [fila["votantes_habilitados"], fila["votos_cand_A"], fila["votos_cand_B"], fila["votos_cand_C"],
                      fila["votos_cand_D"], fila["votos_blanco"], fila["votos_nulos"], fila["votos_no_marcados"],
                      fila["suma_componentes"], fila["total_votos_reportado"]],
        })
        st.dataframe(conteos, hide_index=True, width="stretch")
    with b:
        k = st.columns(3)
        k[0].metric("Participación", textos.pct(fila["participacion"]),
                    f"{(fila['participacion'] - fila['mediana_participacion_municipio']) * 100:+.1f} puntos frente al municipio",
                    delta_color="off")
        k[1].metric("Candidato más votado", textos.pct(fila["pct_max_candidato"]))
        k[2].metric("Puntaje Isolation Forest", f"{fila['score_if']:.3f}", f"umbral {res.umbral_if:.3f}", delta_color="off")
        st.markdown("**Motivos:**")
        for frase in textos.explicar_mesa(fila, res.umbral_if, res.eda["hallazgos"]["pct_nulos_mediana"]):
            st.markdown(f"- {frase}")
        if fila["nivel_riesgo"] != "bajo":
            st.markdown("➡️ **Conviene revisar el formulario E-14 físico de esta mesa** (y, si corresponde, solicitar el recuento ante la comisión escrutadora) antes de aceptar su resultado.")
        if res.tiene_etiquetas:
            tipo = graficos.NOMBRES_TIPO.get(fila["tipo_anomalia"], "ninguna (mesa normal)")
            extra = " · atípica pero legítima" if fila.get("nota_simulacion") == "extremo_legitimo" else ""
            st.caption(f"🔍 Solo para validar (respuesta de la simulación): {tipo}{extra}")

# 7 · Evaluación -------------------------------------------------------------
with pestanas[6]:
    st.header("Evaluación de los detectores")
    if res.evaluacion is None:
        st.info(
            "En un caso real **no se conoce la respuesta correcta**, así que no se puede medir la precisión. "
            "Para ver esta pestaña, pulsa **Cargar otro archivo** en la barra lateral, elige **Con etiquetas** y sube un archivo que las incluya."
        )
    else:
        ev = res.evaluacion
        st.markdown(
            "Como los datos son simulados, sabemos qué mesas manipulamos. **Precisión** = de las mesas alertadas, cuántas "
            "eran realmente anómalas (una falsa alarma = revisión innecesaria de un E-14). **Recall** = de las anomalías, cuántas se "
            "detectaron (una no detectada = inconsistencia sin revisar). **F1** combina ambas."
        )
        m = ev["metricas"]
        st.dataframe(_legible(_a_porcentaje(m, ["precision", "recall", "f1"])), hide_index=True, width="stretch",
                     column_config=CFG)

        st.subheader("Matrices de confusión")
        cols = st.columns(2)
        for col, nombre in zip(cols, ["Reglas simples", "Isolation Forest"]):
            r = m.set_index("detector").loc[nombre]
            matriz = pd.DataFrame(
                {"Predicho: alerta": [int(r["VP"]), int(r["FP"])], "Predicho: sin alerta": [int(r["FN"]), int(r["VN"])]},
                index=["Real: anómala", "Real: normal"],
            )
            col.markdown(f"**{nombre}**")
            col.dataframe(matriz, width="stretch")

        st.plotly_chart(graficos.figura_4_recall_tipo(ev["recall_tipo"]), width="stretch")

        a, b = st.columns(2)
        with a:
            n_ext = int(ev["fp_extremos"]["total_extremos"].iloc[0])
            if n_ext > 0:
                st.markdown(f"**Falsas alarmas en las {n_ext} mesas atípicas pero legítimas**")
                st.dataframe(_legible(_a_porcentaje(ev["fp_extremos"], ["tasa_fp_extremos"])).drop(columns=["total_extremos"]), hide_index=True,
                             width="stretch", column_config=CFG)
            else:
                st.caption("Este archivo no marca mesas atípicas pero legítimas (columna nota_simulacion), "
                           "así que no se puede medir ese tipo de falsa alarma.")
        with b:
            st.plotly_chart(graficos.apoyo_sensibilidad(ev["sensibilidad"], res.contamination), width="stretch")

        st.subheader("Anomalías que no detectó ninguna técnica")
        fn = ev["falsos_negativos"].copy()
        if len(fn):
            fn["tipo_anomalia"] = fn["tipo_anomalia"].map(graficos.NOMBRES_TIPO)
            st.dataframe(_a_porcentaje(fn.drop(columns=["nota_simulacion"]), ["participacion", "pct_max_candidato"]),
                         hide_index=True, width="stretch",
                         column_config=CFG)
            st.info(textos.explicar_falsos_negativos(ev["falsos_negativos"], res.umbral_if))
        else:
            st.success("Ninguna anomalía se escapó con los parámetros actuales.")

# 8 · Hallazgos --------------------------------------------------------------
with pestanas[7]:
    st.header("Hallazgos, riesgos y limitaciones")
    st.subheader("Hallazgos principales")
    for h in textos.hallazgos(res, riesgo_municipal(res, 20)):
        st.markdown(f"- {h}")
    st.success(textos.conclusion())
    st.subheader("Riesgos y limitaciones")
    for r in textos.RIESGOS_LIMITACIONES:
        st.markdown(f"- {r}")
    st.subheader("Consideraciones éticas")
    st.markdown(
        "- Todos los votos son simulados. Los departamentos y municipios son reales, pero los candidatos, las mesas y los resultados son ficticios; no hay partidos ni personas reales.\n"
        "- No se hacen afirmaciones sobre procesos electorales reales.\n"
        "- Una alerta es una **señal para revisar**, no una acusación: la decisión final corresponde a las autoridades electorales (jurados y comisiones escrutadoras) tras revisar el E-14 físico."
    )
