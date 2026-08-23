# Marvo_GT-019_Linux

# Run this first
`sudo grubby --update-kernel=ALL --args="hid.ignore_special_drivers=1 module_blacklist=hid_betopff"`

# Then the script



# (Automatic startup) Systemd service
Run
`sudo nano /etc/systemd/system/Marvo_virtual.service`

Then add this
```[Unit]
Description=Marvo Virtual Gamepad Rumble Bridge
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/phoenix/Documents/Scripts/Login_scripts/SystemD/Marvo_virtual.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then run
`sudo systemctl daemon-reload
sudo systemctl enable --now Marvo_virtual.service`

# (Optional) Hiding the actual controller from Steam and games
Find the physical controller's Vendor ID (VID) and Product ID (PID):
`lsusb`
(example - if it shows ID 20bc:5500, your VID is 0x20bc and PID is 0x5500.)

Add the environment variable to the system configuration
`sudo nano /etc/environment`

Add this line at the bottom
`SDL_GAMECONTROLLER_IGNORE_DEVICES="0x20bc/0x5500"`
