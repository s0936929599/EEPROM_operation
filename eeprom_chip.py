class EEPROMChip():

    chip_info = {

        "24C01":  {"total bytes": 128,   "offset length": 1, "page size": 8,   "total page": 16},
        "24C02":  {"total bytes": 256,   "offset length": 1, "page size": 8,   "total page": 32},
        "24C04":  {"total bytes": 512,   "offset length": 1, "page size": 16,  "total page": 32},
        "24C08":  {"total bytes": 1024,  "offset length": 1, "page size": 16,  "total page": 64},
        "24C16":  {"total bytes": 2048,  "offset length": 1, "page size": 16,  "total page": 128},
        "24C32":  {"total bytes": 4096,  "offset length": 2, "page size": 32,  "total page": 128},
        "24C64":  {"total bytes": 8192,  "offset length": 2, "page size": 32,  "total page": 256},
        "24C128":  {"total bytes": 16384, "offset length": 2, "page size": 64,  "total page": 256},
        "24C256":  {"total bytes": 32768, "offset length": 2, "page size": 64,  "total page": 512},
        "24C512":  {"total bytes": 65536, "offset length": 2, "page size": 128, "total page": 512},

    }

    def __init__(self, type):
        self.type = type

    def get_eeprom_type(self):
        return self.type

    def get_eeprom_bytes(self):
        return self.chip_info[self.type]["total bytes"]

    def get_eeprom_offset_length(self):
        return self.chip_info[self.type]["offset length"]

    def get_eeprom_page_size(self):
        return self.chip_info[self.type]["page size"]

    def get_eeprom_total_page(self):
        return self.chip_info[self.type]["total page"]
