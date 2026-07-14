from openvino import Core

def main():
    core = Core()

    print("=" * 60)
    print("OpenVINO Benchmark")
    print("=" * 60)

    for device in core.available_devices:
        print(f"\nDevice: {device}")

        try:
            print("Full Name :", core.get_property(device, "FULL_DEVICE_NAME"))
            print("Architecture :", core.get_property(device, "DEVICE_ARCHITECTURE"))
            print("Optimization Capabilities :", core.get_property(device, "OPTIMIZATION_CAPABILITIES"))
        except Exception as ex:
            print(f"Error reading properties: {ex}")

if __name__ == "__main__":
    main()