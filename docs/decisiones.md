# Registro de Decisiones y Justificaciones

## Proyecto: Detección de anomalías en un proceso electoral simulado (Ciberseguridad)

---

### Fase 1 — Catálogo de anomalías y justificación de tipos

Para el proceso electoral simulado en la ficticia **República de Simulandia** (5.000 mesas de votación en 8 departamentos y 48 municipios), se definió un catálogo de 6 tipos de anomalía de integridad de datos electorales. Cada anomalía representa una inconsistencia técnica o estadística que en un contexto real activaría una alerta para auditoría manual del acta física:

| # | `tipo_anomalia` | Qué simula | Por qué es sospechosa (Justificación de ciberseguridad / integridad) | Cantidad inyectada |
|---|---|---|---|---|
| 1 | `sobre_participacion` | Más votos que votantes habilitados en el padrón | **Físicamente imposible:** En un proceso íntegro, el total de votos nunca puede superar el censo electoral registrado de la mesa ($> 100\%$). Indica duplicación, votos fantasma o falla severa en el padrón/conteo. | 30 |
| 2 | `relleno_urnas` | Inyección forzada de votos a un candidato hasta elevar la participación al 93–100 % | **Concentración anómala:** Se inyectan votos selectivamente hacia un candidato en mesas específicas (concentradas en 3 municipios), generando valores atípicos simultáneos de participación y preferencia. | 45 |
| 3 | `voto_unanime` | $\ge 92 \%$ de los votos válidos destinados a un único candidato con alta participación | **Uniformidad artificial:** En democracias competitivas con 4 candidatos, la casi unanimidad sistemática suele ser indicio de coacción o actas prefabricadas. | 35 |
| 4 | `inconsistencia_aritmetica` | El total reportado no coincide con la suma de componentes | **Falla de integridad básica:** La suma de votos de candidatos + blancos + nulos + no marcados debe ser idéntica al total reportado. Cualquier discrepancia revela manipulación al transcribir o falla en el software de transmisión. | 35 |
| 5 | `numeros_redondos` | Todos los conteos de los 4 candidatos son múltiplos de 10 | **Fabricación humana de datos:** Los fenómenos aleatorios y votos reales siguen distribuciones discretas naturales; conteos que terminan unánimemente en 0 violan el comportamiento estocástico natural (tendencia humana a inventar cifras redondas). | 25 |
| 6 | `nulos_excesivos` | Reclasificación selectiva de votos válidos de la oposición como nulos (15–35 %) | **Anulación estratégica:** La tasa natural de votos nulos ronda el 3 %. Un incremento abrupto al 15–35 % a expensas de la oposición simula manipulación durante el escrutinio de mesa. | 30 |
| | **Total anomalías** | | | **200 (4 % de las mesas)** |

#### Casos extremos legítimos (40 mesas)
- Se incorporaron 40 mesas rurales pequeñas ($\le 200$ habilitados) con alta participación legítima (85–94 %) y marcada preferencia comunitaria (75–88 % hacia un candidato), pero generadas de manera limpia y sin alteración (`es_anomalia = 0`, `nota_simulacion = "extremo_legitimo"`).
- **Propósito:** Demostrar analítica y éticamente que una alerta algorítmica no equivale a delito o fraude, sino a una señal que requiere verificación de contexto, reconociendo la tasa inevitable de falsos positivos en comunidades rurales homogéneas.

---

### Fase 5 — Análisis de Errores Representativos (Falsos Positivos y Falsos Negativos)

La evaluación con ground truth revela la naturaleza analítica de cada técnica y explica la complementariedad entre reglas e Isolation Forest:

