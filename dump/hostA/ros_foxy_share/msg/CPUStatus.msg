# Raw monitoring data for a single CPU/SoC

builtin_interfaces/Time timestamp       # Data acquisition time
string resource_id                      # Resource ID (e.g., "CPU_103", "CPU_104")
int32 package_temp                    # Package temperature in m°C 
int32[] temps                         # Per-zone temperatures in m°C 
uint16 avg_util                         # Average utilization across all logical CPUs [0–10000], 0.01%
uint16[] util                           # Utilization per logical CPU [0–10000], 0.01%
uint32[] cur_freq_khz                   # Current target frequency (scaling_cur_freq)
uint32[] hw_max_freq_khz                # Hardware max frequency (cpuinfo_max_freq)
uint32[] hw_min_freq_khz                # Hardware min frequency (cpuinfo_min_freq)
