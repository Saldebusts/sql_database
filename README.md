# Capital Bikeshare: alquileres y meteorología

**Mini proyecto de SQL · Ironhack Data Analytics**  
Washington D. C. · Enero de 2011 a diciembre de 2012  
**Autores:** João Miguel Pais y Salva [apellido]  
**Presentación:** [`presentacion/bikeshare_presentacion.pdf`](presentacion/bikeshare_presentacion.pdf)

## Resumen

- **Reforzar:** el 50,9 % de los alquileres se concentra en 7 de las 24 horas: de 7 a 9 h y de 16 a 19 h en días laborables.
- **Mantenimiento:** entre la 1 y las 6 h se hace solo el 2,05 % de los alquileres. Con 10 mm de lluvia o más, la demanda cae un 36 % entre los registrados y un 43 % entre los ocasionales.
- **Captar socios:** en las tardes de fin de semana de primavera y verano, los ocasionales llegan al 44 % de los alquileres.
- **Crecimiento:** la media diaria de alquileres aumenta un 64,4 % de 2011 a 2012.

## Objetivo

Nos ponemos en el lugar de una empresa de bicicletas compartidas que quiere organizar su servicio según la demanda.

Nuestra pregunta principal es: **¿cuándo conviene reforzar el servicio y cuándo podemos programar el mantenimiento?**

Para responderla, conectamos datos de alquileres con información meteorológica. Preparamos los datos con Python, los organizamos en una base de datos MySQL y hacemos el análisis con consultas SQL en MySQL Workbench. Después representamos los resultados con gráficos.

## Fuentes de datos

