"""
Generates docs/api-docs.html — a single standalone file that looks
exactly like http://localhost:8000/docs (Swagger UI).

Share this ONE file with your team. No server needed to open it.
Just double-click api-docs.html in any browser.
"""
import sys, os, json, uuid
from datetime import datetime, timezone

sys.path.insert(0, '.')

os.environ.setdefault('DATABASE_USERNAME', 'x')
os.environ.setdefault('DATABASE_PASSWORD', 'x')
os.environ.setdefault('DATABASE_HOST', 'x')
os.environ.setdefault('DATABASE_NAME', 'x')
os.environ.setdefault('SECRET_KEY', 'x' * 32)
os.environ.setdefault('BLOCKCHAIN_ENABLED', 'False')

from app.main import app

spec = app.openapi()

# ── Inject examples into every schema so fields are visible in Swagger UI ──
SAMPLE_VALUES = {
    "string":  "string",
    "integer": 1,
    "number":  1.0,
    "boolean": True,
}

FORMAT_VALUES = {
    "uuid":      str(uuid.uuid4()),
    "date-time": datetime.now(timezone.utc).isoformat(),
    "email":     "user@example.com",
    "password":  "StrongPass@123",
}

# Known field-name overrides for realistic examples
FIELD_EXAMPLES = {
    "email":           "seller@example.com",
    "username":        "solar_seller_01",
    "password":        "StrongPass@123",
    "full_name":       "John Solar",
    "phone_number":    "+1-416-555-0100",
    "address":         "123 Sunny Lane",
    "city":            "Toronto",
    "country":         "Canada",
    "role":            "SELLER",
    "wallet_address":  "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "energy_kwh":      100,
    "price_per_kwh":   "0.000500",
    "title":           "Rooftop Solar — 100 kWh Available",
    "description":     "Clean solar energy from my rooftop panels in Toronto.",
    "location":        "Toronto, Ontario, Canada",
    "listing_id":      str(uuid.uuid4()),
    "seller_id":       str(uuid.uuid4()),
    "buyer_id":        str(uuid.uuid4()),
    "id":              str(uuid.uuid4()),
    "total_price":     "50.000000",
    "status":          "active",
    "blockchain_tx_hash": "0xabc123def456...",
    "consume_tx_hash":    "0xdef789abc012...",
    "token":           "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type":      "bearer",
    "message":         "Operation completed successfully",
    "amountKwh":       100,
}

def make_example(schema: dict, schemas: dict, depth: int = 0) -> object:
    """Recursively build an example object from a JSON Schema."""
    if depth > 5:
        return {}

    # Resolve $ref
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return make_example(schemas.get(ref_name, {}), schemas, depth + 1)

    # allOf / anyOf / oneOf
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema:
            return make_example(schema[key][0], schemas, depth + 1)

    s_type = schema.get("type")

    if s_type == "object" or "properties" in schema:
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if prop_name in FIELD_EXAMPLES:
                result[prop_name] = FIELD_EXAMPLES[prop_name]
            else:
                fmt = prop_schema.get("format", "")
                typ = prop_schema.get("type", "string")
                result[prop_name] = FORMAT_VALUES.get(fmt) or SAMPLE_VALUES.get(typ, "string")
        return result

    if s_type == "array":
        items = schema.get("items", {})
        return [make_example(items, schemas, depth + 1)]

    if "enum" in schema:
        return schema["enum"][0]

    fmt = schema.get("format", "")
    if fmt in FORMAT_VALUES:
        return FORMAT_VALUES[fmt]

    return SAMPLE_VALUES.get(s_type, "string")


schemas = spec.get("components", {}).get("schemas", {})

# Inject example into every schema
for schema_name, schema_body in schemas.items():
    if "example" not in schema_body:
        example = make_example(schema_body, schemas)
        if example:
            schema_body["example"] = example

# Inject examples into requestBody content of every endpoint
for path, methods in spec.get("paths", {}).items():
    for method, details in methods.items():
        rb = details.get("requestBody", {})
        content = rb.get("content", {})
        for media_type, media_obj in content.items():
            if "example" not in media_obj and "schema" in media_obj:
                ex = make_example(media_obj["schema"], schemas)
                if ex:
                    media_obj["example"] = ex

spec_json = json.dumps(spec, indent=2)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{spec['info']['title']} - API Docs</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css" />
  <style>
    body {{ margin: 0; background: #fafafa; }}
    .swagger-ui .topbar .download-url-wrapper {{ display: none; }}
    /* keep models section always visible */
    .swagger-ui .model-box {{ display: block !important; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-standalone-preset.js"></script>
  <script>
    const spec = {spec_json};

    window.onload = function () {{
      SwaggerUIBundle({{
        spec: spec,
        dom_id: "#swagger-ui",
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout",
        deepLinking: true,
        displayRequestDuration: true,
        defaultModelsExpandDepth: 5,
        defaultModelExpandDepth: 5,
        defaultModelRendering: "example",
        showExtensions: true,
        showCommonExtensions: true,
        tryItOutEnabled: true,
        persistAuthorization: true,
        validatorUrl: null,
        requestSnippetsEnabled: true,
      }});
    }};
  </script>
</body>
</html>"""

os.makedirs('docs', exist_ok=True)
out = os.path.join('docs', 'api-docs.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] Saved  {out}  ({len(html):,} bytes, {len(spec['paths'])} endpoints)")
print(f"[>>] Open  docs/api-docs.html  in any browser -- no server needed")

