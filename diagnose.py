import sys, os, json
sys.path.insert(0, '.')
os.environ.setdefault('DATABASE_USERNAME', 'x')
os.environ.setdefault('DATABASE_PASSWORD', 'x')
os.environ.setdefault('DATABASE_HOST', 'x')
os.environ.setdefault('DATABASE_NAME', 'x')
os.environ.setdefault('SECRET_KEY', 'x' * 32)
os.environ.setdefault('BLOCKCHAIN_ENABLED', 'False')

from app.main import app
spec = app.openapi()

schemas = spec.get('components', {}).get('schemas', {})
result = {
    "schema_count": len(schemas),
    "schema_names": list(schemas.keys()),
    "sample_register": spec['paths'].get('/api/v1/users/register', {}).get('post', {}).get('requestBody', 'MISSING'),
    "components_keys": list(spec.get('components', {}).keys()),
}
with open('docs/diagnose.json', 'w') as f:
    json.dump(result, f, indent=2)
print("done")

