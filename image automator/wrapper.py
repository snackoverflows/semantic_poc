from csv_merger_module import process_csv_files, find_soft_duplicates, find_hard_duplicates
from file_generator_module import index_data, generate_files, set_client
from image_builder_module import build_docker_image, check_docker

import os
import sys

option_description = {
    1: """Index 6 months of data into Elasticsearch.
==========================================================================================
Notes:         
- This process might take a long time (around 18 hours)
==========================================================================================
Dependencies:  
- Elasticsearch installed and running.
- File with 6 months of queries.
==========================================================================================
Input:            
- Path of the file with 6 months of queries.
- Elasticsearch server address e.g. http://localhost:9200
==========================================================================================            
Output:        
- Index with vector embeddings.
==========================================================================================""",

    2: """Generate automated CSV files.
==========================================================================================
Dependencies:
- Elasticsearch installed and running.
- Index with vector embeddings in place
    - By executing step 1.
    - Or by sideloading the index using elasticdump.
==========================================================================================
Input:
- Path where the output files will be stored.
- Elasticsearch server address.
==========================================================================================
Output:         
- Automated CSV files
==========================================================================================""",

    3: """Generate training, test, and validation datasets (by merging manual and automated categories CSV files).
==========================================================================================
Notes:             
- Before starting, add the manual CSV files to the source folder.
==========================================================================================
Dependencies:   
- Automated CSV files (By running Option 2 from the main menu)
- Manual CSV files
==========================================================================================
Input:             
- Path to the folder where CSV files are stored (by default 'output')
==========================================================================================
Output :        
- Training.csv, test.csv, and validation.csv
==========================================================================================""",

    4: """Build Image.
==========================================================================================
Dependencies:    
- Docker engine installed.
- A folder containing the following image files:
    - cat-classifier (folder containing ML model)
    - CatPredict.py (python wrapper)
    - Dockerfile
    - requirements.txt
==========================================================================================
Input:            
- Path to the folder where the files are located.
- Image name and image tag.
==========================================================================================                
Output:           
- Image is created in Docker.
==========================================================================================""",
}

def ensure_directory_exists(directory="output"):
    """
    Checks if the specified directory exists.

    Parameters:
    directory (str): The directory to check (default is "output").

    Returns:
    bool: True if the directory exists, False otherwise.
    """
    if os.path.exists(directory):
        print(f"Directory '{directory}' exists.")
        return True
    else:
        print(f"Directory '{directory}' not found.")
        return False

def ensure_output_has_files(directory="output"):
    """
    Checks if the specified directory contains CSV files.

    Parameters:
    directory (str): The directory to check (default is "output").

    Returns:
    bool: True if the directory contains CSV files, False otherwise.
    """
    files = [f for f in os.listdir(directory) if f.endswith(".csv")]
    if not files:
        print(f"No CSV files found in directory '{directory}'.")
        return False
    return True

def display_menu():
    """
    Displays the main menu options.
    """
    print("==========================================================================================")
    print("CAT Query Intent ML Model Process Automator")
    print("==========================================================================================")
    print("Menu Options:")
    print("1. Index 6 months of data into Elasticsearch.")
    print("2. Generate automated CSV files.")
    print("3. Generate training, test, and validation files.")
    print("4. Build ML model Docker image.")
    print("5. Exit")
    print("==========================================================================================")

def get_user_choice():
    """
    Prompts the user to select a menu option.

    Returns:
    int: The user's choice (1-5).
    """
    while True:
        try:
            choice = int(input("Please select an option (1-5): "))
            if 1 <= choice <= 5:
                return choice
            else:
                print("Invalid choice. Please select a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 5.")

def confirm_choice(choice):
    """
    Asks the user to confirm their choice.

    Parameters:
    choice (int): The user's choice.

    Returns:
    bool: True if the user confirms their choice, False otherwise.
    """
    while True:
        print("\n" + option_description[choice])
        confirmation = input(f"You selected option {choice}. Are you sure you want to proceed? (y/n): ").strip().lower()
        if confirmation in ['y', 'n']:
            return confirmation == 'y'
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def ask_input(choice):
    """
    Prompts the user for necessary inputs based on their choice and executes the corresponding process.

    Parameters:
    choice (int): The user's choice.
    """
    if choice == 1:
        while True:
            files_path = input("Enter the path of the file with 6 months of queries: ")
            elastic_address = input("Enter the Elasticsearch address (default: http://localhost:9200): ").strip()
            elastic_address = elastic_address or "http://localhost:9200"

            if ensure_directory_exists(files_path) and set_client(elastic_address):
                index_data(files_path)
                print("Processing completed successfully.")
                return
            else:
                if not retry_inputs():
                    break

    elif choice == 2:
        while True:
            output_path = input("Enter the path where the files will be stored (by default: output): ").strip()
            output_path = output_path or "output"

            elastic_address = input("Enter the Elasticsearch address (by default: http://localhost:9200): ").strip()
            elastic_address = elastic_address or "http://localhost:9200"

            if ensure_directory_exists(output_path) and set_client(elastic_address):
                generate_files(output_path)
                print("Processing completed successfully.")
                return
            else:
                if not retry_inputs():
                    break

    elif choice == 3:
        while True:
            files_path = input("Enter the path to the folder where CSV files are stored (default is 'output'): ").strip()
            files_path = files_path or "output"

            if ensure_directory_exists(files_path) and ensure_output_has_files(files_path):
                process_csv_files(files_path)
                find_hard_duplicates()
                print("Processing completed successfully.")
                break
            else:
                if not retry_inputs():
                    break

    elif choice == 4:
        while True:
            if check_docker():
                files_path = input("Enter the path to the folder where the files are located (./src by default):  ").strip()
                files_path = files_path or "./src"

                image_name = input("Enter image name:tag (query_intent:latest by default): ").strip()
                image_name = image_name or "query_intent:latest"
                if ensure_directory_exists(files_path):
                    build_docker_image(files_path, image_name)
                    print("Processing completed successfully.")
                    break
                else:
                    if not retry_inputs():
                        break

def clear_terminal():
    """
    Clears the terminal screen.
    """
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def retry_inputs():
    """
    Asks the user if they want to retry entering inputs.

    Returns:
    bool: True if the user wants to retry, False otherwise.
    """
    confirmation = input("Do you want to enter the inputs again? (y/n): ").strip().lower()
    if confirmation == 'n':
        print("Going back to main menu.")
        clear_terminal()
        return False
    elif confirmation != 'y':
        print("Invalid input. Please enter 'y' or 'n'.")
    clear_terminal()
    return True

def main():
    """
    Main function that runs the program.
    """
    while True:
        display_menu()
        choice = get_user_choice()
        clear_terminal()
        print(f"You have selected option {choice}.")

        if choice == 5:
            print("Exiting the program. Goodbye!")
            break

        if confirm_choice(choice):
            clear_terminal()
            print(f"You have proceeded with option {choice}.")
            ask_input(choice)
        else:
            print("Operation cancelled.")
            clear_terminal()

if __name__ == "__main__":
    main()
