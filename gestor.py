import math

TAM_PAGINA = 4
NUM_MARCOS = 16
MARCOS_SO = 2
TAM_SWAP = 64

memoria = ["SO"] * MARCOS_SO + [None] * (NUM_MARCOS - MARCOS_SO)
procesos = {}
swap = {}
siguiente_pid = 1


def huecos():
    res, i = [], 0
    while i < NUM_MARCOS:
        if memoria[i] is None:
            j = i
            while j < NUM_MARCOS and memoria[j] is None:
                j += 1
            res.append((i, j - i))
            i = j
        else:
            i += 1
    return res


def primer_ajuste(n):
    for ini, lon in huecos():
        if lon >= n:
            return ini
    return None


def cargar(pid, base):
    p = procesos[pid]
    for k in range(p["paginas"]):
        memoria[base + k] = pid
    p["base"] = base
    p["estado"] = "MEMORIA"


def liberar(pid):
    for i in range(NUM_MARCOS):
        if memoria[i] == pid:
            memoria[i] = None
    procesos[pid]["base"] = None


def swap_usado():
    return sum(p["tam"] for p in swap.values())


def leer_entero(msg):
    try:
        return int(input(msg).strip())
    except ValueError:
        return None


def mostrar_memoria():
    print("\n=== MAPA DE MEMORIA FÍSICA ===")
    print(f"Marco | Dirección (KB) | Contenido")
    for i, c in enumerate(memoria):
        ini = i * TAM_PAGINA
        fin = ini + TAM_PAGINA - 1
        if c is None:
            cont = "[ LIBRE ]"
        elif c == "SO":
            cont = "[ Sistema Operativo ]"
        else:
            pag = i - procesos[c]["base"]
            cont = f"[ P{c} {procesos[c]['nombre']} - pág {pag} ]"
        print(f"{i:5d} | {ini:4d}K - {fin:4d}K | {cont}")

    libres = sum(1 for m in memoria if m is None)
    hs = huecos()
    print(f"\nLibre: {libres * TAM_PAGINA} KB en {len(hs)} hueco(s)", end="")
    if hs:
        print(" -> " + ", ".join(f"[marco {i}, {l * TAM_PAGINA}KB]" for i, l in hs))
    else:
        print()
    if len(hs) > 1:
        print(f"Fragmentación externa: mayor hueco = "
              f"{max(l for _, l in hs) * TAM_PAGINA} KB (use 'Compactar')")

    print("\nProcesos en memoria:")
    en_mem = [p for p in procesos.values() if p["estado"] == "MEMORIA"]
    if not en_mem:
        print("  (ninguno)")
    for pid, p in procesos.items():
        if p["estado"] == "MEMORIA":
            print(f"  P{pid} {p['nombre']:<10} {p['tam']} KB  "
                  f"marcos {p['base']}-{p['base'] + p['paginas'] - 1}")
    print("\nProcesos en SWAP:")
    if not swap:
        print("  (ninguno)")
    for pid, p in swap.items():
        print(f"  P{pid} {p['nombre']:<10} {p['tam']} KB")
    print(f"Swap usado: {swap_usado()}/{TAM_SWAP} KB")


def crear_proceso():
    global siguiente_pid
    nombre = input("Nombre del proceso: ").strip() or f"proc{siguiente_pid}"
    tam = leer_entero("Tamaño (KB): ")
    if tam is None or tam <= 0:
        print("Tamaño inválido.")
        return
    n = math.ceil(tam / TAM_PAGINA)
    if n > NUM_MARCOS - MARCOS_SO:
        print("El proceso es más grande que la memoria disponible para usuarios.")
        return
    base = primer_ajuste(n)
    if base is None:
        libres = sum(1 for m in memoria if m is None)
        if libres >= n:
            print(f"No hay un hueco contiguo de {n} marcos, pero hay {libres} "
                  f"libres en total. Use la opción 4 (Compactar).")
        else:
            print("Memoria insuficiente. Termine o envíe a SWAP algún proceso.")
        return
    pid = siguiente_pid
    siguiente_pid += 1
    procesos[pid] = {"nombre": nombre, "tam": tam, "paginas": n,
                     "base": None, "estado": None}
    cargar(pid, base)
    desp = n * TAM_PAGINA - tam
    print(f"Proceso P{pid} '{nombre}' creado: {n} página(s) en marcos "
          f"{base}-{base + n - 1}. Fragmentación interna: {desp} KB.")


