from app.main import app
print(f"Total routes: {len(app.router.routes)}")
for i, route in enumerate(app.router.routes):
    print(f"[{i}] type={type(route).__name__}, path={getattr(route, 'path', None)}, methods={getattr(route, 'methods', None)}")
