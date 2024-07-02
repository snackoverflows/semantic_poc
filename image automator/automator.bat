@echo off
cls
echo Welcome to the Query Intent ML Model Proccess Automator for CAT.
echo Do you want to install the necessary dependencies to run this program? (y/n)
set /p userInput=

if /I "%userInput%"=="y" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

cls
echo Running the main script...
python wrapper.py

echo The main script has finished running.
pause