def terminar_proceso():
    pid = leer_entero("PID a terminar: ")
    if pid not in procesos:
        print("PID inexistente.")
        return
    if procesos[pid]["estado"] == "MEMORIA":
        liberar(pid)
    else:
        del swap[pid]
    nombre = procesos.pop(pid)["nombre"]
    print(f"Proceso P{pid} '{nombre}' terminado y memoria liberada.")


def compactar():
    antes = len(huecos())
    orden = sorted((p["base"], pid) for pid, p in procesos.items()
                   if p["estado"] == "MEMORIA")
    cursor = MARCOS_SO
    for _, pid in orden:
        n = procesos[pid]["paginas"]
        liberar(pid)
        cargar(pid, cursor)
        cursor += n
    print(f"Memoria compactada: huecos {antes} -> {len(huecos())}.")
    if cursor < NUM_MARCOS:
        print(f"Hueco único: {(NUM_MARCOS - cursor) * TAM_PAGINA} KB "
              f"desde el marco {cursor}.")


def mostrar_paginas():
    pid = leer_entero("PID (0 = todos): ")
    if pid is None:
        print("Entrada inválida.")
        return
    lista = list(procesos) if pid == 0 else [pid]
    for q in lista:
        if q not in procesos:
            print(f"PID {q} inexistente.")
            continue
        p = procesos[q]
        print(f"\nTabla de páginas de P{q} '{p['nombre']}' "
              f"({p['tam']} KB, {p['paginas']} páginas de {TAM_PAGINA} KB)")
        print("Página | Marco | Presente | Dir. física")
        for k in range(p["paginas"]):
            if p["estado"] == "MEMORIA":
                m = p["base"] + k
                print(f"{k:6d} | {m:5d} | {'1':^8} | {m * TAM_PAGINA}K")
            else:
                print(f"{k:6d} | {'-':>5} | {'0':^8} | (en SWAP)")


def enviar_a_swap():
    pid = leer_entero("PID a enviar a SWAP: ")
    if pid not in procesos or procesos[pid]["estado"] != "MEMORIA":
        print("Ese proceso no existe o ya está en SWAP.")
        return
    p = procesos[pid]
    if swap_usado() + p["tam"] > TAM_SWAP:
        print("No hay espacio suficiente en el área de swap.")
        return
    liberar(pid)
    p["estado"] = "SWAP"
    swap[pid] = p
    print(f"P{pid} '{p['nombre']}' enviado a SWAP ({p['tam']} KB copiados, "
          f"sólo la memoria usada). Marcos liberados.")


def recuperar_de_swap():
    pid = leer_entero("PID a recuperar de SWAP: ")
    if pid not in swap:
        print("Ese proceso no está en SWAP.")
        return
    p = swap[pid]
    base = primer_ajuste(p["paginas"])
    if base is None:
        libres = sum(1 for m in memoria if m is None)
        if libres >= p["paginas"]:
            print("Hay memoria libre pero fragmentada. Use 'Compactar memoria'.")
        else:
            print("Memoria insuficiente. Libere memoria o envíe otro proceso a SWAP.")
        return
    del swap[pid]
    cargar(pid, base)
    print(f"P{pid} '{p['nombre']}' recuperado en marcos "
          f"{base}-{base + p['paginas'] - 1}.")


def menu():
    acciones = {
        "1": mostrar_memoria, "2": crear_proceso, "3": terminar_proceso,
        "4": compactar, "5": mostrar_paginas, "6": enviar_a_swap,
        "7": recuperar_de_swap,
    }
    while True:
        print(f"""
        GESTOR DE MEMORIA  (RAM {NUM_MARCOS * TAM_PAGINA} KB, página {TAM_PAGINA} KB)
        1. Mostrar memoria
        2. Crear proceso
        3. Terminar proceso
        4. Compactar memoria
        5. Mostrar páginas
        6. Enviar proceso a SWAP
        7. Recuperar proceso de SWAP
        8. Salir""")
        op = input("Opción: ").strip()
        if op == "8":
            print("Hasta luego.")
            break
        accion = acciones.get(op)
        if accion:
            accion()
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    menu()