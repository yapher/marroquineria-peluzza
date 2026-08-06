from pathlib import Path

# Carpeta del proyecto
RAIZ = Path(__file__).parent

# Archivo de salida
SALIDA = RAIZ / "Proyecto_Completo.txt"

# Carpetas a ignorar
IGNORAR_CARPETAS = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
}

# Archivos a ignorar
IGNORAR_ARCHIVOS = {
    ".DS_Store",
}

# Extensiones que se consideran texto
EXTENSIONES_TEXTO = {
    ".py", ".html", ".css", ".js", ".json",
    ".txt", ".md", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".env", ".csv", ".sql",
    ".xml", ".bat", ".sh", ".gitignore",
    ".dockerfile", ".log"
}


def dibujar_arbol(carpeta, prefijo=""):
    elementos = sorted(carpeta.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    elementos = [
        e for e in elementos
        if e.name not in IGNORAR_ARCHIVOS
        and e.name not in IGNORAR_CARPETAS
    ]

    for i, elemento in enumerate(elementos):
        ultimo = i == len(elementos) - 1
        rama = "└── " if ultimo else "├── "

        archivo.write(prefijo + rama + elemento.name + "\n")

        if elemento.is_dir():
            extension = "    " if ultimo else "│   "
            dibujar_arbol(elemento, prefijo + extension)


with open(SALIDA, "w", encoding="utf-8") as archivo:

    archivo.write("="*80 + "\n")
    archivo.write("ARBOL DEL PROYECTO\n")
    archivo.write("="*80 + "\n\n")

    archivo.write(RAIZ.name + "\n")
    dibujar_arbol(RAIZ)

    archivo.write("\n\n")
    archivo.write("="*80 + "\n")
    archivo.write("CONTENIDO DE LOS ARCHIVOS\n")
    archivo.write("="*80 + "\n\n")

    for f in sorted(RAIZ.rglob("*")):

        if not f.is_file():
            continue

        if any(parte in IGNORAR_CARPETAS for parte in f.parts):
            continue

        if f.name in IGNORAR_ARCHIVOS:
            continue

        if f.suffix.lower() not in EXTENSIONES_TEXTO and f.name not in {".gitignore", ".env"}:
            continue

        archivo.write("\n")
        archivo.write("="*80 + "\n")
        archivo.write(str(f.relative_to(RAIZ)) + "\n")
        archivo.write("="*80 + "\n\n")

        try:
            contenido = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                contenido = f.read_text(encoding="latin-1")
            except:
                contenido = "<< No se pudo leer el archivo >>"

        archivo.write(contenido)
        archivo.write("\n\n")

print(f"Archivo generado: {SALIDA}")