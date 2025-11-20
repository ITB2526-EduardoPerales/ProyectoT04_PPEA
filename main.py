import xml.etree.ElementTree as ET
from collections import Counter
from colorama import Fore, Style
from datetime import datetime

# Función auxiliar para obtener texto seguro
def txt(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text is not None else ""

# Leer XML
tree = ET.parse("incidencies.xml")
root = tree.getroot()

# Extraer incidencias (incluye todos los campos)
incidencies = []
for inc in root.findall("incidencia"):
    id_incidencia = inc.attrib.get("id", "")
    marca = txt(inc, "Marca_de_temps")
    correo = txt(inc, "Ingresa__tu_correo_electrónico_")
    fecha = txt(inc, "Fecha_de_la_incidencia")
    hora = txt(inc, "Hora")
    nombre_equipo = txt(inc, "Nombre_del_equipo")
    tipo_equipo = txt(inc, "Tipo_de_equipo")
    tipo_otros = txt(inc, "En_caso_de_otros__pon_que_tipo_de_equipo_es_")
    tipo = txt(inc, "Tipos_de_incidencia")
    detalle = txt(inc, "Explica_el_problema_detalladamente")
    prioridad = txt(inc, "Prioridad_del_problema")
    ubicacion = txt(inc, "Ubicación")

    incidencies.append({
        "id": id_incidencia,
        "marca": marca,
        "correo": correo,
        "fecha": fecha,
        "hora": hora,
        "nombre_equipo": nombre_equipo,
        "tipo_equipo": tipo_equipo,
        "tipo_otros": tipo_otros,
        "tipo": tipo,
        "detalle": detalle,
        "prioridad": prioridad,
        "ubicacion": ubicacion
    })

# Mapa de prioridad
prio_map = {"alta": 0, "media": 1, "baja": 2}

# Parse fecha/hora
def parse_fecha_hora(fecha_str, hora_str):
    fecha_str = (fecha_str or "").strip()
    hora_str = (hora_str or "").strip()
    try:
        return datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
    except Exception:
        try:
            dt = datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m %H:%M:%S")
            return dt.replace(year=datetime.now().year)
        except Exception:
            return None

# Filtrar incidencias válidas (descartar futuras)
valides, descartades, sense_any = [], 0, 0
ahora = datetime.now()

for inc in incidencies:
    dt = parse_fecha_hora(inc["fecha"], inc["hora"])
    if dt is None:
        valides.append(inc)
        sense_any += 1
    elif dt <= ahora:
        inc["dt"] = dt
        valides.append(inc)
    else:
        descartades += 1

# Ordenar por prioridad y fecha/hora
valides.sort(key=lambda x: (prio_map.get((x["prioridad"] or "").lower(), 3), x.get("dt", datetime.max)))

# Función que imprime la cabecera fija (mismas columnas siempre)
def imprimir_cabecera_compacta():
    header = (
        "ID   | Marca_de_temps         | Fecha         | Hora     | "
        "Tipo de incidencia      | TipoEquipo       | En_caso_de_otros           | "
        "Ubicación         | Prioridad | Nombre_del_equipo    | Correo"
    )
    print(Fore.CYAN + header + Style.RESET_ALL)
    print(Fore.CYAN + "-" * len(header) + Style.RESET_ALL)

# Función que imprime una incidencia en la misma línea y columnas (sin modificar datos)
def imprimir_linea_incidencia(inc):
    prio = (inc.get("prioridad") or "").lower()
    if "alta" in prio:
        color = Fore.RED
    elif "media" in prio:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN

    # Imprimimos todos los campos en el mismo orden que la cabecera, sin recortarlos
    # Ajustes de formato solo para alinear; los valores completos se muestran (no se modifican los dicts)
    line = (
        f"{inc.get('id',''):4} | "
        f"{inc.get('marca',''):22} | "
        f"{inc.get('fecha',''):13} | "
        f"{inc.get('hora',''):8} | "
        f"{inc.get('tipo',''):22} | "
        f"{inc.get('tipo_equipo',''):15} | "
        f"{inc.get('tipo_otros',''):25} | "
        f"{inc.get('ubicacion',''):16} | "
        f"{inc.get('prioridad',''):9} | "
        f"{inc.get('nombre_equipo',''):20} | "
        f"{inc.get('correo','')}"
    )
    print(color + line + Style.RESET_ALL)

# Mostrar lista principal con la cabecera fija y todas las columnas
print()
print(Fore.CYAN + "📋 Incidencias válidas ordenadas por prioridad y fecha/hora:" + Style.RESET_ALL)
imprimir_cabecera_compacta()
for inc in valides:
    imprimir_linea_incidencia(inc)

# Estadísticas generales
total = len(valides) + descartades
if total == 0:
    total = 1

print(Fore.MAGENTA + "\n===== Estadísticas =====" + Style.RESET_ALL)
print(f"Descartades (futuras): {int(descartades/total*100)}% ({descartades})")
print(f"Sense any: {int(sense_any/total*100)}% ({sense_any})")
print(f"Total vàlides: {int(len(valides)/total*100)}% ({len(valides)})")

# Contadores
tipus_counter = Counter([inc.get("tipo") or "(sense tipus)" for inc in valides])
print(Fore.CYAN + "\n📊 Per tipus:" + Style.RESET_ALL)
for k, v in tipus_counter.items():
    pct = int(v / max(1, len(valides)) * 100)
    print(f"  {k:30} {pct}% ({v})")

prio_counter = Counter([inc.get("prioridad") or "(sense prio)" for inc in valides])
print(Fore.YELLOW + "\n🎯 Per prioritat:" + Style.RESET_ALL)
for k, v in prio_counter.items():
    pct = int(v / max(1, len(valides)) * 100)
    print(f"  {k:30} {pct}% ({v})")

ubi_counter = Counter([inc.get("ubicacion") or "(sense ubicació)" for inc in valides])
print(Fore.GREEN + "\n📍 Per ubicació:" + Style.RESET_ALL)
for k, v in ubi_counter.items():
    pct = int(v / max(1, len(valides)) * 100)
    print(f"  {k:30} {pct}% ({v})")

# =========================
# Menú interactivo — filtra pero NO quita columnas ni modifica datos
# =========================
def mostrar_menu(valides):
    tipos = sorted(set([inc.get("tipo") or "(sense tipus)" for inc in valides]))
    prioridades = ["Alta", "Media", "Baja"]

    while True:
        print(Fore.CYAN + "\n===== MENÚ PRINCIPAL =====" + Style.RESET_ALL)
        print("1. Ver incidencias por tipo")
        print("2. Ver incidencias por prioridad")
        print("3. Ver incidencia por ID")
        print("0. Salir")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            print(Fore.MAGENTA + "Saliendo del menú..." + Style.RESET_ALL)
            break

        elif opcion == "1":
            print(Fore.CYAN + "\n===== TIPOS DE INCIDENCIA =====" + Style.RESET_ALL)
            for i, t in enumerate(tipos, start=1):
                count = sum(1 for inc in valides if (inc.get("tipo") or "(sense tipus)") == t)
                pct = int(count / max(1, len(valides)) * 100)
                print(f"{i}. {t} {pct}% ({count})")
            print("0. Volver")

            subop = input("\nSeleccione un tipo: ").strip()
            if subop == "0":
                continue
            try:
                idx = int(subop) - 1
                if 0 <= idx < len(tipos):
                    tipo_sel = tipos[idx]
                    seleccionadas = [inc for inc in valides if (inc.get("tipo") or "(sense tipus)") == tipo_sel]
                    print(Fore.YELLOW + f"\n📋 Incidencias del tipo: {tipo_sel} ({len(seleccionadas)})" + Style.RESET_ALL)
                    imprimir_cabecera_compacta()
                    for inc in seleccionadas:
                        imprimir_linea_incidencia(inc)
                else:
                    print(Fore.RED + "Opción inválida." + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Debe ingresar un número válido." + Style.RESET_ALL)

        elif opcion == "2":
            print(Fore.CYAN + "\n===== PRIORIDADES =====" + Style.RESET_ALL)
            for i, p in enumerate(prioridades, start=1):
                count = sum(1 for inc in valides if (inc.get("prioridad") or "").lower() == p.lower())
                pct = int(count / max(1, len(valides)) * 100)
                print(f"{i}. {p} {pct}% ({count})")
            print("0. Volver")

            subop = input("\nSeleccione una prioridad: ").strip()
            if subop == "0":
                continue
            try:
                idx = int(subop) - 1
                if 0 <= idx < len(prioridades):
                    p_sel = prioridades[idx].lower()
                    seleccionadas = [inc for inc in valides if (inc.get("prioridad") or "").lower() == p_sel]
                    print(Fore.YELLOW + f"\n📋 Incidencias con prioridad: {prioridades[idx]} ({len(seleccionadas)})" + Style.RESET_ALL)
                    imprimir_cabecera_compacta()
                    for inc in seleccionadas:
                        imprimir_linea_incidencia(inc)
                else:
                    print(Fore.RED + "Opción inválida." + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Debe ingresar un número válido." + Style.RESET_ALL)

        elif opcion == "3":
            id_buscar = input("\nIntroduzca ID de la incidencia: ").strip()
            encontradas = [inc for inc in valides if inc.get("id") == id_buscar]
            if not encontradas:
                print(Fore.RED + f"No se encontró incidencia con ID {id_buscar}" + Style.RESET_ALL)
            else:
                imprimir_cabecera_compacta()
                for inc in encontradas:
                    imprimir_linea_incidencia(inc)

        else:
            print(Fore.RED + "Opción inválida, intente de nuevo." + Style.RESET_ALL)

# Ejecutar menú
mostrar_menu(valides)

print(Fore.MAGENTA + "\nProcess finished with exit code 0" + Style.RESET_ALL)
