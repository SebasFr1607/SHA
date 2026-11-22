# Justificación matemática 

---
## 1. Qué es lo que se está modificando

SHA-1 toma un mensaje, lo parte en bloques de 512 bits y por cada bloque hace dos cosas:

1. **Expansión:** convierte 16 palabras (números de 32 bits) en 80 palabras: $W_0,\dots,W_{79}$.
2. **80 rondas:** con cinco registros $A,B,C,D,E$ calcula en cada ronda
$$TEMP=\big(\mathrm{ROTL}^5(A)+F(B,C,D)+E+W_t+K_t\big)\bmod 2^{32}$$

Solo se tocan **dos piezas**: la fórmula de las palabras $W_{16}$ a $W_{79}$ y la función $F$ de cada grupo de 20 rondas. La fórmula de $TEMP$, los registros, las constantes y las sumas finales no cambian.

---

## 2. Las operaciones, explicadas con bits

Una palabra son 32 bits (ceros y unos). Cada operación trabaja **columna por columna**:

| Operación | Símbolo | Regla (por cada bit) | Idea sencilla |
|---|---|---|---|
| AND | $\wedge$ | 1 solo si **ambos** son 1 | "los dos tienen que estar de acuerdo" |
| OR | $\vee$ | 1 si **alguno** es 1 | "con que uno baste" |
| XOR | $\oplus$ | 1 si son **distintos** | "detecta diferencias" |
| NOT | $\neg$ | invierte el bit | "al revés" |
| ROTL$^n$ | | mueve los bits $n$ lugares a la izquierda; los que salen entran por la derecha | "girar la fila de bits" |

**Nota sobre Python:** el NOT de Python da números negativos. Por eso cada NOT se escribe `(~x) & 0xFFFFFFFF`, que lo deja en 32 bits.

### El campo GF(2): por qué XOR es "lineal" y AND no

$GF(2)$ es el mundo donde solo existen 0 y 1, y donde la suma es XOR y la multiplicación es AND:

$$0+0=0,\quad 0+1=1,\quad 1+1=0 \qquad\text{(suma = XOR)}$$
$$0\cdot0=0,\quad 0\cdot1=0,\quad 1\cdot1=1 \qquad\text{(producto = AND)}$$

Con esto, cualquier función de bits se escribe como un polinomio. Por ejemplo $B\oplus C\oplus D$ es $B+C+D$.

- **Lineal:** solo hay sumas de variables sueltas ($B+C+D$). Cada bit de entrada influye por su cuenta, sin "interactuar" con los demás. Esto se puede resolver como un sistema de ecuaciones.
- **No lineal:** aparecen **productos** como $BC$ o $CD$. Ahora el resultado depende de **combinaciones** de bits.

AND es un producto ($BC$), así que introduce no linealidad. OR también: $B\vee C=B\oplus C\oplus BC$, lleva el producto escondido. NOT es solo "sumar 1", y rotar solo reordena columnas, así que ni NOT ni ROTL agregan no linealidad por sí solos.

---

## 3. La expansión de palabras (W16 a W79)

### 3.1. Las dos fórmulas

Sea $X=W_{t-3}\oplus W_{t-8}\oplus W_{t-14}\oplus W_{t-16}$.

- **SHA-1 original:** $W_t=\mathrm{ROTL}^1(X)$
- **Primera versión (con problemas):** $W_t=\mathrm{ROTL}^1(X\wedge W_{t-1})$
- **Versión final:** $\boxed{W_t=\mathrm{ROTL}^1(X)\oplus(W_{t-1}\wedge W_{t-2})}$

### 3.2. Qué significa cada variable

| Símbolo | Qué es |
|---|---|
| $t$ | posición de la palabra que se está calculando (de 16 a 79) |
| $W_{t-3},W_{t-8},W_{t-14},W_{t-16}$ | cuatro palabras anteriores que la expansión original mezcla |
| $X$ | el XOR de esas cuatro: la mezcla original |
| $\mathrm{ROTL}^1(X)$ | $X$ girado un bit |
| $W_{t-1},W_{t-2}$ | las dos palabras inmediatamente anteriores |
| $W_{t-1}\wedge W_{t-2}$ | 1 solo donde las dos tienen 1: **el término nuevo** |

