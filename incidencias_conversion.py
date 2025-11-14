#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv2xml.py
Llegir incidencies.csv -> escriure incidencies.xml (UTF-8)
No envia dades a cap servei extern (funciona localment).
"""

import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import re
from pathlib import Path

INPUT = Path("incidencies.csv")
OUTPUT = Path("incidencies.xml")


def safe_tag(name: str) -> str:
    """
    Convertir un nom de camp a una etiqueta XML vàlida (lleugera normalització).
    Exemple: "Data d'incidència" -> "Data_d_incidencia"
    """
    name = name.strip()
    # substituir espais i caràcters no alfanumèrics per underscore
    name = re.sub(r"[^\w\-\.]", "_", name, flags=re.UNICODE)
    # no començar per nombre
    if re.match(r"^\d", name):
        name = "_" + name
    return name


def prettify(elem: ET.Element) -> str:
    """Retorna XML bonic (indentat) com a string (utf-8)."""
    rough = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8")


def csv_to_xml(input_path: Path, output_path: Path, root_name="incidencies", row_name="incidencia", id_attr=None):
    if not input_path.exists():
        print(f"ERROR: {input_path} no existeix.", file=sys.stderr)
        sys.exit(1)

    with input_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        if not headers:
            print("ERROR: CSV sense capçalera.", file=sys.stderr)
            sys.exit(1)

        # construir arrel
        root = ET.Element(root_name)

        for i, row in enumerate(reader, start=1):
            # crear element de fila
            if id_attr:
                # posar un atribut id si vols (per exemple id="1")
                item = ET.SubElement(root, row_name, {id_attr: str(i)})
            else:
                item = ET.SubElement(root, row_name)

            for h in headers:
                tag = safe_tag(h)
                value = row.get(h, "")
                # crear subelement per camp
                child = ET.SubElement(item, tag)
                if value is not None:
                    # strip de control i escriure com a text
                    child.text = value.strip()

        xml_bytes = prettify(root)
        with output_path.open("wb") as f:
            f.write(xml_bytes)

    print(f"He creat: {output_path} (encoding UTF-8).")


if __name__ == "__main__":
    # Opcions ràpides: per afegir id com a atribut, canvia id_attr="id"
    csv_to_xml(INPUT, OUTPUT, root_name="incidencies", row_name="incidencia", id_attr="id")