| Fuente | Datos utilizados | Tamaño | Licencia |
|---|---|---:|---|
| [UCI · Bike Sharing Dataset](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) | `day.csv`: alquileres diarios, calendario y condiciones meteorológicas | 731 filas y 16 columnas | CC BY 4.0 |
| UCI · Bike Sharing Dataset | `hour.csv`: alquileres por hora, separados entre ocasionales y registrados | 17 379 filas y 17 columnas | CC BY 4.0 |
| [Open-Meteo · Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | Temperatura media, precipitación acumulada y viento máximo diario | 731 filas y 4 columnas | CC BY 4.0 |

Las dos fuentes corresponden al mismo lugar y periodo. Las relacionamos mediante la fecha. Utilizamos la meteorología de Open-Meteo para las comparaciones diarias y la de UCI para los registros horarios.

Los recuentos representan **alquileres**, no personas diferentes.

## Preguntas e hipótesis

### Preguntas

| | Pregunta |
|---|---|
| **P1** | ¿Qué horas y tipos de día concentran más alquileres? |
| **P2** | ¿Qué diferencias encontramos entre los patrones de alquiler de usuarios ocasionales y registrados? |
| **P3** | ¿Cómo cambia la media diaria de alquileres según la precipitación? ¿La diferencia es igual para ambos tipos de usuario? |
| **P4** | ¿Cómo varían los alquileres según la temperatura? |
| **P5** | ¿Cómo evoluciona la demanda entre 2011 y 2012? |

### Hipótesis

Las escribimos antes de mirar los resultados, para contrastarlas con los datos.

| Hipótesis | Pregunta | Qué esperamos encontrar |
|---|---|---|
| **H1 · Horarios** | P1, P2 | Los registrados presentan picos a las 8:00 y a las 17:00–18:00 en laborables. Los ocasionales tienen más actividad por las tardes de fines de semana y festivos. |
| **H2 · Precipitación** | P3 | Los días con al menos 1 mm de precipitación presentan menos alquileres, con una diferencia porcentual mayor entre los ocasionales. |
| **H3 · Evolución** | P5 | La media diaria aumenta en 2012 y crece más entre los registrados que entre los ocasionales. |
| **H4 · Temperatura** | P4 | La media de alquileres aumenta con la temperatura hasta cierto nivel y disminuye en los días de mayor calor. |

## Preparación de los datos

1. **Descargamos las fuentes.** Leemos los CSV de UCI y convertimos la respuesta de Open-Meteo en un DataFrame.
2. **Revisamos su calidad.** Comprobamos dimensiones, tipos, valores nulos, fechas y registros duplicados.
3. **Preparamos las fechas.** Convertimos las columnas al tipo fecha y comprobamos que ambas fuentes cubren los mismos 731 días.
4. **Comprobamos los alquileres.** Verificamos que ocasionales más registrados coincide con el total y que la suma de las horas coincide con cada total diario.
5. **Interpretamos los códigos.** Revisamos estaciones, días de la semana y situaciones meteorológicas antes de traducirlos.
6. **Transformamos las variables.** Recuperamos temperatura y sensación térmica desde los valores normalizados y expresamos la humedad en porcentaje.
7. **Creamos las tablas.** Preparamos cuatro tablas relacionadas, definimos sus claves y comprobamos que no hay claves repetidas antes de cargarlas en MySQL.

El código de descarga y transformación está organizado en funciones dentro de [`funciones.py`](funciones.py). Las comprobaciones y explicaciones se encuentran en el notebook.

### Calidad de los datos

- **Horas sin registro.** Faltan **165 horas** de 17 544: 76 días tienen menos de 24 registros. Más de la mitad (91) se concentran en 8 días de temporal: el huracán Sandy (29 y 30 de octubre de 2012, 36 horas), los temporales de enero de 2011 (36 horas) y el huracán Irene (27 y 28 de agosto de 2011, 13 horas). Conservamos los datos disponibles sin inventar valores: no sabemos si en esas horas hubo cero alquileres o si no se registraron.
- **Errores en la documentación de UCI.** Comprobamos los códigos con los propios datos. El código 1 de estación corresponde al invierno (de finales de diciembre a marzo), no a la primavera como indica el Readme. Su fórmula de temperatura se desviaba 5,6 °C de Open-Meteo; con nuestra fórmula, la diferencia media entre las dos fuentes es de **0,9 °C**.
- **Claves.** Antes de cargar en MySQL comprobamos que no hay claves repetidas ni fechas sin pareja entre las tablas.

Definimos `dia_lluvioso = 1` cuando la precipitación diaria es de al menos **1 mm**. Aunque utilizamos ese nombre, la precipitación puede incluir lluvia y nieve.

## Modelo de datos

La base de datos se llama **`bikeshare`**.

| Tabla | Qué representa cada fila | Clave primaria | Filas |
|---|---|---|---:|
| `situacion_meteo` | Una situación meteorológica y su descripción | `situacion_id` | 4 |
| `calendario` | Un día y sus características | `fecha` | 731 |
| `meteorologia_dia` | Las condiciones meteorológicas de un día | `fecha` | 731 |
| `alquileres_hora` | Los alquileres y condiciones de una hora | `fecha`, `hora` | 17 379 |

Relacionamos `calendario` con `meteorologia_dia` y `alquileres_hora` mediante `fecha`. Relacionamos `situacion_meteo` con `alquileres_hora` mediante `situacion_id`.

También creamos la vista **`v_dia`**, que reúne el calendario, la meteorología diaria y los alquileres horarios sumados por día. Así podemos hacer las comparaciones diarias desde SQL.

![Diagrama de relaciones de la base bikeshare](erd/bikeshare_erd.png)

El [archivo editable de Workbench](erd/bikeshare_erd.mwb) está en la carpeta `erd/`.

**Una limitación del modelo.** Las columnas del tiempo de cada hora (`situacion_id`, `temp_c`, `sensacion_c`, `humedad_pct` y `viento`) están en `alquileres_hora` porque así vienen en `hour.csv`. En un modelo más normalizado irían en una tabla `meteorologia_hora` con clave (`fecha`, `hora`). Ninguna consulta del análisis depende de esa decisión; la dejamos como mejora.

## Consultas SQL

Todas las consultas están en [`sql/02_queries.sql`](sql/02_queries.sql) y se ejecutan en MySQL Workbench.

| Consulta | Qué responde | Técnicas |
|---|---|---|
| `24a_resumen_por_anio` | Media, mínimo, máximo y variabilidad de los alquileres diarios de cada año | vista `v_dia`, `GROUP BY`, `AVG`, `STDDEV_SAMP` |
| `24b_resumen_por_estacion` | Demanda media por estación del año y tipo de usuario | `GROUP BY`, `ORDER BY CASE` |
| `25a_demanda_hora_dia` (P1) | Media de alquileres por hora y día de la semana | `JOIN`, `GROUP BY` |
| `25b_perfil_horario_tipo_dia` (P1, P2) | Perfil horario de registrados y ocasionales en laborables y fines de semana | `JOIN`, `CASE`, `GROUP BY` |
| `26a_lluvia_por_tramos` (P3) | Demanda por tramos de precipitación | `CASE`, `GROUP BY` |
| `26b_lluvia_seco_por_anio_tipo_dia` (P3) | Días secos frente a lluviosos, dentro de cada año y tipo de día | `AVG(CASE …)` |
| `27_demanda_por_temperatura` (P4) | Demanda por tramos de 5 °C | `FLOOR`, `GROUP BY` |
| `28a_horas_mantenimiento` | Las 3 horas con menos alquileres por estación y tipo de día | CTE (`WITH`), `RANK() OVER (PARTITION BY …)` |
| `28b_peso_madrugada` | Peso de la madrugada y de las horas punta en el total | `SUM(CASE …)` |
| `29_dias_de_refuerzo` | Perfil del 10 % de días con más demanda de cada año | CTE, `RANK() OVER`, `AVG(CASE …)` |
| `30_crecimiento_mensual` (P5) | Crecimiento de cada mes frente al mismo mes del año anterior | CTE, `LAG() OVER` |
| `30b_crecimiento_anual_por_usuario` (P5) | Crecimiento de 2011 a 2012 por tipo de usuario | `AVG(CASE …)` |
| `31a_media_movil_7_dias` | Media de los últimos 7 días | CTE, subconsulta correlacionada, `DATEDIFF` |
| `31b_dias_atipicos` | Días con menos de la mitad de alquileres que la media de los 7 anteriores | CTE, subconsulta correlacionada |
| `32_momentos_ocasionales` (P2) | Peso de los ocasionales por estación, tipo de día y hora | `JOIN`, `CASE`, `SUM`, `AVG` |

### Capturas de MySQL Workbench

En [`capturas/`](capturas/) están las capturas de las consultas ejecutadas en Workbench:

| Captura | Consulta |
|---|---|
| [`capturas/24a_resumen_por_anio.png`](capturas/24a_resumen_por_anio.png) | Resumen por año |
| [`capturas/26a_lluvia_por_tramos.png`](capturas/26a_lluvia_por_tramos.png) | Demanda por tramos de lluvia |
| [`capturas/28a_horas_mantenimiento.png`](capturas/28a_horas_mantenimiento.png) | Horas para el mantenimiento |
| [`capturas/29_dias_de_refuerzo.png`](capturas/29_dias_de_refuerzo.png) | Días de refuerzo |
| [`capturas/30_crecimiento_mensual.png`](capturas/30_crecimiento_mensual.png) | Crecimiento mensual |
| [`capturas/31b_dias_atipicos.png`](capturas/31b_dias_atipicos.png) | Días atípicos |
| [`capturas/32_momentos_ocasionales.png`](capturas/32_momentos_ocasionales.png) | Momentos de los ocasionales |

## Principales resultados

| Tema | Resultado observado |
|---|---|
| **Horarios (P1)** | En laborables, los registrados alcanzan una media de 455 alquileres a las 8:00 y 468 a las 17:00. Las 7 horas de 7 a 9 h y de 16 a 19 h concentran el **50,9 %** de los alquileres. |
| **Tipos de usuario (P2)** | Los ocasionales alcanzan 140 alquileres por hora a las 14:00 en fines de semana o festivos. En los diez grupos de estación del año, tipo de día y hora con mayor media de ocasionales, estos representan entre el 36 % y el **44 %** de los alquileres: son tardes de primavera y verano en fines de semana o festivos. |
| **Precipitación (P3)** | Al comparar dentro de cada año y tipo de día, los días con al menos 1 mm presentan entre un 7,6 % y un 18,2 % menos de alquileres de registrados, y entre un 13,9 % y un 29,3 % menos de ocasionales. Por tramos, de 1 a 10 mm la caída es moderada (entre un 8 % y un 10 % en registrados y un 16 % en ocasionales); con **10 mm o más** llega al **36 %** en registrados y al **43 %** en ocasionales, frente a un día seco. |
| **Temperatura (P4)** | La demanda aumenta hasta el tramo de 15–20 °C y se mantiene relativamente estable hasta 30 °C. Por encima de 30 °C, la media es un 11 % menor que en el tramo anterior. Los 37 días de más demanda de cada año tienen **21,2 °C** de media y solo el **5,4 %** tuvo lluvia, frente al 36,1 % del resto. |
| **Crecimiento (P5)** | La media diaria aumenta un **64,4 %** entre 2011 y 2012: un 67,9 % entre registrados y un 50,4 % entre ocasionales. |
| **Mantenimiento** | Entre la 1:00 y las 5:59 se concentra solo el **2,05 %** de los alquileres. Las tres horas con menos alquileres de cada estación y tipo de día están siempre entre las 2 y las 6 h. |
| **Días atípicos** | Encontramos **30 días** con menos de la mitad de alquileres que la semana anterior; 16 de ellos tuvieron 10 mm de lluvia o más. El día del huracán Sandy (29 de octubre de 2012) solo hubo **22 alquileres**. |

Los resultados **apoyan H1, H2 y H3**. H4 también presenta el patrón esperado, aunque la comparación por encima de 30 °C se basa en solo 19 días y debe interpretarse con cautela.

![Mapa de calor de alquileres por hora y día de la semana](figuras/01_mapa_calor_hora_dia.png)

![Alquileres según la precipitación](figuras/03_efecto_lluvia.png)

![Tendencia diaria y días atípicos](figuras/06_tendencia_atipicos.png)

Las explicaciones y el resto de gráficos están en [`SQL_Data_base.ipynb`](SQL_Data_base.ipynb) y en [`figuras/`](figuras/).

### Prueba con una semana real

Aplicamos las reglas de la sección siguiente a la semana del 17 al 23 de septiembre de 2012, mirando solo el tiempo de cada día. El martes 18 llovieron 37,6 mm y tocaba mantenimiento: fue el día con menos alquileres (4 073). El sábado 22, seco y a 22,1 °C, tocaba reforzar: fue el día con más (8 395). Es un ejemplo, no una validación estadística.

## Aplicación al negocio

A partir del análisis, proponemos estas reglas:

| Decisión | Cuándo | Por qué |
|---|---|---|
| **Reforzar el servicio** | Laborables, de 7 a 9 h y de 16 a 19 h. Días secos de más de 20 °C, sobre todo fines de semana de verano. | Esas horas concentran el 50,9 % de los alquileres y los días fuertes son secos y templados. |
| **Mantenimiento diario** | Cada día, de 1 a 6 h. | La madrugada solo reúne el 2,05 % de los alquileres. |
| **Mantenimiento largo** | Días con previsión de 10 mm o más y semana de Navidad. | La demanda cae entre un 36 % y un 43 %, y ahí aparecen los días atípicos. |
| **Campañas de abono** | Fines de semana y festivos de primavera y verano, de 12 a 17 h. | Los ocasionales llegan al 44 % de los alquileres. |

Con la previsión del tiempo de cada semana, estas reglas dan un plan semanal. La decisión final también debe considerar los turnos y recursos disponibles.

Estas propuestas identifican momentos para actuar sobre el conjunto del servicio. Para decidir en qué estaciones concretas intervenir necesitaríamos información de origen y destino de los viajes.

## Archivos del repositorio

| Archivo o carpeta | Contenido |
|---|---|
| `SQL_Data_base.ipynb` | Extracción, comprobaciones, preparación, gráficos y conclusiones |
| `funciones.py` | Funciones de descarga, lectura y transformación |
| `requirements.txt` | Librerías de Python necesarias |
| `sql/01_schema.sql` | Estructura de las tablas, relaciones y vista |
| `sql/02_queries.sql` | Las 15 consultas del análisis |
| `sql/03_bikeshare_dump.sql` | Exportación de la base `bikeshare` con estructura y datos |
| `erd/` | Diagrama de relaciones y archivo editable de Workbench |
| `capturas/` | Capturas de las consultas en MySQL Workbench |
| `data/raw/` | CSV de las fuentes utilizados en el proyecto |
| `data/clean/` | Las cuatro tablas preparadas para MySQL |
| `figuras/` | Gráficos del análisis |
| `presentacion/` | Presentación en PDF |

## Cómo ejecutar el proyecto

Necesitamos MySQL 8 con MySQL Workbench, Python 3 y VS Code (o Jupyter) para el notebook.

**Base de datos y consultas (MySQL Workbench)**

1. Descargamos o clonamos el repositorio.
2. En Workbench abrimos `sql/03_bikeshare_dump.sql` y lo ejecutamos. Crea la base `bikeshare` con sus tablas, la vista y los datos.  
   Alternativa: creamos la base (`CREATE DATABASE bikeshare; USE bikeshare;`), ejecutamos `sql/01_schema.sql` y cargamos los CSV de `data/clean/` con *Table Data Import Wizard*, en este orden: `situacion_meteo`, `calendario`, `meteorologia_dia` y `alquileres_hora`. El orden importa por las claves foráneas.
3. Comprobamos los recuentos: deben dar **4, 731, 731 y 17 379 filas**.

   ```sql
   SELECT 'situacion_meteo' AS tabla, COUNT(*) AS filas FROM situacion_meteo
   UNION ALL SELECT 'calendario', COUNT(*) FROM calendario
   UNION ALL SELECT 'meteorologia_dia', COUNT(*) FROM meteorologia_dia
   UNION ALL SELECT 'alquileres_hora', COUNT(*) FROM alquileres_hora;
   ```

4. Abrimos `sql/02_queries.sql` y ejecutamos las consultas una a una (con el cursor en la consulta, `Ctrl + Enter`).

**Preparación y gráficos (Python)**

5. Instalamos las dependencias en el entorno que usaremos como kernel:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Abrimos `SQL_Data_base.ipynb` con `funciones.py` en la misma carpeta. Las secciones 1 a 18 repiten la descarga, las comprobaciones y la preparación; necesitan internet. Las tablas ya preparadas están en `data/clean/`, así que este paso es opcional.
7. Para dibujar los gráficos desde la base local, configuramos `DB_USER`, `DB_PASSWORD` y `DB_NAME` (`bikeshare`, servidor `127.0.0.1`, puerto `3306`). La contraseña se escribe solo en local y no se sube a GitHub. Las celdas de instalación de MySQL en Colab no son necesarias, porque la base ya está creada en Workbench.

## Alcance y próximos pasos

Trabajamos con datos históricos de 2011–2012 y analizamos asociaciones, no relaciones de causa y efecto: comparamos medias. Los datos están agregados para todo el sistema y algunas horas no tienen registro.

Como siguientes pasos, proponemos:

- Probar las reglas con los 731 días, no solo con una semana, y contar cuántas veces aciertan.
- Separar el tiempo de cada hora en una tabla `meteorologia_hora`.
- Incorporar viajes por estación para decidir también dónde reforzar.
- Contrastar los patrones con años más recientes y evaluar una previsión de demanda que ayude a planificar el servicio.

## Referencias

- Fanaee-T, H. (2013). *Bike Sharing* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5W894. Licencia [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Open-Meteo. *Historical Weather API*. [Documentación](https://open-meteo.com/en/docs/historical-weather-api). [Weather data by Open-Meteo.com](https://open-meteo.com/), licencia [CC BY 4.0](https://open-meteo.com/en/licence).
