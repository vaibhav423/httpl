# DNS Controller

A web-based DNS controller for managing DNS configurations for multiple users on a rooted Android device. This application allows you to:

- Scan the network for connected devices
- Create individual DNS configurations for each device
- Configure global DNS settings that apply to all devices
- Override DNS settings for specific devices
- Create custom domain-to-IP mappings for specific devices

## Features

- **Network Scanner**: Automatically discover devices on your network
- **On-Demand DNS Creation**: Create DNS configurations only when needed
- **Global DNS Override**: Set a global IP address for all DNS resolutions
- **Per-User DNS Override**: Override the global settings for specific users
- **Custom Domain Mappings**: Map specific domains to specific IP addresses
- **Web Interface**: Easy-to-use web interface for managing all settings

## Requirements

- Rooted Android device
- Python 3.6+
- Flask
- dnsmasq
- iptables

## Installation

1. Clone this repository to your Android device:
   ```
   git clone https://github.com/yourusername/dns-controller.git /sdcard/blserver
   ```

2. Install the required Python packages:
   ```
   pip install flask
   ```

3. Make sure dnsmasq is installed on your device:
   ```
   which dnsmasq
   ```

## Usage

1. Start the Flask application:
   ```
   cd /sdcard/blserver
   python run.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Use the web interface to:
   - Configure global DNS settings
   - Scan for devices on your network
   - Create DNS configurations for specific devices
   - Configure per-device DNS settings

## How It Works

1. **Network Scanning**: The application scans your network using ARP or ping to discover connected devices.

2. **DNS Configuration**: For each device you want to manage, the application:
   - Creates a unique dnsmasq configuration
   - Assigns a unique port for the dnsmasq instance
   - Configures DNS resolution based on your settings

3. **Traffic Redirection**: The application uses iptables to redirect DNS traffic from specific devices to their corresponding dnsmasq instance.

4. **DNS Resolution**: Depending on your settings, DNS queries are either:
   - Resolved normally using a default DNS server (e.g., 1.1.1.1)
   - Redirected to a specific IP address (global or per-device override)
   - Resolved based on custom domain mappings

## File Structure

```
/sdcard/blserver/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # Web routes
│   ├── dns_manager.py       # DNS management functions
│   ├── network_scanner.py   # Device scanning functionality
│   ├── templates/           # HTML templates
│   │   ├── index.html       # Main dashboard
│   │   └── user.html        # User settings
│   └── static/              # CSS, JS, images
├── conf/
│   ├── users/               # User-specific configurations
│   └── global.conf          # Global settings
├── logs/                    # Log files
├── pids/                    # PID files
└── run.py                   # Main application entry point
```

## Security Considerations

This application requires root access to:
- Run dnsmasq instances
- Configure iptables rules
- Access network interfaces

Use this application only on secure networks that you control.

## Troubleshooting

- **DNS not working for a device**: Check if the dnsmasq instance is running and iptables rules are correctly set.
- **Cannot scan network**: Make sure you have the necessary permissions to access network interfaces.
- **Web interface not accessible**: Check if the Flask application is running and listening on the correct port.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
