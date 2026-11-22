# Justificación matemática — SHA-1 Personalizado (versión corregida)

> **Estado:** variante experimental con fines académicos. **No es SHA-1 estándar** y no se afirma que mejore su seguridad. Los datos numéricos de este documento provienen de ejecuciones reales de `SHA1_Personalizado.py` y de las comprobaciones de tablas de verdad realizadas con un script auxiliar (no se usó ninguna biblioteca para calcular hashes).

---

## 1. Expansión de palabras W16–W79

### 1.1. Fórmula original y fórmula implementada

$$\text{Original:}\quad W_t=\mathrm{ROTL}^1(X),\qquad X=W_{t-3}\oplus W_{t-8}\oplus W_{t-14}\oplus W_{t-16}$$

$$\boxed{\text{Implementada:}\quad W_t=\mathrm{ROTL}^1(X)\;\oplus\;(W_{t-1}\wedge W_{t-2}),\qquad 16\le t\le 79}$$

Orden de cálculo en el código: (1) $X$; (2) $\mathrm{ROTL}^1(X)$; (3) $W_{t-1}\wedge W_{t-2}$; (4) XOR de ambos, enmascarado con `MASCARA_32`.

### 1.2. Qué problema provocaba el AND aplicado como filtro

La versión anterior usaba $W_t=\mathrm{ROTL}^1(X\wedge W_{t-1})$. En cada posición de bit $j$:

$$w_{t,j}=x_{j}\cdot w_{t-1,j}\;(\text{tras rotar}).$$

Si $x$ y $w_{t-1}$ fueran bits uniformes independientes, $P(w_{t,j}=1)=\tfrac12\cdot\delta_{t-1}$, donde $\delta_{t-1}$ es la densidad de unos de $W_{t-1}$. Por tanto $\delta_t\approx\tfrac12\delta_{t-1}$: **decaimiento geométrico**. Además, si $W_{t-1}=0$ entonces $W_t=0$, y por inducción todas las palabras posteriores son 0 (**el cero es absorbente**).

Medición real de aquella versión (20 000 bloques aleatorios): ≈ 4.35 palabras no nulas de las 64 (W16–W79); con mensaje vacío, 0 de 64.

Hay además una pérdida de información explícita: en las posiciones donde $W_{t-1}$ vale 0, el valor de $X$ se destruye, y la recurrencia ya no se puede revertir.

### 1.3. Por qué la fórmula corregida evita el colapso

Se conserva íntegra la contribución lineal de SHA-1 ($\mathrm{ROTL}^1(X)$) y el AND entra como **término aditivo**:

- **No hay filtrado.** El término $W_{t-1}\wedge W_{t-2}$ se suma por XOR; no multiplica a $X$. Si $W_{t-1}=0$ o $W_{t-2}=0$, el término adicional vale 0 y queda $W_t=\mathrm{ROTL}^1(X)$, que sigue llevando información.
- **El cero no es absorbente.** Para que $W_t=0$ se necesita $\mathrm{ROTL}^1(X)=W_{t-1}\wedge W_{t-2}$, una coincidencia que depende de cuatro palabras previas, no de una sola.
- **Densidad estable.** Si $\mathrm{ROTL}^1(X)$ es uniforme e independiente del término AND, su XOR también es uniforme, con independencia de la densidad del AND ($u\oplus v$ es uniforme si $u$ lo es). Esto es un argumento heurístico; se contrasta con la medición.
- **La recurrencia es reversible.** Se puede despejar $W_{t-16}$:
$$W_{t-16}=\mathrm{ROTL}^{31}\big(W_t\oplus(W_{t-1}\wedge W_{t-2})\big)\oplus W_{t-3}\oplus W_{t-8}\oplus W_{t-14}.$$
La ventana $(W_{t-16},\dots,W_{t-1})\mapsto(W_{t-15},\dots,W_t)$ es una biyección. Se verificó con 5 000 casos aleatorios (recuperación exacta de $W_{t-16}$).

### 1.4. Por qué combinar con XOR y no con otra compuerta

| Combinación | Comportamiento |
|---|---|
| `AND` (anterior) | Filtra, reduce densidad, cero absorbente, no reversible |
| `OR` | Sesga hacia 1 (densidad $\to$ 1 en cascada) |
| `XOR` | Preserva la densidad uniforme y la reversibilidad; añade un monomio de grado 2 |

### 1.5. Resultados medidos (5 000 bloques aleatorios)

| Medida | Anterior | Corregida |
|---|---|---|
| Densidad de unos en W16, W17, W20, W32, W48, W79 | 0.25, 0.13, 0.016, ≈0, 0, 0 | 0.499, 0.500, 0.500, 0.500, 0.500, 0.500 |
| Palabras nulas en W16–W79 | 100 % de los bloques con colapso | 0 de 320 000 |

Casos especiales: cadena vacía → 52 de 64 palabras no nulas (los ceros son legítimos: solo hay un bit significativo de partida y el relleno), sin colapso en cascada; mensajes con entrada densa → 64/64.

> La variante es experimental. Que la densidad se mantenga en 0.5 no demuestra seguridad.