#### Falsos Positivos representativos (Mesas normales alertadas)
1. **Mesa M00056** (`extremo_legitimo`, rural, Aurora-Mun01):
   - **Métricas:** 148 habilitados, participación 88.51 %, candidato favorito con 84.00 % de los votos válidos, 1.53 % nulos.
   - **Resultado:** Alertada por Isolation Forest (`score_if = 0.6329`), no por Reglas (`alerta_reglas = False`).
   - **Causa:** Al ser una mesa rural pequeña con fuerte consenso comunitario y alta participación, queda rápidamente aislada en el hiperespacio de features de IF (requiere pocas particiones aleatorias). Esto evidencia cómo los detectores estadísticos no supervisados pueden penalizar comunidades rurales homogéneas legítimas.
2. **Mesa M00084** (`extremo_legitimo`, rural, Aurora-Mun01):
   - **Métricas:** 89 habilitados, participación 89.89 %, candidato favorito con 83.33 % de los votos válidos, 5.0 % nulos.
   - **Resultado:** Alertada por Isolation Forest (`score_if = 0.6953`), no por Reglas.
   - **Causa:** Combinación de muy bajo censo electoral con asistencia cercana al 90 %, lo que genera una señal multivariada extrema respecto al promedio municipal urbano/rural.
3. **Mesa M00129** (rural normal, Aurora-Mun01):
   - **Métricas:** 90 habilitados, participación 54.44 %, candidato mayoritario con 34.88 %, `frac_multiplos_10 = 0.50`.
   - **Resultado:** Alertada por Isolation Forest (`score_if = 0.5524`), no por Reglas.
   - **Causa:** Efecto de frontera del hiperparámetro `contamination = 0.04`, donde mesas en zonas rurales de baja densidad caen en la cola superior del score de aislamiento.

#### Falsos Negativos representativos (Anomalías inyectadas no alertadas por la Unión)
1. **Mesa M00261** (`relleno_urnas`):
   - **Métricas:** 277 habilitados, 262 votos reportados, participación 94.58 %, candidato A con 67.95 % de votos válidos (`score_if = 0.5114`).
   - **Resultado:** Ni Reglas ni IF la alertaron (`alerta_reglas = False`, `alerta_if = False`).
   - **Causa:** La participación (94.58 %) quedó sutilmente por debajo del umbral de la regla R3 (95.00 %), y el candidato no superó el 90 % de R4. A su vez, para IF no representó un outlier multivariado suficiente para entrar en el percentil 96 de mayor aislamiento.
2. **Mesa M00284** (`relleno_urnas`):
   - **Métricas:** 398 habilitados, 372 votos reportados, participación 93.47 %, candidato A con 70.57 % (`score_if = 0.5133`).
   - **Resultado:** No alertada por la Unión.
   - **Causa:** El relleno de urnas inyectado en este caso llevó la mesa al 93.47 %, quedando dentro de márgenes que simulan alta concurrencia plausible, esquivando tanto los umbrales rígidos como el corte conservador del 4 % de IF.
3. **Mesa M00324** (`relleno_urnas`):
   - **Métricas:** 435 habilitados, 412 votos reportados, participación 94.71 %, candidato A con 62.40 % (`score_if = 0.4834`).
   - **Resultado:** No alertada por la Unión.
   - **Causa:** La participación quedó a escasas décimas del umbral del 95 % (94.71 %), ilustrando la limitación intrínseca de los detectores deterministas frente a alteraciones calibradas para eludir umbrales fijos.


1. **Entorno de ejecución:**
   - Python 3.14.9 instalado en el sistema. Entorno virtual local creado en `.venv`.
2. **Estructura modular:**
   - Separación estricta entre generación (`generate_dataset.py`), ingeniería de características (`features.py`), análisis exploratorio (`eda.py`), detectores (`rules.py`, `isolation_forest.py`), evaluación (`evaluate.py`) y visualización (`visualize.py`).
3. **Control de data leakage:**
   - Las columnas `es_anomalia`, `tipo_anomalia` y `nota_simulacion` quedan estrictamente aisladas del pipeline de detección, comprobado mediante test automatizado en `tests/test_no_leakage.py`.
