import os

def load_env_local():
    """Load environment variables from env.local at project root."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(base_dir, 'env.local')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    k, sep, v = line.partition('=')
                    if sep:
                        os.environ[k.strip()] = v.strip()
