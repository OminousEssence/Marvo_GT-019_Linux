# Marvo_GT-019_Linux

# Run this first
```
sudo grubby --update-kernel=ALL --args="hid.ignore_special_drivers=1 module_blacklist=hid_betopff"
```
- module_blacklist=hid_betopff - This will disable the default betop driver that gets assigned to this controller.
- hid.ignore_special_drivers=1 - This will disable any device-specific drivers from loading, so use with caution. I wasn't able to make this work without this argument, as the controller wouldn't turn on without it. You may try without it to see if it works for you.

Then run the Python script. If it works as intended, you'll feel a short rumble. If it works, that's about it; the next steps are for automating and removing the original controller entry. If it doesn't work, open an issue; I'll try to help



# (Automatic startup) Systemd service
Run
```
sudo nano /etc/systemd/system/Marvo_virtual.service
```

Then add this
```
[Unit]
Description=Marvo Virtual Gamepad Daemon
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/phoenix/Documents/Scripts/Login_scripts/SystemD/Marvo_virtual.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
(Change the script location to where your Python script is. /home/phoenix/Documents/Scripts/Login_scripts/SystemD/Marvo_virtual.py this is my location).
Save (Ctrl+O - Enter - Ctrl+X)

Then run
```
sudo systemctl daemon-reload
sudo systemctl enable --now Marvo_virtual.service
```
Now it should automatically start at system startup, and you'll feel the short rumble when it starts

# (Optional) Hiding the actual controller from Steam and games
Find the physical controller's Vendor ID (VID) and Product ID (PID):
```
lsusb
```
(example - if it shows ID 20bc:5500, your VID is 0x20bc and PID is 0x5500.)

Add the environment variable to the system configuration
```
sudo nano /etc/environment
```

Add this line at the bottom
```
SDL_GAMECONTROLLER_IGNORE_DEVICES="0x20bc/0x5500"
```
Save (Ctrl+O - Enter - Ctrl+X), then restart
