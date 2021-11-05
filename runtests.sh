
# Start the virtual environment since we'll be running env
# specific commands
poetry shell

# Run the unittest test module and search in "unittests" directory
coverage run -m unittest discover unittests

# Generate report of line coverage
coverage html