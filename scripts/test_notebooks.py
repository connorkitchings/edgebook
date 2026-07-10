# scripts/test_notebooks.py

import os
import sys

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

NOTEBOOK_DIR = "notebooks"


def main():
    notebook_files = [
        os.path.join(NOTEBOOK_DIR, f)
        for f in os.listdir(NOTEBOOK_DIR)
        if f.endswith(".ipynb")
    ]

    if not notebook_files:
        print("No notebooks found to test.")
        return

    print(f"Found notebooks to test: {notebook_files}")

    for notebook_filename in sorted(notebook_files):
        print(f"--- Testing {notebook_filename} ---")
        with open(notebook_filename) as f:
            nb = nbformat.read(f, as_version=4)

        # The preprocessor that executes the notebook
        # The `timeout` is the max time (in seconds) each cell is allowed to run
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

        try:
            # The second argument is a dict of metadata, which we can leave empty
            ep.preprocess(nb, {"metadata": {"path": NOTEBOOK_DIR}})
        except Exception as e:
            print(f"\nERROR: Execution of {notebook_filename} failed.")
            print(f"Error details: {e}")
            sys.exit(1)

        print(f"--- {notebook_filename} passed ---")

    print("\nAll notebooks executed successfully!")


if __name__ == "__main__":
    main()
