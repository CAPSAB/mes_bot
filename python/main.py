import site
site.addsitedir("/home/app/.local/lib/python3.13/site-packages")

from dependency_bootstrap import ensure_runtime_dependencies

ensure_runtime_dependencies()


import serial



import os as _os
_ENV_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".env")
if _os.path.isfile(_ENV_PATH):
    with open(_ENV_PATH) as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _os.environ.setdefault(_k.strip(), _v.strip())


import shutil
import json, ast
from datetime import datetime, UTC
import io
import math
import time
import base64
import collections
import threading
import urllib.request
import urllib.parse
import urllib.error
import typing
import os
import sys
import subprocess
import struct
import wave
import qrcode

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None


def ensure_dependencies(logger):
    
    try:
        ensure_runtime_dependencies()
        logger.info("[BOOT] Dependencies verified.")
    except Exception as e:
        logger.error(f"[BOOT] Failed to install dependencies: {e}")
        







_shared_audio = collections.deque(maxlen=16000 * 2 * 4) 
_audio_lock = threading.Lock()

try:
    import alsaaudio
    _OrigPCM = alsaaudio.PCM
    
    class DummyPCM:
        def __init__(self, *args, **kwargs):
            self._periodsize = kwargs.get("periodsize", 160)
        def read(self, *args, **kwargs):
            frames = args[0] if args else self._periodsize
            time.sleep(frames / 16000.0)
            return frames, b"\x00" * (frames * 2)
        def setrate(self, rate): pass
        def setchannels(self, channels): pass
        def setformat(self, format): pass
        def setperiodsize(self, periodsize):
            self._periodsize = periodsize

    class PatchedPCM:
        def __init__(self, *args, **kwargs):
            try:
                self._pcm = _OrigPCM(*args, **kwargs)
                self._is_dummy = False
            except Exception as e:
                print(f"[VOICE/SR] ALSA open failed ({e}), falling back to dummy mic.", flush=True)
                PERIPHERALS_STATUS["microphone"] = False
                self._pcm = DummyPCM(*args, **kwargs)
                self._is_dummy = True
        def __getattr__(self, name):
            return getattr(self._pcm, name)
        def read(self, *args, **kwargs):
            l, data = self._pcm.read(*args, **kwargs)
            if not self._is_dummy and data and l > 0:
                with _audio_lock:
                    _shared_audio.extend(data)
            return l, data
            
    alsaaudio.PCM = PatchedPCM
    print("[VOICE/SR] Successfully monkey-patched alsaaudio.PCM for mic sharing.")
except ImportError:
    print("[VOICE/SR] alsaaudio not found, cannot monkey-patch.")



from PIL.Image import Image
from PIL import ImageDraw
from arduino.app_bricks.camera_code_detection import CameraCodeDetection, Detection, draw_bounding_box
from arduino.app_bricks.dbstorage_sqlstore import SQLStore
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI

try:
    from arduino.app_bricks.keyword_spotting import KeywordSpotting as _KeywordSpotting
except ImportError:
    _KeywordSpotting = None

import unicodedata
import re
from difflib import SequenceMatcher

from logic import interpret_command, _normalize_state, _ensure_dict, COMMAND_LEXICON

from arduino.app_utils import App, Bridge, FrameDesigner, Logger
from app_frame import AppFrame  
import store  
from control_config import (
    DEFAULT_CONTROL_PROFILE,
    PROFILE_FILENAME,
    ProfileValidationError,
    TUNING_ORDER,
    VERIFICATION_KEYS,
    corrected_ticks_per_mm,
    load_control_profile,
    save_control_profile,
    validated_updates,
)




PERIPHERALS_STATUS = {
    "camera": True,
    "microphone": True,
    "mcu_serial": True,
    "database": True
}

from store import SafeSQLStoreWrapper







_EI_MODEL_PATH = os.environ.get("EI_KEYWORD_SPOTTING_MODEL", "").strip()

_ei_model_available = (
    _KeywordSpotting is not None
    and bool(_EI_MODEL_PATH)
)

spotter = None
if not _ei_model_available:
    PERIPHERALS_STATUS["microphone"] = False

BRIGHTNESS_LEVELS = 8  

logger = Logger("led-matrix-painter")
ensure_dependencies(logger)
designer = FrameDesigner()
ui = WebUI()

CONTROL_PROFILE_PATH = os.path.join(store.DATA_DIR, PROFILE_FILENAME)
try:
    FULL_TUNING_PROFILE, CONTROL_PROFILE_METADATA = load_control_profile(
        CONTROL_PROFILE_PATH
    )
except ProfileValidationError as exc:
    logger.error(f"[ROBOT] Invalid persisted control profile: {exc}")
    FULL_TUNING_PROFILE = dict(DEFAULT_CONTROL_PROFILE)
    CONTROL_PROFILE_METADATA = {
        "source": "bootstrap_defaults_after_invalid_profile",
        "calibrated": False,
        "updated_at": None,
        "error": str(exc),
    }

APPLY_TUNING_ON_START = True
ROBOT_INIT_DELAY_S = 3.5
STATE_POLL_INTERVAL_S = 0.25
IDLE_CONFIRMATION_COUNT = 3
ROBOT_COMMAND_TIMEOUT_S = 80.0

EXPECTED_CRITICAL_TUNING = {
    key: FULL_TUNING_PROFILE[key] for key in VERIFICATION_KEYS
}

COMMAND_TO_BRIDGE = {
    "forward": "move_forward",
    "backward": "move_backward",
    "turn_left": "turn_90_left",
    "turn_right": "turn_90_right",
    "stop": "stop_robot",
}

CANON_TO_ROBOT_COMMAND = {
    "FORWARD": "forward",
    "BACKWARD": "backward",
    "LEFT": "turn_left",
    "RIGHT": "turn_right",
    "STOP": "stop",
}

_robot_motion_lock = threading.RLock()
_robot_step_lock = threading.Lock()
_robot_bridge_io_lock = threading.RLock()
_robot_ready_event = threading.Event()
_robot_motion_complete_event = threading.Event()
_robot_initialized = False
_robot_init_error = ""
_robot_motion_active = False
_robot_motion_result_code = None
_last_known_robot_state = None
_last_robot_state_monotonic = 0.0
ROBOT_STATE_CACHE_TTL_S = 0.50

def bridge_call_serialized(name: str, *args):
    
    with _robot_bridge_io_lock:
        return Bridge.call(name, *args) if args else Bridge.call(name)

def robot_bridge_call(name: str, *args) -> str:
    
    global _last_robot_state_monotonic
    try:
        
        
        
        result = bridge_call_serialized(name, *args)
        text = str(result)
        if name not in {"get_state", "get_motion_state"}:
            _last_robot_state_monotonic = 0.0
        logger.debug(f"[ROBOT] {name} -> {text}")
        return text
    except Exception as exc:
        text = f"ERROR calling {name}: {exc}"
        logger.error(f"[ROBOT] {text}")
        return text

def parse_robot_state(raw: str):
    try:
        raw_str = str(raw or "").strip()
        start_idx = raw_str.find('{')
        end_idx = raw_str.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_slice = raw_str[start_idx:end_idx + 1]
            return json.loads(json_slice)
        return json.loads(raw_str)
    except Exception:
        return None

def get_robot_state(print_raw: bool = False, *, force: bool = False, full: bool = False):
    global _last_known_robot_state, _last_robot_state_monotonic
    if _robot_motion_active and not force:
        
        
        return _last_known_robot_state
    now = time.monotonic()
    if (
        not full
        and not force
        and _last_known_robot_state is not None
        and now - _last_robot_state_monotonic < ROBOT_STATE_CACHE_TTL_S
    ):
        return _last_known_robot_state

    try:
        with _robot_bridge_io_lock:
            
            
            now = time.monotonic()
            if (
                not full
                and not force
                and _last_known_robot_state is not None
                and now - _last_robot_state_monotonic < ROBOT_STATE_CACHE_TTL_S
            ):
                return _last_known_robot_state
            bridge_method = "get_state" if full else "get_motion_state"
            raw = str(bridge_call_serialized(bridge_method))
        if print_raw:
            logger.info(f"[ROBOT] state={raw}")
        parsed = parse_robot_state(raw)
        if parsed and isinstance(parsed, dict) and "mode" in parsed:
            _last_known_robot_state = parsed
            _last_robot_state_monotonic = time.monotonic()
            return parsed
        return _last_known_robot_state
    except Exception as exc:
        logger.error(f"[ROBOT] ERROR calling get_state: {exc}")
        return _last_known_robot_state

def get_full_robot_state(print_raw: bool = False):
    
    return get_robot_state(print_raw=print_raw, force=True, full=True)

def get_robot_guard_state():
    
    try:
        raw = str(bridge_call_serialized("get_motion_guard"))
        return parse_robot_state(raw)
    except Exception as exc:
        logger.error(f"[ROBOT] ERROR calling get_motion_guard: {exc}")
        return None

def on_robot_motion_complete(*args):
    
    global _robot_motion_result_code
    value = args[0] if args else 0
    if isinstance(value, (list, tuple)):
        value = value[0] if value else 0
    try:
        _robot_motion_result_code = int(value)
    except (TypeError, ValueError):
        _robot_motion_result_code = 1
    _robot_motion_complete_event.set()

def set_robot_values(values: dict) -> str:
    payload = json.dumps(values, separators=(",", ":"))
    return robot_bridge_call("set_values", payload)

def apply_tuning_profile() -> bool:
    logger.info(
        "[ROBOT] Applying control profile "
        f"source={CONTROL_PROFILE_METADATA.get('source')} "
        f"calibrated={CONTROL_PROFILE_METADATA.get('calibrated')}."
    )
    success = True
    for key, category in TUNING_ORDER:
        value = FULL_TUNING_PROFILE[key]
        result = set_robot_values({key: value})
        if "ERROR" in result or "applied=1" not in result:
            logger.error(
                f"[ROBOT] Failed to set {key} ({category}): {result}"
            )
            success = False
        time.sleep(0.035)
    return success

def verify_critical_tuning() -> bool:
    state = get_full_robot_state(print_raw=False)
    if state is None:
        logger.error("[ROBOT] Critical tuning verification failed: get_state failed.")
        robot_bridge_call("stop_robot")
        return False

    ok = True
    for key, expected_value in EXPECTED_CRITICAL_TUNING.items():
        if key not in state:
            logger.error(f"[ROBOT] Profile verification field missing: {key}")
            ok = False
            continue
        actual_value = float(state[key])
        logger.info(f"[ROBOT] {key}: expected={expected_value:.4f} actual={actual_value:.4f}")
        tolerance = 0.5 if isinstance(expected_value, int) else 0.001
        if abs(actual_value - expected_value) > tolerance:
            ok = False

    if not ok:
        logger.error("[ROBOT] Critical tuning mismatch. Stopping before movement.")
        robot_bridge_call("stop_robot")
        return False

    logger.info("[ROBOT] Critical tuning verified.")
    return True

def robot_state_is_fault(state) -> bool:
    return bool(state and state.get("mode") == "FAULT")

def robot_state_is_idle(state) -> bool:
    return bool(
        state
        and state.get("mode") == "IDLE"
        and state.get("macro_mode", "NONE") == "NONE"
    )

def robot_motion_succeeded(state, *, require_heading_result: bool = True) -> bool:
    
    if not isinstance(state, dict):
        return False
    if state.get("_motion_timed_out") is not False:
        return False
    if state.get("_motion_event_received") is not True:
        return False
    if state.get("_motion_result_code") != 0:
        return False
    if not robot_state_is_idle(state) or robot_state_is_fault(state):
        return False
    if require_heading_result and state.get("step_heading_result") != "COMPLETED":
        return False
    return True

def validate_init_result(init_result: str) -> bool:
    
    bno_ready = (
        "BNO080=OK" in init_result
        and "yaw_valid=1" in init_result
    )
    if not bno_ready:
        logger.error(f"[ROBOT] IMU/BNO080 not ready: {init_result}")
        robot_bridge_call("stop_robot")
        return False
    if "INA219=NOT_FOUND" in init_result:
        logger.warning("[ROBOT] INA219 not found — battery telemetry disabled, but motion is ready.")
    return True

def wait_until_robot_idle(
    label: str,
    timeout_s: float = ROBOT_COMMAND_TIMEOUT_S,
    *,
    require_heading_result: bool = True,
):
    
    
    event_received = _robot_motion_complete_event.wait(timeout_s)
    timed_out = not event_received
    if timed_out:
        logger.error(f"[ROBOT] Timeout during {label}; stopping robot.")
        robot_bridge_call("stop_robot")
        _robot_motion_complete_event.wait(2.0)

    state = dict(get_robot_state(print_raw=False, force=True) or {})
    state["_motion_event_received"] = bool(event_received)
    state["_motion_result_code"] = _robot_motion_result_code
    state["_motion_timed_out"] = bool(timed_out)
    if robot_state_is_fault(state) or _robot_motion_result_code == 1:
        logger.error(f"[ROBOT] Fault during {label}: {state.get('fault_reason')}")
    elif robot_motion_succeeded(
        state, require_heading_result=require_heading_result
    ):
        logger.info(f"[ROBOT] Done: {label}")
    else:
        logger.error(
            f"[ROBOT] Primitive did not complete successfully during {label}: "
            f"event={event_received} result={_robot_motion_result_code} "
            f"step={state.get('step_heading_result')} state={state}"
        )
    return state

def settle_before_robot_command(label: str) -> bool:
    result = robot_bridge_call("settle_robot")
    if "imu_heading_capture_failed" in result or "ERROR" in result or "busy" in result.lower():
        logger.error(f"[ROBOT] Settle failed before {label}: {result}")
        robot_bridge_call("stop_robot")
        return False
    time.sleep(0.25)
    return True

def initialize_robot() -> bool:
    logger.info("[ROBOT] Initializing qwiic primitive control layer.")
    init_result = robot_bridge_call("init_robot")
    if not validate_init_result(init_result):
        return False

    time.sleep(0.8)
    zero_result = robot_bridge_call("zero_pose")
    if "ERROR" in zero_result or "failed" in zero_result.lower():
        logger.error(f"[ROBOT] Zero pose failed: {zero_result}")
        robot_bridge_call("stop_robot")
        return False

    time.sleep(0.5)
    get_robot_state(print_raw=True)

    if APPLY_TUNING_ON_START:
        tuning_ok = apply_tuning_profile()
        if not tuning_ok:
            logger.warning("[ROBOT] At least one tuning value failed to apply.")
        if not verify_critical_tuning():
            return False

    return True

def initialize_robot_background() -> None:
    global _robot_initialized, _robot_init_error
    time.sleep(ROBOT_INIT_DELAY_S)
    for attempt in range(1, 4):
        try:
            logger.info(f"[ROBOT] Initializing robot attempt {attempt}/3...")
            _robot_initialized = initialize_robot()
            if _robot_initialized:
                _robot_init_error = ""
                PERIPHERALS_STATUS["mcu_serial"] = True
                ui.send_message("robot_init_status", {"ready": True, "error": None, "timestamp": _iso_now()})
                logger.info("[ROBOT] Robot initialized successfully and ready for motion.")
                break
            else:
                _robot_init_error = f"attempt_{attempt}_failed"
                logger.warning(f"[ROBOT] Attempt {attempt} failed, retrying after pause...")
                time.sleep(2.0)
        except Exception as e:
            _robot_initialized = False
            _robot_init_error = str(e)
            logger.error(f"[ROBOT] Robot init exception on attempt {attempt}: {e}")
            time.sleep(2.0)

    if not _robot_initialized:
        PERIPHERALS_STATUS["mcu_serial"] = False
        ui.send_message("robot_init_status", {"ready": False, "error": _robot_init_error, "timestamp": _iso_now()})
    _robot_ready_event.set()

def ensure_robot_ready(timeout_s: float = 6.0) -> bool:
    if _robot_ready_event.wait(timeout_s) and _robot_initialized:
        return True
    if _robot_init_error:
        logger.error(f"[ROBOT] Robot not ready: {_robot_init_error}")
    else:
        logger.error("[ROBOT] Robot initialization has not completed.")
    return False

