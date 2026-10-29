
import math
import subprocess
import time

# Model and world
MODEL_NAME = "block"
SERVICE = "/world/default/set_pose"

# Trajectory parameters (meters and seconds)
CENTER_X = 0.55
AMPLITUDE = 0.05
Y = 0.0
Z = 1.0
PERIOD = 8.0
DURATION = 24.0
UPDATE_INTERVAL = 0.2

start_time = time.monotonic()

try:
    while time.monotonic() - start_time < DURATION:
        t = time.monotonic() - start_time

        # Smooth back-and-forth movement
        x = CENTER_X - AMPLITUDE * math.cos(
            2 * math.pi * t / PERIOD
        )

        request = (
            f'name: "{MODEL_NAME}", '
            f'position: {{x: {x:.4f}, y: {Y}, z: {Z}}}, '
            'orientation: {w: 1.0}'
        )

        result = subprocess.run(
            [
                "gz", "service",
                "-s", SERVICE,
                "--reqtype", "gz.msgs.Pose",
                "--reptype", "gz.msgs.Boolean",
                "--timeout", "1000",
                "--req", request,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 or "data: true" not in result.stdout:
            print("Gazebo pose update failed.")
            print(result.stdout, result.stderr)
            break

        print(f"Time: {t:.2f} s | X: {x:.4f} m")
        time.sleep(UPDATE_INTERVAL)

except KeyboardInterrupt:
    print("Movement stopped by user.")

print("Trajectory script finished.")
