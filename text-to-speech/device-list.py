import sounddevice as sd

device_list = sd.query_devices()
print(device_list)