### 3.3. Por qué la primera versión fallaba

Pensemos el AND como una **rejilla**: $X\wedge W_{t-1}$ deja pasar un bit de $X$ solo donde $W_{t-1}$ tiene 1. Si los bits son aleatorios (la mitad unos), tras el AND queda la **mitad de los unos** que tenía $W_{t-1}$:

$$\text{densidad}(W_t)\approx\tfrac12\cdot\text{densidad}(W_{t-1})$$

Cada palabra tiene la mitad de unos que la anterior: 0.5, 0.25, 0.125, 0.06… hasta quedarse en ceros. Peor aún, si $W_{t-1}=0$ entonces $W_t=0$, y también la siguiente, y así **para siempre** (el cero "contagia").

Medido con el programa (20 000 bloques aleatorios): solo ≈ 4.35 palabras no nulas de las 64; con mensaje vacío, 0 de 64. Además se **perdía información**: donde $W_{t-1}$ tenía 0, el contenido de $X$ se borraba.

### 3.4. Por qué la versión final funciona

Aquí el AND ya no es una rejilla, sino un **ingrediente que se suma** (por XOR):

1. **La mezcla original queda completa.** $\mathrm{ROTL}^1(X)$ sigue ahí sin filtrar.
2. **El cero no se contagia.** Si $W_{t-1}=0$, el término extra vale 0 y queda $W_t=\mathrm{ROTL}^1(X)$, que sigue teniendo información.
3. **La densidad no cae.** XOR con un término independiente mantiene la mitad de unos (idea: $u\oplus v$ es uniforme si $u$ lo es). Medido: densidad ≈ 0.50 en todas las posiciones, y **0 palabras nulas de 320 000** en bloques aleatorios.
4. **No se pierde información.** La recurrencia se puede revertir: despejando,
$$W_{t-16}=\mathrm{ROTL}^{31}\big(W_t\oplus(W_{t-1}\wedge W_{t-2})\big)\oplus W_{t-3}\oplus W_{t-8}\oplus W_{t-14}.$$
Se comprobó en 5 000 casos aleatorios.

**¿Por qué XOR y no OR u otra compuerta?**

| Para combinar | Resultado |
|---|---|
| AND (versión anterior) | filtra, vacía de unos, cero contagia |
| OR | tiende a llenar de unos |
| **XOR** | mantiene el equilibrio y no pierde información |

### 3.5. Qué cambia matemáticamente

- Antes la expansión era **lineal** en $GF(2)$ (solo XOR y giros). Ahora tiene un término de **grado 2** ($W_{t-1}\cdot W_{t-2}$): es no lineal.
- Cada palabra depende de **6** palabras anteriores en vez de 4: $t-1,t-2,t-3,t-8,t-14,t-16$.
- Como cada $W_t$ se usa para calcular las siguientes, el término AND se propaga: un cambio en una palabra afecta a más palabras posteriores.

### 3.6. Ejemplo real con "Hola mundo" (bloque 1)

Para $t=16$: $W_{13}=0$, $W_8=0$, $W_2=\texttt{646F8000}$, $W_0=\texttt{486F6C61}$.

| Paso | Valor |
|---|---|
| $X=W_{13}\oplus W_8\oplus W_2\oplus W_0$ | `2C00EC61` |
| $\mathrm{ROTL}^1(X)$ | `5801D8C2` |
| $W_{15}\wedge W_{14}$ (ver nota) | `00000000` |
| $W_{16}=\mathrm{ROTL}^1(X)\oplus\text{AND}$ | **`5801D8C2`** |

Nota: aquí $W_{14}=0$, así que el AND da 0 y $W_{16}$ es igual a la expansión original. Con la **primera versión** habría salido `00000080` (casi vacío). En cambio, para $t=17$: $\mathrm{ROTL}^1(X)=\texttt{40DAEADC}$ y $W_{16}\wedge W_{15}=\texttt{00000040}$, por lo que $W_{17}=\texttt{40DAEA9C}$: el AND sí modifica el resultado, sin borrar nada.

