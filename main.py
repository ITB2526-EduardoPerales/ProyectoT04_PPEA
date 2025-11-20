import xml.etree.ElementTree as ET
from collections import Counter
from colorama import Fore, Style
from datetime import datetime

# Función auxiliar para obtener texto seguro
def txt(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""

# Leer XML
tree = ET.parse("incidencies.xml")
root = tree.getroot()

# Extraer incidencias
incidencies = []
for inc in root.findall("incidencia"):
    id_incidencia = inc.attrib.get("id", "")
    fecha = txt(inc, "Fecha_de_la_incidencia")
    hora = txt(inc, "Hora")
    tipo = txt(inc, "Tipos_de_incidencia")
    prioridad = txt(inc, "Prioridad_del_problema")
    ubicacion = txt(inc, "Ubicación")
    detalle = txt(inc, "Explica_el_problema_detalladamente")

    incidencies.append({
        "id": id_incidencia,
        "fecha": fecha,
        "hora": hora,
        "tipo": tipo,
        "prioridad": prioridad,
        "ubicacion": ubicacion,
        "detalle": detalle
    })

# Definir mapa de prioridad
prio_map = {"alta": 0, "media": 1, "baja": 2}

# Función para convertir fecha/hora a datetime
def parse_fecha_hora(fecha_str, hora_str):
    """
    Convierte la fecha en datetime. Soporta:
    1. dd/mm/yyyy HH:MM:SS
    2. dd/mm HH:MM:SS (sin año, se asume 2025)
    """
    fecha_str = (fecha_str or "").strip()
    hora_str = (hora_str or "").strip()
    try:
        return datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
    except ValueError:
        try:
            dt = datetime.strptime(f"{fecha_str} {hora_str}", "%d/%m %H:%M:%S")
            return dt.replace(year=2025)
        except ValueError:
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

# Mostrar incidencias con color según prioridad
print(Fore.CYAN + "\n📋 Incidencias válidas ordenadas por prioridad y fecha/hora:" + Style.RESET_ALL)
for inc in valides:
    prio = (inc["prioridad"] or "").lower()
    if "alta" in prio:
        color = Fore.RED
    elif "media" in prio:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN
    print(color + f"ID:{inc['id']:3} | Fecha:{inc['fecha']:15} {inc['hora']:8} | "
          f"Tipo:{inc['tipo']:20} | Ubicación:{inc['ubicacion']:10} | "
          f"Prioridad:{inc['prioridad']:5}" + Style.RESET_ALL)

# Estadísticas generales (porcentaje primero, cantidad entre paréntesis)
total = len(valides) + descartades
print(Fore.MAGENTA + "\n===== Estadísticas =====" + Style.RESET_ALL)
print(f"Descartades (futuras): {int(descartades/total*100)}% ({descartades})")
print(f"Sense any: {int(sense_any/total*100)}% ({sense_any})")
print(f"Total vàlides: {int(len(valides)/total*100)}% ({len(valides)})")

# Por tipo (porcentaje primero, cantidad entre paréntesis)
tipus_counter = Counter([inc["tipo"] or "(sense tipus)" for inc in valides])
print(Fore.CYAN + "\n📊 Per tipus:" + Style.RESET_ALL)
for k, v in tipus_counter.items():
    print(f"  {k:30} {int(v/len(valides)*100)}% ({v})")

# Por prioridad (porcentaje primero, cantidad entre paréntesis)
prio_counter = Counter([inc["prioridad"] or "(sense prio)" for inc in valides])
print(Fore.YELLOW + "\n🎯 Per prioritat:" + Style.RESET_ALL)
for k, v in prio_counter.items():
    print(f"  {k:30} {int(v/len(valides)*100)}% ({v})")

# Por ubicación (porcentaje primero, cantidad entre paréntesis)
ubi_counter = Counter([inc["ubicacion"] or "(sense ubicació)" for inc in valides])
print(Fore.GREEN + "\n📍 Per ubicació:" + Style.RESET_ALL)
for k, v in ubi_counter.items():
    print(f"  {k:30} {int(v/len(valides)*100)}% ({v})")

# =========================
# Menú interactivo
# =========================
def mostrar_menu(valides):
    tipos = sorted(set([inc["tipo"] or "(sense tipus)" for inc in valides]))
    prioridades = ["Alta", "Media", "Baja"]

    while True:
        print(Fore.CYAN + "\n===== MENÚ PRINCIPAL =====" + Style.RESET_ALL)
        print("1. Ver incidencias por tipo")
        print("2. Ver incidencias por prioridad")
        print("0. Salir")

        opcion = input("\nSeleccione una opción: ")

        if opcion == "0":
            print(Fore.MAGENTA + "Saliendo del menú..." + Style.RESET_ALL)
            break

        elif opcion == "1":
            print(Fore.CYAN + "\n===== TIPOS DE INCIDENCIA =====" + Style.RESET_ALL)
            for i, t in enumerate(tipos, start=1):
                count = sum(1 for inc in valides if (inc["tipo"] or "(sense tipus)") == t)
                print(f"{i}. {t} {int(count/len(valides)*100)}% ({count})")
            print("0. Volver")

            subop = input("\nSeleccione un tipo: ")
            if subop == "0":
                continue
            try:
                idx = int(subop) - 1
                if 0 <= idx < len(tipos):
                    tipo_sel = tipos[idx]
                    seleccionadas = [inc for inc in valides if (inc["tipo"] or "(sense tipus)") == tipo_sel]
                    total_sel = len(seleccionadas)
                    print(Fore.YELLOW + f"\n📋 Incidencias del tipo: {tipo_sel} {int(total_sel/len(valides)*100)}% ({total_sel})" + Style.RESET_ALL)
                    for inc in seleccionadas:
                        prio = (inc["prioridad"] or "").lower()
                        if "alta" in prio:
                            color = Fore.RED
                        elif "media" in prio:
                            color = Fore.YELLOW
                        else:
                            color = Fore.GREEN
                        print(color + f"ID:{inc['id']:3} | Fecha:{inc['fecha']:15} {inc['hora']:8} | "
                              f"Ubicación:{inc['ubicacion']:10} | Prioridad:{inc['prioridad']:5}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + "Opción inválida." + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Debe ingresar un número válido." + Style.RESET_ALL)

        elif opcion == "2":
            print(Fore.CYAN + "\n===== PRIORIDADES =====" + Style.RESET_ALL)
            for i, p in enumerate(prioridades, start=1):
                count = sum(1 for inc in valides if (inc["prioridad"] or "").lower() == p.lower())
                print(f"{i}. {p} {int(count/len(valides)*100)}% ({count})")
            print("0. Volver")

            subop = input("\nSeleccione una prioridad: ")
            if subop == "0":
                continue
            try:
                idx = int(subop) - 1
                if 0 <= idx < len(prioridades):
                    p_sel = prioridades[idx].lower()
                    seleccionadas = [inc for inc in valides if (inc["prioridad"] or "").lower() == p_sel]
                    total_sel = len(seleccionadas)
                    print(Fore.YELLOW + f"\n📋 Incidencias con prioridad: {prioridades[idx]} {int(total_sel/len(valides)*100)}% ({total_sel})" + Style.RESET_ALL)
                    for inc in seleccionadas:
                        prio = (inc["prioridad"] or "").lower()
                        if "alta" in prio:
                            color = Fore.RED
                        elif "media" in prio:
                            color = Fore.YELLOW
                        else:
                            color = Fore.GREEN
                        print(color + f"ID:{inc['id']:3} | Fecha:{inc['fecha']:15} {inc['hora']:8} | "
                              f"Tipo:{inc['tipo']:20} | Ubicación:{inc['ubicacion']:10}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + "Opción inválida." + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Debe ingresar un número válido." + Style.RESET_ALL)

        else:
            print(Fore.RED + "Opción inválida, intente de nuevo." + Style.RESET_ALL)

# Llamada al menú
mostrar_menu(valides)

print(Fore.MAGENTA + "\nProcess finished with exit code 0" + Style.RESET_ALL)
