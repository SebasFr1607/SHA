import os
import sys


def rellenar_mensaje(mensaje: str) -> bytes:
    datos = mensaje.encode("utf-8")
    longitud_bits = len(datos) * 8
    datos += b"\x80"

    while len(datos) % 64 != 56:
        datos += b"\x00"

    datos += longitud_bits.to_bytes(8, byteorder="big")

    return datos


def dividir_en_bloques(datos_rellenos: bytes) -> list[bytes]:
    return [datos_rellenos[i:i + 64] for i in range(0, len(datos_rellenos), 64)]


def bloque_a_palabras(bloque: bytes) -> list[int]:
    return [
        int.from_bytes(bloque[i:i + 4], byteorder="big")
        for i in range(0, 64, 4)
    ]


def construir_bloques(mensaje: str) -> list[list[int]]:
    datos = rellenar_mensaje(mensaje)
    bloques = dividir_en_bloques(datos)
    return [bloque_a_palabras(b) for b in bloques]



MASCARA_32 = 0xFFFFFFFF


def rotar_izquierda(valor: int, n: int) -> int:
    return ((valor << n) | (valor >> (32 - n))) & MASCARA_32


def expandir_palabras(w16: list[int]) -> list[int]:
    w = list(w16)

    for t in range(16, 80):
        x = w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16]
        rot = rotar_izquierda(x, 1)
        and_extra = w[t - 1] & w[t - 2]
        w.append((rot ^ and_extra) & MASCARA_32)

    return w


def expandir_bloques(mensaje: str) -> list[list[int]]:
    return [expandir_palabras(w16) for w16 in construir_bloques(mensaje)]


H_INICIAL = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]

K = [0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6]

NOMBRES_F = [
    "Choose personalizada (F1')",
    "Paridad personalizada (F2')",
    "Mayoría personalizada (F3')",
    "Paridad personalizada (F4')",
]

FORMULAS_F = [
    "((B AND C) OR ((NOT B) AND D)) XOR (B OR C)",
    "(B XOR C XOR D) XOR (C AND D)",
    "((B AND C) OR (B AND D) OR (C AND D)) XOR (B OR (NOT C))",
    "(B XOR C XOR D) XOR (B AND C)",
]


def funcion_f(t: int, b: int, c: int, d: int) -> int:
    if t < 20:
        base = (b & c) | (((~b) & MASCARA_32) & d)
        return (base ^ (b | c)) & MASCARA_32
    elif t < 40:
        base = b ^ c ^ d
        return (base ^ (c & d)) & MASCARA_32
    elif t < 60:
        base = (b & c) | (b & d) | (c & d)
        return (base ^ (b | ((~c) & MASCARA_32))) & MASCARA_32
    else:
        base = b ^ c ^ d
        return (base ^ (b & c)) & MASCARA_32


