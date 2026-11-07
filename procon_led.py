#!/usr/bin/env python3
"""Turn the Nintendo Switch Pro Controller Home LED (the blue ring) off.

Protocol: HID output report 0x01, subcommand 0x38 (Set HOME Light), the same
command the Linux hid-nintendo driver and SDL use. Works over Bluetooth; USB
needs the 0x80/0x02 handshake first.

Usage:
  python procon_led.py            # turn the Home LED off (default)
  python procon_led.py --on 40    # set brightness 0-100 (handy to test)
  python procon_led.py --watch    # keep it off, re-apply every 3s
  python procon_led.py --list     # show matching HID devices
  python procon_led.py --selftest # check packet bytes, touch no hardware
"""

import argparse
import sys
import time

import hid

VID = 0x057E
PID = 0x2009
NEUTRAL_RUMBLE = bytes([0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40])
BT_PACKET = 49   # report id + 48 data bytes
USB_PACKET = 64


def make_packet(brightness, size):
    intensity = max(0, min(15, round(brightness * 15 / 100)))
    payload = bytes([0x01, intensity << 4, intensity | (intensity << 4), 0x11, 0x11])
    packet = bytearray(size)
    packet[0] = 0x01                      # output report: rumble + subcommand
    packet[1] = 0x00                      # packet number
    packet[2:10] = NEUTRAL_RUMBLE
    packet[10] = 0x38                     # subcommand: set HOME light
    packet[11:11 + len(payload)] = payload
    return bytes(packet)


def enumerate_controllers():
    return list(hid.enumerate(VID, PID))


def path_str(path):
    return path.decode(errors="replace") if isinstance(path, bytes) else str(path)


def is_usb(path):
    # Bluetooth HID paths contain the Bluetooth HID service GUID.
    return "00001124-0000-1000-8000-00805F9B34FB" not in str(path).upper()


def apply(brightness, verbose=True):
    devices = enumerate_controllers()
    if not devices:
        if verbose:
            print("Pro Controller not found. Wake it (press a button) or pair it.")
        return False

    for info in devices:
        path = info["path"]
        usb = is_usb(path)
        try:
            dev = hid.device()
            dev.open_path(path)
            try:
                if usb:
                    dev.write(bytes([0x80, 0x02]) + bytes(USB_PACKET - 2))
                    time.sleep(0.05)
                written = dev.write(make_packet(brightness, USB_PACKET if usb else BT_PACKET))
            finally:
                dev.close()
        except Exception as exc:
            if verbose:
                print(f"  skip {path_str(path)}: {exc}")
            continue

        if written and written > 0:
            if verbose:
                print(f"  sent to {path_str(path)} ({'USB' if usb else 'BT'}, {written} bytes)")
            return True
        if verbose:
            print(f"  write failed on {path_str(path)}")

    if verbose:
        print("Could not write to the controller. Close Steam or disable its "
              "Nintendo Switch Pro Controller support and try again.")
    return False


def watch(brightness):
    print("Watching for the controller. Ctrl+C to stop.")
    was_present = False
    while True:
        present = bool(enumerate_controllers())
        if present:
            # Re-apply: Steam or a game may set the LED back on.
            apply(brightness, verbose=not was_present)
            was_present = True
        else:
            if was_present:
                print("Controller disconnected.")
            was_present = False
        time.sleep(3)


def selftest():
    off = make_packet(0, BT_PACKET)
    assert len(off) == 49
    assert off[:2] == b"\x01\x00"
    assert off[2:10] == NEUTRAL_RUMBLE
    assert off[10] == 0x38
    assert off[11:16] == b"\x01\x00\x00\x11\x11"
    assert off[16:] == bytes(33)

    full = make_packet(100, USB_PACKET)
    assert len(full) == 64
    assert full[11:16] == b"\x01\xf0\xff\x11\x11"
    print("selftest ok")


def main():
    parser = argparse.ArgumentParser(description="Control the Switch Pro Controller Home LED.")
    parser.add_argument("--on", type=int, metavar="BRIGHTNESS",
                        help="turn the LED on at 0-100 brightness (default action is off)")
    parser.add_argument("--watch", action="store_true", help="keep re-applying every 3s")
    parser.add_argument("--list", action="store_true", help="list matching HID devices")
    parser.add_argument("--selftest", action="store_true", help="verify packet bytes only")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return 0

    if args.list:
        devices = enumerate_controllers()
        if not devices:
            print("No 057E:2009 HID device found.")
            return 1
        for info in devices:
            print(f"{path_str(info['path'])}  ({'USB' if is_usb(info['path']) else 'BT'})")
        return 0

    brightness = 0 if args.on is None else max(0, min(100, args.on))
    if args.watch:
        try:
            watch(brightness)
        except KeyboardInterrupt:
            print()
        return 0
    return 0 if apply(brightness) else 1


if __name__ == "__main__":
    sys.exit(main())
