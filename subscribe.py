import asyncio
import base64
import json
import time
from typing import Union, List, Dict
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

#设备物模型事件上报通知 中间两个是产品id和设备名称,最后两个是事件类型和事件id
ApplicationDeviceReportThingEventAllDevice    = "application.device.*.*.report.thing.event.>"
#设备物模型属性上报通知 中间两个是产品id和设备名称,最后一个是属性id
ApplicationDeviceReportThingPropertyAllDevice = "application.device.*.*.report.thing.property.>"
#设备登录状态推送 中间两个是产品id和设备名称
ApplicationDeviceStatusConnectedAllDevice     = "application.device.*.*.status.connected"
#设备登出状态推送 中间两个是产品id和设备名称
ApplicationDeviceStatusDisConnectedAllDevice  = "application.device.*.*.status.disconnected"
class Core:
    def __init__(self, product_id: str, device_name: str):
        self.ProductID = product_id
        self.DeviceName = device_name

class ConnectMsg:
    def __init__(self, device: Core, timestamp: int):
        self.Device = device
        self.Timestamp = timestamp

class DataType(str):
    Bool = "bool"
    Int = "int"
    String = "string"
    Struct = "struct"
    Float = "float"
    Timestamp = "timestamp"
    Array = "array"
    Enum = "enum"

class ParamValue:
    def __init__(self, value: Union[bool, int, float, str, Dict[str, 'ParamValue'], List['ParamValue']], data_type: DataType):
        self.Value = value
        self.Type = data_type

class PropertyReport:
    def __init__(self, device: Core, timestamp: int, identifier: str, param: ParamValue):
        self.Device = device
        self.Timestamp = timestamp
        self.Identifier = identifier
        self.Param = param

class EventReport:
    def __init__(self, device: Core, timestamp: int, identifier: str, event_type: str, params: Dict[str, ParamValue]):
        self.Device = device
        self.Timestamp = timestamp
        self.Identifier = identifier
        self.Type = event_type
        self.Params = params

class MsgHead:
    def __init__(self, trace, timestamp, data):
        self.trace = trace
        self.timestamp = timestamp
        self.data = data

def connHandle(data):
    connect_msg_dict = json.loads(data)
    device_dict = connect_msg_dict['device']
    device = Core(device_dict['productID'], device_dict['deviceName'])
    connect_msg = ConnectMsg(device, int(connect_msg_dict['timestamp']))
    print(connect_msg.__dict__)

def propertyHandle(data):
    property_report_dict = json.loads(data)
    device_dict = property_report_dict['device']
    device = Core(device_dict['productID'], device_dict['deviceName'])
    param_dict = property_report_dict['param']
    param = ParamValue(param_dict['value'], DataType(param_dict['type']))
    property_report = PropertyReport(device, int(property_report_dict['timestamp']), property_report_dict['identifier'],
                                     param)
    print(property_report.__dict__)

def eventHandle(data):
    event_report_dict = json.loads(data)
    device_dict = event_report_dict['device']
    device = Core(device_dict['productID'], device_dict['deviceName'])
    params_dict = event_report_dict['params']
    params = {}
    for key, value in params_dict.items():
        params[key] = ParamValue(value['value'], DataType(value['type']))
    event_report = EventReport(device, int(event_report_dict['timestamp']), event_report_dict['identifier'],
                               event_report_dict['type'], params)
    print(event_report.__dict__)
def processMsg(handle):
    async def retFunc(msg):
        try:
            payload = json.loads(msg.data.decode())
            trace = payload.get("trace", "")
            timestamp = int(payload.get("timestamp", 0))
            data = base64.b64decode(payload.get("data", ""))
            msg_head = MsgHead(trace, timestamp, data)
            handle(msg_head.data)
        except Exception as e:
            print(f"Error processing message: {e}")
    return retFunc

async def main():
    # It is very likely that the demo server will see traffic from clients other than yours.
    # To avoid this, start your own locally and modify the example to use it.
    nc = await nats.connect("nats://127.0.0.1:4222")

    # You can also use the following for TLS against the demo server.
    #
    # nc = await nats.connect("tls://demo.nats.io:4443")


    # Simple publisher and async subscriber via coroutine.
    sub = await nc.subscribe(ApplicationDeviceReportThingEventAllDevice, cb=processMsg(eventHandle))
    sub = await nc.subscribe(ApplicationDeviceReportThingPropertyAllDevice, cb=processMsg(propertyHandle))
    sub = await nc.subscribe(ApplicationDeviceStatusConnectedAllDevice, cb=processMsg(connHandle))
    sub = await nc.subscribe(ApplicationDeviceStatusDisConnectedAllDevice, cb=processMsg(connHandle))

    await asyncio.sleep(100)  # 等待100秒

    # Remove interest in subscription.
    await sub.unsubscribe()

    # Terminate connection to NATS.
    await nc.drain()

if __name__ == '__main__':
    asyncio.run(main())