def send_robot_command(command: str, wait: bool = True):
    global _robot_motion_active, _robot_motion_result_code
    command = (command or "").strip().lower()
    if command not in COMMAND_TO_BRIDGE:
        logger.error(f"[ROBOT] Unknown command: {command}")
        return {"mode": "FAULT", "fault_reason": f"unknown_command:{command}"}

    bridge_name = COMMAND_TO_BRIDGE[command]
    label = command.upper()

    if command == "stop":
        robot_bridge_call("stop_robot")
        return get_robot_state(print_raw=False)

    if not _robot_initialized and not ensure_robot_ready(timeout_s=1.0):
        
        logger.warning(f"[ROBOT] Executing manual command '{command}' while init is pending.")

    if not _robot_motion_lock.acquire(blocking=False):
        logger.warning(f"[ROBOT] Rejected {label}: another motion command is active.")
        return {"mode": "BUSY", "fault_reason": "motion_command_already_active"}

    try:
        _robot_motion_active = True
        _robot_motion_result_code = None
        _robot_motion_complete_event.clear()
        if not settle_before_robot_command(label):
            return get_robot_state(print_raw=False, force=True)

        
        
        _robot_motion_result_code = None
        _robot_motion_complete_event.clear()
        result = robot_bridge_call(bridge_name)
        if (
            "ERROR" in result
            or "busy" in result.lower()
            or "failed" in result.lower()
            or "sensor_not_ready" in result
            or "imu_heading_capture_failed" in result
        ):
            logger.error(f"[ROBOT] Command failed: {command} -> {result}")
            robot_bridge_call("stop_robot")
            return get_robot_state(print_raw=False, force=True)

        if wait:
            return wait_until_robot_idle(label)

        return {"mode": "STARTED", "fault_reason": ""}
    finally:
        _robot_motion_active = False
        _robot_motion_lock.release()

def send_robot_bridge_primitive(
    bridge_name: str,
    payload: dict,
    label: str,
):
    
    global _robot_motion_active, _robot_motion_result_code
    if not _robot_motion_lock.acquire(blocking=False):
        return {"mode": "BUSY", "fault_reason": "motion_command_already_active"}
    try:
        _robot_motion_active = True
        _robot_motion_result_code = None
        _robot_motion_complete_event.clear()
        if not settle_before_robot_command(label):
            return get_robot_state(print_raw=False, force=True)

        _robot_motion_result_code = None
        _robot_motion_complete_event.clear()
        result = robot_bridge_call(
            bridge_name,
            json.dumps(payload, separators=(",", ":")),
        )
        result_lower = result.lower()
        if (
            "error" in result_lower
            or "invalid" in result_lower
            or "outside_safe_range" in result_lower
            or "busy" in result_lower
            or "failed" in result_lower
        ):
            logger.error(f"[ROBOT] Relative primitive failed: {result}")
            robot_bridge_call("stop_robot")
            return get_robot_state(print_raw=False, force=True)
        return wait_until_robot_idle(label)
    finally:
        _robot_motion_active = False
        _robot_motion_lock.release()

def get_robot_telemetry_for_web():
    
    
    
    if _robot_motion_active and _last_known_robot_state is not None:
        state = _last_known_robot_state
    else:
        state = get_robot_state(print_raw=False)
    if state is None:
        return {
            "ok": False,
            "ready": _robot_initialized,
            "error": _robot_init_error or "get_state_failed",
        }

    return {
        "ok": True,
        "ready": _robot_initialized,
        "state": state,
        "mode": state.get("mode"),
        "fault_reason": state.get("fault_reason", ""),
        "battery_v": state.get("battery_v"),
        "battery_percent_est": state.get("battery_percent_est"),
        "left_ticks": state.get("left_ticks"),
        "right_ticks": state.get("right_ticks"),
        "left_distance_mm": state.get("left_distance_mm"),
        "right_distance_mm": state.get("right_distance_mm"),
        "average_distance_mm": state.get("average_distance_mm"),
        "pose_x_mm": state.get("pose_x_mm"),
        "pose_y_mm": state.get("pose_y_mm"),
        "pose_distance_mm": state.get("pose_distance_mm"),
        "pose_heading_deg": state.get("pose_heading_deg"),
        "left_target": state.get("left_target"),
        "right_target": state.get("right_target"),
        "left_progress": state.get("left_progress"),
        "right_progress": state.get("right_progress"),
        "progress_diff": state.get("progress_diff"),
        "left_speed_tps": state.get("left_speed_tps"),
        "right_speed_tps": state.get("right_speed_tps"),
        "left_raw_speed_tps": state.get("left_raw_speed_tps"),
        "right_raw_speed_tps": state.get("right_raw_speed_tps"),
        "left_target_speed_tps": state.get("left_target_speed_tps"),
        "right_target_speed_tps": state.get("right_target_speed_tps"),
        "left_pwm": state.get("left_pwm"),
        "right_pwm": state.get("right_pwm"),
        "left_ff_term": state.get("left_ff_term"),
        "left_p_term": state.get("left_p_term"),
        "left_i_term": state.get("left_i_term"),
        "left_d_term": state.get("left_d_term"),
        "left_unsaturated_pwm": state.get("left_unsaturated_pwm"),
        "left_saturated": state.get("left_saturated"),
        "right_ff_term": state.get("right_ff_term"),
        "right_p_term": state.get("right_p_term"),
        "right_i_term": state.get("right_i_term"),
        "right_d_term": state.get("right_d_term"),
        "right_unsaturated_pwm": state.get("right_unsaturated_pwm"),
        "right_saturated": state.get("right_saturated"),
        "straight_heading_p_tps": state.get("straight_heading_p_tps"),
        "straight_heading_i_tps": state.get("straight_heading_i_tps"),
        "straight_heading_d_tps": state.get("straight_heading_d_tps"),
        "straight_heading_correction_tps": state.get("straight_heading_correction_tps"),
        "straight_cross_track_error_mm": state.get("straight_cross_track_error_mm"),
        "straight_path_heading_offset_deg": state.get("straight_path_heading_offset_deg"),
        "turn_heading_p_tps": state.get("turn_heading_p_tps"),
        "turn_heading_i_tps": state.get("turn_heading_i_tps"),
        "turn_heading_d_tps": state.get("turn_heading_d_tps"),
        "turn_heading_correction_tps": state.get("turn_heading_correction_tps"),
        "bno_ok": state.get("bno_ok"),
        "ina_ok": state.get("ina_ok"),
        "imu_ax": state.get("imu_ax"),
        "imu_ay": state.get("imu_ay"),
        "imu_az": state.get("imu_az"),
        "imu_gx": state.get("imu_gx"),
        "imu_gy": state.get("imu_gy"),
        "imu_gz": state.get("imu_gz"),
        "robot_heading_deg": state.get("robot_heading_deg"),
        "target_yaw_deg": state.get("target_yaw_deg"),
        "yaw_error_deg": state.get("yaw_error_deg"),
        "yaw_rate_deg_s": state.get("yaw_rate_deg_s"),
        "step_heading_result": state.get("step_heading_result"),
        "step_start_yaw_deg": state.get("step_start_yaw_deg"),
        "step_end_yaw_deg": state.get("step_end_yaw_deg"),
        "step_requested_yaw_delta_deg": state.get("step_requested_yaw_delta_deg"),
        "step_actual_yaw_delta_deg": state.get("step_actual_yaw_delta_deg"),
        "step_final_yaw_error_deg": state.get("step_final_yaw_error_deg"),
        "step_end_heading_stable": state.get("step_end_heading_stable"),
        "step_requested_distance_mm": state.get("step_requested_distance_mm"),
        "step_left_distance_mm": state.get("step_left_distance_mm"),
        "step_right_distance_mm": state.get("step_right_distance_mm"),
        "step_actual_distance_mm": state.get("step_actual_distance_mm"),
        "step_distance_error_mm": state.get("step_distance_error_mm"),
        "imu_rotation_age_ms": state.get("imu_rotation_age_ms"),
        "imu_gyro_age_ms": state.get("imu_gyro_age_ms"),
        "imu_rotation_accuracy": state.get("imu_rotation_accuracy"),
        "imu_heading_accuracy_rad": state.get("imu_heading_accuracy_rad"),
        "turn_requested_delta_deg": state.get("turn_requested_delta_deg"),
        "turn_signed_progress_deg": state.get("turn_signed_progress_deg"),
        "turn_rotation_progress_deg": state.get("turn_unwrapped_progress_deg"),
        "turn_gyro_progress_deg": state.get("turn_gyro_progress_deg"),
        "turn_encoder_progress_deg": state.get("turn_encoder_progress_deg"),
        "turn_fused_progress_deg": state.get("turn_fused_progress_deg"),
        "turn_sensor_disagreement_deg": state.get("turn_sensor_disagreement_deg"),
        "turn_fusion_selected_pair": state.get("turn_fusion_selected_pair"),
        "turn_balance_error_mm": state.get("turn_balance_error_mm"),
        "turn_center_translation_mm": state.get("turn_center_translation_mm"),
        "turn_center_speed_mm_s": state.get("turn_center_speed_mm_s"),
        "turn_balance_correction_tps": state.get("turn_balance_correction_tps"),
        "turn_remaining_deg": state.get("turn_remaining_deg"),
        "bno_empty_polls": state.get("bno_empty_polls"),
        "bno_short_reads": state.get("bno_short_reads"),
        "bno_budget_hits": state.get("bno_budget_hits"),
        "slip_counter": state.get("slip_counter"),
        "left_stall_counter": state.get("left_stall_counter"),
        "right_stall_counter": state.get("right_stall_counter"),
        "tune_version": state.get("tune_version"),
        "control_period_ms": state.get("control_period_ms"),
        "last_control_dt_ms": state.get("last_control_dt_ms"),
        "max_control_dt_ms": state.get("max_control_dt_ms"),
        "control_deadline_misses": state.get("control_deadline_misses"),
        "straight_endpoint_aligning": state.get("straight_endpoint_aligning"),
        "speed_test_left_tps": state.get("speed_test_left_tps"),
        "speed_test_right_tps": state.get("speed_test_right_tps"),
        "LEFT_TICKS_PER_REV": state.get("LEFT_TICKS_PER_REV"),
        "RIGHT_TICKS_PER_REV": state.get("RIGHT_TICKS_PER_REV"),
        "LEFT_TICKS_PER_MM": state.get("LEFT_TICKS_PER_MM"),
        "RIGHT_TICKS_PER_MM": state.get("RIGHT_TICKS_PER_MM"),
        "LEFT_LINEAR_SCALE": state.get("LEFT_LINEAR_SCALE"),
        "RIGHT_LINEAR_SCALE": state.get("RIGHT_LINEAR_SCALE"),
        "FORWARD_DISTANCE_TICK_SCALE": state.get("FORWARD_DISTANCE_TICK_SCALE"),
        "BACKWARD_DISTANCE_TICK_SCALE": state.get("BACKWARD_DISTANCE_TICK_SCALE"),
        "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM": state.get("STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM"),
        "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG": state.get("STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG"),
        "TURN_LEFT_DEG_SCALE": state.get("TURN_LEFT_DEG_SCALE"),
        "TURN_RIGHT_DEG_SCALE": state.get("TURN_RIGHT_DEG_SCALE"),
    }

def execute_robot_motion(canon: str, source: str = "web") -> bool:
    command = CANON_TO_ROBOT_COMMAND.get(canon)
    if not command:
        logger.error(f"[ROBOT] Unsupported canonical command: {canon}")
        return False

    if canon == "STOP":
        stop_event = globals().get("_seq_stop_event")
        if stop_event is not None:
            stop_event.set()
        qr_cancel_event = globals().get("_QR_CENTER_CANCEL_EVENT")
        if qr_cancel_event is not None:
            qr_cancel_event.set()
        qr_active_event = globals().get("_QR_CENTERING_ACTIVE")
        if qr_active_event is not None:
            qr_active_event.clear()
        send_robot_command("stop", wait=False)
        ui.send_message("robot_motion_status", {
            "command": canon,
            "source": source,
            "status": "stopped",
            "timestamp": _iso_now(),
        })
        return True

    
    
    qr_active_event = globals().get("_QR_CENTERING_ACTIVE")
    if qr_active_event is not None:
        qr_active_event.clear()
    detection_state = globals().get("_DETECTION_STATE")
    if isinstance(detection_state, dict):
        detection_state["pending_content"] = None

    if not _robot_step_lock.acquire(blocking=False):
        ui.send_message("robot_motion_status", {
            "command": canon,
            "source": source,
            "status": "busy",
            "fault_reason": "motion_step_already_active",
            "timestamp": _iso_now(),
        })
        return False

    try:
        state = send_robot_command(command, wait=True)
        primary_ok = robot_motion_succeeded(state)
        
        
        qr_centering = {
            "ok": True,
            "status": "qr_motion_control_disabled",
        } if primary_ok else None
        ok = primary_ok
        ui.send_message("robot_motion_status", {
            "command": canon,
            "source": source,
            "status": "ok" if ok else "failed",
            "fault_reason": (
                (state or {}).get("fault_reason")
                if isinstance(state, dict) else None
            ),
            "qr_centering": qr_centering,
            "timestamp": _iso_now(),
        })

        if ok:
            _verify_trajectory_step(canon, state)
        else:
            ui.send_message("trajectory_contrast", {
                "status": "robot_failed",
                "received": canon,
                "fault_reason": (
                    (state or {}).get("fault_reason")
                    if isinstance(state, dict) else "unknown"
                ),
                "qr_centering": qr_centering,
            })

        return ok
    finally:
        _robot_step_lock.release()



PIN_CONFIG = {
    "D21": {"active_low": False},
    "D20": {"active_low": False},   
    "D13": {"active_low": False},
    "D12": {"active_low": False},
    "D11": {"active_low": False},
    "D10": {"active_low": False},
    "D9": {"active_low": False},
    "D8": {"active_low": False},
    "D7": {"active_low": False},
    "D6": {"active_low": False},
    "D5": {"active_low": False},
    "D4": {"active_low": False},
    "D3": {"active_low": False},
    "D2": {"active_low": False},
    "D1": {"active_low": False},
    "D0": {"active_low": False},
    "A0": {"active_low": False},
    "A1": {"active_low": False},
    "A2": {"active_low": False},
    "A3": {"active_low": False},
    "A4": {"active_low": False},
    "A5": {"active_low": False},
    "LED3_R": {"active_low": True},
    "LED3_G": {"active_low": True},
    "LED3_B": {"active_low": True},
    "LED4_R": {"active_low": True},
    "LED4_G": {"active_low": True},
    "LED4_B": {"active_low": True},

}
ROBOT_RESERVED_PIN_NAMES = frozenset({
    "D2", "D3", "D4", "D5", "D6",
    "D7", "D8", "D9", "D10", "D11",
})
PIN_NAMES = tuple(PIN_CONFIG.keys())
pin_states = {name: False for name in PIN_NAMES}

def _iso_now() -> str:
    return datetime.now(UTC).isoformat()

_AUDIO_CUE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "assets",
    "common",
    "temp_audio"
)
_AUDIO_CUE_FILES = {
    "step": os.path.join(_AUDIO_CUE_DIR, "mesbot_step.wav"),
    "complete": os.path.join(_AUDIO_CUE_DIR, "mesbot_complete.wav"),
}
_AUDIO_WARNED_UNAVAILABLE = False


def _write_tone(path: str, notes: list[tuple[float, float]], volume: float = 0.34) -> None:
    
    sample_rate = 44100
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for freq, duration in notes:
            sample_count = int(sample_rate * duration)
            for idx in range(sample_count):
                envelope = min(1.0, idx / max(1, int(sample_rate * 0.012)))
                tail = max(0.0, min(1.0, (sample_count - idx) / max(1, int(sample_rate * 0.035))))
                amp = volume * min(envelope, tail)
                sample = int(32767 * amp * math.sin(2 * math.pi * freq * idx / sample_rate))
                frames.extend(struct.pack("<h", sample))
        wav.writeframes(bytes(frames))


def _ensure_audio_cues() -> None:
    if all(os.path.isfile(path) for path in _AUDIO_CUE_FILES.values()):
        return
    _write_tone(_AUDIO_CUE_FILES["step"], [(880.0, 0.075), (1174.66, 0.095)])
    _write_tone(_AUDIO_CUE_FILES["complete"], [(784.0, 0.08), (987.77, 0.08), (1318.51, 0.13)])


