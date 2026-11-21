# Detección de Anomalías en un Proceso Electoral Simulado

> **Descargo ético obligatorio:**
> *Todos los votos de este proyecto son simulados. Los departamentos y municipios son reales de Colombia, pero los resultados, las mesas y los candidatos son ficticios: no representan ninguna elección real ni hacen afirmaciones sobre ella. Una alerta indica una inconsistencia que merece revisión, no una prueba de fraude.*

---

## 1. Descripción del Proyecto

Este repositorio contiene una solución integral y reproducible para la **auditoría de integridad de datos y detección de anomalías en actas de votación**, enmarcada en la ciberseguridad aplicada a procesos democráticos.

El análisis se centra en **5.000 mesas de votación simuladas** en 48 municipios reales de 8 departamentos de Colombia (votos simulados), evaluando inconsistencias mediante dos técnicas analíticas complementarias:
1. **Reglas simples deterministas:** Verificación estricta de límites físicos, cuadre aritmético del acta y umbrales basados en el dominio.
2. **Isolation Forest (Aprendizaje no supervisado):** Detección multivariada de valores atípicos que eluden reglas fijas (ej. correlaciones anómalas de participación y concentración de voto).

Los resultados se combinan en un indicador clasificado de **Nivel de Riesgo** (`alto`, `medio`, `bajo`) para priorizar inspecciones físicas de actas en auditorías electorales.

---

## 2. Requisitos e Instalación

### Requisitos previos
- Python 3.12 o 3.14
- `pip` y soporte para entornos virtuales (`venv`)

### Configuración del entorno
```bash
# Clonar o situarse en el directorio del proyecto
cd ProyectoFinalCiberseguridad

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias requeridas
pip install -r requirements.txt
```

---

## 3. Cómo Ejecutar el Proyecto

### Pipeline completo de punta a punta (un solo comando)
Regenera el dataset sintético, ejecuta el análisis exploratorio (EDA), aplica ambas técnicas de detección, evalúa métricas cuantitativas contra el Ground Truth y exporta las 5 visualizaciones oficiales:
```bash
python -m src.main
```

### Ejecutar la suite completa de pruebas automatizadas
Verifica reproducibilidad, esquema de columnas, coherencia de conteos, activación de reglas y ausencia estricta de fuga de datos (*No Data Leakage*):
```bash
pytest -v
```

### Demostración guiada interactiva
Para visualizar el flujo interactivo paso a paso y la inspección de actas:
```bash
jupyter lab notebooks/demo.ipynb
# o abrir directamente notebooks/demo.ipynb en VS Code / Cursor
```

### Interfaz web (panel de análisis)
Página local de demostración que presenta todo el análisis de forma visual. No agrega técnicas nuevas:
reutiliza las funciones de `src/` (mismas reglas, mismo Isolation Forest, mismos resultados).
```bash
python -m src.generate_demo_excel   # genera data/demo/*.xlsx (la app también los crea si faltan)
streamlit run app/app.py            # abre http://localhost:8501
```
1. **Paso 1:** elige si tu archivo trae etiquetas. *Con etiquetas* incluye la respuesta correcta de la simulación (`es_anomalia`, `tipo_anomalia`) y habilita la pestaña Evaluación; *Sin etiquetas* es el escenario realista (si el archivo trae etiquetas, se descartan).
2. **Paso 2:** sube manualmente tu Excel/CSV (si no tienes uno, descarga un ejemplo desde el mismo paso y súbelo). La página muestra la validación del archivo.
3. **Paso 3:** pulsa **Analizar datos**. Nada se procesa hasta ese momento; la barra lateral muestra si hay un análisis completado, de qué archivo y a qué hora.
4. Recorre las 8 pestañas: Inicio → Datos cargados → Análisis exploratorio → Reglas simples → Isolation Forest → Patrones sospechosos (incluye la ficha de cada mesa) → Evaluación → Hallazgos.
5. Desde la barra lateral: descargar resultados en Excel, volver a analizar con otro `contamination` o **cargar otro archivo**.

