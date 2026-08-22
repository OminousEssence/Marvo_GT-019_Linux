import time
import select
import glob
import os
from evdev import UInput, ecodes, InputDevice, AbsInfo

# Physical ShanWan Button -> Virtual Xbox 360 Button Map
BUTTON_MAP = {
    304: ecodes.BTN_A,       # A
    305: ecodes.BTN_B,       # B
    307: ecodes.BTN_X,       # X
    308: ecodes.BTN_Y,       # Y
    310: ecodes.BTN_TL,      # LB (Left Shoulder)
    311: ecodes.BTN_TR,      # RB (Right Shoulder)
    314: ecodes.BTN_SELECT,  # Back / Select
    315: ecodes.BTN_START,   # Start
    316: ecodes.BTN_MODE,    # Home / Guide
    317: ecodes.BTN_THUMBL,  # L3 (Left Stick Click)
    318: ecodes.BTN_THUMBR,  # R3 (Right Stick Click)
}

# Physical ShanWan Raw Axis -> Virtual Xbox 360 Axis Map
AXIS_MAP = {
    0:  ecodes.ABS_X,        # Physical Left Stick X
    1:  ecodes.ABS_Y,        # Physical Left Stick Y
    2:  ecodes.ABS_RX,       # Physical Right Stick X
    5:  ecodes.ABS_RY,       # Physical Right Stick Y
    10: ecodes.ABS_Z,        # Physical Left Trigger (LT)
    9:  ecodes.ABS_RZ,       # Physical Right Trigger (RT)
    16: ecodes.ABS_HAT0X,    # Physical D-Pad X
    17: ecodes.ABS_HAT0Y,    # Physical D-Pad Y
}