---

## 4. Las cuatro funciones booleanas

### 4.1. Idea general

$F$ recibe tres registros $B,C,D$ y mezcla sus bits columna por columna. Cada grupo de 20 rondas usa una distinta. En las cuatro se hizo lo mismo: **función original $\oplus$ un término no lineal (AND u OR)**.

### 4.2. Cómo se comprobó que cada una está bien

Como $F$ actúa columna por columna, basta estudiarla con 3 bits ($2^3=8$ combinaciones). Se revisó:

1. **Tabla de verdad** (las 8 combinaciones).
2. **Dependencia:** que cambie al voltear $B$, o $C$, o $D$ (si no, la variable "sobra").
3. **Simplificación (ANF):** el polinomio en $GF(2)$, para ver si la fórmula se reduce a algo trivial.
4. **No linealidad:** qué tan lejos está la función de una lineal (máximo posible con 3 variables: 2).
5. **Balance:** cuántos unos da de 8 (lo ideal es 4: sin preferencia por 0 o 1).
6. **Que no sea igual** a otra de las cuatro ni a su complemento.

### 4.3. Fórmulas y resultados

| Función | Fórmula definitiva | Forma simplificada (ANF) | Unos de 8 | No linealidad |
|---|---|---|---|---|
| $F_1'$ (rondas 0–19) | $[(B\wedge C)\vee(\neg B\wedge D)]\oplus(B\vee C)$ | $B\oplus C\oplus D\oplus BD$ | 4 | 2 |
| $F_2'$ (rondas 20–39) | $(B\oplus C\oplus D)\oplus(C\wedge D)$ | $B\oplus C\oplus D\oplus CD$ | 4 | 2 |
| $F_3'$ (rondas 40–59) | $[(B\wedge C)\vee(B\wedge D)\vee(C\wedge D)]\oplus(B\vee\neg C)$ | $1\oplus C\oplus CD\oplus BD$ | 4 | 2 |
| $F_4'$ (rondas 60–79) | $(B\oplus C\oplus D)\oplus(B\wedge C)$ | $B\oplus C\oplus D\oplus BC$ | 4 | 2 |

Tablas de verdad (orden $BCD=000,001,\dots,111$):

| B C D | $F_1'$ | $F_2'$ | $F_3'$ | $F_4'$ |
|---|---|---|---|---|
| 0 0 0 | 0 | 0 | 1 | 0 |
| 0 0 1 | 1 | 1 | 1 | 1 |
| 0 1 0 | 1 | 1 | 0 | 1 |
| 0 1 1 | 0 | 1 | 1 | 0 |
| 1 0 0 | 1 | 1 | 1 | 1 |
| 1 0 1 | 1 | 0 | 0 | 0 |
| 1 1 0 | 0 | 0 | 0 | 1 |
| 1 1 1 | 0 | 0 | 0 | 0 |

Las cuatro dependen de $B$, $C$ y $D$, están balanceadas (4 unos y 4 ceros), tienen no linealidad 2 y ninguna es igual a otra ni a su complemento.

### 4.4. Qué hace cada una (función original → término extra)

**$F_1$: Choose.** Original: "si $B$ es 1 elige $C$, si no elige $D$", es decir $(B\wedge C)\vee(\neg B\wedge D)$.
Término extra: $\oplus(B\vee C)$. Cambia el resultado en las columnas donde $B$ o $C$ valen 1. Su forma simplificada, $B\oplus C\oplus D\oplus BD$, es suma de las tres variables más **un** producto ($BD$): ese producto es la no linealidad.

**$F_2$: Paridad.** Original: $B\oplus C\oplus D$, que es **lineal** (no hay ningún producto).
Término extra: $\oplus(C\wedge D)$. Voltea la salida cuando $C$ y $D$ valen 1 a la vez. Ahora aparece el producto $CD$: la función dejó de ser lineal.