def _play_linux_audio_cue(kind: str = "step") -> None:
    
    global _AUDIO_WARNED_UNAVAILABLE
    try:
        _ensure_audio_cues()
        cue_path = _AUDIO_CUE_FILES.get(kind, _AUDIO_CUE_FILES["step"])
        player = shutil.which("aplay") or shutil.which("paplay")
        if not player:
            if not _AUDIO_WARNED_UNAVAILABLE:
                logger.warning("[AUDIO] No Linux audio player found (tried aplay, paplay).")
                _AUDIO_WARNED_UNAVAILABLE = True
            return
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL
        subprocess.Popen([player, cue_path], stdout=stdout, stderr=stderr)
    except Exception as e:
        logger.debug(f"[AUDIO] cue playback skipped: {e}")



def _state_for_hw(name: str, logical_state: bool) -> bool:
    cfg = PIN_CONFIG.get(name, {})
    return (not logical_state) if cfg.get("active_low") else logical_state

def on_pin_toggle(sid, message):
    try:
        data = _ensure_dict(message)
        name = data.get("name")
        if name not in PIN_NAMES:
            raise ValueError(f"Unknown Pin '{name}'")
        if name in ROBOT_RESERVED_PIN_NAMES:
            raise ValueError(f"Pin '{name}' is reserved for robot motor/encoder control")

        logical = _normalize_state(data.get("state"))
        pin_states[name] = logical

        state_for_hw = _state_for_hw(name, logical)

        bridge_call_serialized("set_pin_by_name", name, state_for_hw)

        print(f"[{_iso_now()}] [{sid}] {name} -> logical={'ON' if logical else 'OFF'} hw={state_for_hw}")
        ui.send_message("pin_state_update", {
            "name": name,
            "state": logical,
            "timestamp": _iso_now()
        })

    except Exception as e:
        ui.send_message("error", f"Pin toggle error: {e}")

def on_get_states():
    return {"timestamp": _iso_now(), "states": pin_states}

def on_batch_pin_set(sid, message):
    try:
        pins_dict = _ensure_dict(message)
        if not isinstance(pins_dict, dict):
            raise ValueError("Payload must be a dictionary of pin states")
            
        print(f"[{_iso_now()}] [{sid}] BATCH SET -> {pins_dict}")

        for name, raw_state in pins_dict.items():
            if name not in PIN_NAMES:
                print(f"Skipping unknown pin: {name}")
                continue
            if name in ROBOT_RESERVED_PIN_NAMES:
                print(f"Skipping robot-reserved pin: {name}")
                continue

            logical = _normalize_state(raw_state)
            pin_states[name] = logical
            hw_state = _state_for_hw(name, logical)
            
            bridge_call_serialized("set_pin_by_name", name, hw_state)

            ui.send_message("pin_state_update", {
                "name": name,
                "state": logical,
                "timestamp": _iso_now()
            })
            
    except Exception as e:
        print(f"Error handling batch set: {e}")

def on_motor_forward(sid, message=None):
    return execute_robot_motion("FORWARD", source="web")


def on_motor_backward(sid, message=None):
    return execute_robot_motion("BACKWARD", source="web")

def on_motor_left(sid, message=None):
    return execute_robot_motion("LEFT", source="web")

def on_motor_right(sid, message=None):
    return execute_robot_motion("RIGHT", source="web")

def on_motor_stop(sid, message=None):
    return execute_robot_motion("STOP", source="web")


def voice_motor_forward():
    return execute_robot_motion("FORWARD", source="voice")

def voice_motor_backward():
    return execute_robot_motion("BACKWARD", source="voice")

def voice_motor_left():
    return execute_robot_motion("LEFT", source="voice")

def voice_motor_right():
    return execute_robot_motion("RIGHT", source="voice")

def get_config():
    
    return {
        'brightness_levels': BRIGHTNESS_LEVELS,
        'width': designer.width,
        'height': designer.height,
    }


def apply_frame_to_board(frame: AppFrame):
    
    frame_bytes = frame.to_board_bytes()
    bridge_call_serialized("draw", frame_bytes)
    frame_label = f"name={frame.name}, id={frame.id if frame.id else 'None (preview)'}"
    logger.debug(f"Frame sent to board: {frame_label}, bytes_len={len(frame_bytes)}")


def update_board(payload: dict):
    
    frame = AppFrame.from_json(payload)
    apply_frame_to_board(frame)
    vector_text = frame.to_c_string()
    return {'ok': True, 'vector': vector_text}


def persist_frame(payload: dict):
    
    frame = AppFrame.from_json(payload)
    
    if frame.id is None:
        
        logger.debug(f"Creating new frame: name='{frame.name}'")
        frame.id = store.save_frame(frame)
        
        record = store.get_frame_by_id(frame.id)
        if record:
            frame = AppFrame.from_record(record)
        logger.info(f"New frame created: id={frame.id}, name={frame.name}")
    else:
        
        logger.debug(f"Updating frame: id={frame.id}, name={frame.name}")
        store.update_frame(frame)
    
    apply_frame_to_board(frame)
    vector_text = frame.to_c_string()
    return {'ok': True, 'frame': frame.to_json(), 'vector': vector_text}


def bulk_update_frame_duration(payload) -> bool:
    
    duration = payload.get('duration_ms', 1000)
    logger.debug(f"Bulk updating frame duration: duration={duration}")
    store.bulk_update_frame_duration(duration)
    return True


def load_frame(payload: dict = None):
    
    fid = payload.get('id') if payload else None
    
    if fid is not None:
        logger.debug(f"Loading frame by id: {fid}")
        record = store.get_frame_by_id(fid)
        if not record:
            logger.warning(f"Frame not found: id={fid}")
            return {'error': 'frame not found'}
        frame = AppFrame.from_record(record)
        logger.info(f"Frame loaded: id={frame.id}, name={frame.name}")
    else:
        
        logger.debug("Loading last frame or creating empty")
        frame = store.get_or_create_active_frame(brightness_levels=BRIGHTNESS_LEVELS)
        logger.info(f"Active frame ready: id={frame.id}, name={frame.name}")
    
    apply_frame_to_board(frame)
    vector_text = frame.to_c_string()
    return {'ok': True, 'frame': frame.to_json(), 'vector': vector_text}


def list_frames(payload: dict = None):
    
    tid = payload.get('trajectory_id') if payload else None
    records = store.list_frames(trajectory_id=tid, order_by='position ASC, id ASC')
    frames = [AppFrame.from_record(r).to_json() for r in records]
    return {'frames': frames}


def create_trajectory(payload: dict):
    
    name = payload.get('name', 'New Trajectory')
    tid = store.create_trajectory(name)
    logger.info(f"Created trajectory: id={tid}, name='{name}'")
    return {'ok': True, 'id': tid, 'name': name}


def list_trajectories():
    
    trajs = store.list_trajectories()
    return {'trajectories': trajs}


def update_trajectory(payload: dict):
    
    tid = payload.get('id')
    if not tid:
        return {'error': 'id required'}
    
    store.update_trajectory(tid, payload)
    logger.info(f"Updated trajectory: id={tid}")
    return {'ok': True}


def delete_trajectory(payload: dict):
    
    tid = payload.get('id')
    if not tid:
        return {'error': 'id required'}
    store.delete_trajectory(tid)
    logger.info(f"Deleted trajectory: id={tid}")
    return {'ok': True}


def get_frame(payload: dict):
    
    fid = payload.get('id')
    record = store.get_frame_by_id(fid)
    
    if not record:
        return {'error': 'not found'}
    
    frame = AppFrame.from_record(record)
    return {'frame': frame.to_json()}


def delete_frame(payload: dict):
    
    fid = payload.get('id')
    logger.info(f"Deleting frame: id={fid}")
    store.delete_frame(fid)
    return {'ok': True}


def reorder_frames(payload: dict):
    
    order = payload.get('order', [])
    logger.info(f"Reordering frames: new order={order}")
    store.reorder_frames(order)
    return {'ok': True}


def transform_frame(payload: dict):
    
    op = payload.get('op')
    if not op:
        return {'error': 'op required'}

    
    rows = payload.get('rows')
    if rows is not None:
        frame = AppFrame.from_json({'rows': rows, 'brightness_levels': BRIGHTNESS_LEVELS})
        logger.debug(f"Transforming frame from rows: op={op}")
    else:
        fid = payload.get('id')
        if fid is None:
            return {'error': 'id or rows required'}
        record = store.get_frame_by_id(fid)
        if not record:
            return {'error': 'frame not found'}
        frame = AppFrame.from_record(record)
        logger.debug(f"Transforming frame by id: id={fid}, op={op}")

    
    operations = {
        'invert': designer.invert,
        'invert_not_null': designer.invert_not_null,
        'rotate180': designer.rotate180,
        'flip_h': designer.flip_horizontally,
        'flip_v': designer.flip_vertically,
    }
    if op not in operations:
        logger.warning(f"Unsupported transform operation: {op}")
        return {'error': 'unsupported op'}

    operations[op](frame)
    logger.info(f"Transform applied: op={op}")
    
    
    return {'ok': True, 'frame': frame.to_json(), 'vector': frame.to_c_string()}


def export_frames(payload: dict = None):
    
    
    if payload and payload.get('frames'):
        frame_ids = [int(fid) for fid in payload['frames']]
        logger.info(f"Exporting selected frames: ids={frame_ids}")
        records = [store.get_frame_by_id(fid) for fid in frame_ids]
        records = [r for r in records if r is not None]
    else:
        logger.info("Exporting all frames")
        records = store.list_frames(order_by='position ASC, id ASC')
    
    logger.debug(f"Exporting {len(records)} frames to C header")
    
    
    frames = [AppFrame.from_record(r) for r in records]
    frame_names = {}  
    for frame in frames:
        frame_names[frame.name] = frame_names.get(frame.name, 0) + 1
    
    
    name_counters = {}  
    for frame in frames:
        if frame_names[frame.name] > 1:
            
            if frame.name not in name_counters:
                name_counters[frame.name] = 0
            
            frame._export_name = f"{frame.name}_id{frame.id}"
            logger.debug(f"Duplicate name '{frame.name}' -> '{frame._export_name}'")
        else:
            
            frame._export_name = frame.name
    
    
    animations = payload.get('animations') if payload else None
    
    if animations:
        
        logger.info(f"Animation mode: {len(animations)} animation(s)")
        header_parts = []
        
        for anim in animations:
            anim_name = anim.get('name', 'Animation')
            anim_frame_ids = anim.get('frames', [])
            
            
            anim_frames = [f for f in frames if f.id in anim_frame_ids]
            
            if not anim_frames:
                continue
            
            
            header_parts.append(f"// Animation: {anim_name}")
            header_parts.append(AppFrame.frames_to_c_animation_array(anim_frames, anim_name))
        
        header = "\\n".join(header_parts).strip() + "\\n"
        return {'header': header}
    else:
        
        header_parts = []
        for frame in frames:
            header_parts.append(f"// {frame._export_name} (id {frame.id})")
            header_parts.append(frame.to_c_string())
        
        header = "\\n".join(header_parts).strip() + "\\n"
        return {'header': header}


def _play_frames(frame_ids: list[int]):
    
    if not frame_ids:
        logger.warning("No frame IDs provided to _play_frames")
        return {"error": "no frames provided"}

    logger.info(f"Preparing animation: frame_count={len(frame_ids)}")

    
    records = [store.get_frame_by_id(fid) for fid in frame_ids]
    records = [r for r in records if r is not None]

    if not records:
        logger.warning("No valid frames found for animation")
        return {"error": "no valid frames found"}

    frames = [AppFrame.from_record(r) for r in records]
    logger.debug(f"Loaded {len(frames)} frames for animation")

    try:
        for f in frames:
            logger.debug(
                f"Frame id={f.id}, name='{f.name}', duration={f.duration_ms}ms"
            )
            [hex1, hex2, hex3, hex4, duration] = f.to_animation_hex()
            Bridge.notify(
                "load_frame",
                [
                    int(hex1, 16),
                    int(hex2, 16),
                    int(hex3, 16),
                    int(hex4, 16),
                    int(duration),
                ],
            )

        bridge_call_serialized("play_animation")
        logger.info("play_animation called on board")
        return {"ok": True, "frames_played": len(frames)}

    except Exception as e:
        logger.warning(f"Failed to request play_animation: {e}")
        return {"error": str(e)}



_active_trajectory_state: dict = {
    "id": None,
    "name": None,
    "total_frames": 0,
    "total_steps": 0, 
    "current_step": -1, 
    "completed_steps": 0,
    "frames": [], 
    "required_commands": [], 
    "mistakes": 0,           
    "start_time": None       
}

def _get_frame_center(frame_data: dict):
    
    try:
        rows = frame_data.get("rows")
        if isinstance(rows, str):
            rows = json.loads(rows)
        
        active_points = []
        for y, row in enumerate(rows):
            for x, val in enumerate(row):
                if val > 0:
                    active_points.append((x, y))
        
        if not active_points:
            return None
        
        avg_x = sum(p[0] for p in active_points) / len(active_points)
        avg_y = sum(p[1] for p in active_points) / len(active_points)
        return (avg_x, avg_y)
    except Exception as e:
        logger.error(f"Error calculating frame center: {e}")
        return None

def _get_commands_from_frames(frames: list):
    
    commands = []
    
    for f in frames[1:]:
        cmd = f.get("command")
        if cmd:
            commands.append(cmd)
    return commands

def _calculate_trajectory_commands(frames: list):
    
    commands = []
    centers = []
    for f in frames:
        center = _get_frame_center(f)
        if center:
            centers.append(center)
    
    for i in range(len(centers) - 1):
        c1 = centers[i]
        c2 = centers[i+1]
        
        dx = c2[0] - c1[0]
        dy = c1[1] - c2[1] 
        
        if abs(dy) > abs(dx):
            cmd = "FORWARD" if dy > 0 else "BACKWARD"
        else:
            cmd = "RIGHT" if dx > 0 else "LEFT"
        
        commands.append(cmd)
    
    return commands

def _verify_trajectory_step(command_name: str, motion_state: dict | None = None):
    
    global _active_trajectory_state

    if not _active_trajectory_state or not _active_trajectory_state.get("id"):
        return False

    if not robot_motion_succeeded(motion_state):
        logger.warning(
            f"[TRAJECTORY] Rejected non-completed physical step: {command_name}"
        )
        _active_trajectory_state["last_step_status"] = "motion_not_completed"
        ui.send_message("trajectory_contrast", {
            "status": "motion_not_completed",
            "received": command_name,
            "motion_result_code": (
                motion_state.get("_motion_result_code")
                if isinstance(motion_state, dict) else None
            ),
        })
        ui.send_message("trajectory_update", _active_trajectory_state)
        return False

    step = _active_trajectory_state.get("current_step", -1)
    if step == -1:
        logger.warning("[TRAJECTORY] Waiting for Initial Cell. Command ignored.")
        ui.send_message("trajectory_contrast", {
            "status": "waiting_for_start",
            "message": "Place robot on START cell first"
        })
        return False

    required_commands = _active_trajectory_state.get("required_commands", [])
    total_steps = len(required_commands)

    if step < total_steps:
        target_command = required_commands[step]

        if command_name == target_command:
            logger.info(f"[TRAJECTORY] Progress Match: {command_name} (Step {step}/{total_steps})")
            _active_trajectory_state["current_step"] += 1
            new_step = _active_trajectory_state["current_step"]
            _active_trajectory_state["completed_steps"] = new_step
            _active_trajectory_state["last_step_status"] = "completed"
            _play_linux_audio_cue("complete" if new_step >= total_steps else "step")

            
            frames = _active_trajectory_state.get("frames", [])
            if 0 <= new_step < len(frames):
                next_frame = AppFrame.from_record(frames[new_step])
                apply_frame_to_board(next_frame)

            if new_step >= total_steps:
                logger.info(f"[TRAJECTORY] Trajectory COMPLETED: {_active_trajectory_state['name']}")
                ui.send_message("trajectory_complete", {
                    "id": _active_trajectory_state["id"],
                    "name": _active_trajectory_state["name"]
                })

            ui.send_message("trajectory_update", _active_trajectory_state)
            return True

        logger.warning(f"[TRAJECTORY] Progress Mismatch: {command_name} but expected {target_command} (Step {step})")
        ui.send_message("trajectory_contrast", {
            "status": "mismatch",
            "received": command_name,
            "target": target_command,
            "step": step
        })
        _active_trajectory_state["mistakes"] += 1
        _active_trajectory_state["last_step_status"] = "command_mismatch"
        ui.send_message("trajectory_update", _active_trajectory_state)
    return False
