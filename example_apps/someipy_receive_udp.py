import asyncio
import ipaddress
import logging
from someipy import ServiceBuilder, EventGroup, TransportLayerProtocol, SomeIpMessage
from someipy.service_discovery import construct_service_discovery
from someipy.client_service_instance import construct_client_service_instance
from someipy.logging import set_someipy_log_level
from temperature_msg import TemparatureMsg

SD_MULTICAST_GROUP = "224.224.224.245"
SD_PORT = 30490
LOCAL_INTERFACE_IP = "192.168.0.103"

SAMPLE_SERVICE_ID = 0x1234
SAMPLE_INSTANCE_ID = 0x5678
SAMPLE_EVENTGROUP_ID = 0x0321
SAMPLE_EVENT_ID = 0x0123

def temperature_callback(someip_message: SomeIpMessage) -> None:
    """
    Callback function that is called when a temperature message is received.

    Args:
        someip_message (SomeIpMessage): The SomeIpMessage object containing the received message.

    Returns:
        None: This function does not return anything.
    """
    try:
        print(f"Received {len(someip_message.payload)} bytes. Try to deserialize..")
        temperature_msg = TemparatureMsg().deserialize(someip_message.payload)
        print(f"Deserialized message: {temperature_msg}")
        print(f"Measurements: {[m.value for m in temperature_msg.measurements.data]}")
    except Exception as e:
        print(f"Error in deserialization: {e}")

async def main():
    set_someipy_log_level(logging.DEBUG)

    service_discovery = await construct_service_discovery(SD_MULTICAST_GROUP, SD_PORT, LOCAL_INTERFACE_IP)

    temperature_eventgroup = EventGroup(id=SAMPLE_EVENTGROUP_ID, event_ids=[SAMPLE_EVENT_ID])
    temperature_service = (
        ServiceBuilder()
        .with_service_id(SAMPLE_SERVICE_ID)
        .with_major_version(1)
        .with_eventgroup(temperature_eventgroup)
        .build()
    )

    service_instance_temperature = await construct_client_service_instance(
        service=temperature_service,
        instance_id=SAMPLE_INSTANCE_ID,
        endpoint=(ipaddress.IPv4Address(LOCAL_INTERFACE_IP), 3002),
        ttl=5,
        sd_sender=service_discovery,
        protocol=TransportLayerProtocol.UDP
    )

    service_instance_temperature.register_callback(temperature_callback)
    service_instance_temperature.subscribe_eventgroup(SAMPLE_EVENTGROUP_ID)

    service_discovery.attach(service_instance_temperature)

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        print("Shutdown..")
    finally:
        print("Service Discovery close..")
        service_discovery.close()

    print("End main task..")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
