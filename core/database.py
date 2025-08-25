import json
import traceback
import os

from filelock import FileLock

DATA_PATH = "./ai_host"
os.makedirs(DATA_PATH, exist_ok=True)

def ia_usage(data=False):

    return __dataControl(DATA_PATH + "\\ia_usage.json", data)


def queue(data=False):

    return __dataControl(DATA_PATH + "\\queue.json", data)



def __dataControl(path, data=False):

    lockFile = path + ".lock"
    lock = FileLock(lockFile)
    res = None

    try:

        with lock:
            if data != False:

                with open(path, "w", encoding="utf-8") as file:

                    s_data = json.dumps(data)
                    file.write(s_data)
                    return res

            else:

                with open(path, "r", encoding="utf-8") as file:

                    res = json.loads(file.read())

                    return res
    except:
        print(traceback.format_exc())
        return None
