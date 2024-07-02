import os
import subprocess
import sys

def check_docker():
    """
    Checks if Docker is installed and accessible from the command line.

    Returns:
    bool: True if Docker is installed, False otherwise.
    """
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        print("Docker is installed. Version:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError:
        print("Docker is not installed or not in the system PATH.")
        return False

def build_docker_image(path, image_name):
    """
    Builds a Docker image from a specified directory.

    Parameters:
    path (str): The directory containing the Dockerfile and context.
    image_name (str): The name to tag the Docker image with.
    """
    try:
        subprocess.run(['sudo', 'docker', 'build', '-t', image_name, path], check=True)
        print(f"Docker image '{image_name}' built successfully from {path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")