def _initialize_active_trajectory(tid: int):
    
    global _active_trajectory_state
    
    traj_record = store.get_trajectory_by_id(tid)
    traj_name = traj_record["name"] if traj_record else f"Trajectory {tid}"
    
    frames = store.list_frames(tid)
    
    required_commands = _get_commands_from_frames(frames)
    if not required_commands:
        logger.info(f"[TRAJECTORY] No stored commands found for TID {tid}, calculating from centers...")
        required_commands = _calculate_trajectory_commands(frames)
    
    _active_trajectory_state = {
        "id": tid,
        "name": traj_name,
        "total_frames": len(frames),
        "total_steps": len(required_commands),
        "current_step": -1, 
        "completed_steps": 0,
        "frames": frames,
        "required_commands": required_commands,
        "mistakes": 0,
        "start_time": time.time()
    }
    
    
    if frames:
        first_frame = AppFrame.from_record(frames[0])
        apply_frame_to_board(first_frame)
        
    logger.info(f"[TRAJECTORY] Initialized active state for ID {tid}: {traj_name} ({len(required_commands)} steps)")
    
    ui.send_message("trajectory_update", _active_trajectory_state)
    return frames

def _play_trajectory(tid: int):
    
    logger.info(f"Loading/Playing trajectory ID: {tid}")
    frames = _initialize_active_trajectory(tid)
    if not frames:
        logger.warning(f"No frames found for trajectory {tid}")
        return {"error": "trajectory empty"}

    
    
    
    return {"ok": True, "loaded": True}

def set_active_trajectory_api(payload: dict):
    
    tid = payload.get('id')
    if tid is None:
        return {"error": "Trajectory ID required"}
    
    _initialize_active_trajectory(tid)
    return {"ok": True}

def on_animation_progress(current_frame: int):
    
    logger.debug(f"[ANIMATION] Frame progress: {current_frame}")

def play_animation(payload: dict):
    
    frame_ids = payload.get("frames", [])
    return _play_frames(frame_ids)


def stop_animation():
    
    try:
        bridge_call_serialized("stop_animation")
        logger.info("stop_animation called on board")
        return {'ok': True}
    except Exception as e:
        logger.warning(f"Failed to request stop_animation: {e}")
        return {'error': str(e)}

def on_pin_toggle(sid, message):
    try:
        data = _ensure_dict(message)
        name = data.get("name")
        if name not in PIN_NAMES:
            raise ValueError(f"Unknown Pin '{name}'")
        if name in ROBOT_RESERVED_PIN_NAMES:
            raise ValueError(f"Pin '{name}' is reserved for robot motor/encoder control")

        logical = _normalize_state(data.get("state"))
        pin_states[name] = logical

        state_for_hw = _state_for_hw(name, logical)

        bridge_call_serialized("set_pin_by_name", name, state_for_hw)

        print(f"[{_iso_now()}] [{sid}] {name} -> logical={'ON' if logical else 'OFF'} hw={state_for_hw}")
        ui.send_message("pin_state_update", {
            "name": name,
            "state": logical,
            "timestamp": _iso_now()
        })

    except Exception as e:
        ui.send_message("error", f"Pin toggle error: {e}")

def on_get_states():
    return {"timestamp": _iso_now(), "states": pin_states}

def on_batch_pin_set(sid, message):
    try:
        pins_dict = _ensure_dict(message)
        if not isinstance(pins_dict, dict):
            raise ValueError("Payload must be a dictionary of pin states")
            
        print(f"[{_iso_now()}] [{sid}] BATCH SET -> {pins_dict}")

        for name, raw_state in pins_dict.items():
            if name not in PIN_NAMES:
                print(f"Skipping unknown pin: {name}")
                continue
            if name in ROBOT_RESERVED_PIN_NAMES:
                print(f"Skipping robot-reserved pin: {name}")
                continue

            logical = _normalize_state(raw_state)
            pin_states[name] = logical
            hw_state = _state_for_hw(name, logical)
            
            bridge_call_serialized("set_pin_by_name", name, hw_state)

            ui.send_message("pin_state_update", {
                "name": name,
                "state": logical,
                "timestamp": _iso_now()
            })
            
    except Exception as e:
                print(f"Error handling batch set: {e}")
        

_DETECTION_STATE: dict[str, typing.Any] = {
    "last_content": None,
    "last_time": 0.0,
    "miss_frames": 0,
    "pending_content": None,
}








_QR_PRINT_SIZE_MM = 15.0
_QR_VERSION_1_MODULES = 21.0
_QR_QUIET_ZONE_MODULES_PER_SIDE = 4.0
_QR_CODE_SIZE_MM = _QR_PRINT_SIZE_MM * (
    _QR_VERSION_1_MODULES /
    (_QR_VERSION_1_MODULES + 2.0 * _QR_QUIET_ZONE_MODULES_PER_SIDE)
)
_QR_VISIBILITY_MARGIN_PX = 8.0
_QR_VISIBLE_FRACTION_REQUIRED = 0.985
_QR_ORTHOGONALITY_TOLERANCE_DEG = 12.0
_QR_PERSPECTIVE_RATIO_LIMIT = 1.35
_QR_PROBE_DISTANCE_MM = 5.0
_QR_PROBE_DETECT_TIMEOUT_S = 1.2
_QR_HEADING_READY_TOLERANCE_DEG = 3.0
_QR_ROI_LEFT_FRACTION = 0.20
_QR_ROI_RIGHT_FRACTION = 0.76
_QR_ROI_TOP_FRACTION = 0.06
_QR_ROI_BOTTOM_FRACTION = 0.99
_QR_CAMERA_FORWARD_IMAGE_DEG = float(
    os.environ.get("QR_CAMERA_FORWARD_IMAGE_DEG", "-90")
)
_QR_CENTERING_ACTIVE = threading.Event()
_QR_CENTER_CANCEL_EVENT = threading.Event()
_QR_ALIGNMENT_CONDITION = threading.Condition()
_QR_CONTENT_LOCK = threading.Lock()
_QR_OPENCV_AVAILABLE = cv2 is not None and np is not None
_QR_ALIGNMENT_STATE: dict[str, typing.Any] = {
    "sequence": 0,
    "visible": False,
    "timestamp_epoch": 0.0,
    "content": None,
    "frame_width_px": None,
    "frame_height_px": None,
    "center_x_px": None,
    "center_y_px": None,
    "offset_x_mm": None,
    "offset_y_mm": None,
    "distance_mm": None,
    "qr_side_px": None,
    "mm_per_px": None,
    "points_px": None,
    "complete_detection": False,
    "finder_count": 0,
    "visible_fraction": 0.0,
    "orthogonality_error_deg": None,
    "perspective_ratio": None,
    "pose_acceptable": False,
    "required_shift_x_px": None,
    "required_shift_y_px": None,
    "instruction": "ESPERANDO QR",
    "roi_px": None,
    "centering_active": False,
    "status": "idle",
}


def _qr_valid_roi(width_px: int, height_px: int):
    return (
        int(round(width_px * _QR_ROI_LEFT_FRACTION)),
        int(round(height_px * _QR_ROI_TOP_FRACTION)),
        int(round(width_px * _QR_ROI_RIGHT_FRACTION)),
        int(round(height_px * _QR_ROI_BOTTOM_FRACTION)),
    )


def _polygon_area(points: list[list[float]]) -> float:
    return abs(sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )) * 0.5


def _clip_polygon_axis(points, axis: int, boundary: float, keep_greater: bool):
    if not points:
        return []
    output = []
    previous = points[-1]
    previous_inside = (
        previous[axis] >= boundary if keep_greater else previous[axis] <= boundary
    )
    for current in points:
        current_inside = (
            current[axis] >= boundary if keep_greater else current[axis] <= boundary
        )
        if current_inside != previous_inside:
            denominator = current[axis] - previous[axis]
            t = 0.0 if abs(denominator) < 1e-9 else (
                (boundary - previous[axis]) / denominator
            )
            intersection = [
                previous[0] + t * (current[0] - previous[0]),
                previous[1] + t * (current[1] - previous[1]),
            ]
            output.append(intersection)
        if current_inside:
            output.append(list(current))
        previous = current
        previous_inside = current_inside
    return output


def _polygon_visible_fraction(points, width_px: int, height_px: int) -> float:
    full_area = _polygon_area(points)
    if full_area < 1.0:
        return 0.0
    clipped = [list(point) for point in points]
    clipped = _clip_polygon_axis(clipped, 0, 0.0, True)
    clipped = _clip_polygon_axis(clipped, 0, float(width_px - 1), False)
    clipped = _clip_polygon_axis(clipped, 1, 0.0, True)
    clipped = _clip_polygon_axis(clipped, 1, float(height_px - 1), False)
    return max(0.0, min(1.0, _polygon_area(clipped) / full_area))


def _quad_quality(points):
    lengths = [
        math.hypot(
            points[(index + 1) % 4][0] - points[index][0],
            points[(index + 1) % 4][1] - points[index][1],
        )
        for index in range(4)
    ]
    angles = []
    for index in range(4):
        previous = points[(index - 1) % 4]
        current = points[index]
        following = points[(index + 1) % 4]
        a = (previous[0] - current[0], previous[1] - current[1])
        b = (following[0] - current[0], following[1] - current[1])
        denominator = math.hypot(*a) * math.hypot(*b)
        cosine = 0.0 if denominator < 1e-6 else max(
            -1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / denominator)
        )
        angles.append(math.degrees(math.acos(cosine)))
    orthogonality_error = max(abs(angle - 90.0) for angle in angles)
    opposite_ratios = [
        max(lengths[0], lengths[2]) / max(1.0, min(lengths[0], lengths[2])),
        max(lengths[1], lengths[3]) / max(1.0, min(lengths[1], lengths[3])),
    ]
    return lengths, orthogonality_error, max(opposite_ratios)


def _required_visibility_shift(points, width_px: int, height_px: int):
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    margin = _QR_VISIBILITY_MARGIN_PX
    shift_x = 0.0
    shift_y = 0.0
    if min_x < margin:
        shift_x = margin - min_x
    elif max_x > width_px - 1 - margin:
        shift_x = width_px - 1 - margin - max_x
    if min_y < margin:
        shift_y = margin - min_y
    elif max_y > height_px - 1 - margin:
        shift_y = height_px - 1 - margin - max_y
    return shift_x, shift_y

def _record_qr_alignment_points(
    frame,
    raw_points,
    now: float,
    source: str,
    content: str | None = None,
    complete_detection: bool = True,
    finder_count: int = 3,
) -> bool:
    try:
        points = [[float(v) for v in point] for point in raw_points]
        if len(points) != 4:
            return False
        
        
        
        if cv2 is not None and np is not None:
            rgb = np.asarray(frame.convert("RGB"))
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            corners = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
            try:
                cv2.cornerSubPix(
                    gray,
                    corners,
                    (5, 5),
                    (-1, -1),
                    (
                        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
                        30,
                        0.01,
                    ),
                )
                points = corners.reshape(-1, 2).tolist()
            except cv2.error as exc:
                logger.debug(f"[QR-CENTER] Subpixel refinement skipped: {exc}")
        width_px, height_px = frame.size
        center_x = sum(point[0] for point in points) / 4.0
        center_y = sum(point[1] for point in points) / 4.0
        roi_left, roi_top, roi_right, roi_bottom = _qr_valid_roi(
            width_px, height_px
        )
        if not (
            roi_left <= center_x <= roi_right
            and roi_top <= center_y <= roi_bottom
        ):
            return False
        side_lengths, orthogonality_error, perspective_ratio = _quad_quality(points)
        side_px = sum(side_lengths) / 4.0
        if side_px < 4.0:
            return False
        
        
        mm_per_px = _QR_CODE_SIZE_MM / side_px
        offset_x_mm = (center_x - width_px / 2.0) * mm_per_px
        offset_y_mm = (center_y - height_px / 2.0) * mm_per_px
        visible_fraction = _polygon_visible_fraction(points, width_px, height_px)
        shift_x_px, shift_y_px = _required_visibility_shift(
            points, width_px, height_px
        )
        pose_acceptable = bool(
            complete_detection
            and visible_fraction >= _QR_VISIBLE_FRACTION_REQUIRED
            and orthogonality_error <= _QR_ORTHOGONALITY_TOLERANCE_DEG
            and perspective_ratio <= _QR_PERSPECTIVE_RATIO_LIMIT
        )
        with _QR_ALIGNMENT_CONDITION:
            _QR_ALIGNMENT_STATE.update({
                "sequence": int(_QR_ALIGNMENT_STATE["sequence"]) + 1,
                "visible": True,
                "timestamp_epoch": float(now),
                "content": content,
                "source": source,
                "frame_width_px": int(width_px),
                "frame_height_px": int(height_px),
                "center_x_px": center_x,
                "center_y_px": center_y,
                "offset_x_mm": offset_x_mm,
                "offset_y_mm": offset_y_mm,
                "distance_mm": math.hypot(offset_x_mm, offset_y_mm),
                "qr_side_px": side_px,
                "mm_per_px": mm_per_px,
                "points_px": points,
                "complete_detection": bool(complete_detection),
                "finder_count": int(finder_count),
                "visible_fraction": visible_fraction,
                "orthogonality_error_deg": orthogonality_error,
                "perspective_ratio": perspective_ratio,
                "pose_acceptable": pose_acceptable,
                "required_shift_x_px": shift_x_px,
                "required_shift_y_px": shift_y_px,
                "roi_px": [roi_left, roi_top, roi_right, roi_bottom],
                "centering_active": _QR_CENTERING_ACTIVE.is_set(),
            })
            snapshot = dict(_QR_ALIGNMENT_STATE)
            _QR_ALIGNMENT_CONDITION.notify_all()
        ui.send_message("qr_alignment_update", snapshot)
        return True
    except Exception as exc:
        logger.error(f"[QR-CENTER] Geometry error: {exc}")
        return False


def _record_managed_qr_alignment(frame, detection, now: float) -> bool:
    return _record_qr_alignment_points(
        frame,
        detection.coords,
        now,
        source="managed_detector",
        content=(
            None if _QR_CENTERING_ACTIVE.is_set()
            else str(detection.content)
        ),
    )


def _record_opencv_qr_alignment(frame, now: float) -> bool:
    
    if not _QR_OPENCV_AVAILABLE:
        return False
    try:
        rgb = np.asarray(frame.convert("RGB"))
        gray = np.ascontiguousarray(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY))
        roi_left, roi_top, roi_right, roi_bottom = _qr_valid_roi(
            gray.shape[1], gray.shape[0]
        )
        roi_gray = np.ascontiguousarray(
            gray[roi_top:roi_bottom, roi_left:roi_right]
        )
        
        
        found, points = cv2.QRCodeDetector().detect(roi_gray)
        if not found or points is None:
            return False
        polygon = np.asarray(points, dtype=np.float32).reshape(-1, 2)
        polygon[:, 0] += float(roi_left)
        polygon[:, 1] += float(roi_top)
        return _record_qr_alignment_points(
            frame,
            polygon,
            now,
            source="opencv_geometry_only",
            content=None,
            complete_detection=True,
            finder_count=3,
        )
    except cv2.error as exc:
        logger.debug(f"[QR-CENTER] OpenCV full-QR detector skipped frame: {exc}")
        return False


def _finder_nested_depth(hierarchy, index: int) -> int:
    depth = 0
    child = int(hierarchy[index][2])
    while child >= 0 and depth < 8:
        depth += 1
        child = int(hierarchy[child][2])
    return depth


