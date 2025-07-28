import sys
import subprocess
import os


def install_requirements(requirements_path="requirements.txt"):
    """
    Installs packages from a requirements.txt file using pip.

    Args:
        requirements_path (str): The path to the requirements.txt file.
    """
    print(f"Checking for '{requirements_path}'...")

    # 1. Check if the requirements file exists
    if not os.path.exists(requirements_path):
        print(f"Error: '{requirements_path}' not found.")
        print("Please ensure the requirements file is in the correct directory.")
        return

    print(f"Found '{requirements_path}'. Installing packages...")

    try:
        # 2. Use sys.executable to ensure we use the pip of the current Python environment
        #    This is the most reliable way to call pip.
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path]
        )

        print("\nSuccessfully installed all packages from requirements.txt.")
        input("Pres ENTER to exit!")
    except subprocess.CalledProcessError as e:
        print(
            f"\nAn error occurred while installing packages. Pip returned a non-zero exit code."
        )
        print(f"Error details: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


install_requirements("req.txt")
