# FileSystemStatus.msg
builtin_interfaces/Time timestamp

string resource_id            # e.g., "FS_103_root-ro" (SoC_instance)
string mount_point            # e.g., "/root-ro"
string device_path            # e.g., "/dev/mmcblk0p12"
string fs_type                # "ext4", "f2fs", etc.

# Space usage
uint64 total_bytes
uint64 used_bytes
uint64 available_bytes

# Inode usage (prevents "No space left on device" despite free space)
uint64 total_inodes
uint64 used_inodes
uint64 free_inodes
