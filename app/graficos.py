"""Gráficos interactivos (Plotly) de la interfaz.

Las 5 figuras oficiales replican las de `src/visualize.py` y usan la misma paleta de `src/config.py`.
Las demás funciones son "vistas de apoyo".
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import UMBRAL_R3_PARTICIPACION

# Paleta para tema oscuro (validada contra el fondo #141A23: banda de luminosidad, croma,
# separación para daltonismo y contraste ≥ 3:1). Mismo significado que la paleta clara de
# src/config.py que usan las figuras PNG del informe.
COLOR_NORMAL = "#5B6577"       # Gris recesivo: sin alerta
COLOR_SOLO_REGLAS = "#CC7426"  # Naranja: solo reglas
COLOR_SOLO_IF = "#4C8DF0"      # Azul: solo Isolation Forest
COLOR_AMBAS = "#E5605E"        # Rojo: ambas técnicas

COLOR_FONDO = "#141A23"        # Superficie de los gráficos
COLOR_NEUTRO = "#8FA3BF"       # Serie única (vistas de apoyo)
COLOR_NEUTRO_OSCURO = "#56657D"
COLOR_TEXTO = "#DDE3EC"
COLOR_TEXTO_SUAVE = "#9AA6B8"
COLOR_GRILLA = "#253041"

COLORES_DETECCION = {
    "Sin alerta": COLOR_NORMAL,
    "Solo reglas": COLOR_SOLO_REGLAS,
    "Solo Isolation Forest": COLOR_SOLO_IF,
    "Ambas técnicas": COLOR_AMBAS,
}
ORDEN_DETECCION = list(COLORES_DETECCION.keys())

NOMBRES_TIPO = {
    "sobre_participacion": "Sobreparticipación",
    "relleno_urnas": "Relleno de urnas",
    "voto_unanime": "Voto unánime",
    "inconsistencia_aritmetica": "Inconsistencia aritmética",
    "numeros_redondos": "Números redondos",
    "nulos_excesivos": "Nulos excesivos",
}


def _estilo(fig: go.Figure, titulo: str, alto: int = 460) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16, color=COLOR_TEXTO), x=0.01, xanchor="left"),
        template="plotly_dark",
        paper_bgcolor=COLOR_FONDO,
        plot_bgcolor=COLOR_FONDO,
        height=alto,
        margin=dict(l=16, r=24, t=64, b=16),
        font=dict(size=13, color=COLOR_TEXTO_SUAVE),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title_text="",
                    font=dict(color=COLOR_TEXTO), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1F2835", bordercolor="#33405A", font=dict(size=13, color=COLOR_TEXTO)),
        bargap=0.25,
        separators=",.",
    )
    fig.update_xaxes(gridcolor=COLOR_GRILLA, zeroline=False, linecolor=COLOR_GRILLA, title_font=dict(color=COLOR_TEXTO_SUAVE))
    fig.update_yaxes(gridcolor=COLOR_GRILLA, zeroline=False, linecolor=COLOR_GRILLA, title_font=dict(color=COLOR_TEXTO_SUAVE))
    return fig


def _linea_vertical(fig: go.Figure, x: float, texto: str, color: str = COLOR_TEXTO, lado: str = "derecha") -> None:
    fig.add_vline(x=x, line_width=2, line_dash="dash", line_color=color)
    fig.add_annotation(
        x=x, y=1, yref="paper", text=texto, showarrow=False,
        xanchor="left" if lado == "derecha" else "right", yanchor="top",
        xshift=4 if lado == "derecha" else -4, font=dict(size=12, color=color), bgcolor="rgba(20,26,35,0.85)",
    )


# ------------------------------------------------------------------------------
# Figuras oficiales (1 a 5)
# ------------------------------------------------------------------------------
def figura_1_participacion(df: pd.DataFrame) -> go.Figure:
    """Figura 1: distribución de la participación con los umbrales R3 (95 %) y R1 (100 %)."""
    fig = px.histogram(
        df, x=df["participacion"] * 100, nbins=60, color_discrete_sequence=[COLOR_NEUTRO],
    )
    fig.update_traces(
        marker_line_color=COLOR_FONDO, marker_line_width=1,
        hovertemplate="Participación: %{x:.0f} %<br>Mesas: %{y}<extra></extra>",
    )
    _linea_vertical(fig, UMBRAL_R3_PARTICIPACION * 100, "R3: 95 %", COLOR_SOLO_REGLAS, lado="izquierda")
    _linea_vertical(fig, 100, "R1: 100 %", COLOR_AMBAS)
    fig.update_layout(showlegend=False, xaxis_title="Participación (% de ciudadanos habilitados)", yaxis_title="Número de mesas")
    return _estilo(fig, "Figura 1 · Distribución de la participación por mesa")


def figura_2_huella(df: pd.DataFrame) -> go.Figure:
    """Figura 2: huella electoral (participación vs % del candidato más votado), coloreada por detección."""
    datos = df.assign(
        participacion_pct=df["participacion"] * 100,
        pct_max_pct=df["pct_max_candidato"] * 100,
        reglas=df["reglas_activadas"].replace("", "ninguna"),
    )
    fig = go.Figure()
    for categoria in ORDEN_DETECCION:
        sub = datos[datos["deteccion"] == categoria]
        if sub.empty:
            continue
        es_normal = categoria == "Sin alerta"
        fig.add_trace(go.Scattergl(
            x=sub["participacion_pct"], y=sub["pct_max_pct"], mode="markers",
            name=f"{categoria} ({len(sub)})",
            marker=dict(
                size=6 if es_normal else 9,
                color=COLORES_DETECCION[categoria],
                opacity=0.45 if es_normal else 0.95,
                line=dict(width=0 if es_normal else 1.5, color=COLOR_FONDO),
            ),
            customdata=sub[["mesa_id", "municipio", "reglas", "nivel_riesgo"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
                "Participación: %{x:.1f} %<br>Candidato más votado: %{y:.1f} %<br>"
                "Reglas: %{customdata[2]}<br>Riesgo: %{customdata[3]}<extra></extra>"
            ),
        ))
    fig.update_layout(
        xaxis_title="Participación (% de ciudadanos habilitados)",
        yaxis_title="% de votos válidos del candidato más votado",
    )
    return _estilo(fig, "Figura 2 · Huella electoral: participación frente a concentración del voto", alto=540)


def figura_3_score_if(df: pd.DataFrame, umbral: float, con_etiquetas: bool) -> go.Figure:
    """Figura 3: distribución del score de Isolation Forest con el umbral de alerta."""
    fig = go.Figure()
    if con_etiquetas and "es_anomalia" in df.columns:
        grupos = [
            ("Mesas normales (simulación)", df[df["es_anomalia"] == 0], COLOR_NORMAL),
            ("Mesas manipuladas (simulación)", df[df["es_anomalia"] == 1], COLOR_AMBAS),
        ]
        for nombre, sub, color in grupos:
            fig.add_trace(go.Histogram(
                x=sub["score_if"], name=f"{nombre} ({len(sub)})", histnorm="probability density",
                nbinsx=60, marker_color=color, opacity=0.65,
                hovertemplate="Puntaje: %{x:.3f}<br>Densidad: %{y:.1f}<extra></extra>",
            ))
        fig.update_layout(barmode="overlay", yaxis_title="Densidad (cada grupo suma 1)")
    else:
        fig.add_trace(go.Histogram(
            x=df["score_if"], nbinsx=60, marker_color=COLOR_NEUTRO, name="Mesas",
            marker_line_color=COLOR_FONDO, marker_line_width=1,
            hovertemplate="Puntaje: %{x:.3f}<br>Mesas: %{y}<extra></extra>",
        ))
        fig.update_layout(showlegend=False, yaxis_title="Número de mesas")
    _linea_vertical(fig, umbral, f"Umbral de alerta: {umbral:.3f}".replace(".", ","), COLOR_SOLO_IF)
    fig.update_layout(xaxis_title="Puntaje de anomalía (mayor = mesa más rara)")
    return _estilo(fig, "Figura 3 · Puntaje de anomalía de Isolation Forest")


def figura_4_recall_tipo(recall_tipo: pd.DataFrame) -> go.Figure:
    """Figura 4: % detectado de cada tipo de anomalía, Reglas vs Isolation Forest."""
    datos = recall_tipo.assign(tipo=recall_tipo["tipo_anomalia"].map(NOMBRES_TIPO))
    fig = go.Figure()
    for col, nombre, color in [
        ("recall_reglas", "Reglas simples", COLOR_SOLO_REGLAS),
        ("recall_if", "Isolation Forest", COLOR_SOLO_IF),
    ]:
        fig.add_trace(go.Bar(
            y=datos["tipo"], x=datos[col] * 100, name=nombre, orientation="h", marker_color=color,
            text=[f"{v * 100:.0f} %" for v in datos[col]], textposition="outside",
            textfont=dict(color=COLOR_TEXTO),
            customdata=datos["total_inyectadas"],
            hovertemplate="%{y}<br>" + nombre + ": %{x:.1f} % de %{customdata} mesas<extra></extra>",
        ))
    fig.update_layout(
        barmode="group", xaxis=dict(range=[0, 115], title="% de mesas manipuladas que se detectaron (recall)"),
        yaxis=dict(autorange="reversed", title=""),
    )
    return _estilo(fig, "Figura 4 · Detección por tipo de anomalía", alto=480)


def figura_5_riesgo_municipio(riesgo: pd.DataFrame, top: int = 15) -> go.Figure:
    """Figura 5: municipios con mayor % de mesas en riesgo alto (con cantidad en la etiqueta)."""
    datos = riesgo.head(top).iloc[::-1]
    fig = go.Figure(go.Bar(
        y=datos["municipio"], x=datos["pct_riesgo_alto"], orientation="h", marker_color=COLOR_AMBAS,
        text=[f"{p:.1f} % ({a} de {t})".replace(".", ",") for p, a, t in zip(datos["pct_riesgo_alto"], datos["mesas_riesgo_alto"], datos["total_mesas"])],
        textposition="outside", textfont=dict(color=COLOR_TEXTO),
        customdata=datos[["departamento", "mesas_riesgo_alto", "total_mesas"]].values,
        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>%{customdata[1]} de %{customdata[2]} mesas en riesgo alto<br>%{x:.1f} %<extra></extra>",
    ))
    max_x = float(datos["pct_riesgo_alto"].max()) if len(datos) else 1.0
    fig.update_layout(
        showlegend=False, xaxis=dict(range=[0, max_x * 1.35], title="% de mesas del municipio en riesgo alto"),
        yaxis_title="",
    )
    return _estilo(fig, f"Figura 5 · Municipios con mayor proporción de mesas en riesgo alto (top {min(top, len(riesgo))})", alto=max(380, 28 * len(datos) + 120))


# ------------------------------------------------------------------------------
# Vistas de apoyo
# ------------------------------------------------------------------------------
def apoyo_resultados_nacionales(res_nac: pd.DataFrame) -> go.Figure:
    datos = res_nac[res_nac["opcion"].str.startswith("Candidato")].iloc[::-1]
    fig = go.Figure(go.Bar(
        y=datos["opcion"], x=datos["pct_validos"], orientation="h", marker_color=COLOR_NEUTRO,
        text=[f"{p:.1f} %".replace(".", ",") for p in datos["pct_validos"]], textposition="outside",
        textfont=dict(color=COLOR_TEXTO),
        customdata=datos["votos"],
        hovertemplate="%{y}: %{x:.1f} % (%{customdata:,} votos)<extra></extra>",
    ))
    fig.update_layout(showlegend=False, xaxis=dict(range=[0, datos["pct_validos"].max() * 1.25], title="% de votos válidos"), yaxis_title="")
    return _estilo(fig, "Vista de apoyo · Resultados nacionales por candidato", alto=320)


def apoyo_participacion_departamento(df: pd.DataFrame) -> go.Figure:
    datos = df.assign(participacion_pct=df["participacion"] * 100)
    fig = px.box(
        datos, x="departamento", y="participacion_pct", color="zona",
        color_discrete_map={"urbana": COLOR_NEUTRO, "rural": COLOR_NEUTRO_OSCURO},
        category_orders={"zona": ["urbana", "rural"], "departamento": sorted(datos["departamento"].unique())},
        points=False,
    )
    fig.update_traces(hovertemplate=None)
    fig.update_layout(xaxis_title="", yaxis_title="Participación (%)")
    return _estilo(fig, "Vista de apoyo · Participación por departamento y zona", alto=420)


def apoyo_mesas_por_regla(df: pd.DataFrame, columnas_reglas: list, nombres: dict) -> go.Figure:
    conteos = pd.DataFrame({
        "regla": [nombres[c] for c in columnas_reglas],
        "mesas": [int(df[c].sum()) for c in columnas_reglas],
    }).iloc[::-1]
    fig = go.Figure(go.Bar(
        y=conteos["regla"], x=conteos["mesas"], orientation="h", marker_color=COLOR_SOLO_REGLAS,
        text=conteos["mesas"], textposition="outside", textfont=dict(color=COLOR_TEXTO),
        hovertemplate="%{y}: %{x} mesas<extra></extra>",
    ))
    fig.update_layout(showlegend=False, xaxis=dict(range=[0, conteos["mesas"].max() * 1.2 + 1], title="Mesas que activan la regla"), yaxis_title="")
    return _estilo(fig, "Vista de apoyo · Mesas que activa cada regla", alto=340)


def apoyo_perfil_if(perfil: pd.DataFrame, nombres: dict) -> go.Figure:
    datos = perfil.assign(nombre=perfil["feature"].map(nombres)).iloc[::-1]
    fig = go.Figure(go.Bar(
        y=datos["nombre"], x=datos["diferencia"], orientation="h", marker_color=COLOR_SOLO_IF,
        text=[f"{v:+.2f}".replace(".", ",") for v in datos["diferencia"]], textposition="outside",
        textfont=dict(color=COLOR_TEXTO),
        hovertemplate="%{y}<br>Diferencia: %{x:+.2f} desviaciones estándar<extra></extra>",
    ))
    lim = float(datos["diferencia"].abs().max()) * 1.3
    fig.update_layout(showlegend=False, xaxis=dict(range=[-lim, lim], title="Media de mesas alertadas − media de no alertadas (en desviaciones estándar)"), yaxis_title="")
    return _estilo(fig, "Vista de apoyo · ¿En qué se diferencian las mesas que marca Isolation Forest?", alto=460)


def apoyo_sensibilidad(sens: pd.DataFrame, actual: Optional[float] = None) -> go.Figure:
    fig = go.Figure()
    for col, nombre, color, dash in [
        ("precision", "Precisión", COLOR_NEUTRO, "dash"),
        ("recall", "Recall", COLOR_SOLO_IF, "solid"),
        ("f1", "F1", COLOR_AMBAS, "dot"),
    ]:
        fig.add_trace(go.Scatter(
            x=sens["contamination"] * 100, y=sens[col] * 100, name=nombre, mode="lines+markers",
            line=dict(color=color, width=2, dash=dash), marker=dict(size=9),
            hovertemplate=nombre + ": %{y:.1f} % (contamination %{x:.0f} %)<extra></extra>",
        ))
    if actual is not None:
        _linea_vertical(fig, actual * 100, f"Valor actual: {actual * 100:.0f} %", COLOR_TEXTO_SUAVE)
    fig.update_layout(xaxis_title="contamination (% de mesas que marca el modelo)", yaxis=dict(title="%", range=[0, 105]))
    return _estilo(fig, "Vista de apoyo · Resultados según el valor de contamination", alto=400)
