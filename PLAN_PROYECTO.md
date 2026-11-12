# Plan de implementación — Detección de anomalías en un proceso electoral simulado

> **Para el agente de IA que ejecute este plan:** lee este documento completo antes de escribir código.
> Sigue las fases **en orden**, no te saltes las verificaciones de cada fase y no tomes decisiones que contradigan
> las "Reglas obligatorias" (sección 2). Si algo no está especificado, elige la opción más simple y deja
> constancia de la decisión en `docs/decisiones.md`.

---

## 0. Resumen del proyecto

| Ítem | Valor |
|---|---|
| Objetivo | Identificar **anomalías** (no "fraude real") en datos de un proceso electoral **100 % simulado**. |
| Unidad de análisis | La **mesa de votación** (una fila = el acta de una mesa). |
| Técnica 1 | **Reglas simples** (validaciones deterministas de integridad y umbrales justificados). |
| Técnica 2 | **Isolation Forest** (detección no supervisada de outliers multivariados). |
| Evaluación | Como el dataset es simulado, se inyectan anomalías con **etiqueta conocida (ground truth)** → se miden precisión, recall y F1. |
| Visualizaciones | **Exactamente 5** figuras (el enunciado pide 3–5). |
| Entregables | Código reproducible + Informe PDF (contexto, metodología, resultados, visualizaciones, conclusiones) + guion de video ≤ 8 min. |
| Fecha de entrega | 3 de junio. |

### Requisitos del enunciado → dónde se cumplen

| Requisito del enunciado | Cómo se cumple | Fase |
|---|---|---|
| Dataset simulado (creado o adaptado) | Generador sintético `src/generate_dataset.py` con semilla fija | 2 |
| Máximo 2 técnicas de detección | Reglas simples + Isolation Forest (y **nada más**) | 4 |
| 3 a 5 visualizaciones | 5 figuras en `outputs/figures/` | 6 |
| Explicar claramente los hallazgos | Sección "Resultados" y "Discusión" del informe + tablas | 5, 7 |
| Fase 1: definir tipo de anomalía | Catálogo de 6 tipos de anomalía (sección 4) | 1 |
| Fase 3: análisis exploratorio | `src/eda.py` + tabla resumen | 3 |
| Fase 5: evaluar resultados | `src/evaluate.py` (métricas, recall por tipo, sensibilidad) | 5 |
| Fase 6: riesgos y limitaciones | Sección dedicada del informe | 7 |
| Informe PDF | `reports/Informe_Final.pdf` | 7 |
| Video ≤ 8 min (explicación + demo) | Guion en `docs/guion_video.md` | 8 |
| Ética: solo datos simulados, sin afirmaciones sobre elecciones reales | Nombres ficticios, descargo en README, informe y video | Todas |
| Enfoque en análisis, justificación e interpretación | Cada umbral/parámetro se justifica en `src/config.py` y en el informe | Todas |

---

## 1. Qué NO se debe hacer (fuera de alcance)

- ❌ Deep learning (redes neuronales, autoencoders, LSTM, etc.).
- ❌ Interfaces web (Flask, Django, Streamlit, Dash...). La demo se hace por terminal y/o notebook.
- ❌ Sistemas en producción, APIs, bases de datos, Docker.
- ❌ Una tercera técnica de detección (ni clustering, ni z-score como detector, ni Ley de Benford como detector). La estadística descriptiva **sí** se usa en el EDA, pero no como mecanismo de detección.
- ❌ Usar datos electorales reales, nombres de países, partidos, candidatos o lugares reales.
- ❌ Afirmar o sugerir que un proceso electoral real tuvo fraude.

## 2. Reglas obligatorias para el agente

1. **Reproducibilidad:** toda aleatoriedad usa `SEED = 42` desde `src/config.py` (`numpy.random.default_rng(SEED)` y `random_state=SEED`).
2. **Sin fuga de información (data leakage):** las columnas `es_anomalia`, `tipo_anomalia` y `nota_simulacion` **nunca** se usan como entrada de los detectores. Solo se usan en `src/evaluate.py` y en las figuras de evaluación. Debe existir un test que lo verifique.
3. **Toda constante** (umbrales, cantidades, parámetros) vive en `src/config.py`, con un comentario que justifique su valor. Nada de "números mágicos" en otros archivos.
4. **Idioma:** código con nombres en español o inglés consistente (se recomienda español para columnas y textos de figuras, ya que el informe es en español). Etiquetas de gráficos, títulos y tablas **en español**.
5. **Ejecución de punta a punta con un solo comando:** `python -m src.main` regenera dataset, EDA, detección, evaluación y figuras.
6. **No modificar** archivos de `data/raw/` a mano; siempre se regeneran con el script.
7. Al terminar cada fase, ejecutar su verificación (sección "Verificación") antes de pasar a la siguiente.
8. Commits pequeños por fase con mensaje descriptivo (ej.: `feat(fase2): generador de dataset sintético`).

