import sys
sys.path.insert(0, r'C:\Users\GrafiX\Desktop\professional-ai\backend')
from app.main import app
print(f"app.routes: {len(app.routes)}")
for i, route in enumerate(app.routes):
    print(f"[{i}] type={type(route).__name__}, path={getattr(route, 'path', None)}")
