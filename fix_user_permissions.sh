# First, let's identify the service user (often www-data) and set variables
SERVICE_USER=$(ps aux | grep -E 'apache|nginx|www-data' | grep -v 'grep' | head -1 | awk '{print $1}')
PROJECT_DIR="/home/wfz/xai_health_coach"
VENV_DIR="$PROJECT_DIR/venv"  # adjust if your venv is in a different location

# Create a group if it doesn't exist (e.g., 'webdev')
sudo groupadd webdev 2>/dev/null

# Add both users to the group
sudo usermod -a -G webdev wfzimmerman
sudo usermod -a -G webdev $SERVICE_USER

# Set the group ownership and permissions
sudo chown -R wfzimmerman:webdev $PROJECT_DIR
sudo chmod -R 775 $PROJECT_DIR

# Ensure new files inherit group permissions
sudo chmod g+s $PROJECT_DIR
find $PROJECT_DIR -type d -exec sudo chmod g+s {} \;

# Set specific permissions for the virtual environment
if [ -d "$VENV_DIR" ]; then
    sudo chown -R wfzimmerman:webdev $VENV_DIR
    sudo chmod -R 775 $VENV_DIR
fi

# Make sure .git directory is properly handled
if [ -d "$PROJECT_DIR/.git" ]; then
    sudo chown -R wfzimmerman:webdev $PROJECT_DIR/.git
    sudo chmod -R 775 $PROJECT_DIR/.git
fi

# Verify permissions
echo "Checking permissions..."
ls -la $PROJECT_DIR
echo "Checking .git permissions..."
ls -la $PROJECT_DIR/.git
