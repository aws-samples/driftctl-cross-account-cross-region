#!/bin/bash
# Script to update requirements-lock.txt with exact versions
# This should be run when requirements.txt is updated

set -e

echo "Creating temporary virtual environment..."
python3 -m venv temp_lock_env
source temp_lock_env/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Generating requirements-lock.txt..."
pip freeze > requirements-lock.txt

echo "Cleaning up..."
deactivate
rm -rf temp_lock_env

echo "✅ requirements-lock.txt has been updated!"
echo "📝 Please commit the updated requirements-lock.txt file"
