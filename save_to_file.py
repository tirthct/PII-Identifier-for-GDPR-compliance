import datetime
import time
def save(frame_name,objects):
    frame_name = frame_name + ":"+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    print(frame_name)
    object_names = ""
    for i in range(len(objects)):
        object_names=object_names+","+objects[i]
    file = open("logs.txt","a+")
    file.write(frame_name+": This frame contained the following objects:"+ object_names)
    file.write("\n")
    file.close()
