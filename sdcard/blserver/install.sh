#!/system/bin/sh
# DNS Controller Installation Script for Android
# This script should be run on a rooted Android device

# Check if running as root
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 
   echo "Try: su -c 'sh install.sh'"
   exit 1
fi

# Base directory
BASE_DIR="/sdcard/blserver"

# Create directory structure
echo "Creating directory structure..."
mkdir -p $BASE_DIR/app/templates
mkdir -p $BASE_DIR/app/static
mkdir -p $BASE_DIR/conf/users
mkdir -p $BASE_DIR/logs
mkdir -p $BASE_DIR/pids

# Copy files from current directory to target directory
echo "Copying files..."
cp -r app $BASE_DIR/
cp run.py $BASE_DIR/
cp README.md $BASE_DIR/

# Make run.py executable
chmod +x $BASE_DIR/run.py

# Create global DNS settings
echo "Creating default global DNS settings..."
cat > $BASE_DIR/conf/global_dns.json << EOF
{
    "default_dns": "1.1.1.1",
    "global_override_enabled": false,
    "global_override_ip": "192.168.14.190"
}
EOF

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Flask is not installed. Installing Flask..."
    pip install flask
fi

# Check if dnsmasq is installed
if ! command -v dnsmasq &> /dev/null; then
    echo "dnsmasq is not installed. Please install dnsmasq."
    exit 1
fi

# Create a launcher script
echo "Creating launcher script..."
cat > $BASE_DIR/start.sh << EOF
#!/system/bin/sh
cd $BASE_DIR
python3 run.py
EOF
chmod +x $BASE_DIR/start.sh

# Create a service script for init.d
echo "Creating service script..."
cat > /system/etc/init.d/dns_controller << EOF
#!/system/bin/sh
# DNS Controller Service
# This script starts the DNS Controller service at boot

# Start the service
su -c "cd $BASE_DIR && python3 run.py &"
EOF
chmod +x /system/etc/init.d/dns_controller

echo "Installation complete!"
echo "To start the DNS Controller manually, run: su -c 'sh $BASE_DIR/start.sh'"
echo "The service will also start automatically at boot."
echo "Open a web browser and navigate to: http://localhost:5000"