---

## 3. Estructura del repositorio a crear

```
ProyectoFinalCiberseguridad/
├── README.md                    # Descripción, descargo ético, cómo ejecutar
├── PLAN_PROYECTO.md             # Este documento
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py                # Constantes, rutas, umbrales y su justificación
│   ├── generate_dataset.py      # Fase 2: dataset sintético + inyección de anomalías
│   ├── features.py              # Cálculo de variables derivadas (compartido)
│   ├── eda.py                   # Fase 3: análisis exploratorio
│   ├── rules.py                 # Fase 4: Técnica 1 — reglas simples
│   ├── isolation_forest.py      # Fase 4: Técnica 2 — Isolation Forest
│   ├── evaluate.py              # Fase 5: métricas y análisis de errores
│   ├── visualize.py             # Fase 6: las 5 figuras
│   └── main.py                  # Orquestador de todo el pipeline
├── tests/
│   ├── test_generate_dataset.py
│   ├── test_rules.py
│   └── test_no_leakage.py
├── notebooks/
│   └── demo.ipynb               # Demo guiada para el video (opcional pero recomendado)
├── data/
│   ├── raw/mesas_simuladas.csv          # Salida del generador (con ground truth)
│   └── processed/resultados_mesas.csv   # Dataset + features + salidas de detectores
├── outputs/
│   ├── figures/                 # fig1_...png a fig5_...png
│   └── tables/                  # CSVs de métricas y resúmenes
├── reports/
│   ├── informe.md               # Fuente del informe
│   └── Informe_Final.pdf        # Entregable
└── docs/
    ├── decisiones.md            # Registro de decisiones y justificaciones
    └── guion_video.md           # Guion del video ≤ 8 min
```

### `requirements.txt`

```
numpy
pandas
scikit-learn
matplotlib
seaborn
pytest
jupyter
```

