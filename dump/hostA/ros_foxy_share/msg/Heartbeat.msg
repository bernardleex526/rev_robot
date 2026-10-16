# Component heartbeat status message
# Used for monitoring component liveness and detecting timeout faults

builtin_interfaces/Time timestamp      # HeartBeat timestamp
string resource_id                     # Resource ID (support multiple instances, e.g., "motion_planner_0")
uint8 status                           # Status code: 0=normal, 1=degraded, 2=fault
string details                         # Optional additional info (JSON format)
