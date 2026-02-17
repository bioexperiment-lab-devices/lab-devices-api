class LabDevicesError(Exception):
    pass


class DeviceTimeoutError(LabDevicesError):
    pass


class DeviceNotFoundError(LabDevicesError):
    pass


class DeviceConnectionError(LabDevicesError):
    pass


class UnexpectedResponseError(LabDevicesError):
    pass
