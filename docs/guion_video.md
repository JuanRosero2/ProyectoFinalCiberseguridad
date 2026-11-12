# Guion de Video de Presentación y Demostración (≤ 8 min)

**Proyecto:** Detección de anomalías en un proceso electoral simulado  
**Asignatura:** Ciberseguridad / Integridad de Datos  
**Duración estimada:** 7 minutos 45 segundos  

---

## Estructura General y Temporización

| Segmento | Tiempo | Sección | Elemento visual en pantalla |
|---|---|---|---|
| 1 | 0:00 – 0:45 | Introducción y descargo ético | Diapositiva 1: Título, integrantes y descargo ético |
| 2 | 0:45 – 1:45 | Modelado del proceso y catálogo de anomalías | Diagrama del proceso electoral y tabla de las 6 anomalías |
| 3 | 1:45 – 2:45 | Análisis Exploratorio (EDA) | Figura 1 (Distribución de participación) y tabla resumen |
| 4 | 2:45 – 4:15 | Técnicas de detección implementadas | Cuadro comparativo: Reglas simples vs. Isolation Forest |
| 5 | 4:15 – 6:15 | Demostración en vivo (Pipeline y Notebook) | Terminal corriendo `python -m src.main` y `demo.ipynb` |
| 6 | 6:15 – 7:15 | Evaluación cuantitativa y complementariedad | Figura 4 (Recall por tipo) y tabla de métricas |
| 7 | 7:15 – 8:00 | Riesgos, limitaciones y conclusiones | Diapositiva de reflexiones y cierre |

---

## Texto Narrado sugerido paso a paso

### Bloque 1: Introducción y Descargo Ético (0:00 – 0:45)
*(Voz clara, tono formal y pausado)*
> "Buenas a todos. En este proyecto abordamos la integridad de los procesos democráticos desde la perspectiva de la ciberseguridad y el análisis de datos. Nuestro objetivo no es emitir juicios de valor ni denunciar fraude en elecciones reales, sino diseñar una metodología analítica reproducible capaz de detectar inconsistencias en actas electorales para priorizar auditorías físicas manuales.
> 
> Hacemos un descargo ético fundamental: todos los datos, departamentos, municipios y candidatos utilizados en este trabajo son 100 % simulados en la ficticia República de Simulandia. Ningún resultado hace referencia a hechos o actores reales."

---

### Bloque 2: Modelado del Proceso y Catálogo de Anomalías (0:45 – 1:45)
*(Mostrar tabla de las 6 anomalías e inyección de datos)*
> "Simulamos una elección presidencial con 5.000 mesas de votación distribuidas en 8 departamentos y 48 municipios, con una participación media natural del 58 %.
> 
> Para evaluar los detectores con rigor, inyectamos con etiqueta conocida (ground truth) exactamente 200 anomalías clasificadas en 6 patrones de manipulación típicos:
> 1. Sobre-participación: votos que superan físicamente el censo de votantes habilitados.
> 2. Relleno de urnas: votos artificiales concentrados geográficamente en 3 municipios.
> 3. Voto unánime: mesas con más del 92 % de votos válidos a un solo candidato.
> 4. Inconsistencia aritmética: discrepancia entre el total reportado en el acta y la suma de votos.
> 5. Números redondos: todos los votos de candidatos terminados en cero.
> 6. Nulos excesivos: anulación selectiva del 15 al 35 % de los votos de la oposición.
> 
> Además, incluimos 40 mesas rurales legítimas con alta participación para evaluar con transparencia la tasa de falsos positivos."

---

### Bloque 3: Análisis Exploratorio de Datos (1:45 – 2:45)
*(Mostrar Figura 1 y estadísticas)*
> "En el análisis exploratorio observamos que la participación electoral sana sigue una distribución acampanada con una media del 58.4 %. Sin embargo, la Figura 1 revela claramente una cola anómala a la derecha: identificamos 30 mesas donde la participación supera el 100 % y 77 mesas con asistencia superior al 95 %.
> 
> Asimismo, detectamos 35 actas donde el número total reportado no coincide con la suma de sus casillas, lo que confirma fallas graves de integridad en la transcripción. Estos hallazgos fundamentan los umbrales de nuestras técnicas."

