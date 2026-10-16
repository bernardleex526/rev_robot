# NetworkStatus.msg - Enhanced for robust anomaly detection

builtin_interfaces/Time timestamp      # Data acquisition time
string resource_id                     # e.g., "Network_eth0"

# Operational state
bool is_up                             # true if link is up (from operstate)

# THROUGHPUT: use uint64 bytes per second (exact, no precision loss)
uint64 tx_bytes_per_sec    # e.g., 12500000 = 100 Mbps
uint64 rx_bytes_per_sec

# Error counters (cumulative since boot or interface up)
uint64 tx_packets
uint64 rx_packets
uint64 tx_dropped
uint64 rx_dropped
uint64 tx_errors
uint64 rx_errors
uint64 rx_crc_errors                   # Critical for physical layer health
