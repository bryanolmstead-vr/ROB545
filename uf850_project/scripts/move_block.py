
import math
import subprocess
import time

# Model and world
MODEL_NAME = "block"
SERVICE = "/world/default/set_pose"

# Circular trajectory parameters
CENTER_X = 0.30
CENTER_Y = -0.15
RADIUS = 0.10
Z = 1.0

PERIOD = 8.0
UPDATE_INTERVAL = 0.05

start_time = time.monotonic()

try:
    while True:
        t = time.monotonic() - start_time

        angle = 2 * math.pi * t / PERIOD

        # Circular movement in the XY plane
        x = CENTER_X + RADIUS * math.cos(angle)
        y = CENTER_Y + RADIUS * math.sin(angle)

        request = (
            f'name: "{MODEL_NAME}", '
            f'position: {{x: {x:.4f}, y: {y:.4f}, z: {Z}}}, '
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
            continue

        print(f"Time: {t:.2f} s | X: {x:.4f} m | Y: {y:.4f} m")
        time.sleep(UPDATE_INTERVAL)

except KeyboardInterrupt:
    print("Movement stopped by user.")

print("Circular trajectory finished.")