> El sistema tiene Python 3.14. Crear entorno con `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
> Si algún paquete no tiene wheel para 3.14, usar Python 3.12 (`python3.12 -m venv .venv`) y anotarlo en `docs/decisiones.md`.
> Después de instalar, fijar versiones con `pip freeze > requirements.lock.txt` (dejar ambos archivos).

### `.gitignore`

```
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
.pytest_cache/
```

(Los CSV y figuras **sí** se versionan: son pequeños y permiten revisar resultados sin ejecutar.)

---

## FASE 1 — Definir qué anomalías se quieren detectar

### 1.1 Contexto simulado

Se simula la elección presidencial de primera vuelta de un país ficticio, **"República de Simulandia"**,
con 8 departamentos ficticios, 48 municipios ficticios y **5 000 mesas**. Hay **4 candidatos ficticios**
("Candidato A", "Candidato B", "Candidato C", "Candidato D") más votos en blanco, nulos y no marcados.

### 1.2 Catálogo de anomalías (las que se inyectan y se buscan detectar)

Cada anomalía representa una **inconsistencia** que en un sistema real ameritaría revisión manual del acta
(no una prueba de fraude). Esta tabla debe aparecer en el informe.

| # | `tipo_anomalia` | Qué simula | Por qué es sospechosa | Cantidad |
|---|---|---|---|---|
| 1 | `sobre_participacion` | Más votos que votantes habilitados | Imposible físicamente: participación > 100 % | 30 |
| 2 | `relleno_urnas` | Votos extra agregados a un candidato hasta llevar la participación a 93–100 % | Participación y voto por un candidato anormalmente altos a la vez | 45 |
| 3 | `voto_unanime` | ≥ 92 % de los votos válidos a un solo candidato con participación alta | Patrón de actas "fabricadas" | 35 |
| 4 | `inconsistencia_aritmetica` | El total reportado no coincide con la suma de los componentes | Error o manipulación al transcribir el acta | 35 |
| 5 | `numeros_redondos` | Todos los conteos de candidatos son múltiplos de 10 | Cifras inventadas tienden a ser redondas | 25 |
| 6 | `nulos_excesivos` | Votos de la oposición reclasificados como nulos (15–35 % del total) | Anulación selectiva de votos | 30 |
| | **Total** | | | **200 (4 % de las mesas)** |

Además se incluyen **40 "casos extremos legítimos"** (etiqueta normal = 0): mesas rurales pequeñas con
participación alta (85–94 %) y preferencia fuerte (75–88 % por un candidato), **sin** ninguna manipulación.
Sirven para mostrar de forma honesta que los detectores producen **falsos positivos** y por qué
una alerta no equivale a fraude. Se marcan con `nota_simulacion = "extremo_legitimo"`.

### Entregable de la fase
- `docs/decisiones.md` con esta tabla y la justificación de cada tipo.

---

## FASE 2 — Construir el dataset simulado

**Archivo:** `src/generate_dataset.py` · **Salida:** `data/raw/mesas_simuladas.csv`

### 2.1 Esquema de columnas (en este orden)

| Columna | Tipo | Descripción |
|---|---|---|
| `mesa_id` | str | `M00001` … `M05000` |
| `departamento` | str | Nombre ficticio (ver 2.2) |
| `municipio` | str | `<Departamento>-Mun01` … `-Mun06` |
| `zona` | str | `urbana` / `rural` |
| `puesto` | str | `<municipio>-P01`, … (agrupar cada 20 mesas consecutivas del municipio) |
| `votantes_habilitados` | int | Votantes inscritos en la mesa |
| `votos_cand_A` … `votos_cand_D` | int | Votos por candidato |
| `votos_blanco` | int | Votos en blanco |
| `votos_nulos` | int | Votos nulos |
| `votos_no_marcados` | int | Tarjetas no marcadas |
| `total_votos_reportado` | int | Total escrito en el acta (normalmente = suma de los 7 conteos anteriores) |
| `hora_reporte` | str (ISO) | Fecha-hora de transmisión del acta, ej. `2026-03-08T17:42:00` |
| `es_anomalia` | int 0/1 | **Ground truth** (solo para evaluación) |
| `tipo_anomalia` | str | `ninguna` o uno de los 6 tipos |
| `nota_simulacion` | str | `""` o `extremo_legitimo` |

### 2.2 Generación de mesas normales (paso a paso)

Todo con `rng = np.random.default_rng(SEED)`.

1. **Geografía:** 8 departamentos ficticios: `Aurora, Bruma, Cumbre, Delta, Estela, Fénix, Granito, Horizonte`.
   Cada uno con 6 municipios → 48 municipios.
2. **Asignar mesas a municipios:** pesos `w = rng.dirichlet(np.ones(48) * 2)`; cantidades con
   `rng.multinomial(5000, w)`; si algún municipio queda con < 20 mesas, reasignar desde el más grande hasta tener ≥ 20.
3. **Zona:** cada municipio es `urbano` con probabilidad 0.6, si no `rural`. Todas sus mesas heredan la zona.
4. **Votantes habilitados:** urbana → `rng.integers(250, 601)`; rural → `rng.integers(80, 301)`.
5. **Participación (turnout):**
   - Media municipal `mu_m ~ Normal(0.58, 0.07)`, recortada a `[0.35, 0.80]`.
   - Por mesa: `p ~ Beta(mu_m * 60, (1 - mu_m) * 60)`, recortada a `[0.20, 0.92]`.
   - `total = round(p * habilitados)`.
6. **Preferencias por candidato:**
   - Base nacional `[0.38, 0.32, 0.18, 0.12]` (A, B, C, D).
   - Por departamento: `rng.dirichlet(base * 40)`; por municipio: `rng.dirichlet(pref_depto * 80)`;
     por mesa: `rng.dirichlet(pref_muni * 150)`.
7. **Composición del total:** probabilidades `[blanco=0.02, nulos=0.03, no_marcados=0.01]` y el
   restante 0.94 repartido según las preferencias de la mesa. `conteos = rng.multinomial(total, probs)`.
8. `total_votos_reportado = suma de los 7 conteos`.
9. **Hora de reporte:** cierre a las 16:00 del `2026-03-08`. Retraso en minutos
   `~ LogNormal(mean=log(60), sigma=0.5)` en urbana y `LogNormal(log(120), 0.5)` en rural, recortado a 7 h 59 min.
   (Esta variable se usa solo en el EDA; ninguna anomalía depende de ella.)
10. Inicializar `es_anomalia=0`, `tipo_anomalia="ninguna"`, `nota_simulacion=""`.

### 2.3 Casos extremos legítimos (40 mesas)

Elegir 40 mesas **rurales** al azar con `habilitados ≤ 200`. Regenerar sus votos con participación
`U(0.85, 0.94)`, un candidato favorito al azar con participación de voto válido `U(0.75, 0.88)` y el resto
repartido por Dirichlet entre los otros tres. Blanco/nulos/no marcados con las mismas probabilidades base.
Mantener `es_anomalia=0` y poner `nota_simulacion="extremo_legitimo"`. Estas mesas **no** pueden ser
elegidas después para inyectar anomalías.

### 2.4 Inyección de anomalías (200 mesas)

Elegir mesas **sin reemplazo** (cada mesa recibe como máximo un tipo). Para cada mesa elegida poner
`es_anomalia=1` y su `tipo_anomalia`. Después de cada modificación, todos los conteos deben ser enteros ≥ 0.

| Tipo | Selección de mesas | Modificación exacta |
|---|---|---|
| `sobre_participacion` (30) | Al azar | `nuevo_total = round(habilitados * U(1.02, 1.30))`. Escalar todos los conteos proporcionalmente y redondear; ajustar la diferencia de redondeo en `votos_cand_A`. `total_votos_reportado = suma`. |
| `relleno_urnas` (45) | **Concentradas en 3 municipios** elegidos al azar (≈15 por municipio) para que exista un patrón geográfico | `objetivo = floor(habilitados * U(0.93, 1.00))`; `extra = max(objetivo - total, 0)`; sumar `extra` a `votos_cand_A`. `total_votos_reportado = suma`. |
| `voto_unanime` (35) | Al azar | Participación `U(0.85, 0.99)`; candidato ganador al azar con `U(0.92, 1.00)` de los votos válidos; resto de válidos repartido entre los otros 3; blanco+nulos+no marcados ≤ 2 % del total. `total_votos_reportado = suma`. |
| `inconsistencia_aritmetica` (35) | Al azar | No tocar los conteos; `total_votos_reportado = suma + delta`, con `delta` entero en `[-60, -5] ∪ [5, 60]`. |
| `numeros_redondos` (25) | Al azar con `total ≥ 100` | Cada `votos_cand_X = max(10, round(votos_cand_X / 10) * 10)`. `total_votos_reportado = suma`. |
| `nulos_excesivos` (30) | Al azar | `k = round(total * U(0.15, 0.35))`; restar `k` votos de B, C y D proporcionalmente a sus conteos (sin dejar negativos) y sumarlos a `votos_nulos`. El total no cambia. |

### 2.5 Requisitos del script

- Función `generar_dataset(seed: int = SEED) -> pd.DataFrame` y bloque `if __name__ == "__main__":` que guarda el CSV.
- Imprimir al final: número de filas, conteo por `tipo_anomalia` y número de extremos legítimos.

### Verificación de la fase 2

```bash
python -m src.generate_dataset
pytest tests/test_generate_dataset.py -v
```

`tests/test_generate_dataset.py` debe comprobar:
- 5 000 filas y las columnas exactas del esquema 2.1.
- Ningún conteo negativo.
- `value_counts` de `tipo_anomalia` coincide exactamente con la tabla 1.2; 40 `extremo_legitimo` con `es_anomalia == 0`.
- En mesas `ninguna`: `total_votos_reportado == suma de componentes` y `total ≤ habilitados`.
- Reproducibilidad: dos llamadas con la misma semilla producen DataFrames idénticos (`pd.testing.assert_frame_equal`).

---

## FASE 3 — Análisis exploratorio (EDA)

**Archivo:** `src/features.py` (variables derivadas) y `src/eda.py`.

### 3.1 Variables derivadas (`src/features.py`)

Función `agregar_features(df) -> df` (no usa columnas de ground truth):

| Feature | Fórmula |
|---|---|
| `suma_componentes` | suma de los 7 conteos |
| `diferencia_aritmetica` | `abs(total_votos_reportado - suma_componentes)` |
| `participacion` | `total_votos_reportado / votantes_habilitados` |
| `votos_validos` | `votos_cand_A + … + votos_cand_D` |
| `pct_cand_A` … `pct_cand_D` | `votos_cand_X / votos_validos` (0 si `votos_validos == 0`) |
| `pct_max_candidato` | máximo de los 4 `pct_cand_X` |
| `pct_nulos` | `votos_nulos / suma_componentes` |
| `pct_blanco` | `votos_blanco / suma_componentes` |
| `frac_multiplos_10` | fracción de los 4 conteos de candidatos que son múltiplos de 10 y > 0 |
| `desv_participacion_municipal` | `participacion - mediana(participacion del municipio)` |
| `log_habilitados` | `log(votantes_habilitados)` |
| `minutos_reporte` | minutos desde las 16:00 |

### 3.2 Contenido del EDA (`src/eda.py`)

1. Estadísticas descriptivas de las features numéricas → `outputs/tables/resumen_eda.csv`.
2. Resultados agregados nacionales por candidato (votos y %) → `outputs/tables/resultados_nacionales.csv`.
3. Participación media y desviación por departamento y zona → `outputs/tables/participacion_por_departamento.csv`.
4. Imprimir en consola observaciones clave: cuántas mesas tienen participación > 100 %, cuántas con
   diferencia aritmética > 0, distribución de `pct_max_candidato`, etc. (estas observaciones alimentan la
   justificación de los umbrales de la Fase 4).
5. Guardar el dataset con features en `data/processed/features_mesas.csv`.

> El EDA **puede** mirar `tipo_anomalia` solo para describir el dataset (cuántas anomalías hay), pero los
> umbrales de las reglas deben justificarse con argumentos de dominio (sección 4.1), no ajustándolos a la etiqueta.

### Verificación de la fase 3
`python -m src.eda` corre sin errores y genera los 3 CSV de tablas y `features_mesas.csv`.

---

## FASE 4 — Implementar las 2 técnicas de detección

### 4.1 Técnica 1 — Reglas simples (`src/rules.py`)

Función `aplicar_reglas(df) -> df` que agrega una columna booleana por regla, `puntaje_reglas`
(suma de pesos) y `alerta_reglas` (True si se activa al menos una regla).

| Regla | Condición | Peso | Justificación (va en `config.py` y en el informe) |
|---|---|---|---|
| `R1_sobre_participacion` | `total_votos_reportado > votantes_habilitados` | 3 (crítica) | Imposible si el padrón es correcto. |
| `R2_inconsistencia_aritmetica` | `diferencia_aritmetica > 0` | 3 (crítica) | El acta debe cuadrar exactamente. |
| `R3_participacion_extrema` | `participacion >= 0.95` | 2 (alta) | Muy por encima de la participación típica (~58 %); prácticamente nadie del padrón se abstuvo. |
| `R4_voto_concentrado` | `pct_max_candidato >= 0.90` **y** `votos_validos >= 50` | 2 (alta) | Concentración casi unánime; el mínimo de 50 evita alertas por mesas diminutas. |
| `R5_nulos_excesivos` | `pct_nulos >= 0.12` | 1 (media) | Cuatro veces la tasa esperada de nulos (~3 %). |
| `R6_numeros_redondos` | `frac_multiplos_10 == 1.0` | 1 (media) | Bajo datos naturales la probabilidad de que los 4 conteos sean múltiplos de 10 es ≈ 0.1⁴ = 0.0001. |

Nivel de severidad: `puntaje_reglas >= 3` → "crítica"; `2` → "alta"; `1` → "media"; `0` → "sin alerta".
Guardar como columna `severidad_reglas`.

**Verificación:** `tests/test_rules.py` construye un DataFrame pequeño a mano (una fila que activa cada
regla + una fila normal) y comprueba que se activa exactamente la regla esperada en cada fila.

### 4.2 Técnica 2 — Isolation Forest (`src/isolation_forest.py`)

**Por qué Isolation Forest:** no requiere etiquetas (en un escenario real no se sabe qué mesas son anómalas),
detecta combinaciones raras de variables que ninguna regla individual cubre (por ejemplo, participación de 93 %
con 85 % para un candidato), es rápido y explicable en términos sencillos ("cuántos cortes aleatorios se
necesitan para aislar la mesa").

**Features de entrada (lista fija en `config.py` → `FEATURES_IF`):**
`participacion, desv_participacion_municipal, pct_cand_A, pct_cand_B, pct_cand_C, pct_cand_D,
pct_max_candidato, pct_nulos, pct_blanco, diferencia_aritmetica, frac_multiplos_10, log_habilitados`.

No se usan identificadores (`mesa_id`, `departamento`…), ni `hora_reporte`, ni columnas de ground truth.

**Parámetros:**
```python
IsolationForest(n_estimators=300, contamination=0.04, max_samples="auto", random_state=SEED)
```
- `contamination=0.04`: supuesto operativo de "revisar ~4 % de las mesas", coherente con la capacidad de
  auditoría manual. Se documenta que en la realidad la tasa es desconocida → por eso se hace análisis de sensibilidad (Fase 5).
- Escalar features con `StandardScaler` antes de entrenar (no es estrictamente necesario para IF, pero
  homogeneiza y se documenta).

**Salidas a agregar al DataFrame:**
- `score_if` = `-modelo.score_samples(X)` (mayor = más anómalo).
- `alerta_if` = `modelo.predict(X) == -1`.
- `ranking_if` = posición por `score_if` descendente (1 = más anómala).

### 4.3 Combinación de ambas técnicas

En `src/main.py` (o en `evaluate.py`), crear `nivel_riesgo`:
- `"alto"`: alerta de ambas técnicas, o severidad de reglas "crítica".
- `"medio"`: alerta de solo una técnica.
- `"bajo"`: ninguna alerta.

Guardar todo en `data/processed/resultados_mesas.csv`.

**Verificación:** `tests/test_no_leakage.py` comprueba que `FEATURES_IF` no contiene `es_anomalia`,
`tipo_anomalia`, `nota_simulacion`, y que `rules.py` / `isolation_forest.py` no referencian esos nombres
(lectura del código fuente con `pathlib` + búsqueda de string).

---

## FASE 5 — Evaluar resultados (`src/evaluate.py`)

Usar `sklearn.metrics` (`precision_score`, `recall_score`, `f1_score`, `confusion_matrix`).

1. **Métricas globales** para 4 detectores: `Reglas`, `Isolation Forest`, `Unión (cualquiera)`,
   `Intersección (ambas)` → `outputs/tables/metricas_detectores.csv`
   con columnas: `detector, mesas_alertadas, VP, FP, FN, VN, precision, recall, f1`.
2. **Recall por tipo de anomalía** para Reglas e IF → `outputs/tables/recall_por_tipo.csv`
   (filas = 6 tipos, columnas = detector). Esto demuestra la **complementariedad**: las reglas atrapan lo
   aritméticamente imposible; IF atrapa combinaciones raras que no cruzan ningún umbral.
3. **Falsos positivos de los extremos legítimos:** cuántos de los 40 `extremo_legitimo` marca cada técnica
   → `outputs/tables/falsos_positivos_extremos.csv`.
4. **Análisis de sensibilidad de IF:** repetir con `contamination ∈ {0.02, 0.04, 0.06, 0.08}` y
   reportar precision/recall/F1 → `outputs/tables/sensibilidad_contaminacion.csv`.
5. **Top 15 mesas más sospechosas** (ordenar por `nivel_riesgo`, luego `puntaje_reglas`, luego `score_if`)
   con reglas activadas y score → `outputs/tables/top_mesas_sospechosas.csv`.
6. **Análisis de errores:** seleccionar 3 falsos positivos y 3 falsos negativos representativos y escribir en
   consola por qué ocurrieron (qué valores tenían). Copiar ese análisis a `docs/decisiones.md`; se usará en el informe.
7. **Agregado geográfico:** tasa de mesas con `nivel_riesgo == "alto"` por municipio →
   `outputs/tables/riesgo_por_municipio.csv` (debe destacar los 3 municipios con relleno de urnas).

**Resultados esperados aproximados** (sirven para detectar bugs; si se alejan mucho, revisar el código):
- Reglas: precisión alta (> 0.85), recall alto en `sobre_participacion`, `inconsistencia_aritmetica`,
  `numeros_redondos` (≈ 1.0) y parcial en `relleno_urnas` (solo los que superan 95 %).
- IF: detecta parte de `voto_unanime`, `relleno_urnas` y `nulos_excesivos`; marca algunos extremos legítimos.
- Unión: el mayor recall. Intersección: la mayor precisión.

No ajustar umbrales para "mejorar" las métricas mirando la etiqueta; si se cambia algo, documentarlo y explicarlo.

---

## FASE 6 — Visualizaciones (`src/visualize.py`) — exactamente 5

Reglas comunes: matplotlib/seaborn, `dpi=200`, tamaño ~`(9, 6)`, títulos y ejes en español, fuente legible,
guardar en `outputs/figures/` como PNG. Paleta consistente en todas:
normal = gris `#9E9E9E`, solo reglas = naranja `#F28E2B`, solo IF = azul `#4E79A7`, ambas = rojo `#E15759`.
Cada figura debe tener una frase de interpretación lista para el informe (imprimirla en consola al generarla).