---

## 2. Las cuatro funciones booleanas

### 2.1. Funciones base (conservadas de tu código)

$$F_1=(B\wedge C)\vee(\neg B\wedge D),\quad F_2=B\oplus C\oplus D,\quad F_3=(B\wedge C)\vee(B\wedge D)\vee(C\wedge D),\quad F_4=B\oplus C\oplus D$$

Las fórmulas base de F2 y F4 **coinciden ahora con las del código original** (en la versión anterior se habían sustituido por otras).

### 2.2. Comprobaciones de las candidatas propuestas

Se aplicaron los siete controles pedidos: tabla de verdad, dependencia de B, C y D, simplificación algebraica (ANF), no linealidad, conteo de unos y ceros, sesgo, equivalencia con funciones más simples.

| Candidata | Tabla (BCD=000…111) | Unos | Depende de | ANF | No linealidad | Veredicto |
|---|---|---|---|---|---|---|
| $F_1'=\text{Choose}\oplus(B\vee C)$ | 01101100 | 4 | B, C, D | $B\oplus C\oplus D\oplus BD$ | 2 | Correcta, **pero idéntica a la candidata de F2** |
| $F_2'=(B\oplus C\oplus D)\oplus(B\wedge D)$ | 01101100 | 4 | B, C, D | $B\oplus C\oplus D\oplus BD$ | 2 | **Duplica a F1'** |
| $F_3'=\text{Maj}\oplus[(B\vee C)\wedge\neg D]$ | 00111101 | 5 | B, C, D | $B\oplus C\oplus BCD$ | **1** | **Casi afín** (a distancia 1 de $B\oplus C$) y sesgada |
| $F_4'=(B\oplus C\oplus D)\oplus(B\wedge C)$ | 01101010 | 4 | B, C, D | $B\oplus C\oplus D\oplus BC$ | 2 | Correcta |

(Nota: no linealidad = distancia de Hamming mínima a una función afín; el máximo posible para 3 variables es 2.)

**Problemas detectados:**

1. $F_1'$ y $F_2'$ candidatas son **la misma función**, de modo que dos de los cuatro bloques usarían exactamente la misma tabla.
2. $F_3'$ candidata tiene no linealidad 1 (la más baja posible sin ser afín) y 5 de 8 unos.

### 2.3. Alternativas adoptadas y justificación

Para F1 se probó la modificación `Choose ⊕ (x ∨ y)` con los tres pares posibles: solo $B\vee C$ da una función balanceada que depende de las tres variables (los otros dos pares dan 2 unos de 8); por eso **F1' se mantiene**. Para F2 existen tres modificaciones con AND, todas con 4 unos y no linealidad 2, y se eligió la que evita el duplicado. Para F3 se buscaron términos con OR/AND (con literales negados) que den función balanceada, no linealidad 2, dependiente de B, C y D, y distinta de las otras tres y de sus complementos.

| Función | Fórmula definitiva | Cambio |
|---|---|---|
| $F_1'$ | $\big[(B\wedge C)\vee(\neg B\wedge D)\big]\oplus(B\vee C)$ | Sin cambio |
| $F_2'$ | $(B\oplus C\oplus D)\oplus(C\wedge D)$ | AND con $C\wedge D$ en lugar de $B\wedge D$ (evita duplicar F1') |
| $F_3'$ | $\big[(B\wedge C)\vee(B\wedge D)\vee(C\wedge D)\big]\oplus\big(B\vee\neg C\big)$ | OR con $B\vee\neg C$ en lugar de $(B\vee C)\wedge\neg D$ (mejora no linealidad y balance) |
| $F_4'$ | $(B\oplus C\oplus D)\oplus(B\wedge C)$ | Sin cambio |

### 2.4. Tablas de verdad definitivas

| B C D | $F_1$ | $F_2$ | $F_3$ | $F_4$ | $F_1'$ | $F_2'$ | $F_3'$ | $F_4'$ |
|---|---|---|---|---|---|---|---|---|
| 0 0 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 0 0 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |
| 0 1 0 | 0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 |
| 0 1 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 0 |
| 1 0 0 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |
| 1 0 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 |
| 1 1 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| 1 1 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |

### 2.5. Resultado de las comprobaciones de las funciones definitivas

| Función | Unos / ceros | Depende de B, C, D | ANF | Grado | No linealidad |
|---|---|---|---|---|---|
| $F_1'$ | 4 / 4 | Sí | $B\oplus C\oplus D\oplus BD$ | 2 | 2 |
| $F_2'$ | 4 / 4 | Sí | $B\oplus C\oplus D\oplus CD$ | 2 | 2 |
| $F_3'$ | 4 / 4 | Sí | $1\oplus C\oplus CD\oplus BD$ | 2 | 2 |
| $F_4'$ | 4 / 4 | Sí | $B\oplus C\oplus D\oplus BC$ | 2 | 2 |

