# procon-led

Turn off the blue **Home button LED** on a Nintendo Switch Pro Controller connected to a PC.

Steam Input and SDL3 games light that ring (it's normally the "you have a notification" indicator), and the controller keeps it on after you disconnect — sometimes until you power-cycle it. This sends the controller the same HID subcommand the Linux `hid-nintendo` driver uses to switch it off.

## Requirements

- Windows (Bluetooth or USB), Python 3.8+
- A Nintendo Switch Pro Controller (`057E:2009`), paired and awake

```powershell
pip install -r requirements.txt
```

## Usage

```powershell
python procon_led.py            # turn the Home LED off (default)
python procon_led.py --on 40    # set brightness 0-100 (useful for testing)
python procon_led.py --watch    # keep it off, re-applies every 3s
python procon_led.py --list     # show the matching HID device
python procon_led.py --selftest # verify the packet bytes, no hardware needed
```

If Steam turns the ring back on while you play, run `--watch` and leave it running.

## How it works

- Opens the HID device `VID 0x057E / PID 0x2009`.
- Sends **output report `0x01`** (rumble + subcommand) with **subcommand `0x38`** ("Set HOME Light") and payload `01 00 00 11 11` (brightness 0).
- Bluetooth writes a 49-byte report. USB writes 64 bytes after the required `0x80 0x02` handshake.
- No driver, service, or admin rights required.

The player LEDs (the four below the Home button) are a different subcommand (`0x30`) and are not touched.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Pro Controller not found` | Wake the controller (press a button) or re-pair it. Windows can keep the pairing while the HID interface is asleep. |
| `Could not write to the controller` | Close Steam, or disable **Steam → Settings → Controller → Nintendo Switch Pro Configuration Support**. Steam can hold the device open. |
| Light comes back on | Use `--watch`. Steam Input re-applies its LED state when it opens the controller. |

## Limitations

- Written and tested against a genuine Nintendo Pro Controller over Bluetooth. USB is implemented but untested.
- Third-party "Pro" pads may shut down when sent LED commands (SDL guards against this for some models), so use at your own risk.
- Only the Home LED is controlled.

## AI disclosure

This project was developed with help from DeepSeek V4.1 Flash Free through OpenCode.

The AI assistant helped produce the code, tests, and documentation under human direction. Research into the controller's HID protocol, testing against a physical Pro Controller, and final release decisions were handled and reviewed by the repository owner.

## License

MIT