def _partial_qr_finder_candidates(gray):
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )
    contours, hierarchy_raw = cv2.findContours(
        binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    if hierarchy_raw is None:
        return []
    hierarchy = hierarchy_raw[0]
    frame_area = float(gray.shape[0] * gray.shape[1])
    candidates = []
    for index, contour in enumerate(contours):
        depth = _finder_nested_depth(hierarchy, index)
        area = abs(float(cv2.contourArea(contour)))
        
        
        if depth < 2 or area < frame_area * 0.0005 or area > frame_area * 0.12:
            continue
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        if min(width, height) < 8.0:
            continue
        aspect = max(width, height) / max(1.0, min(width, height))
        if aspect > 1.45:
            continue
        candidates.append({
            "center": (float(rect[0][0]), float(rect[0][1])),
            "side": (float(width) + float(height)) * 0.5,
            "depth": depth,
        })

    
    
    candidates.sort(key=lambda item: (item["depth"], item["side"]), reverse=True)
    unique = []
    for candidate in candidates:
        if any(
            math.hypot(
                candidate["center"][0] - kept["center"][0],
                candidate["center"][1] - kept["center"][1],
            ) < max(8.0, 0.45 * max(candidate["side"], kept["side"]))
            for kept in unique
        ):
            continue
        unique.append(candidate)
        if len(unique) >= 8:
            break
    return unique


def _qr_texture_score(gray, points) -> float:
    if gray is None:
        return 0.0
    source = np.asarray(points, dtype=np.float32)
    destination = np.asarray(
        [[0, 0], [145, 0], [145, 145], [0, 145]], dtype=np.float32
    )
    transform = cv2.getPerspectiveTransform(source, destination)
    patch = cv2.warpPerspective(
        gray, transform, (146, 146), flags=cv2.INTER_LINEAR, borderValue=255
    )
    _, binary = cv2.threshold(
        patch, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )
    black_fraction = float(np.mean(binary < 128))
    horizontal_transitions = float(np.mean(binary[:, 1:] != binary[:, :-1]))
    vertical_transitions = float(np.mean(binary[1:, :] != binary[:-1, :]))
    transition_score = horizontal_transitions + vertical_transitions
    balance_penalty = abs(black_fraction - 0.35) * 0.20
    return transition_score - balance_penalty


def _reconstruct_qr_from_finders(
    candidates,
    width_px: int,
    height_px: int,
    gray=None,
):
    if len(candidates) < 2:
        return None

    
    
    best = None
    for first in range(len(candidates) - 2):
        for second in range(first + 1, len(candidates) - 1):
            for third in range(second + 1, len(candidates)):
                trio = [candidates[first], candidates[second], candidates[third]]
                for pivot_index in range(3):
                    pivot = trio[pivot_index]["center"]
                    arms = [
                        trio[index]["center"]
                        for index in range(3) if index != pivot_index
                    ]
                    a = (arms[0][0] - pivot[0], arms[0][1] - pivot[1])
                    b = (arms[1][0] - pivot[0], arms[1][1] - pivot[1])
                    len_a = math.hypot(*a)
                    len_b = math.hypot(*b)
                    if min(len_a, len_b) < 20.0:
                        continue
                    length_ratio = max(len_a, len_b) / min(len_a, len_b)
                    cosine = abs((a[0] * b[0] + a[1] * b[1]) / (len_a * len_b))
                    score = cosine + abs(length_ratio - 1.0)
                    if length_ratio <= 1.55 and (best is None or score < best[0]):
                        best = (score, pivot, a, b, len_a, len_b)

    if best is not None:
        _, pivot, a, b, len_a, len_b = best
        u = (a[0] / len_a, a[1] / len_a)
        v = (b[0] / len_b, b[1] / len_b)
        gap = (len_a + len_b) * 0.5
        top_left = (
            pivot[0] - 0.25 * gap * u[0] - 0.25 * gap * v[0],
            pivot[1] - 0.25 * gap * u[1] - 0.25 * gap * v[1],
        )
        side = 1.5 * gap
        points = [
            [top_left[0], top_left[1]],
            [top_left[0] + side * u[0], top_left[1] + side * u[1]],
            [top_left[0] + side * (u[0] + v[0]), top_left[1] + side * (u[1] + v[1])],
            [top_left[0] + side * v[0], top_left[1] + side * v[1]],
        ]
        return points, 3

    
    
    
    pair = max(
        (
            (candidates[i], candidates[j])
            for i in range(len(candidates) - 1)
            for j in range(i + 1, len(candidates))
        ),
        key=lambda item: math.hypot(
            item[1]["center"][0] - item[0]["center"][0],
            item[1]["center"][1] - item[0]["center"][1],
        ),
    )
    first, second = pair[0]["center"], pair[1]["center"]
    dx, dy = second[0] - first[0], second[1] - first[1]
    gap = math.hypot(dx, dy)
    if gap < 20.0:
        return None
    u = (dx / gap, dy / gap)
    perpendicular = (-u[1], u[0])
    midpoint = ((first[0] + second[0]) * 0.5, (first[1] + second[1]) * 0.5)
    side = 1.5 * gap
    half = side * 0.5
    options = []
    for sign in (-1.0, 1.0):
        center = (
            midpoint[0] + sign * 0.5 * gap * perpendicular[0],
            midpoint[1] + sign * 0.5 * gap * perpendicular[1],
        )
        v = (sign * perpendicular[0], sign * perpendicular[1])
        points = [
            [center[0] - half * u[0] - half * v[0], center[1] - half * u[1] - half * v[1]],
            [center[0] + half * u[0] - half * v[0], center[1] + half * u[1] - half * v[1]],
            [center[0] + half * u[0] + half * v[0], center[1] + half * u[1] + half * v[1]],
            [center[0] - half * u[0] + half * v[0], center[1] - half * u[1] + half * v[1]],
        ]
        visible_fraction = _polygon_visible_fraction(points, width_px, height_px)
        texture_score = _qr_texture_score(gray, points)
        options.append((texture_score + 0.02 * visible_fraction, points))
    return max(options, key=lambda option: option[0])[1], 2


def _record_partial_qr_alignment(frame, now: float) -> bool:
    if not _QR_OPENCV_AVAILABLE:
        return False
    try:
        rgb = np.asarray(frame.convert("RGB"))
        gray = np.ascontiguousarray(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY))
        candidates = _partial_qr_finder_candidates(gray)
        reconstruction = _reconstruct_qr_from_finders(
            candidates, gray.shape[1], gray.shape[0], gray=gray
        )
        if reconstruction is None:
            return False
        points, finder_count = reconstruction
        return _record_qr_alignment_points(
            frame,
            points,
            now,
            source="opencv_partial_finders",
            content=None,
            complete_detection=False,
            finder_count=finder_count,
        )
    except cv2.error as exc:
        logger.debug(f"[QR-CENTER] Partial finder detector skipped frame: {exc}")
        return False

def _execute_qr_content_once(content: str) -> None:
    
    logger.info(f"[CAMERA] Accepting one-shot QR: {content}")
    if not content.startswith("LOAD_TRAJECTORY:"):
        return
    try:
        tid = int(content.split(":", 1)[1])
        if (
            _active_trajectory_state["id"] == tid
            and _active_trajectory_state["current_step"] == -1
        ):
            logger.info(f"[TRAJECTORY] Start pose accepted for TID {tid}.")
            _active_trajectory_state["current_step"] = 0
            _active_trajectory_state["completed_steps"] = 0
            _play_linux_audio_cue("step")
            ui.send_message("trajectory_update", _active_trajectory_state)
        else:
            logger.info(f"[TRAJECTORY] Loading trajectory ID: {tid}")
            frames = _initialize_active_trajectory(tid)
            if frames:
                _active_trajectory_state["current_step"] = 0
                _active_trajectory_state["completed_steps"] = 0
                _play_linux_audio_cue("step")
                ui.send_message("trajectory_update", _active_trajectory_state)
        print(f"[{_iso_now()}] [QR] Triggered trajectory ID once: {tid}")
    except Exception as exc:
        print(f"[{_iso_now()}] [QR] Error triggering trajectory: {exc}")


def _accept_pending_qr_if_pose_ready() -> bool:
    
    if _robot_motion_active or _QR_CENTERING_ACTIVE.is_set():
        return False
    with _QR_CONTENT_LOCK:
        content = _DETECTION_STATE.get("pending_content")
        if not content:
            return False
        with _QR_ALIGNMENT_CONDITION:
            pose_acceptable = bool(_QR_ALIGNMENT_STATE.get("pose_acceptable"))
        if not pose_acceptable:
            return False
        if content == _DETECTION_STATE.get("last_content"):
            _DETECTION_STATE["pending_content"] = None
            return False
        _DETECTION_STATE["last_content"] = content
        _DETECTION_STATE["last_time"] = float(time.time())
        _DETECTION_STATE["pending_content"] = None

    
    
    _execute_qr_content_once(str(content))
    _set_qr_center_status(
        "qr_pose_accepted_camera_released",
        ok=True,
        instruction="QR ACEPTADO UNA VEZ - CAMARA LIBRE",
    )
    return True


def on_code_detected(frame, detection):
    
    _DETECTION_STATE["miss_frames"] = 0
    if _robot_motion_active or _QR_CENTERING_ACTIVE.is_set():
        return

    content = str(detection.content)
    if content in {
        _DETECTION_STATE.get("last_content"),
        _DETECTION_STATE.get("pending_content"),
    }:
        return
    now = time.time()
    _record_managed_qr_alignment(frame, detection, now)
    with _QR_CONTENT_LOCK:
        _DETECTION_STATE["pending_content"] = content
    _set_qr_center_status(
        "qr_payload_buffered_waiting_for_pose",
        ok=False,
        instruction="AJUSTAR ORIENTACION - CONTENIDO LEIDO UNA SOLA VEZ",
    )
    _accept_pending_qr_if_pose_ready()

    
    frame = draw_bounding_box(frame, detection)

    buffer = io.BytesIO()
    frame.save(buffer, format="JPEG", quality=100)
    b64_frame = base64.b64encode(buffer.getvalue()).decode("utf-8")

    entry = {
        "content": detection.content,
        "type": detection.type,
        "timestamp": datetime.now(UTC).isoformat(),
        "image": b64_frame,
        "image_type": "image/jpeg",
    }
    if camera_store is not None:
        try:
            camera_store.store("scan_log", entry)
        except Exception as e:
            logger.error(f"[CAMERA] Failed to store scan log: {e}")
    ui.send_message('code_detected', entry)

def _draw_qr_alignment_overlay(frame):
    if (
        not _QR_CENTERING_ACTIVE.is_set()
        and not _DETECTION_STATE.get("pending_content")
    ):
        return frame
    with _QR_ALIGNMENT_CONDITION:
        state = dict(_QR_ALIGNMENT_STATE)
    output = frame.copy()
    draw = ImageDraw.Draw(output)
    width_px, height_px = output.size
    roi_left, roi_top, roi_right, roi_bottom = _qr_valid_roi(
        width_px, height_px
    )
    draw.rectangle(
        (roi_left, roi_top, roi_right, roi_bottom),
        outline=(80, 180, 255),
        width=2,
    )
    points = state.get("points_px") or []
    if len(points) == 4:
        polygon = [(int(point[0]), int(point[1])) for point in points]
        color = (60, 230, 110) if state.get("pose_acceptable") else (255, 190, 40)
        draw.line(polygon + [polygon[0]], fill=color, width=4)
        center = (
            int(sum(point[0] for point in points) / 4.0),
            int(sum(point[1] for point in points) / 4.0),
        )
        shift = (
            int(float(state.get("required_shift_x_px") or 0.0)),
            int(float(state.get("required_shift_y_px") or 0.0)),
        )
        if shift != (0, 0):
            end = (center[0] + shift[0], center[1] + shift[1])
            draw.line((center, end), fill=(255, 70, 70), width=5)
            radius = 7
            draw.ellipse(
                (end[0] - radius, end[1] - radius, end[0] + radius, end[1] + radius),
                fill=(255, 70, 70),
            )

    visible_pct = 100.0 * float(state.get("visible_fraction") or 0.0)
    orth_error = state.get("orthogonality_error_deg")
    orth_text = "--" if orth_error is None else f"{float(orth_error):.1f} deg"
    detection_text = (
        "QR COMPLETO VERIFICADO" if state.get("complete_detection")
        else "QR NO VERIFICADO"
    )
    instruction = str(state.get("instruction") or "ANALIZANDO")
    status = str(state.get("status") or "")
    lines = [
        f"{detection_text} | visible {visible_pct:.0f}% | ortogonalidad {orth_text}",
        f"INSTRUCCION: {instruction}",
        f"ESTADO: {status}",
    ]
    for index, line in enumerate(lines):
        draw.text(
            (8, 5 + 18 * index),
            line,
            fill=(255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )
    return output


def on_frame(frame):
    
    
    
    try:
        from PIL.Image import Image as PILImage
        if not isinstance(frame, PILImage):
            return
    except Exception:
        return

    
    
    
    vision_tracking = bool(
        not _robot_motion_active
        and (
            _QR_CENTERING_ACTIVE.is_set()
            or _DETECTION_STATE.get("pending_content")
        )
    )
    vision_found = False
    if vision_tracking:
        now = time.time()
        vision_found = _record_opencv_qr_alignment(frame, now)
        if vision_found and _DETECTION_STATE.get("pending_content"):
            _accept_pending_qr_if_pose_ready()

    if vision_tracking and not vision_found:
        with _QR_ALIGNMENT_CONDITION:
            _QR_ALIGNMENT_STATE["visible"] = False
            _QR_ALIGNMENT_STATE["points_px"] = None
            _QR_ALIGNMENT_STATE["complete_detection"] = False
            _QR_ALIGNMENT_STATE["finder_count"] = 0
            _QR_ALIGNMENT_STATE["visible_fraction"] = 0.0
            _QR_ALIGNMENT_STATE["pose_acceptable"] = False
            _QR_ALIGNMENT_STATE["centering_active"] = _QR_CENTERING_ACTIVE.is_set()
            _QR_ALIGNMENT_CONDITION.notify_all()

    try:
        display_frame = _draw_qr_alignment_overlay(frame)
        buffer = io.BytesIO()
        display_frame.save(buffer, format="JPEG", quality=85)
        b64_frame = base64.b64encode(buffer.getvalue()).decode("utf-8")
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "image": b64_frame,
            "image_type": "image/jpeg",
        }
        ui.send_message('frame_detected', entry)
    except Exception as e:
        print(f"[{_iso_now()}] [CAMERA] Frame send error: {e}")

def on_list_scans():
    
    if camera_store is None:
        return {"scans": []}
    try:
        scans = camera_store.read("scan_log", order_by="timestamp DESC", limit=5)
        return {"scans": scans if scans else []}
    except Exception as e:
        logger.error(f"[CAMERA] Failed to read scan log: {e}")
        return {"scans": []}

def reset_detection(_, __):
    
    _DETECTION_STATE["last_content"] = None
    _DETECTION_STATE["last_time"] = 0.0
    _DETECTION_STATE["pending_content"] = None
    try:
        if hasattr(detector, "reset"):
            detector.reset()
        elif hasattr(detector, "already_seen_codes"):
            detector.already_seen_codes.clear()
    except Exception:
        pass

def on_error(e: Exception):
    
    ui.send_message('error', str(e))



camera_store = None
try:
    camera_store = SafeSQLStoreWrapper(SQLStore("code-scanner.db"))
    camera_store.start()
except Exception as e:
    logger.error(f"[BOOT] Failed to initialize camera SQLStore: {e}")
    PERIPHERALS_STATUS["database"] = False


detector = None
try:
    detector = CameraCodeDetection()
    detector.on_detect(on_code_detected)
    detector.on_frame(on_frame)
    detector.on_error(on_error)
except Exception as e:
    logger.error(f"[BOOT] Failed to initialize CameraCodeDetection (camera): {e}")
    PERIPHERALS_STATUS["camera"] = False


def _set_qr_center_status(status: str, **values):
    with _QR_ALIGNMENT_CONDITION:
        _QR_ALIGNMENT_STATE.update(values)
        _QR_ALIGNMENT_STATE["status"] = status
        _QR_ALIGNMENT_STATE["centering_active"] = _QR_CENTERING_ACTIVE.is_set()
        snapshot = dict(_QR_ALIGNMENT_STATE)
        _QR_ALIGNMENT_CONDITION.notify_all()
    ui.send_message("qr_alignment_update", snapshot)
    return snapshot