Las etiquetas (`es_anomalia`, `tipo_anomalia`, `nota_simulacion`) se separan antes de llamar a los detectores y solo se usan en la pestaña Evaluación (verificado en `tests/test_app_logic.py`).

---

## 4. Estructura del Repositorio

```
ProyectoFinalCiberseguridad/
├── README.md                    # Descripción, descargo ético e instrucciones de ejecución
├── PLAN_PROYECTO.md             # Plan maestro de requerimientos y diseño
├── requirements.txt             # Dependencias base de Python
├── requirements.lock.txt        # Versiones congeladas para reproducibilidad
├── pytest.ini                   # Configuración del motor de pruebas
├── .gitignore                   # Exclusiones de Git
├── src/
│   ├── __init__.py
│   ├── config.py                # Constantes centralizadas, rutas y umbrales justificados
│   ├── generate_dataset.py      # Fase 2: Simulación de 5.000 actas e inyección de anomalías
│   ├── features.py              # Fase 3: Cálculo de variables derivadas (sin data leakage)
│   ├── eda.py                   # Fase 3: Análisis exploratorio y agregaciones
│   ├── rules.py                 # Fase 4: Técnica 1 (Reglas simples deterministas)
│   ├── isolation_forest.py      # Fase 4: Técnica 2 (Isolation Forest no supervisado)
│   ├── evaluate.py              # Fase 5: Métricas contra ground truth y análisis de errores
│   ├── visualize.py             # Fase 6: Generación de las 5 figuras oficiales
│   └── main.py                  # Fase 7: Orquestador integral del pipeline
├── tests/
│   ├── test_generate_dataset.py # Pruebas del generador y reproducibilidad
│   ├── test_rules.py            # Pruebas unitarias de activación de reglas simples
│   └── test_no_leakage.py       # Pruebas de prevención de fuga de información
├── notebooks/
│   └── demo.ipynb               # Cuaderno de demostración paso a paso para video
├── data/
│   ├── raw/
│   │   └── mesas_simuladas.csv  # Dataset con ground truth (generado)
│   └── processed/
│       ├── features_mesas.csv   # Variables derivadas del EDA
│       └── resultados_mesas.csv # Dataset con features, scores, alertas y nivel de riesgo
├── outputs/
│   ├── figures/                 # Las 5 figuras oficiales en alta resolución (200 DPI)
│   │   ├── fig1_distribucion_participacion.png
│   │   ├── fig2_huella_electoral.png
│   │   ├── fig3_score_isolation_forest.png
│   │   ├── fig4_recall_por_tipo.png
│   │   └── fig5_riesgo_por_municipio.png
│   └── tables/                  # Tablas de métricas, EDA y sensibilidad en formato CSV
├── reports/
│   ├── informe.md               # Fuente técnica completa del informe final
│   └── Informe_Final.pdf        # Documento PDF final para entrega
└── docs/
    ├── decisiones.md            # Justificación de umbrales, decisiones y análisis de errores
    └── guion_video.md           # Guion narrativo estructurado (<= 8 minutos)
```

---

## 5. Resumen de Resultados Principales

- **Mesas analizadas:** 5.000 (formularios E-14 simulados) en 48 municipios reales de 8 departamentos de Colombia.
- **Calibración con Colombia:** participación media simulada 54,5 % (real en la primera vuelta presidencial de 2022: 54,9 %); voto en blanco ≈ 1,7 % y nulos ≈ 1,2 %.
- **Anomalías inyectadas (respuesta conocida):** 200 mesas (4 %).
- **Casos extremos legítimos:** 40 mesas rurales con alta participación y sin manipulación (para medir falsas alarmas).
- **Rendimiento de los detectores:**
  - **Reglas simples:** precisión **98,9 %**, recall **94,0 %**, F1 **0,964**.
  - **Isolation Forest:** precisión **62,5 %**, recall **62,5 %**, F1 **0,625**; marca las 40 mesas legítimas atípicas.
  - **Unión (cualquiera de las dos):** detecta **199 de las 200** anomalías (recall 99,5 %).
  - **Intersección (ambas):** precisión **99,1 %**, para la revisión prioritaria.