| Archivo | Tipo | Qué muestra | Mensaje que debe transmitir |
|---|---|---|---|
| `fig1_distribucion_participacion.png` | Histograma (bins=60) | Distribución de `participacion` con líneas verticales en 0.95 (R3) y 1.00 (R1) | La mayoría de mesas está entre 40–75 %; hay una cola anómala a la derecha. |
| `fig2_huella_electoral.png` | Hexbin / dispersión 2D | `participacion` (x) vs `pct_max_candidato` (y), puntos coloreados por resultado de detección | "Huella electoral": las mesas sanas forman una nube central; las manipuladas se van a la esquina superior derecha. |
| `fig3_score_isolation_forest.png` | Histograma/KDE | Distribución de `score_if` para mesas normales vs anómalas (ground truth), con línea en el umbral | IF separa bien la mayoría de anomalías, pero hay solapamiento (origen de FP/FN). |
| `fig4_recall_por_tipo.png` | Barras agrupadas | Recall por tipo de anomalía para Reglas vs IF | Las técnicas son complementarias. |
| `fig5_riesgo_por_municipio.png` | Heatmap o barras horizontales | % de mesas con riesgo alto por municipio (top 15) | Las alertas se concentran geográficamente → priorizar auditoría en esos municipios. |

**Verificación:** existen exactamente 5 PNG en `outputs/figures/`; abrirlos y revisar que sean legibles
(textos no cortados, leyenda visible, sin superposición).

