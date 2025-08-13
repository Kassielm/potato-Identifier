import snap7
import logging
import time
import threading

logger = logging.getLogger(__name__)

class Plc:
    def __init__(self):
        self.client = None
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 10  # seconds
        self.auto_reconnect = True
        self.connection_thread = None
        self.stop_reconnect = False
        
    def init_plc(self):
        """Inicializa a conexão com o PLC sem bloquear a aplicação"""
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
                logger.warning("Falha ao conectar ao PLC - aplicação continuará sem PLC.")
                self._start_auto_reconnect()
                return False
        except Exception as e:
            self.connected = False
            logger.warning(f"Erro ao conectar ao PLC - aplicação continuará sem PLC: {e}")
            self._start_auto_reconnect()
            return False
    
    def _start_auto_reconnect(self):
        """Inicia thread de reconexão automática"""
        if self.auto_reconnect and (self.connection_thread is None or not self.connection_thread.is_alive()):
            self.stop_reconnect = False
            self.connection_thread = threading.Thread(target=self._auto_reconnect_loop, daemon=True)
            self.connection_thread.start()
            logger.info("Thread de reconexão automática iniciada")
    
    def _auto_reconnect_loop(self):
        """Loop de reconexão automática executado em thread separada"""
        reconnect_attempts = 0
        while self.auto_reconnect and not self.stop_reconnect:
            if not self.connected:
                current_time = time.time()
                if current_time - self.last_connection_attempt >= self.connection_retry_interval:
                    reconnect_attempts += 1
                    if reconnect_attempts == 1 or reconnect_attempts % 6 == 0:  # Log a cada 6 tentativas (1 minuto)
                        logger.info(f"Tentando reconectar ao PLC automaticamente (tentativa {reconnect_attempts})...")
                    self.last_connection_attempt = current_time
                    try:
                        if self.client:
                            self.client.disconnect()
                        self.client = snap7.client.Client()
                        self.client.connect("192.168.2.201", 0, 1)
                        if self.client.get_connected():
                            self.connected = True
                            logger.info(f"✅ PLC reconectado com sucesso após {reconnect_attempts} tentativas!")
                            reconnect_attempts = 0
                        else:
                            if reconnect_attempts <= 3:  # Log apenas as primeiras tentativas
                                logger.debug("Reconexão falhou - tentará novamente em 10s")
                    except Exception as e:
                        if reconnect_attempts <= 3:  # Log apenas as primeiras tentativas
                            logger.debug(f"Tentativa de reconexão falhou: {e}")
            else:
                reconnect_attempts = 0  # Reset counter quando conectado
            
            time.sleep(2)  # Verifica a cada 2 segundos

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

    @staticmethod
    def int_to_bytearray(number: int) -> bytearray:
        # Convert the integer to bytes
        byte_representation = number.to_bytes(2, byteorder='big', signed=True)
        # Convert the bytes to a bytearray
        return bytearray(byte_representation)
    
    def get_status(self):
        """Retorna o status atual da conexão PLC"""
        return {
            'connected': self.connected,
            'auto_reconnect': self.auto_reconnect,
            'last_attempt': self.last_connection_attempt,
            'retry_interval': self.connection_retry_interval
        }

    def write_db(self, value: int):
        """Escreve valor no PLC com tratamento de erro robusto"""
        try:
            # Se PLC não está conectado, apenas registra e continua
            if not self.connected:
                logger.debug(f"PLC não conectado - valor {value} não foi enviado")
                return False

            # Verifica se a conexão ainda está ativa
            if not self.check_connection():
                logger.warning("Conexão PLC perdida")
                self.connected = False
                self._start_auto_reconnect()
                return False

            # Tenta escrever no PLC
            data = self.int_to_bytearray(value)
            self.client.write_area(snap7.Area.DB, 1, 0, data)
            logger.debug(f"✅ Valor {value} escrito no PLC com sucesso")
            return True
            
        except Exception as e:
            self.connected = False
            logger.warning(f"Falha ao escrever no PLC (valor {value}): {e}")
            self._start_auto_reconnect()
            return False

    def disconnect(self):
        """Desconecta do PLC de forma segura e para reconexão automática"""
        try:
            self.stop_reconnect = True
            self.auto_reconnect = False
            
            if self.connection_thread and self.connection_thread.is_alive():
                logger.info("Parando thread de reconexão...")
                
            if self.client and self.client.get_connected():
                self.client.disconnect()
                logger.info("PLC desconectado.")
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
        finally:
            self.connected = False
