import abc
import asyncio
import enum
import logging
import math
import socket
import struct
from typing import Dict, List, Optional, Union

import serial
import serial_asyncio
from bleak import BleakClient, BleakScanner
from PIL import Image, ImageOps
from serial.tools.list_ports import comports as list_comports

from .packet import NiimbotPacket

logging.basicConfig(level=logging.DEBUG)


class InfoEnum(enum.IntEnum):
    DENSITY = 1
    PRINTSPEED = 2
    LABELTYPE = 3
    LANGUAGETYPE = 6
    AUTOSHUTDOWNTIME = 7
    DEVICETYPE = 8
    SOFTVERSION = 9
    BATTERY = 10
    DEVICESERIAL = 11
    HARDVERSION = 12


class RequestCodeEnum(enum.IntEnum):
    GET_INFO = 64  # 0x40
    GET_RFID = 26  # 0x1A
    HEARTBEAT = 220  # 0xDC
    SET_LABEL_TYPE = 35  # 0x23
    SET_LABEL_DENSITY = 33  # 0x21
    START_PRINT = 1  # 0x01
    END_PRINT = 243  # 0xF3
    START_PAGE_PRINT = 3  # 0x03
    END_PAGE_PRINT = 227  # 0xE3
    ALLOW_PRINT_CLEAR = 32  # 0x20
    SET_DIMENSION = 19  # 0x13
    SET_QUANTITY = 21  # 0x15
    GET_PRINT_STATUS = 163  # 0xA3


def _packet_to_int(x: bytes) -> int:
    return int.from_bytes(x, "big")