---

## FASE 7 — Orquestador, README e Informe PDF

### 7.1 `src/main.py`

Ejecuta en orden: generar dataset → features/EDA → reglas → Isolation Forest → combinación → evaluación →
figuras. Imprime un resumen final (filas, alertas por técnica, métricas principales, rutas de salidas).

```bash
python -m src.main      # todo el pipeline
pytest -v               # todos los tests deben pasar
```

### 7.2 `README.md`

- Descripción breve y **descargo ético** (ver 7.4).
- Requisitos e instalación (venv + `pip install -r requirements.txt`).
- Cómo ejecutar (`python -m src.main`, `pytest`, notebook de demo).
- Estructura de carpetas y descripción de las salidas.

### 7.3 `reports/informe.md` → `reports/Informe_Final.pdf`

Estructura obligatoria (cubre lo que pide el enunciado: contexto, metodología, resultados, visualizaciones,
conclusiones). Extensión sugerida: 10–15 páginas.

1. **Portada:** título, integrantes del grupo (dejar marcadores `[NOMBRE]` para que el grupo complete), curso, fecha.
2. **Resumen** (≈ 150 palabras).
3. **Contexto:** integridad electoral como problema de ciberseguridad/integridad de datos; por qué el análisis
   de datos ayuda a priorizar auditorías; aclaración de que el escenario es ficticio.
