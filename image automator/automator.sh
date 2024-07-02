#!/bin/bash
export CUDA_VISIBLE_DEVICES=""

clear
echo "Welcome to the Query Intent ML Model Proccess Automator for CAT."
echo "Do you want to install the necessary dependencies to run this program? (y/n)"
read userInput

if [ "$userInput" == "y" ] || [ "$userInput" == "Y" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

clear
echo "Running the main script..."
python3 wrapper.py

echo "The main script has finished running."