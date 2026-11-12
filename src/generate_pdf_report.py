"""Generador del informe final en formato PDF (reports/Informe_Final.pdf).

Compila el informe técnico completo integrando portada, resumen, metodología,
tablas de resultados y las 5 figuras oficiales generadas por el proyecto.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

from src.config import (
    OUTPUTS_FIG_DIR,
    OUTPUTS_TAB_DIR,
    REPORTS_DIR,
)


def _crear_pagina_texto(pdf: PdfPages, titulo: str, parrafos: list[str]) -> None:
    """Crea una página de texto estructurada con título y párrafos formateados."""
    fig = plt.figure(figsize=(8.5, 11))  # Formato Carta (Letter)
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.82])
    ax.axis("off")

    y_pos = 1.0
    ax.text(0.0, y_pos, titulo, fontsize=15, fontweight="bold", color="#1F4E79")
    y_pos -= 0.05

    for p in parrafos:
        if p.startswith("## "):
            y_pos -= 0.03
            ax.text(0.0, y_pos, p[3:], fontsize=13, fontweight="bold", color="#2F5597")
            y_pos -= 0.04
        elif p.startswith("### "):
            y_pos -= 0.02
            ax.text(0.0, y_pos, p[4:], fontsize=11, fontweight="bold", color="#333333")
            y_pos -= 0.035
        elif p.startswith("> "):
            ax.text(0.02, y_pos, p[2:], fontsize=9.5, style="italic", color="#555555", wrap=True)
            y_pos -= 0.05
        else:
            # Párrafo normal
            ax.text(0.0, y_pos, p, fontsize=10, color="#222222", wrap=True)
            # Estimar salto según longitud del texto
            salto = max(0.04, (len(p) // 90 + 1) * 0.028)
            y_pos -= salto

        if y_pos < 0.05:
            break

    pdf.savefig(fig)
    plt.close(fig)


def _crear_pagina_figura(pdf: PdfPages, ruta_fig: Path, titulo_fig: str, descripcion: str) -> None:
    """Inserta una de las 5 figuras oficiales con título y pie explicativo."""
    fig = plt.figure(figsize=(8.5, 11))

    # Título superior
    ax_tit = fig.add_axes([0.1, 0.90, 0.8, 0.06])
    ax_tit.axis("off")
    ax_tit.text(0.0, 0.5, titulo_fig, fontsize=13, fontweight="bold", color="#1F4E79", va="center")

    # Imagen
    if ruta_fig.exists():
        img = mpimg.imread(str(ruta_fig))
        ax_img = fig.add_axes([0.1, 0.30, 0.8, 0.58])
        ax_img.imshow(img)
        ax_img.axis("off")

    # Pie de figura explicativo
    ax_desc = fig.add_axes([0.1, 0.08, 0.8, 0.18])
    ax_desc.axis("off")
    ax_desc.text(0.0, 0.85, "Interpretación analítica:", fontsize=10.5, fontweight="bold", color="#2F5597")
    ax_desc.text(0.0, 0.70, descripcion, fontsize=9.5, color="#333333", wrap=True)

    pdf.savefig(fig)
    plt.close(fig)


def compilar_informe_pdf() -> Path:
    """Compila el informe PDF completo en reports/Informe_Final.pdf."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = REPORTS_DIR / "Informe_Final.pdf"

    with PdfPages(pdf_path) as pdf:
        # PÁGINA 1: PORTADA
        fig_portada = plt.figure(figsize=(8.5, 11))
        ax_p = fig_portada.add_axes([0.12, 0.12, 0.76, 0.76])
        ax_p.axis("off")

        ax_p.text(0.5, 0.88, "UNIVERSIDAD ICESI", fontsize=14, fontweight="bold", ha="center", color="#555555")
        ax_p.text(0.5, 0.84, "FACULTAD DE INGENIERÍA - PROYECTO FINAL DE CIBERSEGURIDAD", fontsize=11, ha="center", color="#777777")
        ax_p.plot([0.1, 0.9], [0.80, 0.80], color="#1F4E79", linewidth=2.5)

        ax_p.text(0.5, 0.68, "Auditoría de Integridad Electoral y Detección\nde Anomalías en un Proceso Electoral Simulado",
                  fontsize=18, fontweight="bold", ha="center", color="#1F4E79")

        ax_p.text(0.5, 0.54, "Evaluación de Reglas Deterministas e Isolation Forest en 5.000 Mesas de Votación",
                  fontsize=12, style="italic", ha="center", color="#333333")

        ax_p.text(0.5, 0.38, "Integrantes del Grupo:\n[NOMBRE INTEGRANTE 1] - [CÓDIGO]\n[NOMBRE INTEGRANTE 2] - [CÓDIGO]\n[NOMBRE INTEGRANTE 3] - [CÓDIGO]",
                  fontsize=11, ha="center", color="#222222")

        ax_p.text(0.5, 0.22, "Fecha de Entrega: Noviembre de 2026\nCali, Colombia", fontsize=10.5, ha="center", color="#555555")

        descargo_box = (
            "Descargo Ético: Todos los datos analizados son 100 % simulados en la ficticia República de Simulandia.\n"
            "Los resultados no representan hechos ni elecciones reales. Una alerta indica una inconsistencia estadística\n"
            "para priorizar auditoría manual, nunca una acusación concluyente de fraude."
        )
        ax_p.text(0.5, 0.08, descargo_box, fontsize=8.5, ha="center", style="italic", color="#777777",
                  bbox=dict(boxstyle="round,pad=0.5", facecolor="#F2F2F2", edgecolor="#CCCCCC"))

        pdf.savefig(fig_portada)
        plt.close(fig_portada)

        # PÁGINA 2: RESUMEN Y CONTEXTO
        _crear_pagina_texto(
            pdf,
            "1. Resumen Ejecutivo y Contexto de Ciberseguridad",
            [
                "## Resumen Ejecutivo",
                "Este informe documenta el desarrollo y evaluación de una metodología analítica para la auditoría de integridad en actas electorales simuladas. Sobre un censo de 5.000 mesas en la República de Simulandia, se inyectaron 200 anomalías conocidas correspondientes a 6 patrones habituales de adulteración electoral y 40 casos extremos legítimos.",
                "Se diseñaron y compararon dos enfoques: Reglas Simples Deterministas y el modelo de aprendizaje no supervisado Isolation Forest. Las reglas alcanzaron un 97.4 % de precisión y 94.0 % de recall en inconsistencias directas, mientras que Isolation Forest capturó anomalías multivariadas complejas como el relleno de urnas. La estrategia combinada de Unión logró un recall global del 96.5 % (193 de 200 anomalías capturadas), consolidando una herramienta efectiva para la priorización forense de mesas a auditar.",
                "## Contexto: La Integridad Electoral como Problema de Ciberseguridad",
                "Con la digitalización de la consolidación electoral y la transmisión remota de datos, la seguridad de las elecciones ha evolucionado desde el resguardo físico hacia la protección de la integridad de los datos. Incidentes de transcripción errónea, manipulación forzada de actas, o inyección de votos atentan contra la confianza ciudadana.",
                "Dado que recontar físicamente el 100 % de las mesas es logísticamente inviable, los métodos analíticos de detección de anomalías operan como un sistema de alerta temprana: focalizan el despliegue de peritos y jurados hacia las urnas con mayor probabilidad de inconsistencia material.",
            ]
        )

        # PÁGINA 3: METODOLOGÍA Y CATÁLOGO DE ANOMALÍAS
        _crear_pagina_texto(
            pdf,
            "2. Metodología y Catálogo de Anomalías Inyectadas",
            [
                "## Catálogo de Anomalías de Integridad (Ground Truth)",
                "Para validar objetivamente los detectores, se definieron 6 categorías de inconsistencia inyectadas sin reemplazo sobre 200 mesas (4.0 % del total):",
                "- Sobre-participación (30 mesas): Votos reportados superiores al censo electoral (> 100 %). Físicamente imposible; indica duplicación o inflación de actas.",
                "- Relleno de urnas (45 mesas): Inyección focalizada en 3 municipios que eleva la participación al 93–100 % sumando votos al Candidato A.",
                "- Voto unánime (35 mesas): Mesas donde un candidato recibe >= 92 % de votos válidos bajo alta participación, simulando coacción o actas prefabricadas.",
                "- Inconsistencia aritmética (35 mesas): Discrepancias directas entre el total reportado y la suma de votos parciales por candidato, blanco y nulos.",
                "- Números redondos (25 mesas): Conteos de candidatos que son todos múltiplos de 10, violando las distribuciones estocásticas discretas naturales.",
                "- Nulos excesivos (30 mesas): Reclasificación maliciosa del 15 al 35 % de votos válidos de la oposición como votos nulos.",
                "## Casos Extremos Legítimos (40 mesas)",
                "Se incluyeron 40 mesas rurales pequeñas (<= 200 habilitados) con alta participación (85–94 %) y marcada preferencia comunitaria genuina (75–88 %), sin ninguna manipulación (es_anomalia = 0). Su objetivo es medir con rigor la tasa de falsos positivos en comunidades homogéneas.",
            ]
        )

        # PÁGINA 4: TÉCNICAS IMPLEMENTADAS
        _crear_pagina_texto(
            pdf,
            "3. Técnicas de Detección Implementadas",
            [
                "## Técnica 1: Reglas Simples Deterministas",
                "Evalúa límites lógicos y umbrales basados en el conocimiento del dominio electoral:",
                "- R1 (Sobre-participación): votos > habilitados (Peso 3, Crítica).",
                "- R2 (Inconsistencia aritmética): diferencia reportado vs. suma > 0 (Peso 3, Crítica).",
                "- R3 (Participación extrema): participacion >= 0.95 (Peso 2, Alta).",
                "- R4 (Voto concentrado): voto maximo >= 0.90 y votos validos >= 50 (Peso 2, Alta).",
                "- R5 (Nulos excesivos): porcentaje nulos >= 12 % (Peso 1, Media).",
                "- R6 (Números redondos): los 4 candidatos con votos múltiplos de 10 (Peso 1, Media).",
                "## Técnica 2: Isolation Forest (No Supervisado)",
                "Entrenado sin etiquetas previas mediante 300 árboles de decisión con tasa de contaminación operativa del 4 % (0.04). Emplea 12 variables derivadas estandarizadas.",
                "El algoritmo explota el principio de que los outliers multivariados se encuentran aislados en regiones poco densas del espacio muestral, requiriendo significativamente menor profundidad media de partición que las actas típicas.",
                "## Combinación y Nivel de Riesgo",
                "- Riesgo ALTO: Alerta simultánea de ambas técnicas o severidad de reglas crítica (R1/R2).",
                "- Riesgo MEDIO: Alerta generada por una sola técnica.",
                "- Riesgo BAJO: Sin ninguna alerta.",
            ]
        )

        # PÁGINA 5: RESULTADOS Y MÉTRICAS
        _crear_pagina_texto(
            pdf,
            "4. Resultados Cuantitativos y Evaluación",
            [
                "## Métricas de Clasificación Global (Ground Truth)",
                "- Reglas Simples: Precisión = 97.41 %, Recall = 94.00 %, F1 = 0.9567 (193 alertadas, 188 VP, 5 FP).",
                "- Isolation Forest: Precisión = 58.50 %, Recall = 58.50 %, F1 = 0.5850 (200 alertadas, 117 VP, 83 FP).",
                "- Unión (Cualquiera): Precisión = 69.93 %, Recall = 96.50 %, F1 = 0.8109 (276 alertadas, 193 VP, 83 FP).",
                "- Intersección (Ambas): Precisión = 95.73 %, Recall = 56.00 %, F1 = 0.7066 (117 alertadas, 112 VP, 5 FP).",
                "## Complementariedad de Técnicas por Tipo de Anomalía",
                "- Las reglas alcanzaron un recall perfecto del 100 % en sobre-participación, voto unánime, inconsistencia aritmética, números redondos y nulos excesivos.",
                "- En relleno de urnas, las reglas alcanzaron 73.3 % (solo las mesas que superaron el 95 % de participación). Isolation Forest aportó detección multivariada independiente, elevando el recall de la Unión al 84.4 %.",
                "## Falsos Positivos en Casos Extremos Legítimos",
                "- Las reglas simples solo marcaron 3 de las 40 mesas rurales legítimas (7.5 % FP).",
                "- Isolation Forest marcó las 40 mesas legítimas (100 % FP), demostrando analíticamente que los modelos estadísticos no supervisados penalizan el comportamiento atípico pero genuino de comunidades rurales homogéneas.",
            ]
        )

        # PÁGINAS 6 A 10: LAS 5 FIGURAS OFICIALES
        _crear_pagina_figura(
            pdf,
            OUTPUTS_FIG_DIR / "fig1_distribucion_participacion.png",
            "Figura 1: Distribución de la Participación Electoral en las Actas",
            "Histograma con 60 intervalos de la participación electoral en las 5.000 mesas. La masa normal se concentra entre el 40 % y el 75 % con media en 58.4 %. Las líneas discontinuas señalan los umbrales de alerta R3 (95 %) y R1 (100 %), evidenciando la cola anómala de mesas que sobrepasan los límites físicos del censo."
        )

        _crear_pagina_figura(
            pdf,
            OUTPUTS_FIG_DIR / "fig2_huella_electoral.png",
            "Figura 2: Huella Electoral 2D (Participación vs. Voto Máximo por Candidato)",
            "Dispersión inspirada en Klimek et al. (2012). Las actas normales forman una nube densa central en gris. Las actas con alerta de ambas técnicas (en rojo) se desplazan hacia el cuadrante superior derecho (asistencia extrema combinada con triunfo cuasi-unánime), patrón inequívoco de manipulación coordinada."
        )

        _crear_pagina_figura(
            pdf,
            OUTPUTS_FIG_DIR / "fig3_score_isolation_forest.png",
            "Figura 3: Densidad de Scores de Isolation Forest por Clase Real",
            "Estimación de densidad de Kernel (KDE) para actas normales versus actas manipuladas. El algoritmo desplaza la distribución anómala hacia la derecha. La región intermedia de solapamiento entre scores 0.50 y 0.55 explica matemáticamente la generación de falsos positivos y falsos negativos."
        )

        _crear_pagina_figura(
            pdf,
            OUTPUTS_FIG_DIR / "fig4_recall_por_tipo.png",
            "Figura 4: Comparación de Recall por Tipo de Anomalía Inyectada",
            "Sensibilidad de detección desagregada para las 6 categorías. Demuestra la complementariedad: las reglas logran 100 % en transgresiones formales lógicas, mientras que la combinación con Isolation Forest incrementa sustancialmente la cobertura de alteraciones complejas como relleno de urnas (84.4 %)."
        )

        _crear_pagina_figura(
            pdf,
            OUTPUTS_FIG_DIR / "fig5_riesgo_por_municipio.png",
            "Figura 5: Top 15 Municipios con Mayor Concentración de Mesas en Riesgo Alto",
            "Distribución territorial de las actas clasificadas en nivel de riesgo alto. Municipios como Bruma-Mun05 (16.4 %) y Estela-Mun01 (15.4 %) presentan concentraciones elevadas, coincidiendo con los focos territoriales donde se concentró el relleno de urnas, permitiendo priorizar auditorías sobre el terreno."
        )

        # PÁGINA 11: DISCUSIÓN, RIESGOS Y CONCLUSIONES
        _crear_pagina_texto(
            pdf,
            "5. Discusión, Riesgos, Ética y Conclusiones",
            [
                "## Discusión y Riesgos Operativos",
                "- Limitación de umbrales fijos: Si las reglas se conocen públicamente, un adversario puede calibrar la manipulación al 94.8 % de participación para eludir la alerta determinista.",
                "- Sesgo contra la ruralidad: Como demostró el experimento con extremos legítimos, los modelos no supervisados penalizan comunidades pequeñas y unificadas. Una alerta nunca debe desencadenar la anulación automática de una mesa sin cotejo documental.",
                "- Riesgo de polarización política: La divulgación irresponsable de índices de anomalía sin verificación forense puede ser instrumentalizada para desacreditar elecciones legítimas.",
                "## Conclusiones",
                "1. Se diseñó, implementó y validó con éxito una solución automatizada de auditoría electoral para 5.000 actas de votación, reproducible con un único comando.",
                "2. La estrategia de Unión entre Reglas Simples e Isolation Forest ofrece un balance óptimo con un Recall global del 96.50 % (capturando 193 de las 200 anomalías).",
                "3. Para la priorización táctica inmediata de peritajes forenses, la Intersección aporta una precisión del 95.73 %, garantizando máxima eficiencia en el uso de los recursos de auditoría electoral.",
                "## Referencias Principales",
                "- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. IEEE ICDM, 413-422.",
                "- Klimek, P., Yegorov, Y., Hanel, R., & Thurner, S. (2012). Statistical detection of systematic election irregularities. PNAS, 109(41), 16469-16474.",
                "- Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. JMLR, 12, 2825-2830.",
            ]
        )

    print(f"Informe PDF generado exitosamente en: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    compilar_informe_pdf()