class BaseTransport(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def read(self, length: int) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    async def write(self, data: bytes) -> None:
        raise NotImplementedError


class BluetoothTransport(BaseTransport):
    def __init__(self, address: str) -> None:
        self._sock = socket.socket(
            socket.AF_BLUETOOTH,
            socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM,
        )
        self._sock.connect((address, 1))

    async def read(self, length: int) -> bytes:
        return self._sock.recv(length)

    async def write(self, data: bytes) -> None:
        return self._sock.send(data)


class SerialTransport(BaseTransport):
    def __init__(self, port: str = "auto") -> None:
        port = port if port != "auto" else self._detect_port()
        logging.debug(f"Opening serial port {port}")
        self.port = port
        self._reader = None
        self._writer = None

    async def _open(self) -> None:
        if self._reader is not None:
            return

        try:
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

            # Try to get device info
            cmd = bytes([0x55, 0x55, 0x40, 0x01, 0x08, 0x49, 0xAA, 0xAA])
            logging.debug(f"Sending device type command: {cmd.hex()}")
            await self.write(cmd)

            # Read response with timeout
            try:
                response = await asyncio.wait_for(self._reader.read(100), timeout=1.0)
                if response:
                    logging.debug(f"Got response: {response.hex()}")
                else:
                    logging.debug("No response to device type command")
            except asyncio.TimeoutError:
                logging.debug("Timeout waiting for response")

        except Exception as e:
            logging.error(f"Failed to open serial port: {e}")
            raise

    def _detect_port(self) -> str:
        all_ports = list(list_comports())
        if len(all_ports) == 0:
            raise RuntimeError("No serial ports detected")
        if len(all_ports) > 1:
            msg = "Too many serial ports, please select specific one:"
            for port, desc, hwid in all_ports:
                msg += f"\n- {port} : {desc} [{hwid}]"
            raise RuntimeError(msg)
        return all_ports[0][0]

    async def read(self, length: int) -> bytes:
        if self._reader is None:
            await self._open()
        data = await self._reader.read(length)
        logging.debug(f"Read {len(data)} bytes: {data.hex()}")
        return data

    async def write(self, data: bytes) -> None:
        if self._writer is None:
            await self._open()
        logging.debug(f"Writing {len(data)} bytes: {data.hex()}")
        self._writer.write(data)
        await self._writer.drain()

    def close(self) -> None:
        if self._writer:
            self._writer.close()
            self._writer = None
            self._reader = None


class BLETransport(BaseTransport):
    """Transport for Bluetooth Low Energy (BLE) communication with Niimbot printers"""

    # Niimbot D110 BLE service and characteristic UUIDs
    SERVICE_UUID = "49535343-FE7D-4AE5-8FA9-9FAFD205E455"
    WRITE_CHAR_UUID = "49535343-8841-43F4-A8D4-ECBE34729BB3"
    READ_CHAR_UUID = "49535343-1E4D-4BD9-BA61-23C647249616"
    NOTIFY_CHAR_UUID = "49535343-6DAA-4D02-ABF6-19569ACA69FE"

    def __init__(self, address: str) -> None:
        """Initialize BLE printer

        Args:
            address: Bluetooth address of the printer
        """
        self._address = address
        self._client = BleakClient(self._address)
        self._connected = False
        self._read_buffer = bytearray()
        self._read_event = asyncio.Event()
        self._read_event.set()  # Initially set so first read works

    def _notification_handler(self, _, data: bytearray) -> None:
        """Handle notifications from the printer"""
        logging.debug(f"Received notification: {':'.join([f'{b:02x}' for b in data])}")
        self._read_buffer.extend(data)
        self._read_event.set()

    async def connect(self) -> None:
        """Connect to the printer"""
        if self._connected:
            return

        # Connect with retry
        max_retries = 3
        retry_delay = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                if not self._client.is_connected:
                    await self._client.connect()
                    await self._client.get_services()  # Discover services

                    # Try to enable notifications, but don't fail if not supported
                    try:
                        await self._client.start_notify(self.READ_CHAR_UUID, self._notification_handler)
                    except Exception as e:
                        logging.warning(f"Could not enable notifications: {e}. Continuing without notifications.")

                # Send initial heartbeat to verify connection
                if await self._verify_connection():
                    self._connected = True
                    return
                else:
                    # Force disconnect and retry if verification failed
                    await self._client.disconnect()

            except Exception as e:
                last_error = e
                logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
                try:
                    await self._client.disconnect()
                except Exception:
                    logging.warning("Failed to disconnect")

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                continue

        self._connected = False
        raise ConnectionError(f"Failed to connect after {max_retries} attempts: {last_error}")

    async def disconnect(self) -> None:
        """Disconnect from the BLE device"""
        if self._client and self._connected:
            try:
                await self._client.stop_notify(self.NOTIFY_CHAR_UUID)
            except Exception:
                pass
            await self._client.disconnect()
            self._connected = False
            self._client = None

    async def read(self, length: int) -> bytes:
        """Read data from the BLE device

        Args:
            length: Number of bytes to read

        Returns:
            bytes: Data read from device
        """
        if not self._connected:
            await self.connect()

        # If notifications failed, fall back to polling reads
        if not self._read_event.is_set():
            try:
                data = await self._client.read_gatt_char(self.READ_CHAR_UUID)
                if data:
                    self._read_buffer.extend(data)
                    self._read_event.set()
            except Exception as e:
                logging.warning(f"Failed to poll read: {e}")

        # Wait for data with timeout
        if not await asyncio.wait_for(self._read_event.wait(), timeout=5.0):
            raise TimeoutError("No response from printer")

        # Get data from buffer
        data = bytes(self._read_buffer[:length])
        self._read_buffer = self._read_buffer[length:]
        if not self._read_buffer:
            self._read_event.clear()
        return data

    async def write(self, data: bytes) -> None:
        """Write data to the BLE device

        Args:
            data: Data to write
        """
        if not self._connected:
            await self.connect()
            if not self._connected:
                raise ConnectionError("Failed to establish connection")

        try:
            await self._client.write_gatt_char(self.WRITE_CHAR_UUID, data, response=True)
        except Exception as e:
            logging.error(f"Failed to write: {e}")
            self._connected = False  # Mark as disconnected on write error
            raise

    async def _verify_connection(self) -> bool:
        """Verify connection by sending heartbeat

        Returns:
            bool: True if connection verified, False otherwise
        """
        try:
            # Send heartbeat command directly via client
            heartbeat = bytes([0x55, 0x55, 0xDC, 0x01, 0x01, 0xDC, 0xAA, 0xAA])
            logging.debug("Sending heartbeat...")
            logging.debug(f"send: {':'.join([f'{b:02x}' for b in heartbeat])}")

            await self._client.write_gatt_char(self.WRITE_CHAR_UUID, heartbeat, response=True)

            # Read response with timeout
            response = await asyncio.wait_for(self.read(20), timeout=2.0)
            logging.debug(f"recv: {':'.join([f'{b:02x}' for b in response])}")

            # Check if response is all zeros
            if all(b == 0 for b in response):
                # Try reading again after a short delay
                await asyncio.sleep(0.5)
                response = await asyncio.wait_for(self.read(20), timeout=2.0)
                logging.debug(f"recv retry: {':'.join([f'{b:02x}' for b in response])}")

            # Accept any non-zero response for now
            return not all(b == 0 for b in response)

        except Exception as e:
            logging.warning(f"Connection verification failed: {e}")
            return False

    @staticmethod
    async def discover() -> List[str]:
        """Discover nearby Niimbot printers

        Returns:
            List[str]: List of Bluetooth addresses of discovered printers
        """
        devices = await BleakScanner.discover()
        printers = []

        for device in devices:
            if device.name:
                logging.debug(f"Found BLE device: {device.name} at {device.address}")

                # Niimbot printers can advertise with different name formats:
                # - "D110-XXXXXXXXX" (standard format)
                # - "NIIMBOT-XXXXXXXXX" (alternative format)
                # - "E904100934" (serial number only)
                if (
                    device.name.startswith("D110-")
                    or device.name.startswith("NIIMBOT-")
                    or device.name == "E904100934"  # Add specific printer we found
                    or (
                        len(device.name) == 10 and device.name.startswith("E") and device.name[1:].isdigit()
                    )  # Match E + 9 digits
                ):
                    logging.debug(f"Found Niimbot printer: {device.name} at {device.address}")
                    printers.append(device.address)

        if not printers:
            logging.warning("No Niimbot printers found!")
        else:
            logging.info(f"Found {len(printers)} Niimbot printer(s)")

        return printers


class PrinterClient:
    def __init__(self, transport: BaseTransport) -> None:
        self._transport = transport
        self._packetbuf = bytearray()

    async def print_image(self, image: Image.Image, density: int = 3) -> None:
        await self.set_label_density(density)
        await self.set_label_type(1)
        await self.start_print()
        await self.start_page_print()
        await self.set_dimension(image.height, image.width)
        # self.set_quantity(1)  # Same thing (B21)
        for pkt in self._encode_image(image):
            await self._send(pkt)
        await self.end_page_print()
        await asyncio.sleep(0.3)  # FIXME: Check get_print_status()
        while not await self.end_print():
            await asyncio.sleep(0.1)

    def _encode_image(self, image: Image.Image) -> List[NiimbotPacket]:
        img = ImageOps.invert(image.convert("L")).convert("1")
        for y in range(img.height):
            line_data = [img.getpixel((x, y)) for x in range(img.width)]
            line_data = "".join("0" if pix == 0 else "1" for pix in line_data)
            line_data = int(line_data, 2).to_bytes(math.ceil(img.width / 8), "big")
            counts = (0, 0, 0)  # It seems like you can always send zeros
            header = struct.pack(">H3BB", y, *counts, 1)
            pkt = NiimbotPacket(0x85, header + line_data)
            yield pkt

    async def _recv(self) -> List[NiimbotPacket]:
        packets = []
        self._packetbuf.extend(await self._transport.read(1024))
        while len(self._packetbuf) > 4:
            pkt_len = self._packetbuf[3] + 7
            if len(self._packetbuf) >= pkt_len:
                packet = NiimbotPacket.from_bytes(self._packetbuf[:pkt_len])
                self._log_buffer("recv", packet.to_bytes())
                packets.append(packet)
                del self._packetbuf[:pkt_len]
        return packets

    async def _send(self, packet: NiimbotPacket) -> None:
        await self._transport.write(packet.to_bytes())

    def _log_buffer(self, prefix: str, buff: bytes) -> None:
        msg = ":".join(f"{i:#04x}"[-2:] for i in buff)
        logging.debug(f"{prefix}: {msg}")

    async def _transceive(self, reqcode: int, data: bytes, respoffset: int = 1) -> Optional[NiimbotPacket]:
        respcode = respoffset + reqcode
        packet = NiimbotPacket(reqcode, data)
        self._log_buffer("send", packet.to_bytes())
        await self._send(packet)
        resp = None
        for _ in range(6):
            for packet in await self._recv():
                if packet.type == 219:
                    raise ValueError
                elif packet.type == 0:
                    raise NotImplementedError
                elif packet.type == respcode:
                    resp = packet
            if resp:
                return resp
            await asyncio.sleep(0.1)
        return resp

    async def get_info(self, key: InfoEnum) -> Optional[Union[str, float, int]]:
        if packet := await self._transceive(RequestCodeEnum.GET_INFO, bytes((key,)), key):
            match key:
                case InfoEnum.DEVICESERIAL:
                    return packet.data.hex()
                case InfoEnum.SOFTVERSION:
                    return _packet_to_int(packet) / 100
                case InfoEnum.HARDVERSION:
                    return _packet_to_int(packet) / 100
                case _:
                    return _packet_to_int(packet)
        else:
            return None

    async def get_rfid(self) -> Optional[Dict[str, Union[str, int]]]:
        packet = await self._transceive(RequestCodeEnum.GET_RFID, b"\x01")
        data = packet.data

        if data[0] == 0:
            return None
        uuid = data[0:8].hex()
        idx = 8

        barcode_len = data[idx]
        idx += 1
        barcode = data[idx : idx + barcode_len].decode()

        idx += barcode_len
        serial_len = data[idx]
        idx += 1
        serial = data[idx : idx + serial_len].decode()

        idx += serial_len
        total_len, used_len, type_ = struct.unpack(">HHB", data[idx:])
        return {
            "uuid": uuid,
            "barcode": barcode,
            "serial": serial,
            "used_len": used_len,
            "total_len": total_len,
            "type": type_,
        }

    async def heartbeat(self) -> Dict[str, Optional[int]]:
        if isinstance(self._transport, BLETransport):
            await self._transport._send_heartbeat()
        else:
            packet = await self._transceive(RequestCodeEnum.HEARTBEAT, b"\x01")
            closingstate = None
            powerlevel = None
            paperstate = None
            rfidreadstate = None

            match len(packet.data):
                case 20:
                    paperstate = packet.data[18]
                    rfidreadstate = packet.data[19]
                case 13:
                    closingstate = packet.data[9]
                    powerlevel = packet.data[10]
                    paperstate = packet.data[11]
                    rfidreadstate = packet.data[12]
                case 19:
                    closingstate = packet.data[15]
                    powerlevel = packet.data[16]
                    paperstate = packet.data[17]
                    rfidreadstate = packet.data[18]
                case 10:
                    closingstate = packet.data[8]
                    powerlevel = packet.data[9]
                    rfidreadstate = packet.data[8]
                case 9:
                    closingstate = packet.data[8]

            return {
                "closingstate": closingstate,
                "powerlevel": powerlevel,
                "paperstate": paperstate,
                "rfidreadstate": rfidreadstate,
            }

    async def set_label_type(self, n: int) -> bool:
        assert 1 <= n <= 3
        packet = await self._transceive(RequestCodeEnum.SET_LABEL_TYPE, bytes((n,)), 16)
        return bool(packet.data[0])

    async def set_label_density(self, n: int) -> bool:
        assert 1 <= n <= 5  # B21 has 5 levels, not sure for D11
        packet = await self._transceive(RequestCodeEnum.SET_LABEL_DENSITY, bytes((n,)), 16)
        return bool(packet.data[0])

    async def start_print(self) -> bool:
        packet = await self._transceive(RequestCodeEnum.START_PRINT, b"\x01")
        return bool(packet.data[0])

    async def end_print(self) -> bool:
        packet = await self._transceive(RequestCodeEnum.END_PRINT, b"\x01")
        return bool(packet.data[0])

    async def start_page_print(self) -> bool:
        packet = await self._transceive(RequestCodeEnum.START_PAGE_PRINT, b"\x01")
        return bool(packet.data[0])

    async def end_page_print(self) -> bool:
        packet = await self._transceive(RequestCodeEnum.END_PAGE_PRINT, b"\x01")
        return bool(packet.data[0])

    async def allow_print_clear(self) -> bool:
        packet = await self._transceive(RequestCodeEnum.ALLOW_PRINT_CLEAR, b"\x01", 16)
        return bool(packet.data[0])

    async def set_dimension(self, w: int, h: int) -> bool:
        packet = await self._transceive(RequestCodeEnum.SET_DIMENSION, struct.pack(">HH", w, h))
        return bool(packet.data[0])

    async def set_quantity(self, n: int) -> bool:
        packet = await self._transceive(RequestCodeEnum.SET_QUANTITY, struct.pack(">H", n))
        return bool(packet.data[0])

    async def get_print_status(self) -> Dict[str, int]:
        packet = await self._transceive(RequestCodeEnum.GET_PRINT_STATUS, b"\x01", 16)
        page, progress1, progress2 = struct.unpack(">HBB", packet.data)
        return {"page": page, "progress1": progress1, "progress2": progress2}
