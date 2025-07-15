import snap7

class Plc:
    def __init__(self):
        self.client = None

    def init_plc(self):
        try:
            self.client = snap7.client.Client()
            self.client.connect("192.168.2.201", 0, 1)  # IP, rack, slot
            if self.client.get_connected():
                print("PLC connected!")
                return True
            else:
                print("Failed to connect to PLC!.")
                return False
        except Exception as e:
            print(f"Erro to connect to PLC: {e}")
            return False

    @staticmethod
    def int_to_bytearray(number: int) -> bytearray:
        # Convert the integer to bytes
        byte_representation = number.to_bytes(2, byteorder='big', signed=True)

        # Convert the bytes to a bytearray
        return bytearray(byte_representation)

    def write_db(self, value: int):
        try:
            data = self.int_to_bytearray(value)
            self.client.write_area(snap7.Area.DB, 1, 0, data)
            print(f"Wrote value {value} to PLC")
        except Exception as e:
            raise Exception(f"Failed to write to PLC: {e}")
