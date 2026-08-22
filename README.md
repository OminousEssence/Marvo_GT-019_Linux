# Marvo_GT-019_Linux

# Run this first
sudo grubby --update-kernel=ALL --args="hid.ignore_special_drivers=1 module_blacklist=hid_betopff"

# Then the script



# Systemd service
sudo nano /etc/systemd/system/Marvo_virtual.service

# Then add this
[Unit]
Description=Marvo Virtual Gamepad Rumble Bridge
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/phoenix/Documents/Scripts/Login_scripts/SystemD/Marvo_virtual.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# Then run
sudo systemctl daemon-reload
sudo systemctl enable --now Marvo_virtual.service
