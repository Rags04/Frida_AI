from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_result import AdbResult
from adb_pywrapper.pull_result import PullResult

devices = AdbDevice.list_devices()
print ("connected Devices:", devices)

status = AdbDevice.get_device_status('Device connected')
print ("Devices Status:", status)

adb_device = AdbDevice(device='your_device_identifier')
adb_device.root()
1