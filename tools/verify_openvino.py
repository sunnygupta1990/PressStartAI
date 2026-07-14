from openvino import Core

def main():
    core = Core()

    print("=" * 60)
    print("OpenVINO Device Verification")
    print("=" * 60)

    devices = core.available_devices

    print(f"\nDetected {len(devices)} device(s):\n")

    for device in devices:
        print(f"Device: {device}")
        try:
            print(f"Name : {core.get_property(device, 'FULL_DEVICE_NAME')}")
        except Exception as ex:
            print(f"Error: {ex}")
        print("-" * 60)

if __name__ == "__main__":
    main()