def constante_k(t: int) -> int:
    return K[t // 20]


def ronda(t: int, a: int, b: int, c: int, d: int, e: int, wt: int):
    temp = (rotar_izquierda(a, 5) + funcion_f(t, b, c, d) + e + wt + constante_k(t)) & MASCARA_32
    return temp, a, rotar_izquierda(b, 30), c, d


def ejecutar_bloques_de_rondas(w80: list[int], h: list[int]) -> list[dict]:
    a, b, c, d, e = h
    bloques_rondas = []

    for n in range(4):
        t_inicio = n * 20
        t_fin = t_inicio + 19
        entrada = (a, b, c, d, e)
        estados = []

        for t in range(t_inicio, t_fin + 1):
            a, b, c, d, e = ronda(t, a, b, c, d, e, w80[t])
            estados.append((a, b, c, d, e))

        bloques_rondas.append({
            "numero": n + 1,
            "t_inicio": t_inicio,
            "t_fin": t_fin,
            "regla": NOMBRES_F[n],
            "formula": FORMULAS_F[n],
            "k": K[n],
            "temp_primera": estados[0][0],
            "entrada": entrada,
            "estados": estados,
        })

    return bloques_rondas


def estados_planos(bloques_rondas: list[dict]) -> list[tuple]:
    return [estado for br in bloques_rondas for estado in br["estados"]]


def texto_abcde(estado: tuple) -> str:
    return " ".join(f"{nombre}={valor:08X}" for nombre, valor in zip("ABCDE", estado))


def texto_h(h: list[int]) -> str:
    return " ".join(f"H{i}={valor:08X}" for i, valor in enumerate(h))


def sumar_h(h: list[int], estado_final: tuple) -> list[int]:
    return [(x + y) & MASCARA_32 for x, y in zip(h, estado_final)]


def sumar_con_llevadas(x: int, y: int) -> dict:
    digitos_x = f"{x:08X}"
    digitos_y = f"{y:08X}"
    llevada = 0
    columnas = []

    for i in range(7, -1, -1):
        dx = int(digitos_x[i], 16)
        dy = int(digitos_y[i], 16)
        suma = dx + dy + llevada
        columnas.append({
            "x": dx,
            "y": dy,
            "suma": suma,
            "digito": suma % 16,
            "llevada": suma // 16,
        })
        llevada = suma // 16

    columnas.reverse()
    resultado = int("".join(f"{c['digito']:X}" for c in columnas), 16)

    return {"columnas": columnas, "desbordo": llevada, "resultado": resultado}


def procesar_bloque(w80: list[int], h: list[int]) -> list[int]:
    bloques_rondas = ejecutar_bloques_de_rondas(w80, h)
    estado_final = estados_planos(bloques_rondas)[-1]
    return sumar_h(h, estado_final)


def h_a_hex(h: list[int]) -> str:
    return "".join(f"{x:08x}" for x in h)


def calcular_sha1(mensaje: str) -> str:
    h = H_INICIAL[:]

    for w80 in expandir_bloques(mensaje):
        h = procesar_bloque(w80, h)

    return h_a_hex(h)


MENU = """
==============================================
        SHA-1 PERSONALIZADO  (por bloques)
   Variante experimental, NO es el SHA-1 estándar
==============================================
  1. Calcular el SHA-1 Personalizado de un mensaje
  2. Ver las palabras W0 a W79 (primero 16, luego hasta 80)
  3. Ver los 4 bloques de rondas (información completa)
  4. Ver la suma final y la concatenación
  5. Ver el proceso completo paso a paso
  6. Salir
"""


def pausa() -> None:
    input("\n  [Enter para continuar] ")


def mostrar_palabras_en_dos_partes(w80: list[int]) -> None:
    print("\n  PARTE 1: Las 16 palabras del bloque (W0 a W15)")
    for t in range(0, 16):
        print(f"  W{t:<2} = 0x{w80[t]:08X}   {w80[t]:032b}")

    print("\n  PARTE 2: Continuación hasta completar las 80 palabras (W16 a W79)")
    for t in range(16, 80):
        print(f"  W{t:<2} = 0x{w80[t]:08X}   {w80[t]:032b}")


def mostrar_tabla_rondas(w80: list[int], bloques_rondas: list[dict], t_desde: int, t_hasta: int, h_partida: list[int]) -> None:
    estados = estados_planos(bloques_rondas)

    print("\n  TEMP = ROTL5(A) + F(B,C,D) + E + Wt + Kt   (módulo 2^32)")
    print("  F(t) = función booleana personalizada del bloque (ver fórmula en cada encabezado)")
    print("  A = TEMP ; B = A anterior ; C = ROTL30(B anterior) ; D = C anterior ; E = D anterior\n")
    print(" t |    Wt    |   F(t)   | ROTL5(A) | TEMP = A |    B     |    C     |    D     |    E")

    for t in range(t_desde, t_hasta + 1):
        br = bloques_rondas[t // 20]

        if t % 20 == 0 or t == t_desde:
            continuacion = "" if t % 20 == 0 else "  (continuación)"
            print(f"--- BLOQUE {br['numero']} (rondas {br['t_inicio']}-{br['t_fin']}) | "
                  f"F: {br['regla']} | K = 0x{br['k']:08X}{continuacion} ---")
            print(f"    F(B,C,D) = {br['formula']}")

        anterior = tuple(h_partida) if t == 0 else estados[t - 1]
        f = funcion_f(t, anterior[1], anterior[2], anterior[3])
        a5 = rotar_izquierda(anterior[0], 5)
        a, b, c, d, e = estados[t]

        print(f"{t:>2} | {w80[t]:08X} | {f:08X} | {a5:08X} | {a:08X} | "
              f"{b:08X} | {c:08X} | {d:08X} | {e:08X}")


def mostrar_resumen_bloques(bloques_rondas: list[dict]) -> None:
    print("\n  RESUMEN DE LOS 4 BLOQUES")
    for br in bloques_rondas:
        print(f"\n  BLOQUE {br['numero']}   Rondas {br['t_inicio']} - {br['t_fin']}")
        print(f"    Función f           : {br['regla']}")
        print(f"    Fórmula de f        : {br['formula']}")
        print(f"    Constante K         : 0x{br['k']:08X}")
        print(f"    TEMP (1ª ronda)     : 0x{br['temp_primera']:08X}")
        print(f"    A..E al inicio      : {texto_abcde(br['entrada'])}")
        print(f"    A..E al terminar    : {texto_abcde(br['estados'][-1])}")


def mostrar_bloques_completo(w80: list[int], bloques_rondas: list[dict], h_partida: list[int], con_pausas: bool) -> None:
    print("\n=== PARTE 1: primeras 16 palabras (t = 0 a 15) ===")
    mostrar_tabla_rondas(w80, bloques_rondas, 0, 15, h_partida)
    if con_pausas:
        pausa()

    print("\n=== PARTE 2: continuación hasta completar las 80 palabras (t = 16 a 79) ===")
    mostrar_tabla_rondas(w80, bloques_rondas, 16, 79, h_partida)
    if con_pausas:
        pausa()

    mostrar_resumen_bloques(bloques_rondas)


def mostrar_detalle_suma(i: int, x: int, y: int) -> None:
    variable = "ABCDE"[i]
    s = sumar_con_llevadas(x, y)
    columnas = s["columnas"]

    def fila(etiqueta: str, valores: list) -> None:
        print(f"    {etiqueta:<28}" + "".join(f"{v:>3}" for v in valores))

    print(f"\n  Suma {i + 1}. H{i} = H{i} + {variable}   (suma hexadecimal con llevadas, módulo 2^32)")
    fila("Llevada que sale", [c["llevada"] for c in columnas])
    fila(f"H{i}", list(f"{x:08X}"))
    fila(f"+ {variable} (final)", list(f"{y:08X}"))
    fila("Suma decimal (con llevada)", [c["suma"] for c in columnas])
    fila("Dígito que se escribe", [f"{c['digito']:X}" for c in columnas])

    puro = f"{s['desbordo']}{s['resultado']:08X}"
    print(f"    {'Resultado puro':<28}{puro}")
    print(f"    {'Resultado real (32 bits)':<28}{s['resultado']:08X}")
    if s["desbordo"]:
        print("    El 1 de la izquierda se descarta (módulo 2^32): solo se conservan 32 bits.")
    else:
        print("    No hubo desbordamiento: el resultado cabe en 32 bits.")


def mostrar_suma_final(h: list[int], estado_final: tuple) -> None:
    print("\n  Después de la ronda 79:")
    print("  H0 = H0 + A ; H1 = H1 + B ; H2 = H2 + C ; H3 = H3 + D ; H4 = H4 + E   (módulo 2^32)\n")

    nuevo_h = sumar_h(h, estado_final)

    print("  Registro        Valor H      Valor final    Suma completa   ¿Desbordó?   Resultado")
    for i, (x, y, r) in enumerate(zip(h, estado_final, nuevo_h)):
        completa = x + y
        desbordo = "Sí" if completa > MASCARA_32 else "No"
        print(f"  H{i} = H{i} + {'ABCDE'[i]}   {x:08X}     {y:08X}      {completa:>9X}         "
            f"{desbordo:<9}    {r:08X}")

    for i, (x, y) in enumerate(zip(h, estado_final)):
        mostrar_detalle_suma(i, x, y)


def mostrar_concatenacion(h: list[int]) -> None:
    print("\n  Hash final:  H0 || H1 || H2 || H3 || H4   (se escriben uno junto al otro)\n")

    for i, x in enumerate(h):
        print(f"  H{i} nuevo = 0x{x:08X}   {x:032b}")

    resultado = h_a_hex(h)

    print(f"\n  5 valores x 32 bits = 160 bits = {len(resultado)} dígitos hexadecimales")
    print(f"\n  SHA-1 Personalizado (hexadecimal) : {resultado}")


def mostrar_proceso(mensaje: str) -> None:
    bytes_msg = len(mensaje.encode("utf-8"))
    bloques = construir_bloques(mensaje)

    print(f"\nMensaje: {mensaje!r}  ({bytes_msg} bytes = {bytes_msg * 8} bits)")
    print(f"Después del relleno: {len(bloques)} bloque(s) de 512 bits")

    print("\n--- PASO 1: Construcción del bloque (W0 a W15) ---")
    for n, w16 in enumerate(bloques, start=1):
        print(f"\nBloque {n}")
        for t, w in enumerate(w16):
            print(f"  W{t:<2} = 0x{w:08X}   {w:032b}")
    pausa()

    print("\n--- PASO 2: Expansión del bloque (W16 a W79) ---")
    print("  X  = W[t-3] XOR W[t-8] XOR W[t-14] XOR W[t-16]")
    print("  Wt = ROTL1(X) XOR (W[t-1] AND W[t-2])")
    print("  Orden: 1) XOR de cuatro palabras  2) ROTL1  3) AND de W[t-1] y W[t-2]  4) XOR de ambos (todo en 32 bits)")
    for n, w16 in enumerate(bloques, start=1):
        w80 = expandir_palabras(w16)

        print(f"\nBloque {n}")
        print(" t  |  W[t-3]  |  W[t-8]  | W[t-14]  | W[t-16]  |  X = XOR |  ROTL1(X)|  W[t-1]  |  W[t-2]  |   AND    | Wt = ROTL1 XOR AND")
        for t in range(16, 80):
            x = w80[t - 3] ^ w80[t - 8] ^ w80[t - 14] ^ w80[t - 16]
            rot = rotar_izquierda(x, 1)
            y = (w80[t - 1] & w80[t - 2]) & MASCARA_32
            print(f"{t:>3} | {w80[t - 3]:08X} | {w80[t - 8]:08X} | "
                f"{w80[t - 14]:08X} | {w80[t - 16]:08X} | "
                f"{x:08X} | {rot:08X} | {w80[t - 1]:08X} | {w80[t - 2]:08X} | {y:08X} | {w80[t]:08X}")

        if n < len(bloques):
            pausa()
    pausa()

    h = H_INICIAL[:]
    for n, w16 in enumerate(bloques, start=1):
        w80 = expandir_palabras(w16)

        print(f"\n--- PASO 3: Las 80 rondas en 4 bloques de 20, funciones personalizadas (bloque {n} del mensaje) ---")
        print(f"  H de partida: {texto_h(h)}")

        bloques_rondas = ejecutar_bloques_de_rondas(w80, h)
        mostrar_bloques_completo(w80, bloques_rondas, h, con_pausas=True)
        pausa()

        print(f"\n--- PASO 4: Suma final (bloque {n} del mensaje) ---")
        estado_final = estados_planos(bloques_rondas)[-1]
        mostrar_suma_final(h, estado_final)
        h = sumar_h(h, estado_final)
        pausa()

    print("\n--- PASO 5: Concatenación y resultado final ---")
    mostrar_concatenacion(h)


def opcion_calcular() -> None:
    mensaje = input("\nEscriba el mensaje (puede dejarlo vacío): ")

    print(f"\n  Mensaje : {mensaje!r}")
    print(f"  SHA-1 Personalizado : {calcular_sha1(mensaje)}")


def opcion_ver_palabras() -> None:
    mensaje = input("\nEscriba el mensaje (puede dejarlo vacío): ")
    bytes_msg = len(mensaje.encode("utf-8"))

    print(f"\n  Mensaje : {mensaje!r}  ({bytes_msg * 8} bits)")

    for n, w80 in enumerate(expandir_bloques(mensaje), start=1):
        print(f"\n  ===== BLOQUE {n} DEL MENSAJE =====")
        mostrar_palabras_en_dos_partes(w80)


def opcion_bloques_completo() -> None:
    mensaje = input("\nEscriba el mensaje (puede dejarlo vacío): ")
    bytes_msg = len(mensaje.encode("utf-8"))
    bloques = expandir_bloques(mensaje)

    print(f"\n  Mensaje : {mensaje!r}  ({bytes_msg * 8} bits)")

    h = H_INICIAL[:]
    for n, w80 in enumerate(bloques, start=1):
        print(f"\n  ######## BLOQUE {n} DEL MENSAJE (de {len(bloques)}) ########")
        print(f"  H de partida: {texto_h(h)}")

        bloques_rondas = ejecutar_bloques_de_rondas(w80, h)
        mostrar_bloques_completo(w80, bloques_rondas, h, con_pausas=False)
        h = sumar_h(h, estados_planos(bloques_rondas)[-1])


def opcion_suma_y_concatenacion() -> None:
    mensaje = input("\nEscriba el mensaje (puede dejarlo vacío): ")
    bytes_msg = len(mensaje.encode("utf-8"))
    bloques = expandir_bloques(mensaje)

    print(f"\n  Mensaje : {mensaje!r}  ({bytes_msg * 8} bits)")

    h = H_INICIAL[:]
    for n, w80 in enumerate(bloques, start=1):
        print(f"\n  ######## SUMA FINAL DEL BLOQUE {n} DEL MENSAJE (de {len(bloques)}) ########")
        print(f"  H de partida: {texto_h(h)}")

        estado_final = estados_planos(ejecutar_bloques_de_rondas(w80, h))[-1]
        mostrar_suma_final(h, estado_final)
        h = sumar_h(h, estado_final)

    print("\n  ######## CONCATENACIÓN Y RESULTADO FINAL ########")
    mostrar_concatenacion(h)


def opcion_paso_a_paso() -> None:
    mensaje = input("\nEscriba el mensaje (puede dejarlo vacío): ")
    mostrar_proceso(mensaje)


TERMINALES = [
    ("gnome-terminal", "gnome-terminal -- '{py}' '{ruta}' --ventana"),
    ("konsole", "konsole -e '{py}' '{ruta}' --ventana"),
    ("x-terminal-emulator", "x-terminal-emulator -e '{py}' '{ruta}' --ventana"),
    ("xterm", "xterm -e '{py}' '{ruta}' --ventana"),
]


def limpiar_pantalla() -> None:
    if os.isatty(1):
        os.system("cls" if os.name == "nt" else "clear")


def volver_al_menu() -> None:
    input("\n  [Enter para volver al menú] ")


def lanzar_en_otra_ventana() -> bool:
    ruta = os.path.abspath(__file__)
    py = sys.executable

    try:
        if os.name == "nt":
            return os.system(f'start "SHA-1 Personalizado por bloques" "{py}" "{ruta}" --ventana') == 0

        if os.uname().sysname == "Darwin":
            comando = f'\\"{py}\\" \\"{ruta}\\" --ventana'
            return os.system(
                f"""osascript -e 'tell application "Terminal" to do script "{comando}"' """
                f"""-e 'tell application "Terminal" to activate' >/dev/null 2>&1"""
            ) == 0

        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False

        for terminal, plantilla in TERMINALES:
            if os.system(f"command -v {terminal} >/dev/null 2>&1") == 0:
                os.system(plantilla.format(py=py, ruta=ruta) + " >/dev/null 2>&1 &")
                return True
    except OSError:
        pass

    return False


def main() -> None:
    acciones = {
        "1": opcion_calcular,
        "2": opcion_ver_palabras,
        "3": opcion_bloques_completo,
        "4": opcion_suma_y_concatenacion,
        "5": opcion_paso_a_paso,
    }

    try:
        while True:
            limpiar_pantalla()
            print(MENU)
            opcion = input("Elija una opción: ").strip()

            if opcion == "6":
                print("\nHasta luego.")
                break
            elif opcion in acciones:
                acciones[opcion]()
            else:
                print("\nOpción no válida. Escriba un número del 1 al 6.")

            volver_al_menu()
    except (EOFError, KeyboardInterrupt):
        print("\n\nHasta luego.")


def iniciar() -> None:
    if "--ventana" in sys.argv:
        try:
            main()
        except Exception as error:
            print(f"\nError inesperado: {error}")

        try:
            input("\nPresione Enter para cerrar esta ventana...")
        except (EOFError, KeyboardInterrupt):
            pass
    elif lanzar_en_otra_ventana():
        print("La aplicación se abrió en otra ventana.")
    else:
        print("No se pudo abrir otra ventana; la aplicación se ejecuta aquí.")
        main()


if __name__ == "__main__":
    iniciar()