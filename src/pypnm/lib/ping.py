# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import platform
import subprocess

class Ping:
    """
    A simple cross-platform Ping utility to check if a device is reachable.
    """

    @staticmethod
    def is_reachable(host: str, timeout: int = 1, count: int = 1) -> bool:
        """
        Checks if the given host is reachable via ICMP ping.

        Parameters:
        - host (str): The IP address or hostname to ping.
        - timeout (int): Timeout in seconds (default: 1)
        - count (int): Number of ping attempts (default: 1)

        Returns:
        - bool: True if the host is reachable, False otherwise.
        """
        system = platform.system().lower()

        if system == "windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:  # macOS and Linux
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

        try:
            result = subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[Ping Error] {e}")
            return False
