import os
import sys
import getpass
import hashlib
import xml.etree.ElementTree as ET
from collections import Counter
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)

# =========================
# Autenticación del creador
# =========================
CREATOR_USER = os.environ.get("CREATOR_USER", "admin")  # cambia si quieres
CREATOR_PASS_HASH = os.environ.get("CREATOR_PASS_HASH", "replace_with_your_sha256_hash")

def verify_password(plain_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == CREATOR_PASS_HASH

def require_creator() -> bool:
    print(Fore.CYAN + "\nAutenticación requerida (solo creador)" + Style.RESET_ALL)
    user = input("Usuario: ").strip()
    passwd = getpass.getpass("Contraseña: ")
    if user == CREATOR_USER and verify_password(passwd):
        print(Fore.GREEN + "Autenticación correcta." + Style.RESET_ALL)
        return True
    print(Fore.RED + "Autenticación fallida." + Style.RESET_ALL)
    return False

# =========================
# Utilidades de UI
# =========================
def txt(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text is not None else ""

def pct_color(pct):
    if pct >= 75:
        return Fore.GREEN
    elif pct >= 50:
        return Fore.YELLOW
    else:
        return Fore.RED

def bar(pct, width=20):
    filled = int((pct / 100) * width)
    return f"{'█' * filled}{'░' * (width - filled)}"

def format_pct(pct):
    c = pct_color(pct)
    return f"{c}{pct:3d}%{Style.RESET_ALL}"

def print_panel(title):
    line = "─" * (len(title) + 2)
    print(Fore.CYAN + f"┌{line}┐" + Style.RESET_ALL)
    print(Fore.CYAN + f"│ {title} │" + Style.RESET_ALL)
    print(Fore.CYAN + f"└{line}┘" + Style.RESET_ALL)

def print_menu_main():
    print_panel("MENÚ PRINCIPAL")
    print("1) Ver incidencias por tipo")
    print("2) Ver incidencias por prioridad")
    print("3) Ver incidencias por ubicación")
    print("4) Ver estadísticas generales")
    print("5) Administrar (requiere clave)")
    print("0) Salir")

def print_section_header(text):
    print()
    print_panel(text)

# =========================
# Cargar XML con manejo de errores (sin mostrar la ruta)
# =========================
XML_FILE = "incidencies.xml"
try:
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
except FileNotFoundError:
    print(Fore.RED + f"Error: no se encontró el archivo '{XML_FILE}'. Asegúrate de que existe en el directorio actual." + Style.RESET_ALL)
    sys.exit(1)
except ET.ParseError as e:
    print(Fore.RED + f"Error al parsear '{XML_FILE}': {e}" + Style.RESET_ALL)
    sys.exit(1)

# =========================
# Extraer incidencias
# =========================
incidencies = []
for inc in root.findall("incidencia"):
    id_incidencia = inc.attrib.get("id", "")
    incidencies.append({
        "id": id_incidencia,
        "marca": txt(inc, "Marca_de_temps"),
        "correo": txt(inc, "Ingresa__tu_correo_electrónico_"),
        "fecha": txt(inc, "Fecha_de_la_incidencia"),
        "hora": txt(inc, "Hora"),
        "nombre_equipo": txt(inc, "Nombre_del_equipo"),
        "tipo_equipo": txt(inc, "Tipo_de_equipo"),
        "tipo_otros": txt(inc, "En_caso_de_otros__pon_que_tipo_de_equipo_es_"),
        "tipo": txt(inc, "Tipos_de_incidencia"),
        "detalle": txt(inc, "Explica_el_problema_detalladamente"),
        "prioridad": txt(inc, "Prioridad_del_problema"),
        "ubicacion": txt(inc, "Ubicación")
    })

# =========================
# Orden y filtrado
# =========================
prio_map = {"alta": 0, "media": 1, "baja": 2}

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

valides.sort(key=lambda x: (prio_map.get((x["prioridad"] or "").lower(), 3), x.get("dt", datetime.max)))

# =========================
# Impresión de tabla (cabecera + filas)
# =========================
def imprimir_cabecera_compacta():
    header = (
        "ID   | Marca_de_temps         | Fecha         | Hora     | "
        "Tipo de incidencia      | TipoEquipo       | En_caso_de_otros           | "
        "Ubicación         | Prioridad | Nombre_del_equipo    | Correo"
    )
    print(Fore.CYAN + header + Style.RESET_ALL)
    print(Fore.CYAN + "-" * len(header) + Style.RESET_ALL)

def imprimir_linea_incidencia(inc):
    prio = (inc.get("prioridad") or "").lower()
    if "alta" in prio:
        color = Fore.RED
    elif "media" in prio:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN

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

# =========================
# Módulos de menú con porcentajes destacados
# =========================
def stats_counter(campo):
    total = len(valides)
    c = Counter([inc.get(campo) or f"(sin {campo})" for inc in valides])
    items = []
    for k, v in sorted(c.items(), key=lambda kv: kv[1], reverse=True):
        pct = int(v / max(1, total) * 100)
        items.append((k, v, pct))
    return items, total

def mostrar_lista_filtrada_por(campo, valor):
    seleccionadas = [inc for inc in valides if (inc.get(campo) or f"(sin {campo})") == valor]
    print_section_header(f"Resultados: {campo} = {valor}")
    imprimir_cabecera_compacta()
    for inc in seleccionadas:
        imprimir_linea_incidencia(inc)
    print()

def menu_por_campo(campo, titulo):
    items, total = stats_counter(campo)
    print_section_header(titulo)
    print(f"Total registros: {total}")
    print(Fore.CYAN + "Seleccione una opción:" + Style.RESET_ALL)
    for i, (k, v, pct) in enumerate(items, start=1):
        print(
            f"{i}) {k:<24} "
            f"| {format_pct(pct)} "
            f"| {bar(pct, width=25)} "
            f"| {v} items"
        )
    print("0) Volver")

    sel = input("\nOpción: ").strip()
    if sel == "0":
        return
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(items):
            valor = items[idx][0]
            mostrar_lista_filtrada_por(campo, valor)
        else:
            print(Fore.RED + "Opción inválida." + Style.RESET_ALL)
    except ValueError:
        print(Fore.RED + "Debe ingresar un número válido." + Style.RESET_ALL)

def menu_estadisticas_generales():
    print_section_header("Estadísticas generales")
    total = len(valides) + descartades
    total = total if total > 0 else 1

    pct_desc = int(descartades/total*100)
    pct_any = int(sense_any/total*100)
    pct_valid = int(len(valides)/total*100)
    print(Fore.MAGENTA + "Distribución temporal" + Style.RESET_ALL)
    print(f"- Descartadas (futuras): {format_pct(pct_desc)} | {bar(pct_desc)} | {descartades}")
    print(f"- Sin fecha/hora (sense any): {format_pct(pct_any)} | {bar(pct_any)} | {sense_any}")
    print(f"- Válidas: {format_pct(pct_valid)} | {bar(pct_valid)} | {len(valides)}")

    print(Fore.CYAN + "\nPor tipo" + Style.RESET_ALL)
    items, _ = stats_counter("tipo")
    for k, v, pct in items:
        print(f"• {k:<24} {format_pct(pct)}  {bar(pct, 30)}  ({v})")

    print(Fore.YELLOW + "\nPor prioridad" + Style.RESET_ALL)
    items, _ = stats_counter("prioridad")
    for k, v, pct in items:
        print(f"• {k:<24} {format_pct(pct)}  {bar(pct, 30)}  ({v})")

    print(Fore.GREEN + "\nPor ubicación" + Style.RESET_ALL)
    items, _ = stats_counter("ubicacion")
    for k, v, pct in items:
        print(f"• {k:<24} {format_pct(pct)}  {bar(pct, 30)}  ({v})")

# =========================
# Operaciones administrativas (requiere autenticación)
# =========================
def safe_tree_write(tree_obj, filename):
    try:
        tree_obj.write(filename, encoding="utf-8", xml_declaration=True)
        print(Fore.GREEN + f"Cambios guardados en {filename}" + Style.RESET_ALL)
    except FileNotFoundError:
        print(Fore.RED + f"No se pudo guardar: ruta no encontrada para '{filename}'." + Style.RESET_ALL)
    except PermissionError:
        print(Fore.RED + f"No se pudo guardar: permiso denegado para '{filename}'." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error al guardar '{filename}': {e}" + Style.RESET_ALL)

def admin_menu(valides):
    print_section_header("ADMINISTRAR (requiere clave)")
    print("1) Cambiar prioridad de una incidencia")
    print("2) Cambiar tipo de una incidencia")
    print("0) Volver")
    op = input("\nSeleccione: ").strip()
    if op == "0":
        return
    if not require_creator():
        return
    if op in {"1", "2"}:
        id_sel = input("ID de la incidencia: ").strip()
        incs = [i for i in valides if i.get("id") == id_sel]
        if not incs:
            print(Fore.RED + "ID no encontrado." + Style.RESET_ALL)
            return
        nodo = next((n for n in root.findall("incidencia") if n.attrib.get("id") == id_sel), None)
        if nodo is None:
            print(Fore.RED + "Nodo XML no encontrado." + Style.RESET_ALL)
            return
        if op == "1":
            nueva = input("Nueva prioridad (Alta/Media/Baja): ").strip()
            incs[0]["prioridad"] = nueva
            prio_node = nodo.find("Prioridad_del_problema")
            if prio_node is None:
                prio_node = ET.SubElement(nodo, "Prioridad_del_problema")
            prio_node.text = nueva
        elif op == "2":
            nuevo_tipo = input("Nuevo tipo de incidencia: ").strip()
            incs[0]["tipo"] = nuevo_tipo
            tipo_node = nodo.find("Tipos_de_incidencia")
            if tipo_node is None:
                tipo_node = ET.SubElement(nodo, "Tipos_de_incidencia")
            tipo_node.text = nuevo_tipo
        safe_tree_write(tree, XML_FILE)

# =========================
# Menú principal (estético, porcentajes resaltados)
# =========================
def mostrar_menu(valides):
    while True:
        print_menu_main()
        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            print(Fore.MAGENTA + "Saliendo del menú..." + Style.RESET_ALL)
            break
        elif opcion == "1":
            menu_por_campo("tipo", "Incidencias por tipo")
        elif opcion == "2":
            menu_por_campo("prioridad", "Incidencias por prioridad")
        elif opcion == "3":
            menu_por_campo("ubicacion", "Incidencias por ubicación")
        elif opcion == "4":
            menu_estadisticas_generales()
        elif opcion == "5":
            admin_menu(valides)
        else:
            print(Fore.RED + "Opción inválida, intente de nuevo." + Style.RESET_ALL)

# Ejecutar menú
if __name__ == "__main__":
    mostrar_menu(valides)
    print(Fore.MAGENTA + "\nProcess finished with exit code 0" + Style.RESET_ALL)
#