4. **Metodología**
   - 4.1 Tipos de anomalía definidos (tabla de la Fase 1).
   - 4.2 Construcción del dataset (resumen de la Fase 2, parámetros clave, por qué simulado e inyección con ground truth).
   - 4.3 Análisis exploratorio (hallazgos principales + tablas).
   - 4.4 Técnica 1: reglas (tabla de reglas, umbrales y justificación).
   - 4.5 Técnica 2: Isolation Forest (intuición del algoritmo, features, parámetros, por qué `contamination=0.04`).
   - 4.6 Combinación y nivel de riesgo.
   - 4.7 Métricas de evaluación (qué significan precisión, recall, F1 en este contexto: un FP = auditoría
     innecesaria, un FN = inconsistencia no revisada).
5. **Resultados:** tablas de métricas, recall por tipo, sensibilidad, top mesas, análisis de errores.
6. **Visualizaciones:** las 5 figuras, cada una con pie de figura y 2–4 líneas de interpretación.
7. **Discusión:** complementariedad de técnicas, por qué alerta ≠ fraude (extremos legítimos), cómo se usaría
   en la práctica (priorizar auditoría de actas).
8. **Riesgos y limitaciones:** datos sintéticos con anomalías "fáciles" y conocidas; umbrales dependientes del
   contexto; sesgo contra zonas con comportamiento legítimamente atípico (rurales, comunidades homogéneas);
   el adversario real puede adaptarse a reglas conocidas; IF depende de `contamination` y de las features;
   no considera dimensión temporal ni geográfica en el modelo; riesgo de uso político de falsas alarmas.
