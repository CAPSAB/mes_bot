

import logging
import struct
import time

from dependency_bootstrap import ensure_runtime_dependencies

logger = logging.getLogger("mesbot.sensors")


_MPU_ADDR_PRIMARY  = 0x68
_MPU_ADDR_ALT      = 0x69
_MPU_PWR_MGMT_1    = 0x6B
_MPU_ACCEL_XOUT_H  = 0x3B   


_INA_ADDR          = 0x40
_INA_REG_CONFIG    = 0x00
_INA_REG_SHUNT     = 0x01
_INA_REG_BUS       = 0x02
_INA_REG_POWER     = 0x03
_INA_REG_CURRENT   = 0x04
_INA_REG_CALIB     = 0x05



_INA_CALIB         = 4096
_INA_CUR_LSB_A     = 0.0001   


class SensorReader:
    

    def __init__(self, bus_number: int = 1):
        self._preferred_bus = bus_number
        self._bus = None
        self._bus_num: int | None = None
        self._mpu_addr: int | None = None
        self._ina_ok: bool = False

    

    def open(self) -> bool:
        
        ensure_runtime_dependencies(["smbus2"])
        try:
            import smbus2 as _smbus  
        except ImportError:
            logger.error(
                "[SENSOR] smbus2 not installed — run: pip install smbus2"
            )
            return False

        for bus_num in (self._preferred_bus, 0, 2, 3):
            try:
                self._bus = _smbus.SMBus(bus_num)
                self._bus_num = bus_num
                logger.info(f"[SENSOR] I2C bus {bus_num} opened (/dev/i2c-{bus_num})")
                break
            except OSError:
                continue

        if self._bus is None:
            logger.error("[SENSOR] Could not open any I2C bus (/dev/i2c-0..3)")
            return False

        self._init_mpu6050()
        self._init_ina219()
        return True

    def close(self):
        if self._bus:
            try:
                self._bus.close()
            except Exception:
                pass
            self._bus = None

    

    def _init_mpu6050(self):
        for addr in (_MPU_ADDR_PRIMARY, _MPU_ADDR_ALT):
            try:
                
                self._bus.write_byte_data(addr, _MPU_PWR_MGMT_1, 0x00)
                time.sleep(0.05)
                
                self._mpu_addr = addr
                logger.info(f"[SENSOR] MPU6050 found at 0x{addr:02X} on /dev/i2c-{self._bus_num}")
                return
            except OSError:
                continue
        logger.warning(
            f"[SENSOR] MPU6050 NOT found on /dev/i2c-{self._bus_num} "
            f"(tried 0x{_MPU_ADDR_PRIMARY:02X} and 0x{_MPU_ADDR_ALT:02X})"
        )

    def _init_ina219(self):
        try:
            
            self._bus.write_i2c_block_data(
                _INA_ADDR, _INA_REG_CONFIG, [0x3F, 0xFF]
            )
            
            self._bus.write_i2c_block_data(
                _INA_ADDR, _INA_REG_CALIB,
                [(_INA_CALIB >> 8) & 0xFF, _INA_CALIB & 0xFF]
            )
            self._ina_ok = True
            logger.info(f"[SENSOR] INA219 found at 0x{_INA_ADDR:02X} on /dev/i2c-{self._bus_num}")
        except OSError:
            logger.warning(
                f"[SENSOR] INA219 NOT found on /dev/i2c-{self._bus_num} at 0x{_INA_ADDR:02X}"
            )

    

    def read_mpu6050(self) -> "dict | None":
        
        if self._mpu_addr is None or self._bus is None:
            return None
        try:
            raw  = self._bus.read_i2c_block_data(self._mpu_addr, _MPU_ACCEL_XOUT_H, 14)
            
            vals = struct.unpack(">7h", bytes(raw))
            ax, ay, az, _temp, gx, gy, gz = vals
            return {
                "ax_g":   round(ax / 16384.0, 4),
                "ay_g":   round(ay / 16384.0, 4),
                "az_g":   round(az / 16384.0, 4),
                "gx_dps": round(gx / 131.0,   2),
                "gy_dps": round(gy / 131.0,   2),
                "gz_dps": round(gz / 131.0,   2),
            }
        except OSError as e:
            logger.debug(f"[SENSOR] MPU6050 read error: {e}")
            return None

    def read_ina219(self) -> "dict | None":
        
        if not self._ina_ok or self._bus is None:
            return None
        try:
            def _read_reg(reg: int, signed: bool) -> int:
                raw = self._bus.read_i2c_block_data(_INA_ADDR, reg, 2)
                fmt = ">h" if signed else ">H"
                return struct.unpack(fmt, bytes(raw))[0]

            bus_raw   = _read_reg(_INA_REG_BUS,     signed=False)
            shunt_raw = _read_reg(_INA_REG_SHUNT,   signed=True)
            cur_raw   = _read_reg(_INA_REG_CURRENT, signed=True)
            pow_raw   = _read_reg(_INA_REG_POWER,   signed=False)

            
            bus_v      = ((bus_raw >> 3) & 0x1FFF) * 0.004
            
            shunt_mv   = shunt_raw * 0.01
            
            current_ma = cur_raw   * (_INA_CUR_LSB_A * 1000.0)
            
            power_mw   = pow_raw   * (20.0 * _INA_CUR_LSB_A * 1000.0)

            return {
                "voltage_v":  round(bus_v,      3),
                "shunt_mv":   round(shunt_mv,   2),
                "current_ma": round(current_ma, 1),
                "power_mw":   round(power_mw,   1),
            }
        except OSError as e:
            logger.debug(f"[SENSOR] INA219 read error: {e}")
            return None

    @property
    def mpu_ok(self) -> bool:
        return self._mpu_addr is not None

    @property
    def ina_ok(self) -> bool:
        return self._ina_ok