---

### Bloque 4: Técnicas de Detección Implementadas (2:45 – 4:15)
*(Mostrar comparativa de las 2 técnicas)*
> "Siguiendo las restricciones del proyecto, implementamos únicamente dos técnicas analíticas complementarias:
> 
> La primera técnica son Reglas Simples Deterministas: evalúa violaciones físicas directas, diferencias aritméticas y límites estadísticos de nulos y concentración, calculando un puntaje de severidad de riesgo. Es rápida, transparente y con cero falsos positivos en límites matemáticos.
> 
> La segunda técnica es Isolation Forest: un algoritmo de aprendizaje automático no supervisado. Su intuición es fascinante: en lugar de modelar lo normal, aísla puntos atípicos mediante hiperplanos aleatorios; las mesas manipuladas requieren significativamente menos cortes para quedar aisladas. Utilizamos 12 variables sin etiquetas de ground truth, evitando cualquier fuga de información."

---

### Bloque 5: Demostración en Vivo (4:15 – 6:15)
*(Cambiar a pantalla compartida con terminal y Jupyter Notebook)*
> "Veamos la ejecución en vivo. Ejecutamos el pipeline con un solo comando: `python -m src.main`. En menos de 4 segundos, el sistema regenera el dataset, calcula variables, aplica las reglas, entrena el Isolation Forest, evalúa contra el Ground Truth y genera las figuras oficiales.
> 
> Pasemos al notebook de demostración:
> Al examinar la Huella Electoral en la Figura 2, vemos que las mesas normales forman una nube densa central, mientras que las actas alteradas son proyectadas hacia la esquina superior derecha.
> 
> Miremos la mesa clasificada como la número 1 en riesgo de la auditoría: la mesa M00007 en Aurora. Tiene 300 votantes habilitados pero reportó 345 votos, con una participación imposible del 115 %. El sistema le asigna severidad crítica en reglas y un score extremo de Isolation Forest, recomendando su apertura física inmediata."

---

### Bloque 6: Evaluación y Complementariedad (6:15 – 7:15)
*(Mostrar Figura 4 de recall por tipo y tabla de métricas)*
> "Al evaluar cuantitativamente, las reglas simples lograron una precisión del 97.4 % y un recall del 94.0 %. Por su parte, Isolation Forest capturó anomalías multivariadas complejas como el relleno de urnas.
> 
> Lo más potente es la combinación: la Unión de ambas técnicas alcanzó un Recall global del 96.5 %, atrapando 193 de las 200 anomalías. Por otro lado, la Intersección ofrece una precisión del 95.7 %, garantizando que casi cada mesa donde ambas concuerdan es una anomalía real.
> 
> Asimismo, evidenciamos que Isolation Forest marcó las 40 mesas rurales legítimas como atípicas, demostrando por qué en ciberseguridad una alerta es un llamado a auditar y nunca una sentencia automática."

---

### Bloque 7: Riesgos, Limitaciones y Conclusiones (7:15 – 8:00)
*(Diapositiva final de conclusiones)*
> "Como conclusiones clave:
> Primero, la combinación de reglas deterministas con modelos de aislamiento estadístico proporciona una herramienta de priorización de auditorías sumamente efectiva para autoridades electorales.
> Segundo, reconocemos limitaciones: los datos reales poseen ruido y los adversarios pueden adaptarse si conocen los umbrales fijos; además, el sesgo hacia comunidades rurales exige siempre contexto humano.
> 
> Este proyecto demuestra cómo la ciencia de datos y la ciberseguridad pueden fortalecer la confianza en los procesos democráticos. Muchas gracias."

