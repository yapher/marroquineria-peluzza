# debug_imports.py
import sys

print("="*60)
print("🔍 DIAGNÓSTICO DE IMPORTACIONES")
print("="*60)

# 1. Probar importar la app
print("\n[1/5] Importando app...")
try:
    from app import create_app
    print("✅ app importada correctamente")
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)

# 2. Probar importar el blueprint
print("\n[2/5] Importando blueprint checkout...")
try:
    from app.blueprints.checkout import checkout_bp
    print(f"✅ checkout_bp importado: {checkout_bp}")
    print(f"   Defered functions: {checkout_bp.deferred_functions}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# 3. Probar importar routes directamente
print("\n[3/5] Importando routes.py directamente...")
try:
    from app.blueprints.checkout import routes
    print(f"✅ routes.py importado")
    print(f"   Funciones en routes: {[x for x in dir(routes) if not x.startswith('_')]}")
except Exception as e:
    print(f"❌ ERROR al importar routes.py:")
    import traceback
    traceback.print_exc()

# 4. Probar importar Cart
print("\n[4/5] Importando Cart service...")
try:
    from app.services.cart_service import Cart
    print(f"✅ Cart importado: {Cart}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# 5. Probar importar Product
print("\n[5/5] Importando Product model...")
try:
    from app.models import Product
    print(f"✅ Product importado: {Product}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)