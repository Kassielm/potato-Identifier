import snap7
import logging
import time

logger = logging.getLogger(__name__)

class Plc:
    def __init__(self):
        self.client = None
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 5  # seconds

    def init_plc(self):
        try:
            logger.info("Tentando conectar ao PLC...")
            self.client = snap7.client.Client()
            self.client.connect("192.168.2.201", 0, 1)  # IP, rack, slot
            if self.client.get_connected():
                self.connected = True
                logger.info("PLC conectado com sucesso!")
                return True
            else:
                self.connected = False
                logger.error("Falha ao conectar ao PLC.")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"Erro ao conectar ao PLC: {e}")
            return False

    def check_connection(self):
        """Verifica se a conexão com o PLC ainda está ativa"""
        try:
            if self.client and self.client.get_connected():
                return True
            else:
                self.connected = False
                return False
        except Exception:
            self.connected = False
            return False

    def reconnect_if_needed(self):
        """Tenta reconectar ao PLC se necessário"""
        current_time = time.time()
        if (not self.connected and 
            current_time - self.last_connection_attempt > self.connection_retry_interval):
            
            logger.info("Tentando reconectar ao PLC...")
            self.last_connection_attempt = current_time
            return self.init_plc()
        return self.connected

    @staticmethod
    def int_to_bytearray(number: int) -> bytearray:
        # Convert the integer to bytes
        byte_representation = number.to_bytes(2, byteorder='big', signed=True)
        # Convert the bytes to a bytearray
        return bytearray(byte_representation)

    def write_db(self, value: int):
        try:
            # Verifica conexão antes de escrever
            if not self.check_connection():
                if not self.reconnect_if_needed():
                    logger.warning(f"PLC não conectado. Valor {value} não foi enviado.")
                    return False

            data = self.int_to_bytearray(value)
            self.client.write_area(snap7.Area.DB, 1, 0, data)
            logger.debug(f"Valor {value} escrito no PLC com sucesso")
            return True
            
        except Exception as e:
            self.connected = False
            logger.error(f"Falha ao escrever no PLC: {e}")
            return False

    def disconnect(self):
        """Desconecta do PLC de forma segura"""
        try:
            if self.client and self.client.get_connected():
                self.client.disconnect()
                logger.info("PLC desconectado.")
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
        finally:
            self.connected = False
