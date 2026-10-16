# Fault event message for system faults
# Fault Code Categories (Revised)
# 0x80xx: Joints (motors, drivers, encoders, IMU, etc.)
# 0x81xx: Battery (cells, BMS, voltage, current, temperature, etc.)
# 0x82xx: Mainboard (CPU, memory, storage, network, system time, etc.)
# 0x83xx: Peripherals (LiDAR, cameras, buttons, RTK, handheld devices, etc.)
# 0x84xx: Motion control (manual control & autonomous control)
# 0x85xx: Charging (autonomous and manual charging scenarios)
# 0x86xx: System monitoring (heartbeats, process liveness, module responsiveness, etc.)

builtin_interfaces/Time timestamp  # Timestamp of fault occurrence
string name                        # Fault name; unique across types, identical for same-type faults
uint32 code                        # Fault code; unique across types, identical for same-type faults
string type                        # Event type: State type (start/end/update), pulse type (pulse)
string severity                    # Severity level: "warn", "error", or "fatal"
string[] sources                   # Resource IDs; array of source IDs for aggregated instances of the same fault code
string details                     # Additional data in compact JSON format
