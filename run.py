# run.py

from app import app

# This 'app' object is now directly at the module level.
# Gunicorn will import 'run.py' and use this 'app' object.
# The 'if __name__ == "__main__":' block is removed because Gunicorn handles the server startup.