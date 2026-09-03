



import re
import json
from arduino.app_utils import Frame

class AppFrame(Frame):
    
    def __init__(
            self,
            id: int,
            name: str,
            position: int,
            duration_ms: int,
            arr,
            brightness_levels: int = 256,
            trajectory_id: int = None,
            command: str = None,
        ):
        
        super().__init__(arr, brightness_levels=brightness_levels)  
        self.id = id
        self.name = name
        self.position = position
        self.duration_ms = duration_ms
        self.trajectory_id = trajectory_id
        self.command = command
        
        self._export_name = self._sanitize_c_ident(self.name or f"frame_{self.id}")

    
    @classmethod
    def from_json(cls, data: dict) -> "AppFrame":
        
        id = data.get('id')
        name = data.get('name')
        position = data.get('position')
        duration_ms = data.get('duration_ms')
        rows = data.get('rows')
        brightness_levels = data.get('brightness_levels')
        trajectory_id = data.get('trajectory_id')
        command = data.get('command')
        return cls.from_rows(id, name, position, duration_ms, rows, brightness_levels=brightness_levels, trajectory_id=trajectory_id, command=command)

    def to_json(self) -> dict:
        
        return {
            "id": self.id,
            "name": self.name,
            "rows": self.arr.tolist(),
            "brightness_levels": int(self.brightness_levels),
            "position": self.position,
            "duration_ms": int(self.duration_ms) if self.duration_ms is not None else 1000,
            "trajectory_id": self.trajectory_id,
            "command": self.command
        }

    

    @classmethod
    def from_record(cls, record: dict) -> "AppFrame":
        
        id = record.get('id')
        name = record.get('name')
        position = record.get('position')
        duration_ms = record.get('duration_ms')
        rows = json.loads(record.get('rows'))
        brightness_levels = record.get('brightness_levels')
        trajectory_id = record.get('trajectory_id')
        command = record.get('command')
        return cls.from_rows(id, name, position, duration_ms, rows, brightness_levels=brightness_levels, trajectory_id=trajectory_id, command=command)

    def to_record(self) -> dict:
        
        return {
            "id": self.id,
            "name": self.name,
            "rows": json.dumps(self.arr.tolist()),
            "brightness_levels": int(self.brightness_levels),
            "position": self.position,
            "duration_ms": int(self.duration_ms) if self.duration_ms is not None else 1000,
            "trajectory_id": self.trajectory_id,
            "command": self.command
        }

    
    def to_c_string(self) -> str:
        
        c_type = "uint8_t"
        
        snake_name = self._export_name
        
        scaled_arr = self.rescale_quantized_frame(scale_max=max(1, int(self.brightness_levels) - 1))

        parts = [f"{c_type} {snake_name} [] = {{"]
        rows = scaled_arr.tolist()
        
        for r_idx, row in enumerate(rows):
            line = ", ".join(str(int(v)) for v in row)
            if r_idx < len(rows) - 1:
                parts.append(f"  {line},")
            else:
                parts.append(f"  {line}")
        parts.append("};")
        parts.append("")
        return "\n".join(parts)

    def to_board_bytes(self) -> bytes:
        
        scaled = self.rescale_quantized_frame(scale_max=max(1, int(self.brightness_levels) - 1))
        flat = [int(x) for x in scaled.flatten().tolist()]
        return bytes(flat)

    @staticmethod
    def _sanitize_c_ident(name: str, fallback: str = "frame") -> str:
        

        if name is None:
            return fallback
        s = str(name).strip().lower()
        if not s:
            return fallback

        
        s = re.sub(r'[^a-z0-9_]', '_', s)
        
        s = re.sub(r'_+', '_', s)
        
        s = s.strip('_')
        if not s:
            return fallback
        if re.match(r'^[0-9]', s):
            s = f"f_{s}"
        return s
    
    
    @classmethod
    def create_empty(
        cls,
        id: int,
        name: str,
        position: int,
        duration_ms: int,
        brightness_levels: int = 256,
        trajectory_id: int = None,
        command: str = None,
    ) -> "AppFrame":
        
        import numpy as np
        height = 8
        width = 13
        arr = np.zeros((height, width), dtype=np.uint8)
        return cls(id, name, position, duration_ms, arr, brightness_levels=brightness_levels, trajectory_id=trajectory_id, command=command)

    
    def set_array(self, arr) -> "AppFrame":
        super().set_array(arr)
        return self

    def set_value(self, row: int, col: int, value: int) -> None:
        return super().set_value(row, col, value)

    
    def to_animation_hex(self) -> list[str]:
        
        
        arr_scaled = self.rescale_quantized_frame(scale_max=255)
        height, width = arr_scaled.shape
        
        
        pixels = (arr_scaled > 0).astype(int).flatten().tolist()
        
        
        if len(pixels) > 128:
            raise ValueError(f"Pixel buffer too large: {len(pixels)} > 128")
        pixels += [0] * (128 - len(pixels))
        
        
        hex_values = []
        for i in range(0, 128, 32):
            value = 0
            for j in range(32):
                bit = int(pixels[i + j]) & 1
                value |= bit << (31 - j)
            hex_values.append(f"0x{value:08x}")
        
        
        duration = int(self.duration_ms) if self.duration_ms is not None else 1000
        hex_values.append(str(duration))
        
        return hex_values

    @staticmethod
    def frames_to_c_animation_array(frames: list, name: str = 'Animation') -> str:
        
        
        snake = AppFrame._sanitize_c_ident(name or 'Animation')
        parts = [f"const uint32_t {snake}[][5] = {{"]
        for frame in frames:
            hex_values = frame.to_animation_hex()
            hex_str = ", ".join(hex_values)
            parts.append(f"    {{{hex_str}}},  // {getattr(frame, '_export_name', frame.name)}")
        parts.append("};")
        parts.append("")
        return "\n".join(parts)

    
    @classmethod
    def from_rows(
        cls,
        id: int,
        name: str,
        position: int,
        duration_ms: int,
        rows: list[list[int]] | list[str],
        brightness_levels: int = 256,
        trajectory_id: int = None,
        command: str = None,
    ) -> "AppFrame":
        
        
        
        
        
        try:
            frame_instance = super().from_rows(rows, brightness_levels=brightness_levels)
            arr = frame_instance.arr.copy()
            return cls(id, name, position, duration_ms, arr, brightness_levels=frame_instance.brightness_levels, trajectory_id=trajectory_id, command=command)
        except ValueError:
            
            raw = super().from_rows(rows, brightness_levels=256)
            
            target_max = max(1, int(brightness_levels) - 1)
            scaled = raw.rescale_quantized_frame(scale_max=target_max)
            arr = scaled.copy()
            return cls(id, name, position, duration_ms, arr, brightness_levels=brightness_levels, trajectory_id=trajectory_id, command=command)

