import sys
import os

# Add uk_dsa_app to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'uk_dsa_app'))

# Import and run the main app
from uk_dsa_app.app import main

if __name__ == "__main__":
    main()
