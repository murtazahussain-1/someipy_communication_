import asyncio
import ipaddress
import logging
import psutil  # Ensure psutil is installed
from someipy import TransportLayerProtocol, ServiceBuilder, EventGroup, construct_server_service_instance
from someipy.service_discovery import construct_service_discovery
from someipy.logging import set_someipy_log_level
from someipy.serialization import Uint8, Uint64, Float32
from temperature_msg import TemparatureMsg

SD_MULTICAST_GROUP = "224.224.224.245"
SD_PORT = 30490
LOCAL_INTERFACE_IP = "192.168.0.105"
REMOTE_INTERFACE_IP = "192.168.0.103"

SAMPLE_SERVICE_ID = 0x1234
SAMPLE_INSTANCE_ID = 0x5678
SAMPLE_EVENTGROUP_ID = 0x0321
SAMPLE_EVENT_ID = 0x0123

async def main():
    set_someipy_log_level(logging.DEBUG)

    logging.debug("Initializing service discovery...")
    try:
        service_discovery = await construct_service_discovery(SD_MULTICAST_GROUP, SD_PORT, LOCAL_INTERFACE_IP)
    except OSError as e:
        logging.error(f"Failed to create service discovery: {e}")
        return

    logging.debug("Service discovery initialized.")

    temperature_eventgroup = EventGroup(id=SAMPLE_EVENTGROUP_ID, event_ids=[SAMPLE_EVENT_ID])
    temperature_service = (
        ServiceBuilder()
        .with_service_id(SAMPLE_SERVICE_ID)
        .with_major_version(1)
        .with_eventgroup(temperature_eventgroup)
        .build()
    )

    logging.debug("Creating server service instance...")
    try:
        service_instance_temperature = await construct_server_service_instance(
            temperature_service,
            instance_id=SAMPLE_INSTANCE_ID,
            endpoint=(ipaddress.IPv4Address(LOCAL_INTERFACE_IP), 3000),
            ttl=5,
            sd_sender=service_discovery,
            cyclic_offer_delay_ms=2000,
            protocol=TransportLayerProtocol.UDP
        )
    except OSError as e:
        logging.error(f"Failed to create service instance: {e}")
        return

    logging.debug("Server service instance created.")

    service_discovery.attach(service_instance_temperature)
    print("Start offering service..")
    service_instance_temperature.start_offer()

    tmp_msg = TemparatureMsg()
    tmp_msg.version.major = Uint8(1)
    tmp_msg.version.minor = Uint8(0)

    try:
        while True:
            await asyncio.sleep(1)

            # Get CPU temperature
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                core_temps = temps["coretemp"]
                for i in range(min(len(core_temps), len(tmp_msg.measurements.data))):
                    tmp_msg.measurements.data[i] = Float32(core_temps[i].current)

            tmp_msg.timestamp = Uint64(tmp_msg.timestamp.value + 1)
            payload = tmp_msg.serialize()

            print(f"Serialized payload: {payload.hex()}")

            service_instance_temperature.send_event(SAMPLE_EVENTGROUP_ID, SAMPLE_EVENT_ID, payload)
    except asyncio.CancelledError:
        print("Stop offering service..")
        await service_instance_temperature.stop_offer()
    finally:
        print("Service Discovery close..")
        service_discovery.close()

    print("End main task..")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
