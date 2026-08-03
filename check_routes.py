# check_routes.py
from app import create_app

app = create_app('development')

print("\n" + "="*60)
print("🔍 RUTAS REGISTRADAS EN FLASK (Buscando 'checkout' o 'agregar'):")
print("="*60)

found = False
for rule in app.url_map.iter_rules():
    if 'checkout' in rule.rule.lower() or 'agregar' in rule.rule.lower():
        methods = ", ".join([m for m in rule.methods if m not in ['HEAD', 'OPTIONS']])
        print(f"✅ {methods.ljust(6)} | {rule.rule.ljust(30)} | {rule.endpoint}")
        found = True

if not found:
    print("❌ NO SE ENCONTRÓ NINGUNA RUTA DE 'checkout' o 'agregar'.")
    print("Esto significa que el blueprint NO se está cargando.")

print("="*60 + "\n")