def _wait_for_qr_alignment(after_sequence: int, timeout_s: float):
    deadline = time.monotonic() + timeout_s
    with _QR_ALIGNMENT_CONDITION:
        while True:
            if _QR_CENTER_CANCEL_EVENT.is_set():
                return None
            snapshot = dict(_QR_ALIGNMENT_STATE)
            age_s = time.time() - float(snapshot.get("timestamp_epoch") or 0.0)
            if (
                snapshot.get("visible")
                and int(snapshot.get("sequence") or 0) > after_sequence
                and age_s <= 0.75
                and snapshot.get("distance_mm") is not None
            ):
                return snapshot
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                return None
            _QR_ALIGNMENT_CONDITION.wait(min(remaining, 0.25))


def _image_motion_to_robot_frame(dx_mm: float, dy_mm: float) -> tuple[float, float]:
    
    forward_angle = math.radians(_QR_CAMERA_FORWARD_IMAGE_DEG)
    right_angle = forward_angle + math.pi / 2.0
    forward_mm = (
        dx_mm * math.cos(forward_angle) + dy_mm * math.sin(forward_angle)
    )
    right_mm = dx_mm * math.cos(right_angle) + dy_mm * math.sin(right_angle)
    return forward_mm, right_mm


def _qr_relative_primitive(bridge_name: str, payload: dict, label: str) -> bool:
    state = send_robot_bridge_primitive(bridge_name, payload, label)
    return robot_state_is_idle(state) and not robot_state_is_fault(state)


def _heading_ready_for_qr_probe(robot_state: dict | None) -> bool:
    if not isinstance(robot_state, dict):
        return False
    error = robot_state.get("step_final_yaw_error_deg")
    if error is None:
        error = robot_state.get("yaw_error_deg")
    try:
        error_ok = abs(float(error)) <= _QR_HEADING_READY_TOLERANCE_DEG
    except (TypeError, ValueError):
        return False
    stable = robot_state.get("step_end_heading_stable")
    return error_ok and stable is not False


def _wait_for_verified_qr(after_sequence: int, timeout_s: float):
    deadline = time.monotonic() + timeout_s
    sequence = after_sequence
    accepted = 0
    last_alignment = None
    while time.monotonic() < deadline and accepted < 3:
        alignment = _wait_for_qr_alignment(
            sequence,
            min(0.45, max(0.05, deadline - time.monotonic())),
        )
        if alignment is None:
            continue
        sequence = int(alignment["sequence"])
        if alignment.get("complete_detection") and alignment.get("pose_acceptable"):
            accepted += 1
            last_alignment = alignment
        else:
            accepted = 0
            last_alignment = None
    return last_alignment


def _run_qr_centering_after_step(command: str, robot_state: dict | None = None) -> dict:
    
    _QR_CENTER_CANCEL_EVENT.clear()
    _QR_CENTERING_ACTIVE.set()
    with _QR_ALIGNMENT_CONDITION:
        sequence = int(_QR_ALIGNMENT_STATE["sequence"])
        _QR_ALIGNMENT_STATE.update({
            "visible": False,
            "points_px": None,
            "complete_detection": False,
            "finder_count": 0,
            "pose_acceptable": False,
        })

    if not _QR_OPENCV_AVAILABLE:
        return _set_qr_center_status(
            "opencv_unavailable_camera_locked",
            command=command,
            ok=False,
            instruction="OPENCV NO DISPONIBLE - SIN MOVIMIENTO",
        )
    if not _heading_ready_for_qr_probe(robot_state):
        return _set_qr_center_status(
            "heading_not_ready_no_qr_probe_camera_locked",
            command=command,
            ok=False,
            instruction="ANGULO NO ESTABLE - SIN BUSQUEDA QR",
        )

    _set_qr_center_status(
        "checking_original_position",
        command=command,
        probe_offset_mm=0.0,
        instruction="QUIETO - BUSCANDO QR COMPLETO",
    )
    alignment = _wait_for_verified_qr(sequence, _QR_PROBE_DETECT_TIMEOUT_S)
    if alignment is not None:
        _QR_CENTERING_ACTIVE.clear()
        return _set_qr_center_status(
            "qr_fully_visible_orthogonal_camera_released",
            command=command,
            probe_offset_mm=0.0,
            ok=True,
            instruction="LISTO - QR VERIFICADO",
        )

    for probe_index, probe_mm in enumerate(
        (_QR_PROBE_DISTANCE_MM, -_QR_PROBE_DISTANCE_MM), start=1
    ):
        if _QR_CENTER_CANCEL_EVENT.is_set():
            return _set_qr_center_status(
                "cancelled_camera_locked",
                command=command,
                ok=False,
                instruction="CANCELADO",
            )

        direction = "AVANZAR" if probe_mm > 0.0 else "RETROCEDER"
        _set_qr_center_status(
            "bounded_qr_probe",
            command=command,
            probe_index=probe_index,
            probe_offset_mm=probe_mm,
            instruction=f"{direction} 5.0 mm - BUSQUEDA LIMITADA",
        )
        if not _qr_relative_primitive(
            "move_relative_mm",
            {"distance_mm": probe_mm},
            f"QR_PROBE_{probe_index}",
        ):
            return _set_qr_center_status(
                "qr_probe_motion_failed_camera_locked",
                command=command,
                probe_index=probe_index,
                ok=False,
                instruction="FALLO SONDEO - DETENIDO",
            )

        with _QR_ALIGNMENT_CONDITION:
            sequence = int(_QR_ALIGNMENT_STATE["sequence"])
        alignment = _wait_for_verified_qr(
            sequence, _QR_PROBE_DETECT_TIMEOUT_S
        )
        if alignment is not None:
            _QR_CENTERING_ACTIVE.clear()
            return _set_qr_center_status(
                "qr_fully_visible_orthogonal_camera_released",
                command=command,
                probe_index=probe_index,
                probe_offset_mm=probe_mm,
                ok=True,
                instruction=f"LISTO - QR ENCONTRADO A {probe_mm:+.1f} mm",
            )

        _set_qr_center_status(
            "undoing_failed_qr_probe",
            command=command,
            probe_index=probe_index,
            probe_offset_mm=probe_mm,
            instruction=f"QR NO ENCONTRADO - DESHACER {probe_mm:+.1f} mm",
        )
        if not _qr_relative_primitive(
            "move_relative_mm",
            {"distance_mm": -probe_mm},
            f"QR_PROBE_UNDO_{probe_index}",
        ):
            return _set_qr_center_status(
                "qr_probe_undo_failed_camera_locked",
                command=command,
                probe_index=probe_index,
                ok=False,
                instruction="FALLO AL DESHACER - DETENIDO",
            )
        with _QR_ALIGNMENT_CONDITION:
            sequence = int(_QR_ALIGNMENT_STATE["sequence"])

    return _set_qr_center_status(
        "qr_not_found_after_bounded_probe_original_position_restored_camera_locked",
        command=command,
        probe_offset_mm=0.0,
        ok=False,
        instruction="QR NO ENCONTRADO - POSICION ORIGINAL RESTAURADA",
    )


def get_qr_alignment_state():
    with _QR_ALIGNMENT_CONDITION:
        snapshot = dict(_QR_ALIGNMENT_STATE)
    snapshot["centering_active"] = _QR_CENTERING_ACTIVE.is_set()
    snapshot["camera_forward_image_deg"] = _QR_CAMERA_FORWARD_IMAGE_DEG
    snapshot["visible_fraction_required"] = _QR_VISIBLE_FRACTION_REQUIRED
    snapshot["orthogonality_tolerance_deg"] = _QR_ORTHOGONALITY_TOLERANCE_DEG
    snapshot["lateral_automotion_enabled"] = False
    return {"ok": True, "alignment": snapshot}


def create_user_api(payload: dict):
    name = payload.get('name')
    avatar = payload.get('avatar', 'fas fa-robot')
    color = payload.get('color', '#3b82f6')
    world = payload.get('world', 'world-space')
    if not name:
        return {'error': 'name required'}
    uid = store.create_user(name, avatar, color, world)
    return {'ok': True, 'id': uid}

def list_users_api():
    users = store.list_users()
    return {'users': users}

def get_user_api(payload: dict):
    uid = payload.get('id')
    user = store.get_user(uid)
    return {'user': user} if user else {'error': 'not found'}

def update_user_api(payload: dict):
    uid = payload.get('id')
    if not uid:
        return {'error': 'id required'}
    
    data = dict(payload)
    del data['id']
    store.update_user(uid, data)
    return {'ok': True}

def delete_user_api(payload: dict):
    uid = payload.get('id')
    store.delete_user(uid)
    return {'ok': True}


def record_game_api(payload: dict):
    
    try:
        uid = payload.get('user_id')
        trajectory_id = payload.get('trajectory_id')
        won_raw = payload.get('won')
        
        if uid is None:
            return {'error': 'user_id required'}
            
        
        mistakes = _active_trajectory_state.get("mistakes", 0)
        total_steps = _active_trajectory_state.get("total_steps", 0)
        completed_steps = max(
            0, int(_active_trajectory_state.get("completed_steps", 0) or 0)
        )
        
        start_time = _active_trajectory_state.get("start_time")
        duration = int(time.time() - start_time) if start_time else 0
        
        if not isinstance(won_raw, bool):
            if isinstance(won_raw, int): won_raw = bool(won_raw)
            elif isinstance(won_raw, str) and won_raw.lower() in ('true', '1', 'yes'): won_raw = True
            elif isinstance(won_raw, str) and won_raw.lower() in ('false', '0', 'no'): won_raw = False

        store.record_game(
            uid=int(uid), 
            trajectory_id=trajectory_id, 
            won=won_raw,
            mistakes=mistakes,
            total_steps=total_steps,
            completed_steps=completed_steps,
            duration_seconds=duration
        )
        
        logger.info(f"Detailed game recorded: user_id={uid}, tid={trajectory_id}, mistakes={mistakes}")
        return {'ok': True}
    except Exception as e:
        logger.warning(f"record_game_api error: {e}")
        return {'error': str(e)}

def list_game_history_api(payload: dict):
    
    uid = payload.get('user_id')
    tid = payload.get('trajectory_id')
    history = store.list_game_history(uid, tid)
    return {'history': history}


def get_active_trajectory():
    
    return _active_trajectory_state









import time as _time

_last_ei_fire: float = 0.0   
_EI_DEBOUNCE_WINDOW = 1.5    




_seq_stop_event = threading.Event()

def _run_sequence(canons: list[str], raw: str, source: str):
    ui.send_message("speech_event", {
        "raw": raw,
        "command": " -> ".join(canons),
        "source": source,
        "timestamp": _iso_now(),
    })
    for canon in canons:
        if _seq_stop_event.is_set():
            break
        logger.info(f"[VOICE/{source}] Executing Sequence Vector: {canon}")
        movement_ok = True
        if canon == "FORWARD":  movement_ok = voice_motor_forward()
        elif canon == "BACKWARD": movement_ok = voice_motor_backward()
        elif canon == "LEFT":   movement_ok = voice_motor_left()
        elif canon == "RIGHT":  movement_ok = voice_motor_right()
        elif canon == "STOP":   
            execute_robot_motion("STOP", source=source)
            break
        if not movement_ok:
            logger.warning(f"[VOICE/{source}] Sequence stopped after failed robot command: {canon}")
            break
        
        import time
        
        for _ in range(2):
            if _seq_stop_event.is_set(): break
            time.sleep(0.1)

def _dispatch_voice_sequence(canons: list[str], raw: str, source: str = "?") -> None:
    if not canons: return
    
    _seq_stop_event.set()
    import time
    time.sleep(0.15)
    _seq_stop_event.clear()
    
    t = threading.Thread(target=_run_sequence, args=(canons, raw, source), daemon=True)
    t.start()




def _ei_detect_cb(label: str, score: float = 1.0) -> None:
    global _last_ei_fire
    _last_ei_fire = _time.time()
    canons = interpret_command(label)   
    if canons:
        logger.info(f"[VOICE/EI] Detected '{label}' (score={score:.2f}) -> {' -> '.join(canons)}")
        _dispatch_voice_sequence(canons, raw=label, source="EI")
    else:
        logger.debug(f"[VOICE/EI] Detected '{label}' (score={score:.2f}) — no matching command")




_SR_SAMPLE_RATE = 16000
_SR_CHUNK_SECONDS = 2.0
_sr_thread_stop = threading.Event()

_GOOGLE_SR_KEY = None
def _get_google_sr_key():
    
    global _GOOGLE_SR_KEY
    if _GOOGLE_SR_KEY is not None:
        return _GOOGLE_SR_KEY
    try:
        import urllib.request, re
        logger.info("[VOICE/SR] Fetching fallback Chromium API key from GitHub...")
        content = urllib.request.urlopen('https://raw.githubusercontent.com/Uberi/speech_recognition/master/speech_recognition/recognizers/google.py', timeout=5).read().decode('utf-8')
        keys = re.findall(r'AIza[A-Za-z0-9_\-]+', content)
        if keys:
            _GOOGLE_SR_KEY = keys[0]
            logger.info(f"[VOICE/SR] Successfully extracted API Key: {_GOOGLE_SR_KEY[:10]}...")
            return _GOOGLE_SR_KEY
    except Exception as e:
        logger.warning(f"[VOICE/SR] Failed to fetch fallback Chromium key: {e}")
    _GOOGLE_SR_KEY = ""
    return _GOOGLE_SR_KEY

def _capture_and_recognise():
    
    import time
    time.sleep(_SR_CHUNK_SECONDS)  
    
    with _audio_lock:
        data_len = len(_shared_audio)
        if data_len == 0:
            logger.debug(f"[VOICE/SR] {int(_SR_CHUNK_SECONDS)}s window elapsed: Shared audio buffer is empty.")
            return None
        data = bytes(_shared_audio)
        _shared_audio.clear()
        
    
    if len(data) < _SR_SAMPLE_RATE * 2:
        logger.debug(f"[VOICE/SR] {int(_SR_CHUNK_SECONDS)}s window elapsed: Buffer too small ({len(data)} bytes).")
        return None
        
    try:
        import urllib.request, urllib.parse
        api_key = _get_google_sr_key()
        
        url = "http://www.google.com/speech-api/v2/recognize?{}".format(
            urllib.parse.urlencode({
                "client": "chromium",
                "lang": "es-ES",
                "pfilter": 0,
                "key": api_key
            })
        )
        req = urllib.request.Request(url, data=data)
        req.add_header("Content-Type", f"audio/l16; rate={_SR_SAMPLE_RATE}")
        
        res = urllib.request.urlopen(req, timeout=5)
        text = res.read().decode('utf-8')
        
        
        lines = text.strip().split('\n')
        for line in reversed(lines):
            try:
                msg = json.loads(line)
                if "result" in msg and len(msg["result"]) > 0:
                    return msg["result"][0]["alternative"][0]["transcript"]
            except Exception:
                pass
                
        logger.debug(f"[VOICE/SR] Google SR: {int(_SR_CHUNK_SECONDS)}s window processed ({len(data)} bytes), but heard no words.")
        return None
        
    except Exception as e:
        logger.warning(f"[VOICE/SR] Google SR API error: {e}")
        return None

def _sr_loop():
    import time
    logger.info("[VOICE/SR] Google SR fallback thread started, natively waiting 5s to yield mic to EI...")
    
    time.sleep(5.0)
    
    while not _sr_thread_stop.is_set():
        raw = _capture_and_recognise()
        if not raw:
            continue
        
        if _time.time() - _last_ei_fire < _EI_DEBOUNCE_WINDOW:
            logger.debug(f"[VOICE/SR] Heard '{raw}' but EI fired recently — skipping.")
            continue
        canons = interpret_command(raw)
        if canons:
            logger.info(f"[VOICE/SR] Heard '{raw}' -> {' -> '.join(canons)}")
            _dispatch_voice_sequence(canons, raw=raw, source="SR")
        else:
            logger.debug(f"[VOICE/SR] Heard '{raw}' — no command match, discarding.")

def start_speech_recognition():
    
    t = threading.Thread(target=_sr_loop, daemon=True, name="SpeechRecognition")
    t.start()