9. **Consideraciones éticas.**
10. **Conclusiones** (respuesta directa al objetivo) y **trabajo futuro** (validar con auditorías reales de
    actas, incorporar series temporales, etc. — solo como ideas).
11. **Referencias:** documentación de scikit-learn (IsolationForest), Liu, Ting & Zhou (2008)
    "Isolation Forest", Klimek et al. (2012) "Statistical detection of systematic election irregularities"
    (PNAS) como antecedente conceptual de la "huella electoral"; Kaggle como fuente de inspiración de estructura
    de datos (sin usar datos reales).

**Conversión a PDF** (el agente debe verificar qué hay disponible, en este orden):
1. `pandoc --version` → si existe y hay motor LaTeX (`xelatex --version`):
   `pandoc reports/informe.md -o reports/Informe_Final.pdf --pdf-engine=xelatex -V geometry:margin=2.5cm -V lang=es --toc`
   (ejecutar desde `reports/` o usar `--resource-path` para que encuentre las figuras).
2. Si hay pandoc pero no LaTeX: `pandoc ... -o informe.html --standalone --embed-resources` y luego
   `chromium --headless --print-to-pdf=Informe_Final.pdf informe.html` (o pedir al usuario que imprima a PDF).
3. Si no hay pandoc: informar al usuario y dejar `informe.md` listo; **no** instalar paquetes del sistema sin permiso.