**$F_3$: Mayoría.** Original: da el valor que más se repite entre $B,C,D$.
Término extra: $\oplus(B\vee\neg C)$. Voltea la salida cuando $B$ es 1 o $C$ es 0. El resultado sigue dependiendo de las tres variables y queda balanceado.

**$F_4$: Paridad.** Original: $B\oplus C\oplus D$ (lineal).
Término extra: $\oplus(B\wedge C)$. Voltea la salida cuando $B$ y $C$ valen 1 a la vez. Aparece el producto $BC$.

### 4.5. Dos candidatas se corrigieron

Al comprobar las fórmulas propuestas inicialmente, se detectaron dos problemas:

| Candidata original | Problema | Corrección |
|---|---|---|
| $F_2'=(B\oplus C\oplus D)\oplus(B\wedge D)$ | Daba **la misma tabla** (`01101100`) que $F_1'$: dos bloques usarían la misma función | Se cambió a $\oplus(C\wedge D)$ |
| $F_3'=\text{Maj}\oplus[(B\vee C)\wedge\neg D]$ | No linealidad 1 (casi lineal) y 5 unos de 8 (sesgada) | Se cambió a $\oplus(B\vee\neg C)$ |

En ambas se conservó la función base y la idea (término AND/OR combinado por XOR).

---

## 5. Efecto sobre las 80 rondas

Cada ronda hace:

$$TEMP=\mathrm{ROTL}^5(A)+F(B,C,D)+E+W_t+K_t,\qquad (A,B,C,D,E)\leftarrow(TEMP,\;A,\;\mathrm{ROTL}^{30}(B),\;C,\;D)$$

- **Qué entra de $F$ y de $W$:** $F$ aporta una mezcla no lineal de $B,C,D$; $W_t$ aporta información del mensaje. Ambas se suman a $TEMP$.
- **La suma módulo $2^{32}$** es la parte que "arrastra" acarreos de una columna a la siguiente; no se modificó.
- **Los registros se desplazan** ($A\to B\to C\to D\to E$), así que lo que calcula $F$ en una ronda llega, rondas después, a todos los registros.
- **El cambio total** es que ahora $F$ es no lineal en los cuatro bloques (antes $F_2$ y $F_4$ eran lineales) y $W_t$ tiene un término no lineal.

---

## 6. Cuatro conceptos que no son lo mismo

| Concepto | Significa | En este proyecto |
|---|---|---|
| **No linealidad** | Aparecen productos de bits (no solo sumas) | Los términos $BD,CD,BC$ y el AND de la expansión |
| **Balance** | Da 1 en la mitad exacta de las combinaciones | Las cuatro $F'$ dan 4 de 8 |
| **Pérdida de información** | Dos entradas distintas dan la misma salida | Un AND aislado sí pierde; la primera expansión también |
| **Seguridad criptográfica** | Resistencia comprobada a ataques | **No evaluada** |

**Importante:** que $F$ sea no lineal y pierda información por sí sola **no hace irreversible** la ronda. Dado el estado nuevo, $A$, $B$, $C$ y $D$ anteriores se recuperan directamente (porque los registros solo se desplazan y rotan):
$$E=TEMP-\mathrm{ROTL}^5(A)-F(B,C,D)-W_t-K_t \pmod{2^{32}}.$$
Cada ronda es reversible sin importar qué $F$ se use. Lo que hace irreversible al bloque completo es la suma final con los valores iniciales, igual que en SHA-1 estándar.

---

## 7. Comparación con SHA-1 estándar

| Aspecto | SHA-1 estándar | SHA-1 Personalizado |
|---|---|---|
| Expansión | $\mathrm{ROTL}^1(X)$ | $\mathrm{ROTL}^1(X)\oplus(W_{t-1}\wedge W_{t-2})$ |
| Linealidad de la expansión | Lineal | No lineal |
| Palabras previas usadas | 4 | 6 |
| $F_2$ y $F_4$ | Lineales | No lineales |
| Rondas | 4 × 20 | 4 × 20 |
| Constantes, registros, suma de $TEMP$ | Estándar | Iguales |
| Resultado | 160 bits | 160 bits (40 hex) |

---