if _ei_model_available and spotter is not None:
    logger.info(f"[VOICE] EI model active ({_EI_MODEL_PATH}) — registering on_detect callbacks.")
    
    def _make_ei_cb(lbl: str):
        def _cb():
            _ei_detect_cb(lbl)
        return _cb

    
    
    for _ei_label in ["izquierda", "derecha", "adelante", "atras",
                      "left", "right", "forward", "back", "stop"]:
        spotter.on_detect(_ei_label, _make_ei_cb(_ei_label))
else:
    logger.warning("[VOICE] EI model not available — EI path disabled.")


start_speech_recognition()




ui.on_message("pin_toggle", on_pin_toggle)
ui.on_message("batch_pin_set", on_batch_pin_set)


ui.on_message("motor_forward", on_motor_forward)
ui.on_message("motor_backward", on_motor_backward)
ui.on_message("motor_left", on_motor_left)
ui.on_message("motor_right", on_motor_right)

ui.on_message("motor_stop", on_motor_stop)
ui.on_message("reset_detection", reset_detection)


Bridge.provide("animation_progress", on_animation_progress)
Bridge.provide("robot_motion_complete", on_robot_motion_complete)



ui.expose_api('POST', '/create_user', create_user_api)
ui.expose_api('GET', '/list_users', list_users_api)
ui.expose_api('POST', '/get_user', get_user_api)
ui.expose_api('POST', '/update_user', update_user_api)
ui.expose_api('POST', '/delete_user', delete_user_api)


ui.expose_api("GET", "/states", on_get_states)


ui.expose_api('GET', '/list_scans', on_list_scans)
ui.expose_api('POST', '/update_board', update_board)


ui.expose_api('POST', '/persist_frame', persist_frame)
ui.expose_api('POST', '/load_frame', load_frame)
ui.expose_api('POST', '/list_frames', list_frames)
ui.expose_api('POST', '/get_frame', get_frame)
ui.expose_api('POST', '/delete_frame', delete_frame)
ui.expose_api('POST', '/transform_frame', transform_frame)
ui.expose_api('POST', '/export_frames', export_frames)
ui.expose_api('POST', '/reorder_frames', reorder_frames)


ui.expose_api('POST', '/play_animation', play_animation)
ui.expose_api('POST', '/stop_animation', stop_animation)


ui.expose_api('GET', '/config', get_config)
ui.expose_api('GET', '/robot_state', get_robot_telemetry_for_web)
ui.expose_api('GET', '/qr_alignment_state', get_qr_alignment_state)

def get_control_profile_api():
    return {
        "ok": True,
        "path": CONTROL_PROFILE_PATH,
        "metadata": dict(CONTROL_PROFILE_METADATA),
        "profile": dict(FULL_TUNING_PROFILE),
        "verification_keys": list(VERIFICATION_KEYS),
    }


def update_control_profile_api(payload: dict):
    
    global CONTROL_PROFILE_METADATA
    try:
        raw_values = payload.get("values", payload)
        if not isinstance(raw_values, dict):
            return {"error": "values must be an object"}
        updates = validated_updates(raw_values)
        if not updates:
            return {"error": "at least one control value is required"}

        result = set_robot_values(updates)
        expected_count = len(updates)
        if "ERROR" in result or f"applied={expected_count}" not in result:
            return {"error": f"MCU rejected control values: {result}"}

        
        
        
        state = get_full_robot_state(print_raw=False) or {}
        mismatches = {}
        for key, expected in updates.items():
            if key not in state:
                mismatches[key] = {"expected": expected, "actual": None}
                continue
            actual = float(state[key])
            tolerance = 0.5 if isinstance(expected, int) else 0.001
            if abs(actual - float(expected)) > tolerance:
                mismatches[key] = {"expected": expected, "actual": actual}
        if mismatches:
            return {"error": "MCU verification failed", "mismatches": mismatches}

        FULL_TUNING_PROFILE.update(updates)
        document = save_control_profile(
            CONTROL_PROFILE_PATH,
            FULL_TUNING_PROFILE,
            source=str(payload.get("source", "manual_api")),
            calibrated=bool(payload.get(
                "calibrated", CONTROL_PROFILE_METADATA.get("calibrated", False)
            )),
            notes=payload.get("notes"),
        )
        CONTROL_PROFILE_METADATA = {
            key: document.get(key)
            for key in ("schema_version", "source", "calibrated", "updated_at", "notes")
        }
        EXPECTED_CRITICAL_TUNING.update({
            key: FULL_TUNING_PROFILE[key]
            for key in VERIFICATION_KEYS
        })
        return {
            "ok": True,
            "applied": updates,
            "metadata": dict(CONTROL_PROFILE_METADATA),
            "set_values_result": result,
        }
    except ProfileValidationError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        logger.error(f"[ROBOT] update_control_profile_api error: {exc}")
        return {"error": str(exc)}


def calibrate_distance_api(payload: dict):
    
    try:
        actual_mm    = float(payload.get("actual_mm", 0))
        commanded_mm = float(payload.get("commanded_mm",
                              FULL_TUNING_PROFILE.get("CELL_DISTANCE_MM", 200.0)))
        wheel        = str(payload.get("wheel", "both")).lower()

        state = get_robot_state(print_raw=False) or {}
        if "LEFT_TICKS_PER_MM" not in state or "RIGHT_TICKS_PER_MM" not in state:
            return {
                "error": "MCU firmware does not expose ticks/mm; upload the updated sketch first"
            }
        cur_left = float(state["LEFT_TICKS_PER_MM"])
        cur_right = float(state["RIGHT_TICKS_PER_MM"])
        correction = corrected_ticks_per_mm(
            current_left=cur_left,
            current_right=cur_right,
            commanded_mm=commanded_mm,
            actual_mm=actual_mm,
            wheel=wheel,
        )
        ratio = correction["ratio"]
        new_left = round(correction["left_ticks_per_mm"], 4)
        new_right = round(correction["right_ticks_per_mm"], 4)

        apply_vals = {}
        if wheel in ("both", "left"):
            apply_vals["LEFT_TICKS_PER_MM"]  = new_left
        if wheel in ("both", "right"):
            apply_vals["RIGHT_TICKS_PER_MM"] = new_right

        update_result = update_control_profile_api({
            "values": apply_vals,
            "source": "distance_calibration",
            "calibrated": True,
            "notes": (
                f"commanded_mm={commanded_mm}, actual_mm={actual_mm}, "
                f"wheel={wheel}, ratio={ratio:.6f}"
            ),
        })
        if not update_result.get("ok"):
            return update_result

        logger.info(
            f"[CALIB] distance: L={new_left} R={new_right} ratio={ratio:.4f}"
        )
        return {
            "ok": True,
            "ratio": ratio,
            "left_ticks_per_mm":  new_left,
            "right_ticks_per_mm": new_right,
            "previous_left_ticks_per_mm": cur_left,
            "previous_right_ticks_per_mm": cur_right,
            "metadata": update_result.get("metadata"),
            "note": "Calibration was applied, MCU-verified, and persisted atomically.",
        }
    except (ProfileValidationError, TypeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"[CALIB] calibrate_distance_api error: {e}")
        return {"error": str(e)}


def calibrate_ratio_api(payload: dict):
    try:
        commanded = float(payload.get("commanded_value", 0))
        actual = float(payload.get("actual_value", 0))
        if not math.isfinite(commanded) or not math.isfinite(actual):
            return {"error": "commanded_value and actual_value must be finite"}
        if commanded <= 0 or actual <= 0:
            return {"error": "commanded_value and actual_value must be greater than zero"}

        raw_keys = payload.get("parameter_keys", [])
        if isinstance(raw_keys, str):
            raw_keys = [raw_keys]
        if not isinstance(raw_keys, list) or not raw_keys:
            return {"error": "parameter_keys must contain at least one profile key"}

        keys = list(dict.fromkeys(str(key).strip() for key in raw_keys if str(key).strip()))
        if not keys:
            return {"error": "parameter_keys must contain at least one profile key"}
        if len(keys) > 32:
            return {"error": "no more than 32 profile keys may be calibrated at once"}

        unknown = [key for key in keys if key not in FULL_TUNING_PROFILE]
        if unknown:
            return {"error": f"unknown control keys: {', '.join(unknown)}"}

        ratio = commanded / actual
        previous = {key: FULL_TUNING_PROFILE[key] for key in keys}
        proposed = {key: float(previous[key]) * ratio for key in keys}
        updates = validated_updates(proposed)
        unit = str(payload.get("unit", "unit")).strip()[:16] or "unit"
        update_result = update_control_profile_api({
            "values": updates,
            "source": "ratio_calibration",
            "calibrated": True,
            "notes": (
                f"commanded={commanded}, actual={actual}, unit={unit}, "
                f"ratio={ratio:.8f}, keys={','.join(keys)}"
            ),
        })
        if not update_result.get("ok"):
            return update_result
        return {
            "ok": True,
            "ratio": ratio,
            "unit": unit,
            "commanded_value": commanded,
            "actual_value": actual,
            "previous": previous,
            "applied": updates,
            "metadata": update_result.get("metadata"),
        }
    except (ProfileValidationError, TypeError, ValueError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        logger.error(f"[CALIB] calibrate_ratio_api error: {exc}")
        return {"error": str(exc)}


def run_speed_test_api(payload: dict):
    
    try:
        if payload.get("confirm_safe_test") is not True:
            return {
                "error": (
                    "confirm_safe_test=true is required; lift/secure the robot "
                    "for single-track tests and keep a physical STOP available"
                )
            }

        left_tps = float(payload.get("left_tps", 0.0))
        right_tps = float(payload.get("right_tps", 0.0))
        duration_ms = int(payload.get("duration_ms", 0))
        if not math.isfinite(left_tps) or not math.isfinite(right_tps):
            return {"error": "speed targets must be finite numbers"}
        if not -1000.0 <= left_tps <= 1000.0 or not -1000.0 <= right_tps <= 1000.0:
            return {"error": "left_tps and right_tps must be within -1000..1000"}
        if abs(left_tps) < 1.0 and abs(right_tps) < 1.0:
            return {"error": "at least one speed target must have magnitude >= 1 tick/s"}
        if not 200 <= duration_ms <= 5000:
            return {"error": "duration_ms must be within 200..5000"}
        if not ensure_robot_ready():
            return {"error": "robot_not_initialized"}

        lock_acquired = _robot_motion_lock.acquire(blocking=False)
        if not lock_acquired:
            return {"error": "motion_command_already_active"}

        _robot_motion_active = True
        _robot_motion_result_code = None
        _robot_motion_complete_event.clear()
        result = robot_bridge_call("start_speed_test", json.dumps({
            "left_tps": left_tps,
            "right_tps": right_tps,
            "duration_ms": duration_ms,
        }))
        if "start_speed_test:" not in result:
            robot_bridge_call("stop_robot")
            return {"error": f"MCU rejected speed test: {result}"}

        final_state = wait_until_robot_idle(
            "SPEED_TEST",
            timeout_s=(duration_ms / 1000.0) + 4.0,
            require_heading_result=False,
        ) or {}
        if robot_state_is_fault(final_state):
            return {
                "error": f"speed test fault: {final_state.get('fault_reason', 'unknown')}",
                "start_result": result,
                "state": final_state,
            }
        return {
            "ok": robot_motion_succeeded(
                final_state, require_heading_result=False
            ),
            "start_result": result,
            "state": final_state,
        }
    except (TypeError, ValueError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        logger.error(f"[CALIB] run_speed_test_api error: {exc}")
        robot_bridge_call("stop_robot")
        return {"error": str(exc)}
    finally:
        if lock_acquired:
            _robot_motion_active = False
            _robot_motion_lock.release()

def robot_motion_api(payload: dict):
    try:
        command = str(payload.get("command", "")).strip().upper()
        if not command:
            return {"error": "command is required (FORWARD, BACKWARD, LEFT, RIGHT, STOP)"}
        ok = execute_robot_motion(command, source="calibration_ui")
        state = get_robot_state(print_raw=False) or {}
        return {
            "ok": ok,
            "command": command,
            "mode": state.get("mode"),
            "fault_reason": state.get("fault_reason", ""),
            "state": state,
        }
    except Exception as exc:
        logger.error(f"[CALIB] robot_motion_api error: {exc}")
        return {"error": str(exc)}

def robot_zero_pose_api(payload: dict = None):
    try:
        result = robot_bridge_call("zero_pose")
        state = get_robot_state(print_raw=False) or {}
        return {
            "ok": "failed" not in str(result).lower(),
            "result": str(result),
            "state": state,
        }
    except Exception as exc:
        logger.error(f"[CALIB] robot_zero_pose_api error: {exc}")
        return {"error": str(exc)}

ui.expose_api('GET', '/robot_control_profile', get_control_profile_api)
ui.expose_api('POST', '/robot_control_profile', update_control_profile_api)
ui.expose_api('POST', '/robot_calibrate_distance', calibrate_distance_api)
ui.expose_api('POST', '/robot_calibrate_ratio', calibrate_ratio_api)
ui.expose_api('POST', '/robot_speed_test', run_speed_test_api)
ui.expose_api('POST', '/robot_motion', robot_motion_api)
ui.expose_api('POST', '/robot_zero_pose', robot_zero_pose_api)


ui.expose_api('POST', '/create_trajectory', create_trajectory)
ui.expose_api('GET', '/list_trajectories', list_trajectories)
ui.expose_api('POST', '/update_trajectory', update_trajectory)
ui.expose_api('POST', '/delete_trajectory', delete_trajectory)


ui.expose_api('POST', '/record_game', record_game_api)
ui.expose_api('GET', '/active_trajectory', get_active_trajectory)
ui.expose_api('POST', '/set_active_trajectory', set_active_trajectory_api)
ui.expose_api('POST', '/list_game_history', list_game_history_api)


def generate_trajectory_pdf_api(payload):
    try:
        tid = int(payload.get('trajectory_id'))
        trajectory = store.get_trajectory_by_id(tid)
        if not trajectory:
            return {"error": "Trajectory not found"}
        
        frames = store.list_frames(tid)
        out_name = f"trajectory_{tid}_qrcodes.pdf"
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "common", "temp_pdf")
        out_path = os.path.join(out_dir, out_name)
        os.makedirs(out_dir, exist_ok=True)
        
        from pdf_manager import generate_trajectory_pdf
        generate_trajectory_pdf(
            trajectory['name'],
            frames,
            out_path,
            trajectory_image=trajectory.get('cell_image'),
            trajectory_id=tid
        )
        
        return {"ok": True, "url": f"/common/temp_pdf/{out_name}"}
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return {"error": str(e)}

def generate_qr_api(payload: dict):
    
    content = payload.get('data')
    if not content:
        return {"error": "Missing data for QR"}
    
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {"ok": True, "image": img_str}
    except Exception as e:
        logger.error(f"Failed to generate QR: {e}")
        return {"error": str(e)}

def generate_multi_trajectory_pdf_api(payload: dict):
    try:
        tids = payload.get('trajectory_ids', [])
        layout = payload.get('layout', '2x3')
        if not tids:
            return {"error": "No trajectory IDs provided"}
        
        trajectories_data = []
        for tid in tids:
            traj = store.get_trajectory_by_id(int(tid))
            if traj:
                frames = store.list_frames(int(tid))
                trajectories_data.append({
                    **traj,
                    "frames": frames
                })
        
        if not trajectories_data:
            return {"error": "No valid trajectories found"}

        out_name = f"batch_trajectories_{int(time.time())}.pdf"
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "trajectories", out_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        from pdf_manager import generate_multi_trajectory_pdf
        generate_multi_trajectory_pdf(trajectories_data, out_path, layout=layout)
        
        return {"ok": True, "url": f"/trajectories/{out_name}"}
    except Exception as e:
        logger.error(f"Multi-PDF generation error: {e}")
        return {"error": str(e)}

ui.expose_api('GET', '/generate_trajectory_pdf', generate_trajectory_pdf_api)
ui.expose_api('POST', '/generate_qr', generate_qr_api)
ui.expose_api('POST', '/generate_multi_trajectory_pdf', generate_multi_trajectory_pdf_api)

_EMAIL_LAST_SENT: float = 0.0
_EMAIL_COOLDOWN: float = 10.0

def send_pdf_email_api(payload: dict):
    global _EMAIL_LAST_SENT
    now = time.time()
    if now - _EMAIL_LAST_SENT < _EMAIL_COOLDOWN:
        return {"error": "Rate limit: wait before sending another email"}

    destination = str(payload.get("email", "")).strip()
    tids = payload.get("trajectory_ids", [])
    layout = payload.get("layout", "2x3")

    if not destination:
        return {"error": "email required"}
    if not tids:
        return {"error": "No trajectory IDs provided"}

    try:
        from pdf_manager import generate_multi_trajectory_pdf, send_pdf_email

        trajectories_data = []
        for tid in tids:
            traj = store.get_trajectory_by_id(int(tid))
            if traj:
                frames = store.list_frames(int(tid))
                trajectories_data.append({**traj, "frames": frames})

        if not trajectories_data:
            return {"error": "No valid trajectories found"}

        out_name = f"email_report_{int(time.time())}.pdf"
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "trajectories", out_name)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        generate_multi_trajectory_pdf(trajectories_data, out_path, layout=layout)

        send_pdf_email(destination, out_path)
        _EMAIL_LAST_SENT = time.time()
        return {"ok": True}
    except (ValueError, RuntimeError) as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"send_pdf_email_api: {e}")
        return {"error": "Failed to send email"}

