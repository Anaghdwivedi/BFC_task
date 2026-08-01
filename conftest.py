import sys
import os

# Add the project root to sys.path so pytest can resolve `import backend.*`
# regardless of the working directory from which pytest is invoked.
sys.path.insert(0, os.path.dirname(__file__))
