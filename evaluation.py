#!/usr/bin/env python3
"""
Easy evaluation runner - run this from project root
"""

import os
import sys

# Add the current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now run the evaluation
from src.evaluation.run_evaluation import main

if __name__ == "__main__":
    main()