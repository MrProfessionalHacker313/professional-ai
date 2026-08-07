import os
from app.config import settings

frontend_out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'out')
print('frontend_out_dir:', frontend_out_dir)
print('exists:', os.path.exists(frontend_out_dir))
if os.path.exists(frontend_out_dir):
    files = os.listdir(frontend_out_dir)
    print('file count:', len(files))
    print('sample files:', files[:10])
