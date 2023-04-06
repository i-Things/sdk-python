import asyncio
import base64
import json
import time
from typing import Union, List, Dict
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

#物模型上报 最后两个是产品id和设备名称
DeviceUpThing = "device.up.thing.{}.{}"
#设备发送消息体
class DevPublish:
    def __init__(self, topic:str, timestamp:int, productID:str, deviceName:str, handle:str, types:List[str], payload:str):
        self.topic = topic
        self.timestamp = timestamp
        self.productID = productID
        self.deviceName = deviceName
        self.handle = handle
        self.types = types
        self.payload = payload


class MsgThingReq():
    def __init__(self):
        self.Method = ""  # 操作方法
        self.ClientToken = ""  # 方便排查随机数
        self.Timestamp = 0  # 毫秒时间戳
        self.Code = 0  # 状态码
        self.Status = ""  # 返回信息
        self.Data = None  # 返回具体设备上报的最新数据内容
        self.Sys = SysConfig()  # 系统配置
        self.Params = {}  # 参数列表
        self.Version = ""  # 协议版本，默认为1.0。
        self.EventID = ""  # 事件的 Id，在数据模板事件中定义。
        self.ActionID = ""  # 数据模板中的行为标识符，由开发者自行根据设备的应用场景定义
        self.ShowMeta = 0  # 标识回复消息是否带 metadata，缺省为0表示不返回 metadata
        self.Type = ""  # 表示获取什么类型的信息。report:表示设备上报的信息 info:信息 alert:告警 fault:故障

class SysConfig:
    def __init__(self, noAsk:bool):
        self.noAsk = noAsk
class MsgHead:
    def __init__(self, trace:str, timestamp:int, data:str):
        self.trace = trace
        self.timestamp = timestamp
        self.data = data


async def main():
    # It is very likely that the demo server will see traffic from clients other than yours.
    # To avoid this, start your own locally and modify the example to use it.
    nc = await nats.connect("nats://127.0.0.1:4222")

    # You can also use the following for TLS against the demo server.
    #
    # nc = await nats.connect("tls://demo.nats.io:4443")
    payload = """
    {
  "method":"report",
  "clientToken":"123",
  "params":{
    "tem":112
  },
  "sys":{
    "noAsk":true
  }
}
    """
    now= int(round(time.time() * 1000))
    payloadB64 = base64.b64encode(payload.encode('ascii'))
    payloadB64=payloadB64.decode('ascii')
    msg= DevPublish("",now,"25RKSGsdAZi","EC800M","thing",["property"],payloadB64)
    req=json.dumps(msg.__dict__).encode('ascii')
    basdData=base64.b64encode(req).decode('ascii')
    reqMsg= MsgHead("",now,basdData)
    reqStr=json.dumps(reqMsg.__dict__).encode('ascii')
    topic=DeviceUpThing.format(msg.productID,msg.deviceName)
    await nc.publish(topic,reqStr)
    await asyncio.sleep(100)  # 等待100秒
    # Terminate connection to NATS.
    await nc.drain()

if __name__ == '__main__':
    asyncio.run(main())