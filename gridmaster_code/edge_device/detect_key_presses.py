import subprocess
import time
import requests
import datetime

COL_MAP = {1: 1, 2: 2, 5: 3, 7: 4, 8: 5, 11: 6, 14: 7, 19: 8, 20: 9, 22: 10, 23: 11, 25: 12}
ROW_MAP = {27: 1, 26: 2, 24: 3, 21: 4, 16: 5, 15: 6, 13: 7, 10: 8, 9: 9, 6: 10, 4: 11, 3: 12}

ROWS = list(ROW_MAP.keys())
COLS = list(COL_MAP.keys())
COL_VALUES = list(COL_MAP.values())

LEHRE_SERVER_URL = ("CALLBACK_URL")


def setup_gpio():
    for row in ROWS:
        subprocess.run(["gpio", "mode", str(row), "in"])
        subprocess.run(["gpio", "mode", str(row), "up"])

    for col in COLS:
        subprocess.run(["gpio", "mode", str(col), "out"])
        subprocess.run(["gpio", "write", str(col), "0"])


def turn_off_grid():
    print("Resetting GPIO states...")
    for col in COLS:
        subprocess.run(["gpio", "write", str(col), "0"])
    for row in ROWS:
        subprocess.run(["gpio", "mode", str(row), "down"])


def detect_keys():
    print("Listening for key presses on grid...")

    try:
        while True:
            detected_columns = []
            for col in COLS:
                for c in COLS:
                    subprocess.run(["gpio", "write", str(c), "0"])

                subprocess.run(["gpio", "write", str(col), "1"])

                for row in ROWS:
                    result = subprocess.run(["gpio", "read", str(row)], capture_output=True, text=True)
                    state = result.stdout.strip()

                    if state == "0":
                        row_num = ROW_MAP.get(row, "?")
                        col_num = COL_MAP.get(col, "?")
                        detected_columns.append(col_num)

                        if len(detected_columns) == 11:
                            correct_col = list(set(COL_VALUES).difference(set(detected_columns)))[0]
                            position = [row_num, correct_col]
                            print("Key Pressed:", position, ".")
                            send_movement(position)

                subprocess.run(["gpio", "write", str(col), "0"])
            time.sleep(1)

    except KeyboardInterrupt:
        turn_off_grid()


def send_movement(arr):
    movement_data = {
        "position": arr,
        "timestamp": datetime.datetime.now().isoformat()
    }

    response = requests.post(LEHRE_SERVER_URL, json=movement_data)
    print("Server Response: ", response.status_code)


setup_gpio()
detect_keys()