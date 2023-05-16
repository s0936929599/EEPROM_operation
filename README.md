# EEPROM Operation

## Support 
  24C01, 24C02, 24C04, 24C08, 24C16, 24C32, 24C64, 24C128, 24C256, 24C512
## Tool usage

### Read
  * python3 eeprom.py 1 0x50 24C02 -r -o 0x00
  
### Read block
  * python3 eeprom.py 1 0x50 24C02 -rb -o 0x00 -rbs 5
  
### Write
  * python3 eeprom.py 1 0x50 24C02 -w -o 0x00 -d 0x10
  
### Write block
  * python3 eeprom.py 1 0x50 24C02 -wb -o 0x00 -dl 0x10 0x20 0x30 0x40 0x50
  
### Dump
  * python3 eeprom.py 1 0x50 24C02 -edc
  * python3 eeprom.py 1 0x50 24C02 -edc -eds 128 (specify size to dump)
  
### clear
  * python3 eeprom.py 1 0x50 24C02 -ec
  * python3 eeprom.py 1 0x50 24C02 -ec -ecs 128 (specify size to clear)
  
### Write binary content to EEPROM
  * python3 eeprom.py 1 0x50 24C02 -ewb file.bin

### Save EEPROM content to binary file
  * python3 eeprom.py 1 0x50 24C02 -edf file.bin
