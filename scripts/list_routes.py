"""List all registered routes in the Flask application"""
from app import app

print("="*80)
print("REGISTERED ROUTES")
print("="*80)
print()

routes = []
with app.app_context():
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                'path': rule.rule
            })

# Group by path prefix
api_routes = [r for r in routes if r['path'].startswith('/api/')]
auth_routes = [r for r in routes if '/login' in r['path'] or '/logout' in r['path'] or '/auth' in r['path']]
admin_routes = [r for r in routes if '/admin' in r['path'] or '/settings' in r['path']]
other_routes = [r for r in routes if r not in api_routes and r not in auth_routes and r not in admin_routes]

print(f"API Routes ({len(api_routes)}):")
print("-"*80)
for route in sorted(api_routes, key=lambda x: x['path']):
    print(f"  {route['path']:50} [{route['methods']}]")

print(f"\nAuthentication Routes ({len(auth_routes)}):")
print("-"*80)
for route in sorted(auth_routes, key=lambda x: x['path']):
    print(f"  {route['path']:50} [{route['methods']}]")

print(f"\nAdmin/Settings Routes ({len(admin_routes)}):")
print("-"*80)
for route in sorted(admin_routes, key=lambda x: x['path']):
    print(f"  {route['path']:50} [{route['methods']}]")

print(f"\nOther Routes ({len(other_routes)}):")
print("-"*80)
for route in sorted(other_routes, key=lambda x: x['path'])[:20]:
    print(f"  {route['path']:50} [{route['methods']}]")

if len(other_routes) > 20:
    print(f"  ... and {len(other_routes) - 20} more routes")

print(f"\n{'='*80}")
print(f"Total: {len(routes)} routes")
print("="*80)