ui.expose_api('POST', '/send_pdf_email', send_pdf_email_api)

def upload_trajectory_image_api(payload: dict):
    try:
        tid = int(payload.get('id'))
        image_data = payload.get('image')
        if not image_data:
            return {"error": "No image data"}
        
        if image_data.startswith("data:"):
            header, encoded = image_data.split(",", 1)
        else:
            encoded = image_data
            
        img_bytes = base64.b64decode(encoded)
        filename = f"traj_{tid}_{int(time.time())}.png"
        filepath = os.path.join(store.TRAJECTORY_ASSETS_DIR, filename)
        
        os.makedirs(store.TRAJECTORY_ASSETS_DIR, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
            
        
        store.update_trajectory(tid, {"cell_image": filename})
        
        return {"ok": True, "cell_image": filename}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"error": str(e)}

ui.expose_api('POST', '/upload_trajectory_image', upload_trajectory_image_api)





















_4S_VMIN = 13.2   
_4S_VMAX = 16.8   

_sensor_cache: dict = {
    "mpu6050":    None,
    "ina219":     None,
    "battery_pct": None,
    "timestamp":  None,
    "peripherals": PERIPHERALS_STATUS,
}
_last_mpu_push_monotonic = 0.0
_last_ina_push_monotonic = 0.0
_SENSOR_PUSH_FRESH_S = 3.0


def _calc_battery_pct(voltage_v: float) -> float:
    pct = (voltage_v - _4S_VMIN) / (_4S_VMAX - _4S_VMIN) * 100.0
    return round(max(0.0, min(100.0, pct)), 1)


def _flatten_sensor_args(*args):
    
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return [float(x) for x in args[0]]
    return [float(x) for x in args]


def _apply_mpu6050(values: list):
    
    if len(values) < 6:
        logger.warning(f"[SENSOR] mpu6050 short read: {values}")
        return
    reading = {
        "ax_g":   round(values[0], 4),
        "ay_g":   round(values[1], 4),
        "az_g":   round(values[2], 4),
        "gx_dps": round(values[3], 2),
        "gy_dps": round(values[4], 2),
        "gz_dps": round(values[5], 2),
    }
    _sensor_cache["mpu6050"]   = reading
    _sensor_cache["timestamp"] = _iso_now()
    ui.send_message("sensor_update", _sensor_cache)


def _apply_ina219(values: list):
    
    if len(values) < 4:
        logger.warning(f"[SENSOR] ina219 short read: {values}")
        return
    _ina_partial["v"]     = float(values[0])
    _ina_partial["shunt"] = float(values[1])
    _ina_partial["i"]     = float(values[2])
    _ina_partial["pw"]    = float(values[3])
    _flush_ina()




def on_mpu6050_data(*args):
    
    global _last_mpu_push_monotonic
    global _robot_motion_active, _robot_motion_result_code
    lock_acquired = False
    try:
        _apply_mpu6050(_flatten_sensor_args(*args))
        _last_mpu_push_monotonic = time.monotonic()
    except Exception as e:
        logger.warning(f"[SENSOR/PUSH] mpu6050 parse error: {e}  raw={args}")


def on_ina219_data(*args):
    
    global _last_ina_push_monotonic
    try:
        _apply_ina219(_flatten_sensor_args(*args))
        _last_ina_push_monotonic = time.monotonic()
    except Exception as e:
        logger.warning(f"[SENSOR/PUSH] ina219 parse error: {e}  raw={args}")















_SERIAL_PORTS = [
    "/dev/ttyACM0", "/dev/ttyACM1",
    "/dev/ttyUSB0", "/dev/ttyUSB1",
    "/dev/ttyS0",   "/dev/ttyS1",
]


def _open_sensor_serial():
    
    try:
        import serial as _pyserial  
        for port in _SERIAL_PORTS:
            try:
                ser = _pyserial.Serial(port, 115200, timeout=2)
                logger.info(f"[SENSOR/SERIAL] Opened {port} at 115200 baud")
                PERIPHERALS_STATUS["mcu_serial"] = True
                return ser
            except Exception:
                continue
        logger.warning(f"[SENSOR/SERIAL] No MCU serial port found (tried {_SERIAL_PORTS})")
        PERIPHERALS_STATUS["mcu_serial"] = False
        return None
    except ImportError:
        logger.error("[SENSOR/SERIAL] pyserial not installed — run: pip install pyserial")
        PERIPHERALS_STATUS["mcu_serial"] = False
        return None


def _parse_mesbot_line(line: str):
    
    try:
        if line.startswith("MESBOT:MPU:"):
            parts = line[len("MESBOT:MPU:"):].strip().split(",")
            if len(parts) < 6:
                return
            ax, ay, az, gx, gy, gz = [float(p) for p in parts[:6]]
            mpu_data = {
                "ax_g":   round(ax / 9.80665, 4),
                "ay_g":   round(ay / 9.80665, 4),
                "az_g":   round(az / 9.80665, 4),
                "gx_dps": round(gx * 57.2958, 2),
                "gy_dps": round(gy * 57.2958, 2),
                "gz_dps": round(gz * 57.2958, 2),
                "ax_ms2": round(ax, 4),
                "ay_ms2": round(ay, 4),
                "az_ms2": round(az, 4),
            }
            _sensor_cache["mpu6050"]   = mpu_data
            _sensor_cache["timestamp"] = _iso_now()
            
            
            ui.send_message("sensor_update", {
                "mpu6050":   mpu_data,
                "timestamp": _sensor_cache["timestamp"],
                "peripherals": _sensor_cache["peripherals"],
            })

        elif line.startswith("MESBOT:INA:"):
            parts = line[len("MESBOT:INA:"):].strip().split(",")
            if len(parts) < 4:
                return
            bus_v, shunt_mv, current_ma, power_mw = [float(p) for p in parts[:4]]
            
            
            _ina_partial["v"]     = bus_v
            _ina_partial["shunt"] = shunt_mv
            _ina_partial["i"]     = current_ma
            _ina_partial["pw"]    = power_mw
            _flush_ina()

        elif line.startswith("[SENSOR]"):
            logger.info(f"[MCU] {line.strip()}")

    except Exception as e:
        logger.debug(f"[SENSOR/SERIAL] parse error on line {repr(line)}: {e}")



def _sensor_poll_loop():
    import time as _t
    _t.sleep(4.0)  

    while True:
        now = _t.monotonic()
        mpu_push_fresh = now - _last_mpu_push_monotonic < _SENSOR_PUSH_FRESH_S
        ina_push_fresh = now - _last_ina_push_monotonic < _SENSOR_PUSH_FRESH_S
        mcu_ok = mpu_push_fresh or ina_push_fresh or bool(_robot_initialized)

        
        
        
        allow_legacy_pull = not _robot_initialized and not _robot_motion_active
        if allow_legacy_pull and not mpu_push_fresh:
            try:
                try:
                    raw = bridge_call_serialized("read_imu")
                except Exception:
                    raw = bridge_call_serialized("read_mpu6050")
                if raw:
                    _apply_mpu6050(_flatten_sensor_args(raw))
                    mcu_ok = True
            except Exception as e:
                logger.debug(f"[SENSOR/BRIDGE] IMU read failed: {e}")
        if allow_legacy_pull and not ina_push_fresh:
            try:
                raw = bridge_call_serialized("read_ina219")
                if raw:
                    _apply_ina219(_flatten_sensor_args(raw))
                    mcu_ok = True
            except Exception as e:
                logger.debug(f"[SENSOR/BRIDGE] INA219 read failed: {e}")
        
        old_mcu_state = PERIPHERALS_STATUS["mcu_serial"]
        PERIPHERALS_STATUS["mcu_serial"] = mcu_ok or bool(_robot_initialized)
        if old_mcu_state != PERIPHERALS_STATUS["mcu_serial"]:
            ui.send_message("sensor_update", _sensor_cache)
        _t.sleep(1.5)


_sensor_poll_thread = threading.Thread(
    target=_sensor_poll_loop, daemon=True, name="SensorPoll"
)
_sensor_poll_thread.start()
logger.info("[SENSOR] Poll thread started — reading MESBOT: lines from MCU serial")





def get_sensors():
    
    return _sensor_cache








_mpu_partial: dict = {}
_ina_partial: dict = {}


def _flush_mpu():
    p = _mpu_partial
    if all(k in p for k in ("ax","ay","az","gx","gy","gz")):
        _sensor_cache["mpu6050"] = {
            "ax_g":   round(p["ax"] / 9.80665, 4),
            "ay_g":   round(p["ay"] / 9.80665, 4),
            "az_g":   round(p["az"] / 9.80665, 4),
            "gx_dps": round(p["gx"] * 57.2958, 2),   
            "gy_dps": round(p["gy"] * 57.2958, 2),
            "gz_dps": round(p["gz"] * 57.2958, 2),
            "ax_ms2": round(p["ax"], 4),
            "ay_ms2": round(p["ay"], 4),
            "az_ms2": round(p["az"], 4),
        }
        _sensor_cache["timestamp"] = _iso_now()
        _mpu_partial.clear()
        ui.send_message("sensor_update", _sensor_cache)



_INA_MEDIAN_WINDOW = 9
_INA_SIGMA_K       = 2.5
_INA_DEADBAND_V    = 0.05
_INA_DEADBAND_I    = 3.0
_INA_DEADBAND_P    = 10.0

_ina_win_v: collections.deque = collections.deque(maxlen=_INA_MEDIAN_WINDOW)
_ina_win_s: collections.deque = collections.deque(maxlen=_INA_MEDIAN_WINDOW)
_ina_win_i: collections.deque = collections.deque(maxlen=_INA_MEDIAN_WINDOW)
_ina_win_p: collections.deque = collections.deque(maxlen=_INA_MEDIAN_WINDOW)

_ina_sent: dict = {"v": None, "s": None, "i": None, "p": None}


def _median(buf: collections.deque) -> float:
    s = sorted(buf)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _sigma_clip(new_val: float, window: collections.deque) -> float:
    n = len(window)
    if n < 3:
        return new_val
    mean = sum(window) / n
    variance = sum((x - mean) ** 2 for x in window) / n
    sigma = variance ** 0.5
    if sigma > 0 and abs(new_val - mean) > _INA_SIGMA_K * sigma:
        return _median(window)
    return new_val


def _flush_ina():
    p = _ina_partial
    if not all(k in p for k in ("v", "shunt", "i", "pw")):
        return

    _ina_win_v.append(_sigma_clip(p["v"],     _ina_win_v))
    _ina_win_s.append(_sigma_clip(p["shunt"], _ina_win_s))
    _ina_win_i.append(_sigma_clip(p["i"],     _ina_win_i))
    _ina_win_p.append(_sigma_clip(p["pw"],    _ina_win_p))
    _ina_partial.clear()

    if len(_ina_win_v) < 4:
        return

    filt_v = _median(_ina_win_v)
    filt_s = _median(_ina_win_s)
    filt_i = _median(_ina_win_i)
    filt_p = _median(_ina_win_p)

    last_v = _ina_sent["v"]
    last_i = _ina_sent["i"]
    last_p = _ina_sent["p"]

    v_changed = last_v is None or abs(filt_v - last_v) >= _INA_DEADBAND_V
    i_changed = last_i is None or abs(filt_i - last_i) >= _INA_DEADBAND_I
    p_changed = last_p is None or abs(filt_p - last_p) >= _INA_DEADBAND_P

    if not (v_changed or i_changed or p_changed):
        return

    _ina_sent["v"] = filt_v
    _ina_sent["i"] = filt_i
    _ina_sent["p"] = filt_p

    _sensor_cache["ina219"] = {
        "voltage_v":  round(filt_v, 3),
        "shunt_mv":   round(filt_s, 2),
        "current_ma": round(filt_i, 1),
        "power_mw":   round(filt_p, 1),
    }
    _sensor_cache["battery_pct"] = _calc_battery_pct(filt_v)
    _sensor_cache["timestamp"]   = _iso_now()
    ui.send_message("sensor_update", _sensor_cache)





def _on_mpu_ax(v): _mpu_partial["ax"] = float(v); _flush_mpu()
def _on_mpu_ay(v): _mpu_partial["ay"] = float(v)
def _on_mpu_az(v): _mpu_partial["az"] = float(v)
def _on_mpu_gx(v): _mpu_partial["gx"] = float(v)
def _on_mpu_gy(v): _mpu_partial["gy"] = float(v)
def _on_mpu_gz(v): _mpu_partial["gz"] = float(v); _flush_mpu()


def _on_ina_bus_v(v):    _ina_partial["v"]     = float(v)
def _on_ina_shunt(v):    _ina_partial["shunt"] = float(v)
def _on_ina_current(v):  _ina_partial["i"]     = float(v)
def _on_ina_power(v):    _ina_partial["pw"]    = float(v); _flush_ina()


Bridge.provide("mpu_ax",      _on_mpu_ax)
Bridge.provide("mpu_ay",      _on_mpu_ay)
Bridge.provide("mpu_az",      _on_mpu_az)
Bridge.provide("mpu_gx",      _on_mpu_gx)
Bridge.provide("mpu_gy",      _on_mpu_gy)
Bridge.provide("mpu_gz",      _on_mpu_gz)
Bridge.provide("ina_v",       _on_ina_bus_v)
Bridge.provide("ina_shunt_mv",_on_ina_shunt)
Bridge.provide("ina_current", _on_ina_current)
Bridge.provide("ina_power",   _on_ina_power)


Bridge.provide("mpu6050_data", on_mpu6050_data)
Bridge.provide("ina219_data",  on_ina219_data)

logger.info("[SENSOR] All Bridge handlers registered (per-channel + vector compat).")


def _debug_monitor():
    while True:
        m = _sensor_cache.get("mpu6050") or {}
        i = _sensor_cache.get("ina219") or {}
        ax = m.get("ax_ms2", 0.0)
        ay = m.get("ay_ms2", 0.0)
        az = m.get("az_ms2", 0.0)
        v = i.get("voltage_v", 0.0)
        if any([ax, ay, az, v]):
             logger.info(f"DEBUG -> MPU({ax:>5.2f}, {ay:>5.2f}, {az:>5.2f}) | INA:{v:>5.2f}V")
        time.sleep(1.0)

threading.Thread(target=_debug_monitor, daemon=True, name="DebugMonitor").start()


ui.expose_api("GET", "/sensors", get_sensors)

logger.info("[SENSOR] Handlers registered (push + 2 s poll fallback).")


def _cleanup_temp_files():
    
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "common", "temp_pdf")
    while True:
        try:
            if os.path.exists(temp_dir):
                now = time.time()
                for f in os.listdir(temp_dir):
                    fp = os.path.join(temp_dir, f)
                    if os.path.isfile(fp) and (now - os.path.getmtime(fp)) > 600:
                        os.remove(fp)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        time.sleep(300) 

threading.Thread(target=_cleanup_temp_files, daemon=True, name="FileCleanup").start()

threading.Thread(target=initialize_robot_background, daemon=True, name="RobotInit").start()

try:
    store.init_db()
except Exception as e:
    logger.error(f"[BOOT] Failed to initialize store DB: {e}")
    PERIPHERALS_STATUS["database"] = False

App.run()