# Virtual Gamepad Capabilities
cap = {
    ecodes.EV_KEY: [
        ecodes.BTN_A, ecodes.BTN_B, ecodes.BTN_X, ecodes.BTN_Y,
        ecodes.BTN_TL, ecodes.BTN_TR,
        ecodes.BTN_SELECT, ecodes.BTN_START, ecodes.BTN_MODE,
        ecodes.BTN_THUMBL, ecodes.BTN_THUMBR
    ],
    ecodes.EV_ABS: [
        (ecodes.ABS_X, AbsInfo(value=128, min=0, max=255, fuzz=0, flat=15, resolution=0)),
        (ecodes.ABS_Y, AbsInfo(value=128, min=0, max=255, fuzz=0, flat=15, resolution=0)),
        (ecodes.ABS_RX, AbsInfo(value=128, min=0, max=255, fuzz=0, flat=15, resolution=0)),
        (ecodes.ABS_RY, AbsInfo(value=128, min=0, max=255, fuzz=0, flat=15, resolution=0)),
        (ecodes.ABS_Z, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
        (ecodes.ABS_RZ, AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)),
        (ecodes.ABS_HAT0X, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
        (ecodes.ABS_HAT0Y, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
    ],
    ecodes.EV_FF: [ecodes.FF_RUMBLE]
}

def find_hidraw_for_event(event_path):
    # Locates matching /dev/hidraw node via sysfs hierarchy
    event_name = os.path.basename(event_path)
    base = f"/sys/class/input/{event_name}/device"
    for depth in ["", "..", "../.."]:
        matches = glob.glob(os.path.join(base, depth, "hidraw", "hidraw*"))
        if matches:
            return f"/dev/{os.path.basename(matches[0])}"
    return None

def find_controller_nodes():
    # Scans /dev/input/event* for physical controller matching input capabilities
    for dev_path in sorted(glob.glob("/dev/input/event*")):
        try:
            dev = InputDevice(dev_path)
            # Skip virtual Xbox controller
            if dev.info.vendor == 0x045e and dev.info.product == 0x028e:
                continue

            caps = dev.capabilities()
            if ecodes.EV_ABS in caps and ecodes.EV_KEY in caps:
                abs_codes = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                key_codes = caps[ecodes.EV_KEY]
                # Controller has ABS_X (axis 0) and physical Button 304 (A)
                if 0 in abs_codes and 304 in key_codes:
                    hidraw_node = find_hidraw_for_event(dev_path)
                    return dev_path, hidraw_node
        except Exception:
            pass
    return None, None

def send_hid_rumble(hidraw_node, strong, weak):
    if not hidraw_node:
        return
    try:
        with open(hidraw_node, "wb") as f:
            f.write(bytes([0x02, 0x08, strong, weak, 0xFF, 0x00, 0x00, 0x00]))
    except Exception:
        pass

def stop_hid_rumble(hidraw_node):
    if not hidraw_node:
        return
    try:
        with open(hidraw_node, "wb") as f:
            f.write(bytes([0x02, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
    except Exception:
        pass

print("Starting Marvo Virtual Gamepad Daemon...")

while True:
    real_dev = None
    ui = None
    event_path, hidraw_path = None, None

    # 1. Dynamically discover controller nodes
    while event_path is None:
        event_path, hidraw_path = find_controller_nodes()
        if event_path is None:
            time.sleep(5)

    try:
        # 2. Grab physical controller first to isolate it from system
        real_dev = InputDevice(event_path)
        real_dev.grab()

        # 3. Create virtual Xbox 360 controller
        ui = UInput(cap, name="Microsoft X-Box 360 pad", vendor=0x045e, product=0x028e)
        print(f"Connected: {event_path} ({real_dev.name}) | Hidraw: {hidraw_path}")

        # 4. Startup Haptic Pulse (0.2s at ~10% power)
        send_hid_rumble(hidraw_path, 30, 30)
        time.sleep(0.20)
        stop_hid_rumble(hidraw_path)

        effects = {}

        # 5. Main event translation loop
        while True:
            r, _, _ = select.select([real_dev.fd, ui.fd], [], [], 0.1)

            if r:
                if real_dev.fd in r:
                    for event in real_dev.read():
                        if event.type == ecodes.EV_KEY:
                            if event.code in BUTTON_MAP:
                                ui.write(ecodes.EV_KEY, BUTTON_MAP[event.code], event.value)
                                ui.syn()
                        elif event.type == ecodes.EV_ABS:
                            if event.code in AXIS_MAP:
                                ui.write(ecodes.EV_ABS, AXIS_MAP[event.code], event.value)
                                ui.syn()

                if ui.fd in r:
                    for event in ui.read():
                        if event.type == ecodes.EV_UINPUT:
                            if event.code == ecodes.UI_FF_UPLOAD:
                                upload = ui.begin_upload(event.value)
                                effect = upload.effect
                                if effect.type == ecodes.FF_RUMBLE:
                                    strong = effect.u.ff_rumble_effect.strong_magnitude >> 8
                                    weak = effect.u.ff_rumble_effect.weak_magnitude >> 8
                                    effects[effect.id] = (strong, weak)
                                upload.retval = 0
                                ui.end_upload(upload)
                            elif event.code == ecodes.UI_FF_ERASE:
                                erase = ui.begin_erase(event.value)
                                if erase.effect_id in effects:
                                    del effects[erase.effect_id]
                                erase.retval = 0
                                ui.end_erase(erase)

                        elif event.type == ecodes.EV_FF:
                            if event.value > 0:
                                strong, weak = effects.get(event.code, (255, 255))
                                send_hid_rumble(hidraw_path, strong, weak)
                            else:
                                stop_hid_rumble(hidraw_path)

    except (OSError, FileNotFoundError, Exception) as e:
        print(f"Controller disconnected or error ({e}). Cleaning up...")
    finally:
        if real_dev:
            try:
                real_dev.ungrab()
            except Exception:
                pass
        if ui:
            try:
                ui.close()
            except Exception:
                pass
        time.sleep(5)