Revisar el PDF resultante: figuras visibles, tildes correctas, tablas no cortadas.

### 7.4 Descargo ético (copiar textualmente en README, informe y primera diapositiva del video)

> *Todos los datos de este proyecto son simulados. Los nombres de país, departamentos, municipios y candidatos
> son ficticios. Los resultados no representan ni hacen afirmaciones sobre ningún proceso electoral real.
> Una alerta generada por los detectores indica una inconsistencia que merece revisión, no una prueba de fraude.*

---

## FASE 8 — Demo y guion del video (≤ 8 min)

### 8.1 `notebooks/demo.ipynb`

Celdas cortas que importan las funciones de `src/` (no duplicar lógica): cargar dataset → mostrar 5 filas →
aplicar reglas → aplicar IF → tabla de métricas → mostrar las 5 figuras → mostrar top 5 mesas sospechosas y
explicar una de ellas. Debe ejecutarse completo con "Run All" sin errores.

### 8.2 `docs/guion_video.md`

| Tiempo | Sección | Contenido |
|---|---|---|
| 0:00–0:45 | Introducción | Problema, objetivo, descargo ético |
| 0:45–1:45 | Anomalías y dataset | Los 6 tipos, cómo se simuló, por qué ground truth |
| 1:45–2:45 | EDA | Fig. 1 y hallazgos principales |
| 2:45–4:15 | Técnicas | Reglas (tabla) e Isolation Forest (intuición), justificación |
| 4:15–6:15 | Demo en vivo | `python -m src.main` + notebook: métricas, Fig. 2–5, una mesa explicada |
| 6:15–7:15 | Evaluación | Precisión/recall, complementariedad, falsos positivos legítimos |
| 7:15–8:00 | Cierre | Riesgos, limitaciones, conclusiones |

Incluir el texto narrado sugerido para cada bloque (en español, tono claro y no técnico en exceso).

---

## 9. Checklist final (Definition of Done)

El agente solo da el proyecto por terminado cuando **todo** esté marcado:

- [ ] `python -m src.main` corre de punta a punta sin errores en un entorno limpio.
- [ ] `pytest -v` pasa todos los tests (generador, reglas, no-leakage).
- [ ] `data/raw/mesas_simuladas.csv` tiene 5 000 filas, 200 anomalías con la distribución de la tabla 1.2 y 40 extremos legítimos.
- [ ] Solo se usan **2 técnicas** de detección: reglas simples e Isolation Forest.
- [ ] Las columnas de ground truth no se usan en la detección.
- [ ] Todos los umbrales/parámetros están en `src/config.py` con justificación.
- [ ] Existen exactamente **5 figuras** legibles en `outputs/figures/`.
- [ ] Existen las tablas de `outputs/tables/` listadas en las fases 3 y 5.
- [ ] `reports/Informe_Final.pdf` contiene: contexto, metodología, resultados, visualizaciones, conclusiones, riesgos/limitaciones y ética.
- [ ] `docs/guion_video.md` con guion de ≤ 8 minutos que incluye demo.
- [ ] `notebooks/demo.ipynb` se ejecuta completo sin errores.
- [ ] README con instrucciones y descargo ético.
- [ ] No aparece ningún nombre real de país, partido, candidato o lugar.
- [ ] No hay deep learning, interfaz web ni componentes de producción.
- [ ] `docs/decisiones.md` registra decisiones, justificaciones y el análisis de errores.

---

## 10. Orden de ejecución resumido para el agente

1. Crear estructura de carpetas, `requirements.txt`, `.gitignore`, entorno virtual. → commit
2. `src/config.py` con todas las constantes de este documento. → commit
3. `src/generate_dataset.py` + `tests/test_generate_dataset.py`; verificar. → commit
4. `src/features.py` + `src/eda.py`; verificar. → commit
5. `src/rules.py` + `tests/test_rules.py`; verificar. → commit
6. `src/isolation_forest.py` + `tests/test_no_leakage.py`; verificar. → commit
7. `src/evaluate.py`; revisar que las métricas se parezcan a las esperadas. → commit
8. `src/visualize.py`; revisar las 5 figuras. → commit
9. `src/main.py`; correr pipeline completo + `pytest`. → commit
10. `README.md`, `docs/decisiones.md`, `notebooks/demo.ipynb`. → commit
11. `reports/informe.md` con números **reales** obtenidos (nunca inventados) + conversión a PDF. → commit
12. `docs/guion_video.md`. → commit
13. Recorrer el checklist de la sección 9 y reportar al usuario el estado de cada ítem.
