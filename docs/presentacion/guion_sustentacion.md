# Guion de sustentación: OptiAgro-Llanos

Documento de apoyo para exponer y defender el proyecto. Acompaña a `OptiAgro_sustentacion.pptx` (36 diapositivas; el guion corto de cada una también está en sus notas del orador).

> **Antes de exponer:** completa los nombres de los integrantes en la portada. Todas las cifras de resultados salen de ejecutar el código real (ver `reproducir_resultados.py`); los datos de la red de prueba son **ficticios**.

## Índice

1. [Guía técnica de los dos métodos de optimización](#guía-técnica)
2. [Fragmentos de código seleccionados](#fragmentos-de-código)
3. [Guion diapositiva por diapositiva](#guion-por-diapositiva)
4. [Preguntas difíciles del profesor](#preguntas-difíciles)

## Guía técnica

### A. Método exacto: programación lineal con HiGHS

**Qué es un método exacto.** Un procedimiento que garantiza encontrar el óptimo global y puede demostrarlo. Se diferencia de un algoritmo genético en que éste solo entrega la mejor solución que encontró, sin prueba de que no exista otra mejor.

**Cuál es el método en nuestro código (verificado).** `backend/optimizacion/metodo_exacto/solver.py` llama a `scipy.optimize.linprog(..., method="highs")`: es **programación lineal continua** resuelta con el solver **HiGHS**. No es fuerza bruta ni ramificación y acotamiento. Con `method="highs"`, SciPy deja que HiGHS elija entre simplex dual y puntos interiores; nosotros no lo forzamos.

**Planteamiento (tal como está en el docstring del solver).**

```
min  Σ_i Σ_j c_ij · x_ij        con c_ij = transporte + operación de la planta j + precio de la empresa i
s.a. Σ_j x_ij  = s_i            (oferta de cada empresa; ≤ si modo_oferta = "maximum")
     Σ_i x_ij ≤ d_j            (capacidad de cada planta; = o ≥ según tipo_demanda)
     0 ≤ x_ij ≤ límite_ij
```

- **Variables de decisión:** x_ij = toneladas por semana que la empresa i envía a la planta j. En la red de prueba son **40** variables continuas.
- **Función objetivo:** minimizar el costo efectivo total (transporte = distancia × tarifa, más operación de la planta, más precio de la empresa).
- **Restricciones:** 10 igualdades de oferta + 4 desigualdades de capacidad + cotas 0 ≤ x_ij ≤ límite.
- **Por qué la solución sale entera aunque las variables sean continuas:** el problema de transporte tiene matriz de restricciones totalmente unimodular; con ofertas y capacidades enteras, existe un óptimo entero (en los resultados: 11, 10, 2, 13 toneladas…).

**Cómo se 'explora'.** No se prueban soluciones: la región factible es un poliedro convexo y el óptimo de un LP está en un vértice. HiGHS recorre vértices (simplex) o se acerca por el interior (puntos interiores) hasta cumplir las condiciones de optimalidad.

**Cómo se sabe que es óptima.** HiGHS reporta estado óptimo (en nuestros mensajes: *«Optimization terminated successfully. (HiGHS Status 7: Optimal)»*): factibilidad primal, factibilidad dual y holgura complementaria. Como el LP es convexo, ese óptimo local es global. Además, `verificar()` recalcula oferta, capacidad y límites con tolerancia 1e-7.

**Resultados reales (red de prueba).** Estado OPTIMAL; costo **2.051.515 COP/semana** (transporte 1.846.515 + operación 205.000); 115 t movidas; mediana de 1,54 ms en 30 ejecuciones; verificación válida (violación máxima 0). Validación con el caso CP-01 (óptimo conocido 64).

**Precios sombra (duales) y rangos.** Los duales salen de `r.eqlin.marginals` y `r.ineqlin.marginals`; los rangos de variación de la base óptima, de `highspy.Highs.getRanging()` (`metodo_exacto/sensibilidad.py`). Ejemplo real: Puerto Gaitán (P4) tiene precio sombra −1.150: ampliar su capacidad en 1 t reduce el costo en 1.150 COP/semana, mientras la capacidad esté entre 27 y 35 t; con 35 t el costo sería 2.050.365. Villavicencio y Granada tienen precio 0 porque no usan toda su capacidad.

### B. Algoritmo genético

**Qué es.** Metaheurística poblacional inspirada en la selección natural: mantiene una población de soluciones, y en cada generación selecciona, cruza y muta para producir mejores soluciones. No garantiza el óptimo.

**Por qué lo usamos.** (1) El proyecto pide comparar un método exacto con uno heurístico. (2) No exige linealidad: si el modelo creciera (costos fijos, cargas por camión), el LP dejaría de aplicar y el AG se adaptaría cambiando solo la función de evaluación. En este problema lineal el exacto es superior; lo mostramos con datos.

**Cómo funciona en nuestro sistema** (`backend/optimizacion/algoritmo_genetico/solver.py`):

1. **Cromosoma:** vector de 40 números reales en [0, 1) (uno por ruta), *random keys*; cada valor es la **prioridad** de su ruta.
2. **Decodificador con reparación:** ordena las rutas por prioridad y envía por cada una `min(oferta restante, capacidad restante, límite)`. Garantiza oferta y capacidad; solo puede quedar oferta sin asignar (déficit).
3. **Población inicial:** 60 individuos con genes aleatorios (por defecto). Opción `heuristica`: el individuo 0 ordena las rutas por costo y la primera mitad lo imita con ruido.
4. **Aptitud:** `1 / (1 + costo + λ · violación)`, con violación = toneladas sin asignar y λ = 10 · (costo_máx + 1) · (oferta_total + 1) = **57.467.560** en la red de prueba.
5. **Selección:** torneo (k = 3, por defecto) o ruleta con escalamiento por ventana `w = f − f_min + 0,05·(f_max − f_min)`.
6. **Cruce:** un punto o dos puntos, con probabilidad 0,8; produce dos hijos.
7. **Mutación:** cada gen se reemplaza por un valor aleatorio con probabilidad 0,12.
8. **Elitismo:** los 2 mejores pasan intactos.
9. **Terminación:** número fijo de generaciones (150); sin parada anticipada. Se conserva el mejor de toda la corrida (primero factibles, luego menor costo penalizado). Evaluaciones: 60 + 149 × 58 = 8.702.
10. **Salida:** se decodifica el mejor cromosoma → asignaciones → `verificar()` → estado FEASIBLE / INFEASIBLE, costo, historial de convergencia y gap frente al exacto.

**Resultados reales.** Parámetros por defecto, semilla 42: costo **2.051.515** (gap 0,00 %), 363 ms. Convergencia: 2.701.355 en la generación 0 → 2.082.605 en la 10 → 2.051.515 en la 20 (el óptimo exacto).

| Configuración (10 semillas) | Gap promedio | Gap máximo | Tiempo medio |
|---|---|---|---|
| Torneo + 1 punto | 0,053 % | 0,166 % | 322 ms |
| Ruleta + 1 punto | 0,053 % | 0,166 % | 281 ms |
| Torneo + 2 puntos | 0,022 % | 0,166 % | 317 ms |
| Ruleta + 2 puntos | 0,087 % | 0,166 % | 332 ms |
| Inicialización heurística | 0,000 % | 0,000 % | 276 ms |

**Limitación a reconocer:** el AG solo admite el modo base (oferta exacta y plantas con capacidad máxima); fuera de él responde INVALID_INPUT.

### C. Comparación (datos medidos)

| Criterio | Método exacto | Algoritmo genético |
|---|---|---|
| Solución | Óptima global certificada | Aproximada, factible |
| Garantía de optimalidad | Sí | No |
| Tiempo en 10 × 4 | 1,5 ms (mediana) | ≈ 363 ms (semilla 42) |
| Calidad en 10 × 4 | 2.051.515 | gap 0–0,17 % (10 semillas) |

| Tamaño de red (sintética) | Rutas | Exacto | Algoritmo genético | Gap | AG / exacto |
|---|---|---|---|---|---|
| 10×4 | 40 | 1,4 ms | 95 ms | 0,00 % | 69× |
| 20×6 | 120 | 1,4 ms | 249 ms | 3,31 % | 180× |
| 40×10 | 400 | 4,1 ms | 662 ms | 10,94 % | 160× |
| 80×16 | 1280 | 13,7 ms | 2.236 ms | 6,30 % | 163× |

AG de la prueba de escalabilidad: población 40, 80 generaciones, inicialización heurística. El gap no es monótono con el tamaño (10,9 % en 40×10 y 6,3 % en 80×16): depende de la red concreta y del presupuesto de búsqueda; no lo interpretamos como una ley.

**Cuándo usar cada uno.** Exacto: modelo lineal, se necesitan garantías y precios sombra (nuestro caso). Genético: modelo no lineal o con restricciones difíciles de escribir como LP, o cuando basta una solución buena rápida y aproximada.

## Fragmentos de código

Todo el código está extraído de los archivos reales del proyecto. Cuando aparece `# …` indica líneas omitidas del mismo archivo.

### Diapositiva 14: ARMANDO EL LP

**Archivo:** `backend/optimizacion/metodo_exacto/solver.py` (líneas 27–48)

```python
c = np.array(parametros.costos_efectivos())
eq, beq, ub, bub = [], [], [], []
for e in empresas:
    fila = [1.0 if a.empresa_id == e.id else 0.0 for a in arcos]
    if parametros.modo_oferta == "exact":
        eq.append(fila)
        beq.append(e.oferta)
    else:
        ub.append(fila)
        bub.append(e.oferta)
for p in plantas:
    fila = [1.0 if a.planta_id == p.id else 0.0 for a in arcos]
    if p.tipo_demanda == "exact":
        eq.append(fila)
        beq.append(p.capacidad)
    elif p.tipo_demanda == "capacity_max":
        ub.append(fila)
        bub.append(p.capacidad)
    else:
        ub.append([-v for v in fila])
        bub.append(-p.capacidad)
limites = [(0, a.limite) for a in arcos]
```

- **Qué hace:** Construye el vector de costos c (costo efectivo de cada ruta), una fila de restricción por empresa (igualdad con su oferta) y una por planta (desigualdad con su capacidad), y las cotas de cada variable.
- **Función en el sistema:** Traduce el modelo matemático a la forma matricial que exige scipy.optimize.linprog.
- **Qué debo explicar:** Que cada fila tiene unos en las columnas (rutas) de una empresa o planta; que la oferta es igualdad porque todo el residuo debe recogerse y la capacidad es ≤; que bounds=(0, límite) impone x ≥ 0.

### Diapositiva 15: RESOLVER Y VERIFICAR

**Archivo:** `backend/optimizacion/metodo_exacto/solver.py` (líneas 49–64)

```python
inicio = perf_counter()
try:
    r = linprog(
        c,
        A_ub=np.array(ub) if ub else None, b_ub=np.array(bub) if bub else None,
        A_eq=np.array(eq) if eq else None, b_eq=np.array(beq) if beq else None,
        bounds=limites, method="highs",
    )  # fmt: skip
# …
asignaciones = construir_asignaciones(parametros, [(k, r.x[k]) for k in range(len(arcos)) if r.x[k] > 1e-9])
comprobacion = verificar(parametros, asignaciones)
```

**Archivo:** `backend/optimizacion/validacion.py` (líneas 40–46)

```python
flujo = {(a["empresa_id"], a["planta_id"]): float(a["cantidad"]) for a in asignaciones}
errores=[]; maximo=0.0
for e in parametros.empresas:
    lhs=sum(flujo.get((e.id,p.id),0) for p in parametros.plantas)
    residuo=abs(lhs-e.oferta) if parametros.modo_oferta == "exact" else max(0,lhs-e.oferta)
    maximo=max(maximo,residuo)
    if residuo > tolerancia: errores.append(f"Oferta de {e.id} no cumple: {lhs:.6g}.")
```

- **Qué hace:** Llama a linprog con method="highs", convierte la solución en asignaciones (solo flujos > 1e-9) y la verifica recalculando las sumas por empresa contra su oferta con tolerancia 1e-7.
- **Función en el sistema:** Resuelve el LP y es la segunda línea de defensa: no se confía solo en el solver.
- **Qué debo explicar:** Que r.x son las toneladas, r.fun el costo mínimo, r.status == 0 significa óptimo, y que verificar() recalcula todo de forma independiente (oferta, capacidad y límites).

### Diapositiva 19: CROMOSOMA

**Archivo:** `backend/optimizacion/algoritmo_genetico/solver.py` (líneas 90–106)

```python
def decodificar(genes):
    """Prioridades -> flujos [(índice de arco, t)], costo y violación (t sin asignar)."""
    restante_o, restante_c = oferta[:], capacidad[:]
    pendiente = oferta_total
    flujos, costo = [], 0.0
    for k in sorted(rango_n, key=genes.__getitem__):
        if pendiente <= 1e-10:
            break
        e, p = arco_e[k], arco_p[k]
        disponible = min(restante_o[e], restante_c[p], arco_limite[k])
        if disponible > 1e-10:
            flujos.append((k, disponible))
            restante_o[e] -= disponible
            restante_c[p] -= disponible
            pendiente -= disponible
            costo += disponible * costos[k]
    return flujos, costo, max(0.0, pendiente)
```

- **Qué hace:** Decodificador: ordena las rutas por prioridad (el valor del gen) y envía por cada una el mínimo entre la oferta restante de la empresa, la capacidad restante de la planta y el límite de la ruta; acumula el costo y devuelve las toneladas que quedaron sin asignar.
- **Función en el sistema:** Convierte un cromosoma (vector de prioridades) en un plan de envíos factible: es la 'reparación' que garantiza oferta y capacidad.
- **Qué debo explicar:** Que el cromosoma no guarda toneladas sino prioridades (random keys), por eso cualquier cruce o mutación produce un individuo válido; y que la única restricción que puede incumplirse es dejar oferta sin asignar.

### Diapositiva 20: POBLACIÓN Y APTITUD

**Archivo:** `backend/optimizacion/algoritmo_genetico/solver.py` (líneas 87–150)

```python
penalizacion = FACTOR_PENALIZACION * (max(costos, default=0.0) + 1.0) * (oferta_total + 1.0)
# …
def evaluar(genes) -> _Individuo:
    _, costo, violacion = decodificar(genes)
    penalizado = costo + penalizacion * violacion
    return _Individuo(genes, costo, violacion, penalizado, 1.0 / (1.0 + penalizado))
# …
    if cfg.inicializacion == "heuristica" and i < max(1, cfg.poblacion // 2):
        ruido = 0.0 if i == 0 else rng.uniform(0.05, 0.5)
        return [costos[k] / costo_max * (1 - ruido) + rng.random() * ruido for k in rango_n]
    return [rng.random() for _ in rango_n]

inicio = perf_counter()
poblacion = [evaluar(genes_iniciales(i)) for i in range(cfg.poblacion)]
```

- **Qué hace:** Calcula λ (la penalización), evalúa un individuo (costo + penalización × déficit) y su aptitud 1/(1+costo penalizado), y crea la población inicial (aleatoria o heurística).
- **Función en el sistema:** Define qué tan bueno es un individuo y desde dónde parte la búsqueda.
- **Qué debo explicar:** Que aptitud mayor = menor costo penalizado; que λ depende del costo máximo y de la oferta total para que una solución infactible siempre pierda; y la diferencia entre inicialización aleatoria y heurística.

### Diapositiva 21: SELECCIÓN

**Archivo:** `backend/optimizacion/algoritmo_genetico/solver.py` (líneas 113–121)

```python
def crear_selector(poblacion):
    if cfg.seleccion == "torneo":
        return lambda: max(rng.sample(poblacion, cfg.tamano_torneo), key=lambda i: i.aptitud)
    aptitudes = [i.aptitud for i in poblacion]
    minimo, tramo = min(aptitudes), max(aptitudes) - min(aptitudes)
    pesos = [1.0] * len(aptitudes) if tramo <= 0 else [a - minimo + 0.05 * tramo for a in aptitudes]
    acumulado = list(accumulate(pesos))
    total, ultimo = acumulado[-1], len(poblacion) - 1
    return lambda: poblacion[min(bisect_left(acumulado, rng.random() * total), ultimo)]
```

- **Qué hace:** Devuelve una función selectora: torneo (gana el mejor de k individuos al azar) o ruleta con pesos escalados por ventana, buscados con bisect_left sobre pesos acumulados.
- **Función en el sistema:** Decide qué individuos se reproducen: controla la presión de selección.
- **Qué debo explicar:** Que el torneo es la opción por defecto (k=3) y que la ruleta necesita escalamiento porque las aptitudes son casi iguales (1/65 vs 1/67).

### Diapositiva 22: CRUCE Y MUTACIÓN

**Archivo:** `backend/optimizacion/algoritmo_genetico/solver.py` (líneas 123–139)

```python
def cruzar(a, b):
    if n < 2:
        return a[:], b[:]
    if cfg.tipo_cruce == "un_punto" or n < 3:
        c = rng.randrange(1, n)
        return a[:c] + b[c:], b[:c] + a[c:]
    c1, c2 = sorted(rng.sample(range(1, n), 2))
    return a[:c1] + b[c1:c2] + a[c2:], b[:c1] + a[c1:c2] + b[c2:]

def mutar(genes):
    if cfg.mutacion > 0:
        for i in rango_n:
            if rng.random() < cfg.mutacion:
                genes[i] = rng.random()
    return genes

costo_max = max(costos, default=0.0) or 1.0
```

- **Qué hace:** cruzar(): intercambia tramos de dos padres con uno o dos puntos de corte y devuelve dos hijos. mutar(): cada gen se reemplaza por un número aleatorio con probabilidad cfg.mutacion.
- **Función en el sistema:** Genera diversidad y combina buenas soluciones.
- **Qué debo explicar:** Que el cruce se aplica con probabilidad 0,8, la mutación es por gen con 0,12, y que los hijos siempre son vectores válidos de prioridades.

### Diapositiva 23: CICLO EVOLUTIVO

**Archivo:** `backend/optimizacion/algoritmo_genetico/solver.py` (líneas 154–178)

```python
for generacion in range(cfg.generaciones):
    poblacion.sort(key=lambda i: i.penalizado)
# …
candidato = min(poblacion, key=lambda i: (i.violacion > TOLERANCIA_DEFICIT, i.penalizado))
if mejor is None or (candidato.violacion > TOLERANCIA_DEFICIT, candidato.penalizado) < (
    mejor.violacion > TOLERANCIA_DEFICIT, mejor.penalizado
):
    mejor = candidato
# …
seleccionar = crear_selector(poblacion)
nueva = poblacion[: cfg.elitismo]
while len(nueva) < cfg.poblacion:
    a, b = seleccionar().genes, seleccionar().genes
    h1, h2 = cruzar(a, b) if rng.random() < cfg.cruce else (a[:], b[:])
    for hijo in (h1, h2):
        if len(nueva) < cfg.poblacion:
            nueva.append(evaluar(mutar(hijo)))
            evaluaciones += 1
poblacion = nueva
```

- **Qué hace:** Bucle principal: ordena por costo penalizado, registra el mejor de toda la corrida (primero los factibles), conserva a los 2 mejores (elitismo) y completa la nueva población con hijos cruzados y mutados.
- **Función en el sistema:** Es la evolución: repite evaluar → seleccionar → cruzar → mutar durante cfg.generaciones.
- **Qué debo explicar:** Que no hay parada anticipada (150 generaciones), que 'mejor' se actualiza con una tupla (infactible?, costo) para preferir siempre factibles, y que con los parámetros por defecto hay 8.702 evaluaciones (60 + 149 × 58).

### Diapositiva 30: CONEXIÓN

**Archivo:** `backend/api/views.py` (líneas 558–579)

```python
class EjecutarExactoView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.EjecutarExactoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        parametros, escenario = _parametros_para(d, d["modo_oferta"])
        resultado = svc.resolver_exacto(parametros)
        ejecucion_id = None
# …
return Response({"ejecucion_id": ejecucion_id, "resultado": resultado.como_dict()})
```

**Archivo:** `backend/servicios/ejecucion.py` (líneas 21–85)

```python
def resolver_exacto(parametros: ParametrosModelo) -> ResultadoOptimizacion:
    validar_tamano(parametros)
    resultado = MetodoExacto().resolver(parametros)
    if resultado.estado == "INVALID_INPUT":
        raise ErrorDeNegocio("El escenario no es válido para optimizar.", resultado.mensajes)
    return resultado
# …
def gap_porcentual(heuristico: float | None, exacto: float | None) -> float | None:
    if heuristico is None or exacto is None or abs(exacto) < 1e-12:
        return None
    return (heuristico - exacto) / abs(exacto) * 100

```

- **Qué hace:** La vista valida la petición, construye los parámetros desde la base de datos, llama a resolver_exacto y devuelve el resultado en JSON (y opcionalmente guarda la ejecución). El servicio valida el tamaño y traduce un resultado inválido en un error de negocio; gap_porcentual calcula (heurístico − exacto)/|exacto| × 100.
- **Función en el sistema:** Conecta la API REST con el núcleo de optimización y entrega el resultado que la interfaz muestra.
- **Qué debo explicar:** El recorrido vista → servicio → solver puro, y que el núcleo no depende de Django.

### Diapositiva 31: DATOS DE ENTRADA

**Archivo:** `backend/servicios/conversion.py` (líneas 15–42)

```python
def construir_parametros(modo_oferta: str = "exact") -> ParametrosModelo:
    """Red actual (solo elementos activos) -> ParametrosModelo."""
    empresas = Empresa.objects.filter(activa=True).order_by("codigo")
    plantas = Planta.objects.filter(activa=True).order_by("codigo")
    rutas = (
        Ruta.objects.filter(activa=True, empresa__activa=True, planta__activa=True)
        .select_related("empresa", "planta")
        .order_by("empresa__codigo", "planta__codigo")
    )
    return ParametrosModelo(
# …
    arcos=tuple(
        ArcoCosto(
            r.empresa.codigo,
            r.planta.codigo,
            r.costo_efectivo,
            r.distancia_km,
            r.tarifa_km_ton,
            r.limite,
        )
        for r in rutas
    ),
    modo_oferta=modo_oferta,
)
```

- **Qué hace:** construir_parametros lee de PostgreSQL solo las empresas, plantas y rutas activas y arma el objeto ParametrosModelo, con el costo efectivo (transporte + operación + precio) de cada ruta.
- **Función en el sistema:** Es la entrada de datos de los dos solvers: lo que el usuario registra en la interfaz se convierte en modelo matemático.
- **Qué debo explicar:** Que lo desactivado no entra al cálculo y que ambos métodos reciben exactamente el mismo modelo.

## Guion por diapositiva

### Diapositiva 1: OPTIAGRO-LLANOS

**Qué se muestra:** Portada: nombre del proyecto, asignatura, programa y equipo.

**Qué debo decir:** Buenos días. Les presentamos OptiAgro-Llanos, el sistema que desarrollamos para el proyecto final de Optimización: una aplicación web que calcula la forma más barata de llevar los residuos de 10 agroempresas a 4 plantas del Meta, con dos enfoques que compararemos: un método exacto y un algoritmo genético.

**Conceptos clave:** Problema de transporte · Método exacto vs metaheurística

**Posibles preguntas:**

- **P:** ¿Cuál es el aporte principal del proyecto?
  **R:** Una herramienta completa (modelo, dos optimizadores, sensibilidad, comparación e interfaz web) para decidir la distribución de residuos al menor costo.

### Diapositiva 2: CONTENIDO

**Qué se muestra:** Cuatro bloques: contexto, el sistema, optimización (exacto y genético) y resultados.

**Qué debo decir:** Empezamos con el contexto y el problema; luego el sistema y su arquitectura; después el corazón del trabajo, que es la optimización: primero el método exacto y luego el algoritmo genético, con el código real; finalmente la comparación, los resultados y las conclusiones.

**Conceptos clave:** Orden de la exposición

**Posibles preguntas:**

- **P:** ¿Dónde está lo más importante?
  **R:** En el bloque de optimización: diapositivas del método exacto, del algoritmo genético y su comparación.

### Diapositiva 3: INTRODUCCIÓN

**Qué se muestra:** Qué es el proyecto y para quién: EcoResiduos del Llano S.A.S. y su red de 10 empresas y 4 plantas.

**Qué debo decir:** EcoResiduos del Llano transforma residuos agropecuarios en abonos, biocombustibles y suplementos. Recibe residuos de 10 empresas aliadas y los procesa en 4 plantas: Villavicencio, Restrepo, Granada y Puerto Gaitán. La pregunta es cuántas toneladas debe enviar cada empresa a cada planta para que el costo total sea mínimo. Nuestro sistema responde esa pregunta y permite explorar escenarios.

**Conceptos clave:** Residuos agropecuarios · Costo logístico · Red empresa → planta

**Posibles preguntas:**

- **P:** ¿Los datos son reales?
  **R:** Las plantas están en municipios reales, pero ofertas, capacidades y costos de la demostración son ficticios: las fuentes no traían una matriz regional completa. Está declarado en SUPUESTOS.md.

### Diapositiva 4: EL PROBLEMA

**Qué se muestra:** Asignación empírica de rutas → sobrecostos; la gerencia pide un sistema que minimice el costo total.

**Qué debo decir:** Hoy la recolección y el transporte se asignan de forma empírica, y eso genera sobrecostos. Con 10 orígenes y 4 destinos hay 40 rutas posibles y cada una tiene un costo distinto; decidir a mano cuánto enviar por cada una sin pasarse de la capacidad de las plantas es difícil y casi nunca óptimo. La gerencia pidió un sistema que minimice el costo y que permita cambiar ofertas, capacidades y costos para ver qué pasa.

**Conceptos clave:** Asignación empírica · 40 rutas posibles · Capacidad de plantas

**Posibles preguntas:**

- **P:** ¿Por qué no se puede resolver a mano?
  **R:** Porque las decisiones están acopladas: enviar más a una planta consume su capacidad y obliga a cambiar el resto. Son 40 variables con 14 restricciones simultáneas.

### Diapositiva 5: PROBLEMAS

**Qué se muestra:** Cuatro problemas específicos: costo, capacidad, incertidumbre y adaptabilidad.

**Qué debo decir:** Identificamos cuatro problemas concretos: primero, el costo de transporte alto por rutas mal asignadas; segundo, respetar la capacidad de cada planta y la oferta de cada empresa; tercero, la incertidumbre: combustible, oferta y capacidad cambian; y cuarto, que la red crece, entran nuevas empresas y sedes y el sistema debe adaptarse sin reprogramar.

**Conceptos clave:** Restricciones de oferta y capacidad · Análisis de sensibilidad · Ampliación de la red

**Posibles preguntas:**

- **P:** ¿Cómo se atiende que la red crezca?
  **R:** Las empresas, plantas y rutas se guardan en la base de datos y se editan desde la aplicación; el modelo se reconstruye en cada cálculo a partir de lo que esté activo.

### Diapositiva 6: OBJETIVOS

**Qué se muestra:** Objetivo general y cuatro específicos.

**Qué debo decir:** El objetivo general es diseñar una solución computacional para minimizar el costo logístico de la red. Los específicos: estructurar el problema de transporte; implementar el modelo exacto; implementar un algoritmo genético; hacer el análisis de sensibilidad; y comparar ambos métodos en costo, tiempo y escalabilidad. Cada uno tiene un módulo en el código, y más adelante mostramos el resultado de cada uno.

**Conceptos clave:** Modelo exacto · Algoritmo genético · Sensibilidad · Comparación

**Posibles preguntas:**

- **P:** ¿Cómo comprueban que cumplieron los objetivos?
  **R:** Con pruebas automatizadas (por ejemplo el caso CP-01 con óptimo conocido 64) y con la comparación numérica exacto vs genético que veremos en resultados.

### Diapositiva 7: EL SISTEMA

**Qué se muestra:** Captura real de la aplicación y las funciones principales.

**Qué debo decir:** OptiAgro-Llanos es una aplicación web. El administrador gestiona empresas, plantas y rutas; el sistema ubica cada estación en el mapa y calcula la distancia por carretera. Con esa red se puede calcular la distribución óptima con el método exacto o con el algoritmo genético, ver los envíos dibujados sobre las vías, responder preguntas del tipo qué pasa si sube el combustible, y generar el reporte comparativo.

**Conceptos clave:** Mapa de la red · Distancia por carretera (OSRM) · Roles administrador / analista

**Posibles preguntas:**

- **P:** ¿Quién puede cambiar los datos?
  **R:** Solo el rol administrador. El analista ejecuta cálculos y consulta, pero no modifica la red; el backend valida el permiso, no solo la interfaz.

### Diapositiva 8: TECNOLOGÍAS

**Qué se muestra:** Stack real tomado de requirements.txt, package.json y los Dockerfile.

**Qué debo decir:** En el backend usamos Python 3.12 con Django 5.2 y Django REST Framework; la autenticación es con JWT. La optimización usa NumPy y SciPy, con el solver HiGHS, y la biblioteca highspy para obtener los rangos de sensibilidad. En el frontend, Vue 3 con TypeScript y Vite, Pinia para el estado y Leaflet para los mapas. Todo corre en contenedores Docker: PostgreSQL 16, gunicorn para Django y nginx para servir la aplicación. Las distancias por carretera vienen de OSRM sobre OpenStreetMap.

**Conceptos clave:** Django REST Framework · SciPy / HiGHS · Vue 3 · Docker Compose · OSRM

**Posibles preguntas:**

- **P:** ¿Por qué Django y Vue y no una sola herramienta?
  **R:** Para separar responsabilidades: el backend concentra el modelo, los solvers y los permisos; el frontend solo consume una API REST. Eso permite probar cada parte por separado y cambiar la interfaz sin tocar la optimización.
- **P:** ¿Por qué HiGHS?
  **R:** Es un solver de programación lineal de código abierto, rápido y que viene integrado en SciPy; además highspy da acceso a la base óptima y al análisis de rangos.

### Diapositiva 9: ARQUITECTURA

**Qué se muestra:** Diagrama de capas: navegador → nginx → Django → servicios → núcleo de optimización, con PostgreSQL y OSRM.

**Qué debo decir:** El navegador solo habla con nginx. Nginx sirve la aplicación Vue y reenvía las peticiones /api a Django. Django valida permisos y datos en la capa de API; la capa de servicios convierte lo que hay en la base de datos en un modelo matemático y llama a los solvers. Los paquetes dominio y optimizacion son Python puro, sin Django: así el núcleo se puede probar y reutilizar solo. PostgreSQL guarda la red, los usuarios y el historial; OSRM se consulta para las distancias.

**Conceptos clave:** API REST · Capa de servicios · Núcleo sin dependencias de Django · JWT

**Posibles preguntas:**

- **P:** ¿Por qué el núcleo no depende de Django?
  **R:** Para que los algoritmos se puedan probar con datos en memoria, sin base de datos, y para que cualquier cambio de framework no afecte la lógica de optimización.

### Diapositiva 10: RECORRIDO

**Qué se muestra:** Diagrama de flujo: del dato ingresado a la solución mostrada.

**Qué debo decir:** El recorrido completo: el administrador registra empresas, plantas y rutas, y el backend calcula las distancias por carretera. El usuario pulsa Calcular; la API lee la red activa de PostgreSQL y construye el modelo con costos efectivos; valida el modelo, resuelve con HiGHS o con el algoritmo genético, y verifica que el resultado cumpla todas las restricciones. La respuesta vuelve en JSON y la interfaz la muestra como resumen en lenguaje natural, tabla de envíos y mapa. Además el cálculo puede guardarse en el historial.

**Conceptos clave:** Modelo → solver → verificación · Costo efectivo · Historial de ejecuciones

**Posibles preguntas:**

- **P:** ¿Qué pasa si los datos son inconsistentes?
  **R:** La función validar rechaza el modelo (por ejemplo, capacidad total menor que la oferta) y la API responde 400 con el motivo; nunca se llega al solver con datos inválidos.

### Diapositiva 11: MODELO

**Qué se muestra:** Formulación matemática del problema de transporte tal como está implementada.

**Qué debo decir:** El modelo es un problema de transporte. Los conjuntos son las empresas i y las plantas j. La variable x_ij son las toneladas por semana que la empresa i envía a la planta j. La función objetivo minimiza la suma de x_ij por el costo efectivo c_ij, que en nuestro sistema es transporte, o sea distancia por tarifa, más el costo de operación de la planta, más el precio de la empresa. Las restricciones: cada empresa envía exactamente su oferta; cada planta recibe como máximo su capacidad; y cada ruta tiene cota inferior cero y, opcionalmente, un límite.

**Conceptos clave:** x_ij ≥ 0 · c_ij = transporte + operación + precio · Oferta = ; capacidad ≤

**Posibles preguntas:**

- **P:** ¿Por qué la oferta es una igualdad y la capacidad una desigualdad?
  **R:** Porque todo el residuo de una empresa debe recogerse (no se puede dejar), pero una planta puede quedar con capacidad sin usar. En el código también se admiten demanda exacta o mínima en el exacto.
- **P:** ¿Las variables son enteras?
  **R:** Son continuas. Como las ofertas y capacidades son enteras, el problema de transporte tiene matriz totalmente unimodular y el óptimo sale entero (lo vimos en los resultados: 11, 10, 2 toneladas, etc.).

### Diapositiva 12: DOS ENFOQUES

**Qué se muestra:** Sección de optimización: método exacto (garantiza el óptimo) y algoritmo genético (heurística).

**Qué debo decir:** Entramos a la parte central. Implementamos dos formas de resolver el mismo modelo. El método exacto resuelve el problema lineal y garantiza el óptimo global. El algoritmo genético busca soluciones buenas imitando la evolución y no garantiza el óptimo, pero es flexible. Los dos usan el mismo modelo y la misma verificación de restricciones, así que la comparación es justa.

**Conceptos clave:** Optimalidad garantizada vs aproximada · Mismo modelo, misma verificación

**Posibles preguntas:**

- **P:** ¿Cuál es la diferencia esencial?
  **R:** El exacto prueba matemáticamente que no existe una solución mejor; el genético solo entrega la mejor que encontró.

### Diapositiva 13: MÉTODO EXACTO

**Qué se muestra:** Qué es y cómo se plantea: programación lineal resuelta con HiGHS.

**Qué debo decir:** Un método exacto es el que garantiza encontrar el óptimo global y lo certifica. El que implementa nuestro código es programación lineal, resuelta con el solver HiGHS a través de la función linprog de SciPy. Lo comprobamos en el código: se llama linprog con method igual a highs. Variables: las toneladas x_ij, 40 en la red de prueba. Objetivo: minimizar el costo efectivo total. Restricciones: 10 igualdades de oferta y 4 desigualdades de capacidad, más las cotas de cada variable. A diferencia del genético, aquí no se prueban soluciones al azar: se recorre el poliedro de soluciones factibles hasta cumplir las condiciones de optimalidad.

**Conceptos clave:** Programación lineal · HiGHS (simplex dual / puntos interiores) · Solución global certificada

**Posibles preguntas:**

- **P:** ¿Es fuerza bruta o ramificación y acotamiento?
  **R:** No. Es programación lineal continua; no enumera soluciones ni ramifica. HiGHS la resuelve con métodos de simplex o de puntos interiores.
- **P:** ¿Qué algoritmo usa HiGHS por dentro?
  **R:** Con method='highs', SciPy deja que HiGHS elija entre simplex dual y puntos interiores. No lo forzamos; lo importante es que el resultado queda certificado como óptimo.

### Diapositiva 14: ARMANDO EL LP

**Qué se muestra:** Código: vector de costos y matrices de restricciones (metodo_exacto/solver.py).

**Qué debo decir:** Este es el código real que arma el problema. El vector c son los costos efectivos de las 40 rutas. Para cada empresa se crea una fila con unos en las columnas de sus rutas: si el modo es exacto, va a las igualdades con la oferta como lado derecho. Para cada planta pasa igual, pero como desigualdad con su capacidad. Al final, los límites: cada x_ij va de cero al límite de la ruta.

**Conceptos clave:** A_eq, b_eq · A_ub, b_ub · bounds

**Posibles preguntas:**

- **P:** ¿Qué significa cada fila de la matriz?
  **R:** Cada fila es una restricción: tiene un 1 en las variables de una empresa (o de una planta) y su suma debe igualar la oferta (o no pasar la capacidad).

### Diapositiva 15: RESOLVER Y VERIFICAR

**Qué se muestra:** Código: llamada a linprog con HiGHS y verificación independiente de la solución.

**Qué debo decir:** Aquí se llama a linprog con method highs. Si el estado no es cero, se traduce a infactible, no acotado, etcétera. Si es óptimo, se construyen las asignaciones y, antes de aceptar el resultado, pasa por la función verificar, que recalcula las sumas por empresa y por planta y comprueba oferta, capacidad y límites con tolerancia 1e-7. Es una segunda línea de defensa: no confiamos solo en el solver. Después se extraen los duales, que son los precios sombra.

**Conceptos clave:** r.status == 0 · Verificación con tolerancia · Duales (marginals)

**Posibles preguntas:**

- **P:** ¿Cómo saben que la solución es óptima?
  **R:** HiGHS reporta estado óptimo (Status 7: Optimal en nuestros mensajes): cumple factibilidad primal, factibilidad dual y holgura complementaria, y como el LP es convexo, ese óptimo es global. Además verificamos las restricciones por nuestra cuenta.

### Diapositiva 16: RESULTADO EXACTO

**Qué se muestra:** Resultado real sobre la red de prueba: costo, desglose y uso de cada planta.

**Qué debo decir:** Sobre la red de prueba, de 10 empresas y 4 plantas, el método exacto da un costo óptimo de 2.051.515 pesos por semana: 1.846.515 de transporte y 205.000 de operación. Se mueven 115 toneladas. Dos plantas quedan al 100 por ciento, Restrepo y Puerto Gaitán; Villavicencio queda al 65 y Granada al 77. El cálculo tarda una mediana de 1,5 milisegundos en 30 ejecuciones. Como validación, el caso CP-01, con óptimo conocido de 64, lo resuelve exactamente.

**Conceptos clave:** 2.051.515 COP/semana · Plantas al 100 % = cuello de botella · CP-01 = 64

**Posibles preguntas:**

- **P:** ¿Cómo validaron que el modelo está bien?
  **R:** Con el caso CP-01, un ejemplo pequeño con óptimo conocido (E1→P1 12 t, E2→P2 8 t, costo 64), incluido en las pruebas automáticas, y con la verificación de restricciones en cada ejecución.

### Diapositiva 17: SENSIBILIDAD

**Qué se muestra:** Precios sombra y rangos de variación (HiGHS getRanging), con valores reales.

**Qué debo decir:** El exacto además entrega los precios sombra. En la red de prueba, Puerto Gaitán tiene un precio sombra de menos 1.150: ampliar su capacidad en una tonelada ahorraría 1.150 pesos por semana, y eso es válido mientras la capacidad esté entre 27 y 35 toneladas, que es el rango donde la base óptima no cambia. Restrepo vale 50 pesos por tonelada. Villavicencio y Granada tienen precio cero porque les sobra capacidad. Estos rangos los obtenemos con la función getRanging de highspy; los escenarios además se reoptimizan y se comparan contra el genético.

**Conceptos clave:** Precio sombra (dual) · Rango de la base óptima · Cuello de botella

**Posibles preguntas:**

- **P:** ¿Qué es un precio sombra?
  **R:** El cambio en el costo óptimo por cada unidad adicional de un recurso (aquí, una tonelada de capacidad), mientras no cambie la base óptima.
- **P:** ¿Por qué el de Villavicencio es cero?
  **R:** Porque usa 26 de sus 40 toneladas: su restricción no está activa, así que más capacidad no reduce el costo.

### Diapositiva 18: ALGORITMO GENÉTICO

**Qué se muestra:** Qué es y por qué lo usamos: metaheurística inspirada en la evolución.

**Qué debo decir:** Un algoritmo genético es una metaheurística inspirada en la selección natural. Mantiene una población de soluciones candidatas; en cada generación elige a las mejores, las cruza, las muta y se queda con las mejores. Lo usamos por dos razones: el proyecto exige comparar un método exacto con uno heurístico, y porque el genético no necesita que el problema sea lineal; si mañana el modelo incluyera costos fijos o cargas por camión, el exacto lineal ya no aplicaría y el genético se adaptaría cambiando solo la función de evaluación. Aquí resuelve el mismo problema de transporte, pero buscando por prioridades de rutas en vez de resolver ecuaciones.

**Conceptos clave:** Metaheurística · Población, generación · Sin garantía de óptimo

**Posibles preguntas:**

- **P:** Si el exacto es mejor aquí, ¿para qué el genético?
  **R:** Porque el PDF pide compararlos, y porque demuestra una alternativa que sirve cuando el modelo deja de ser lineal. En este problema lineal el exacto gana en tiempo y garantía; lo mostramos con datos.
- **P:** ¿Qué problema concreto resuelve el AG?
  **R:** Decidir cuántas toneladas enviar por cada una de las 40 rutas, respetando oferta y capacidad, minimizando el costo.

### Diapositiva 19: CROMOSOMA

**Qué se muestra:** Esquema: vector de prioridades → decodificador voraz → flujos factibles; código de decodificar().

**Qué debo decir:** Cada individuo es un vector de números entre 0 y 1, uno por ruta: 40 genes en la red de prueba. Cada gen es la prioridad de su ruta, y esto se conoce como llaves aleatorias. El decodificador ordena las rutas por prioridad y, siguiendo ese orden, envía por cada ruta el mínimo entre la oferta que le queda a la empresa, la capacidad que le queda a la planta y el límite de la ruta. Así, por construcción, ninguna solución excede oferta ni capacidad. La única restricción que puede incumplirse es que quede oferta sin asignar, y eso se penaliza.

**Conceptos clave:** Random keys · Decodificador con reparación · Toneladas sin asignar = déficit

**Posibles preguntas:**

- **P:** ¿Por qué no codificar directamente las toneladas?
  **R:** Porque un cruce de toneladas casi siempre rompe la oferta o la capacidad. Con prioridades, cualquier cruce o mutación produce un vector válido que el decodificador convierte en un plan factible.
- **P:** ¿Dónde queda la restricción de capacidad?
  **R:** Dentro del decodificador: restante_c por planta nunca baja de cero porque se envía el mínimo entre lo disponible.

### Diapositiva 20: POBLACIÓN Y APTITUD

**Qué se muestra:** Población inicial y función de aptitud con penalización (evaluar(), genes_iniciales()).

**Qué debo decir:** La población inicial son 60 individuos con genes aleatorios por defecto; hay una opción heurística que sesga la mitad hacia rutas baratas. La aptitud es la inversa del costo penalizado: uno dividido entre uno más el costo más lambda por la violación, donde la violación son las toneladas sin asignar. Lambda se calcula de los datos: diez por el costo máximo más uno por la oferta total más uno. En la red de prueba es 57 millones, así que dejar una tonelada sin asignar es mucho peor que cualquier ahorro de costo. Mayor aptitud es mejor.

**Conceptos clave:** Fitness = 1/(1+costo+λ·violación) · Penalización por déficit · Población inicial

**Posibles preguntas:**

- **P:** ¿Por qué la inversa del costo?
  **R:** Porque el AG maximiza aptitud y el problema es de minimización; además la ruleta necesita aptitudes positivas.
- **P:** ¿Cómo eligieron lambda?
  **R:** Proporcional al peor costo por la oferta total, para que cualquier solución factible siempre supere a una infactible y aun así haya una señal gradual: menos déficit es mejor.

### Diapositiva 21: SELECCIÓN

**Qué se muestra:** Torneo y ruleta con escalamiento por ventana (crear_selector()).

**Qué debo decir:** Hay dos formas de seleccionar padres, configurables. En el torneo se toman tres individuos al azar y gana el de mayor aptitud: es la opción por defecto. En la ruleta, la probabilidad es proporcional a la aptitud, pero con escalamiento por ventana, porque las aptitudes son casi iguales, como uno sobre sesenta y cinco contra uno sobre sesenta y siete, y sin escalar la ruleta casi no distinguiría entre buenos y malos.

**Conceptos clave:** Torneo (k = 3) · Ruleta · Presión de selección

**Posibles preguntas:**

- **P:** ¿Qué selección funcionó mejor?
  **R:** En 10 semillas con la red de prueba, el gap promedio fue 0,053 % con torneo y 0,053 % con ruleta (cruce de un punto): prácticamente igual en este problema pequeño.

### Diapositiva 22: CRUCE Y MUTACIÓN

**Qué se muestra:** Cruce de uno o dos puntos y mutación génica (cruzar(), mutar()).

**Qué debo decir:** El cruce combina dos padres con probabilidad 0,8. En uno o dos puntos, se cortan los vectores de prioridades y se intercambian los tramos para generar dos hijos. La mutación revisa cada gen y, con probabilidad 0,12, lo reemplaza por un número aleatorio nuevo: introduce diversidad y evita quedar atrapados. Como los genes son prioridades, cualquier hijo es válido: el decodificador siempre produce un plan factible.

**Conceptos clave:** Cruce un punto / dos puntos · Mutación (0,12 por gen) · Diversidad

**Posibles preguntas:**

- **P:** ¿Por qué una tasa de mutación de 0,12?
  **R:** Es el valor por defecto del proyecto, ajustable desde la interfaz. Con 40 genes, en promedio muta alrededor de 5 genes por individuo, suficiente para explorar sin destruir las buenas soluciones.

### Diapositiva 23: CICLO EVOLUTIVO

**Qué se muestra:** Diagrama de flujo del algoritmo y código del bucle principal.

**Qué debo decir:** El ciclo: evaluar la población, ordenar, guardar el mejor, y construir la siguiente generación con elitismo, selección, cruce y mutación. El elitismo pasa intactos a los dos mejores. El algoritmo termina al completar el número de generaciones, 150 por defecto; no hay parada anticipada. Durante toda la corrida se guarda el mejor individuo: primero los factibles y, entre ellos, el de menor costo penalizado. En total son 8.702 evaluaciones con los parámetros por defecto.

**Conceptos clave:** Elitismo = 2 · Criterio de parada: generaciones · Mejor de toda la corrida

**Posibles preguntas:**

- **P:** ¿Cómo determinan cuándo termina?
  **R:** Por número fijo de generaciones (150). En la curva se ve que converge hacia la generación 20, pero el algoritmo no se detiene antes.
- **P:** ¿Es reproducible?
  **R:** Sí: todo el azar sale de random.Random(semilla); con la misma semilla y datos, el mismo resultado.

### Diapositiva 24: RESULTADO DEL AG

**Qué se muestra:** Parámetros usados y curva de convergencia real (mejor costo por generación).

**Qué debo decir:** Con los parámetros por defecto y semilla 42, el algoritmo parte de un mejor costo de 2,70 millones en la generación cero, baja a 2,08 millones en la generación 10 y alcanza 2.051.515 en la generación 20, que es el mismo óptimo del método exacto: gap de cero por ciento. El promedio de la población no baja tanto porque la mutación mantiene diversidad. Interpretamos el resultado como un plan de envíos factible; su calidad se mide con el gap frente al óptimo exacto.

**Conceptos clave:** Convergencia · Gap % = (AG − exacto) / exacto · Mejor individuo → plan de envíos

**Posibles preguntas:**

- **P:** ¿Cómo se interpreta la mejor solución?
  **R:** El mejor individuo se decodifica en toneladas por ruta, se verifica y se reporta con su costo. El gap indica qué tan lejos está del óptimo exacto.
- **P:** ¿El AG siempre llega al óptimo?
  **R:** No. En 10 semillas con torneo y un punto, el gap fue 0 % en 5 y llegó hasta 0,17 % en otras; y en redes más grandes llegó hasta 10,9 % con la configuración de la prueba de escalabilidad.

### Diapositiva 25: EXACTO VS GENÉTICO

**Qué se muestra:** Tabla comparativa con datos medidos en el proyecto.

**Qué debo decir:** Comparemos. El exacto entrega el óptimo certificado, con una mediana de 1,5 milisegundos en la red de prueba; el genético tarda unos 360 milisegundos, más de 200 veces más, y entrega una solución muy buena pero sin garantía. En la red de prueba el genético alcanzó el óptimo con la configuración por defecto; en redes sintéticas más grandes el gap subió hasta 10,9 %. Conviene el exacto cuando el modelo es lineal, como éste; conviene el genético cuando el modelo tiene no linealidades o restricciones difíciles de escribir como un LP.

**Conceptos clave:** Garantía de optimalidad · Tiempo de cómputo · Escalabilidad · Flexibilidad

**Posibles preguntas:**

- **P:** ¿Cuál recomiendan para la empresa?
  **R:** El método exacto: es más rápido, preciso y entrega precios sombra. El genético queda como alternativa si el modelo evoluciona a no lineal y como contraste académico.

### Diapositiva 26: RESULTADOS: RED

**Qué se muestra:** Gráfico de uso de cada planta y asignación óptima (datos reales de la ejecución).

**Qué debo decir:** Este es el plan óptimo de la red de prueba. Restrepo y Puerto Gaitán se llenan, con 32 y 34 toneladas; Villavicencio recibe 26 de 40; Granada recibe 23 de 30. La empresa E10 es la que tiene el precio sombra de oferta más alto, 40.130 pesos por tonelada: es decir, cada tonelada adicional que ofrezca le cuesta a la red 40.130 pesos más, porque sus rutas son las más caras de la matriz de costos de la demostración. Todo esto lo calcula el método exacto en un par de milisegundos.

**Conceptos clave:** Uso de planta · Asignación óptima · Precio sombra de oferta

**Posibles preguntas:**

- **P:** ¿Por qué E10 tiene el costo marginal más alto?
  **R:** Porque en la matriz de costos de demostración sus rutas son las más caras (las distancias de la red de prueba son una fórmula ficticia, no distancias geográficas). Su precio sombra de oferta es de 40.130 COP/t, el mayor de las 10 empresas.

### Diapositiva 27: RESULTADOS: AG

**Qué se muestra:** Gap % del AG según configuración, con 10 semillas (barras reales).

**Qué debo decir:** Para medir al genético no basta una corrida. Ejecutamos 10 semillas por configuración sobre la red de prueba. Con torneo y cruce de un punto el gap promedio fue 0,053 por ciento y el máximo 0,17; con torneo y dos puntos fue el mejor entre los aleatorios, 0,022; con ruleta y dos puntos, 0,087. Con la inicialización heurística, las 10 corridas llegaron al óptimo. Todos los gaps son menores al 0,2 por ciento: en este tamaño el genético es muy bueno, aunque más lento.

**Conceptos clave:** Gap promedio y máximo · Configuración de operadores · Inicialización heurística

**Posibles preguntas:**

- **P:** ¿Por qué dos puntos fue mejor?
  **R:** Con diez semillas y diferencias de centésimas de porcentaje no es concluyente; es una tendencia, no una prueba estadística.

### Diapositiva 28: RESULTADOS: ESCENARIOS

**Qué se muestra:** Tabla de 5 escenarios de sensibilidad: costo exacto, costo AG, gap, tiempos y cambio de base.

**Qué debo decir:** Probamos cinco escenarios. Si el combustible sube 10 por ciento, el costo sube 9 por ciento y el plan no cambia. Con 20 por ciento, el costo sube 18 y el plan sí cambia en cuatro envíos. Si la oferta baja 10 por ciento, el costo baja 10; si sube 15, sube casi 16. Si Granada pierde 30 por ciento de capacidad, el costo sube solo 0,5 por ciento. En todos, el genético quedó a menos de 0,012 por ciento del exacto, y en cuatro de cinco igualó el óptimo.

**Conceptos clave:** Escenario reoptimizado · Cambio de base óptima · Gap por escenario

**Posibles preguntas:**

- **P:** ¿Qué significa que la base cambie?
  **R:** Que la estructura de la solución óptima cambió: otras rutas entran a la solución. Si no cambia, los precios sombra siguen siendo válidos.

### Diapositiva 29: RESULTADOS: ESCALA

**Qué se muestra:** Gap % y relación de tiempos del AG para redes sintéticas crecientes.

**Qué debo decir:** Para la escalabilidad generamos redes sintéticas deterministas de 10 por 4 hasta 80 por 16, o sea 1.280 rutas. El exacto sigue por debajo de 14 milisegundos. El genético con población 40 y 80 generaciones tarda entre 70 y 180 veces más y su gap sube: 0 por ciento en 10 por 4, 3,3 en 20 por 6, 10,9 en 40 por 10 y 6,3 en 80 por 16. La conclusión: a mayor tamaño, el genético se aleja del óptimo con un presupuesto de búsqueda fijo.

**Conceptos clave:** Escalabilidad · Presupuesto de búsqueda · Redes sintéticas (ficticias)

**Posibles preguntas:**

- **P:** ¿El gap 10,9 % se puede bajar?
  **R:** Probablemente con más población o generaciones, pero no lo medimos; lo reportamos tal como salió con la configuración de la prueba (población 40, 80 generaciones, inicialización heurística).

### Diapositiva 30: CONEXIÓN

**Qué se muestra:** Código: vista de la API y servicio que llama al solver (api/views.py, servicios/ejecucion.py).

**Qué debo decir:** Así se conectan las capas. La vista recibe la petición validada, construye los parámetros desde la base de datos, llama al servicio resolver_exacto y, si se pidió guardar, registra la ejecución en el historial. El servicio valida el tamaño del problema, instancia el solver puro y convierte un resultado inválido en un error de negocio con mensaje claro. El gap se calcula con una función simple: la diferencia relativa entre el heurístico y el exacto.

**Conceptos clave:** Vista → servicio → solver · Registro de ejecución · Gap porcentual

**Posibles preguntas:**

- **P:** ¿Qué evita que alguien mande un problema enorme?
  **R:** validar_tamano aplica límites configurables (200 empresas, 50 plantas, 2.000 rutas) y el AG valida su presupuesto de trabajo; si se exceden, la API responde 400.

### Diapositiva 31: DATOS DE ENTRADA

**Qué se muestra:** Código: construir_parametros() (base de datos → ParametrosModelo) con el costo efectivo de cada ruta.

**Qué debo decir:** La entrada del usuario vive en la base de datos. construir_parametros toma solo las empresas, plantas y rutas activas y arma el objeto ParametrosModelo, con el costo efectivo de cada ruta. Este mismo objeto lo consumen los dos métodos. Después de resolver, verificar recalcula las sumas por empresa y por planta y comprueba oferta, capacidad y límites con tolerancia; ese código se mostró en la diapositiva del método exacto.

**Conceptos clave:** ParametrosModelo · Solo elementos activos · Verificación independiente

**Posibles preguntas:**

- **P:** ¿Qué pasa si desactivan una empresa?
  **R:** Deja de entrar al modelo y desaparece del mapa; el siguiente cálculo ya no la considera.

### Diapositiva 32: LA APLICACIÓN

**Qué se muestra:** Capturas reales: mapa de la red y resultado de optimización con los envíos sobre las carreteras.

**Qué debo decir:** Aquí está la aplicación en funcionamiento. A la izquierda, el mapa con las empresas y plantas; a la derecha, el resultado de optimización: un resumen en lenguaje natural, el uso de cada planta y los envíos dibujados sobre las carreteras reales con grosor proporcional a las toneladas. Las capturas son de una sesión de pruebas; las cifras exactas del informe son las de la red de demostración.

**Conceptos clave:** Mapa de flujos · Resumen en lenguaje natural · Datos de demostración

**Posibles preguntas:**

- **P:** ¿De dónde salen las líneas del mapa?
  **R:** De OSRM: la ruta por carretera más corta o rápida sobre OpenStreetMap. No se restringe a vías nacionales y puede diferir de la ruta real de un transportista.

### Diapositiva 33: BENEFICIOS Y LÍMITES

**Qué se muestra:** Dos columnas: beneficios logrados y limitaciones reconocidas.

**Qué debo decir:** Los beneficios: una decisión de distribución óptima y verificable, escenarios en segundos, una interfaz que no exige saber optimización, y una arquitectura que permite ampliar la red. Las limitaciones, con honestidad: los datos son de demostración; el algoritmo genético solo soporta el modo base; no implementamos nodos de paso porque las rutas son directas empresa a planta; la distancia depende del servidor público de OSRM y puede estimarse si no hay internet; y el AG pierde calidad en redes grandes con el presupuesto probado.

**Conceptos clave:** Modo base del AG · Nodos de paso no aplicables · Datos ficticios

**Posibles preguntas:**

- **P:** ¿Por qué no hay nodos de paso?
  **R:** El PDF los pide 'si aplica'; en nuestro modelo cada empresa envía directo a una planta. Está justificado en SUPUESTOS.md y el modelo es extensible.

### Diapositiva 34: CONCLUSIONES

**Qué se muestra:** Cuatro conclusiones respaldadas por los resultados.

**Qué debo decir:** Uno: el problema se modela de forma natural como un LP y el método exacto lo resuelve en milisegundos con garantía de optimalidad. Dos: el algoritmo genético logra soluciones muy cercanas al óptimo en la red de prueba, con gap menor a 0,2 por ciento, pero es más de 200 veces más lento y se degrada al crecer la red. Tres: la sensibilidad, con precios sombra y rangos, da información de negocio que el genético no entrega: dónde invertir capacidad. Cuatro: la arquitectura por capas con pruebas automatizadas permite ampliar y mantener el sistema.

**Conceptos clave:** LP exacto óptimo y rápido · AG cercano pero más lento · Precios sombra

**Posibles preguntas:**

- **P:** ¿Qué aprendieron?
  **R:** Que elegir el método depende del modelo: para un LP, el exacto domina; las metaheurísticas valen cuando el modelo deja de ser lineal.

### Diapositiva 35: TRABAJO FUTURO

**Qué se muestra:** Mejoras propuestas.

**Qué debo decir:** Como trabajo futuro: ampliar el algoritmo genético a los modos de demanda exacta y mínima; incorporar nodos de paso con un modelo de flujo en redes; probar presupuestos mayores de búsqueda del genético y medir su efecto en el gap; alojar un servidor OSRM propio para no depender del servidor público; y sustituir los datos ficticios por datos reales de EcoResiduos del Llano.

**Conceptos clave:** Nodos de paso · OSRM propio · Datos reales

**Posibles preguntas:**

- **P:** ¿Qué sería lo primero?
  **R:** Cargar datos reales de la empresa: es lo que más valor aporta, porque el modelo y las herramientas ya están listos.

### Diapositiva 36: FIN DE LA PRESENTACIÓN

**Qué se muestra:** Cierre y preguntas.

**Qué debo decir:** Eso es OptiAgro-Llanos. Muchas gracias; quedamos atentos a sus preguntas.

**Posibles preguntas:**

- **P:** ¿Se puede ejecutar en otro computador?
  **R:** Sí: con Docker, siguiendo el README: copiar .env.example a .env y ejecutar docker compose up -d --build.

## Preguntas difíciles

- **P:** ¿El algoritmo genético garantiza una solución factible?
  **R:** Sí, por construcción: el decodificador nunca excede oferta, capacidad ni límites; solo puede dejar oferta sin asignar, y eso se penaliza con λ. Si el mejor individuo final deja déficit o `verificar()` falla, el resultado se declara INFEASIBLE.

- **P:** ¿Qué pasa si la oferta total supera la capacidad total?
  **R:** `validar()` rechaza el modelo antes de resolver (estado INVALID_INPUT) y la API responde 400 con el motivo. Hay una prueba automática de capacidad insuficiente.

- **P:** ¿Cómo eligieron los parámetros del AG?
  **R:** Son valores por defecto razonables (población 60, 150 generaciones, cruce 0,8, mutación 0,12, elitismo 2, torneo k = 3), ajustables desde la interfaz. No hicimos una calibración exhaustiva; medimos 10 semillas por configuración y reportamos los resultados tal cual.

- **P:** ¿Por qué el gap del AG no crece de forma regular con el tamaño?
  **R:** Porque cada tamaño es una red distinta y el AG es estocástico con un presupuesto fijo (población 40, 80 generaciones). Con una sola red por tamaño y una semilla no se puede concluir una tendencia; lo reportamos como observación.

- **P:** ¿Los tiempos son comparables?
  **R:** Se midieron con `perf_counter` en el mismo equipo y el mismo contenedor, solo del solver (sin red ni base de datos). El exacto se midió con la mediana de 30 ejecuciones; el AG, con una corrida por configuración (o el promedio de 10 semillas en la tabla de calidad). Son órdenes de magnitud, no microbenchmarks.

- **P:** ¿Por qué el método exacto no necesita variables enteras?
  **R:** Porque el problema de transporte tiene matriz totalmente unimodular: con datos enteros, el vértice óptimo es entero. Si hubiera camiones indivisibles o costos fijos, sí se necesitaría programación entera.

- **P:** ¿Qué es el precio sombra y cuándo deja de valer?
  **R:** Es la derivada del costo óptimo respecto al lado derecho de una restricción (aquí, una tonelada de capacidad). Vale mientras la base óptima no cambie; los rangos de `getRanging` dan ese intervalo (P4: 27–35 t).

- **P:** ¿Las distancias son exactas?
  **R:** Son las que calcula OSRM sobre OpenStreetMap (ruta por carretera más corta o rápida), redondeadas a 0,1 km. No se restringe a vías nacionales y puede diferir de la ruta real de un transportista. Si el servicio falla, se estima en línea recta × 1,3 y se marca «estimada».

- **P:** ¿Los resultados son con datos reales?
  **R:** No: la red de prueba es ficticia (10 empresas, 4 plantas con capacidades de ejemplo). Las plantas están en municipios reales, pero capacidades, ofertas y costos son de demostración, y así está declarado en SUPUESTOS.md.

- **P:** ¿Cómo se prueba que el código funciona?
  **R:** Con 200 pruebas automatizadas del backend (incluye el caso CP-01 con óptimo conocido 64, reproducibilidad del AG por semilla, permisos y sensibilidad) y 73 pruebas del frontend.

- **P:** Si el exacto es mejor, ¿para qué sirve el AG?
  **R:** Para comparar enfoques (requisito del proyecto) y como alternativa cuando el modelo deje de ser lineal. En este problema lineal lo honesto es decir que el exacto gana en tiempo, calidad y garantía.
