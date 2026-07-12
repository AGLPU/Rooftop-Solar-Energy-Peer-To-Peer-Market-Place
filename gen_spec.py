import sys, os, json

sys.path.insert(0, '.')

# Set dummy env vars so app loads without real DB/blockchain
os.environ.setdefault('DATABASE_USERNAME', 'x')
os.environ.setdefault('DATABASE_PASSWORD', 'x')
os.environ.setdefault('DATABASE_HOST', 'x')
os.environ.setdefault('DATABASE_NAME', 'x')
os.environ.setdefault('SECRET_KEY', 'x'*32)
os.environ.setdefault('BLOCKCHAIN_ENABLED', 'False')

from app.main import app

spec = app.openapi()

os.makedirs('docs', exist_ok=True)
with open('docs/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2)

print(f"✅ Saved docs/openapi.json — {len(spec['paths'])} endpoints")