- **Dependencia:** cada función cambia de valor al invertir cualquiera de B, C o D en alguna fila; ninguna se simplifica a una expresión que ignore una variable.
- **Incorporan no linealidad:** las cuatro tienen un monomio de grado 2 (no linealidad 2, el máximo para 3 variables).
- **Balance:** todas tienen 4 unos de 8, sin sesgo de salida con entradas uniformes. Un efecto lateral: $F_2$ y $F_4$ base eran lineales (grado 1, no linealidad 0) y ahora ya no lo son.
- **Distintas entre sí:** ningún par es idéntico ni complementario.
- **Observación:** $F_1'$ se simplifica a $B\oplus C\oplus D\oplus BD$: es una función de paridad más un solo término cuadrático. Sigue cumpliendo los criterios, pero conviene saberlo.
- **Verificación en el código:** se evaluó `funcion_f()` bit a bit en las rondas 0, 19, 20, 39, 40, 59, 60 y 79 y la tabla coincide con la de arriba; además, 20 000 tripletas aleatorias de 32 bits coinciden con una implementación independiente.

---

## 3. Conceptos que no deben confundirse

| Concepto | Definición | Dónde se aplica aquí |
|---|---|---|
| **No linealidad booleana** | Distancia a la función afín más cercana; ausencia de grado 1 en la ANF | Presencia de monomios $BD$, $CD$, $BC$ en F1'–F4' y del AND en la expansión |
| **Equilibrio (balance)** | Una función de $n$ variables está balanceada si da 1 en exactamente $2^{n-1}$ entradas | Las cuatro F' dan 4 de 8 |
| **Pérdida de información / no invertibilidad** | La función no es inyectiva: dos entradas distintas dan la misma salida | Un AND aislado no es inyectivo; el filtro $X\wedge W_{t-1}$ propagaba esa pérdida |
| **Seguridad criptográfica** | Resistencia demostrable o contrastada a ataques de colisión, preimagen, diferenciales, etc. | **No evaluada ni afirmada** |

Que un AND u OR sea no lineal y no inyectivo **no implica** que la construcción completa sea irreversible. En las rondas:

$$(A,B,C,D,E)\mapsto(TEMP,\;A,\;\mathrm{ROTL}^{30}(B),\;C,\;D)$$

dado el nuevo estado y los valores de $W_t$ y $K_t$, el estado anterior se recupera así: $A=B_{\text{nuevo}}$, $B=\mathrm{ROTL}^{2}(C_{\text{nuevo}})$, $C=D_{\text{nuevo}}$, $D=E_{\text{nuevo}}$, y
$$E=TEMP-\mathrm{ROTL}^5(A)-F(B,C,D)-W_t-K_t \pmod{2^{32}}.$$
Es decir, **cada ronda es una biyección del estado de 160 bits sin importar qué $F$ se use**, porque $B,C,D$ se recuperan antes de evaluar $F$. Por lo tanto, que $F$ sea no lineal y no inyectiva no hace irreversible la ronda. La función de compresión global sí pierde información, pero por la suma final $H+\text{estado}$ (y por el relleno/longitud), igual que SHA-1 estándar. Del mismo modo, la expansión corregida es reversible (sección 1.3).

---

## 4. Diferencias respecto a SHA-1 estándar

| Aspecto | SHA-1 estándar | SHA-1 Personalizado (corregido) |
|---|---|---|
| Expansión | $\mathrm{ROTL}^1(W_{t-3}\oplus W_{t-8}\oplus W_{t-14}\oplus W_{t-16})$ | $\mathrm{ROTL}^1(X)\oplus(W_{t-1}\wedge W_{t-2})$ |
| Palabras previas de las que depende $W_t$ | 4 | 6 ($t-1,t-2,t-3,t-8,t-14,t-16$) |
| Linealidad de la expansión | Lineal sobre GF(2) | No lineal (término de grado 2) |
| F1 / F2 / F3 / F4 | Ch, Parity, Maj, Parity | F1'–F4' (sección 2.3) |
| Linealidad de F2 y F4 | Lineales (grado 1) | No lineales (grado 2) |
| Rondas | 4 × 20 | 4 × 20 |
| Constantes, valores iniciales, actualización de registros | Estándar | Iguales |
| Resultado | 160 bits | 160 bits (40 hex) |

---

## 5. Limitaciones criptográficas

- No se realizaron análisis diferencial, lineal, de colisiones ni de preimágenes. Sin ellos **no se puede afirmar** que la variante sea más segura, ni que sea más débil que SHA-1.
- Más operaciones por palabra o por ronda no equivalen a más seguridad. Añadir términos puede introducir debilidades (como el colapso de la versión anterior o la dependencia perdida de $C$ en la primera versión de $F_3'$).
- Un solo experimento de avalancha (cambio de un carácter, 50 pares de mensajes) dio una diferencia media de 80.26 de 160 bits (≈ 50 %). Es una medida descriptiva; no sustituye un análisis criptográfico.
- SHA-1 estándar está roto en resistencia a colisiones; esta variante tampoco debe usarse en aplicaciones reales.
- Las propiedades booleanas estudiadas (balance, no linealidad 2 en 3 variables) son locales a cada función $F_i$; la seguridad de una construcción iterada depende de cómo interactúan 80 rondas, la expansión y la suma final.