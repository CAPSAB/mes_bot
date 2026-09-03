

from __future__ import annotations

from datetime import UTC, datetime
import json
import math
import os
import tempfile
from typing import Any, Iterable, Mapping


PROFILE_SCHEMA_VERSION = 1
PROFILE_FILENAME = "robot_control_profile.json"





DEFAULT_CONTROL_PROFILE: dict[str, float | int] = {
    "CELL_DISTANCE_MM": 200.0,
    "LEFT_TICKS_PER_MM": 37.99462551,
    "RIGHT_TICKS_PER_MM": 37.99462551,
    "LEFT_LINEAR_SCALE": 1.0,
    "RIGHT_LINEAR_SCALE": 1.0,
    "FORWARD_DISTANCE_TICK_SCALE": 1.035197,
    "BACKWARD_DISTANCE_TICK_SCALE": 1.035197,
    "TURN_LEFT_DEG_SCALE": 1.0,
    "TURN_RIGHT_DEG_SCALE": 1.0,
    "KP_DISTANCE": 0.95,
    "KP_YAW_STRAIGHT": 50.0,
    "KI_YAW_STRAIGHT": 3.0,
    "KD_YAW_STRAIGHT": 5.0,
    "MAX_YAW_CORRECTION_TPS": 200.0,
    "YAW_INTEGRAL_LIMIT_TPS": 80.0,
    "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM": 0.35,
    "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG": 10.0,
    "YAW_RATE_FILTER_TAU_S": 0.040,
    "KP_TURN_YAW": 14.00,
    "KI_TURN_YAW": 0.0,
    "KD_TURN_YAW": 1.10,
    "TURN_BALANCE_KP_TPS_PER_MM": 12.0,
    "TURN_CENTER_SPEED_KP_TPS_PER_MM_S": 20.0,
    "MAX_TURN_BALANCE_TPS": 100.0,
    "RIGHT_STRAIGHT_BIAS_TPS": 0.0,
    "LEFT_STRAIGHT_SOFTEN_TPS": 0.0,
    "RIGHT_TRACK_SLIP_BOOST_TPS": 0.0,
    "MAX_RIGHT_SLIP_BOOST_TPS": 0.0,
    "LEFT_PWM_MIN": 140,
    "RIGHT_PWM_MIN": 150,
    "LEFT_PWM_MAX": 225,
    "RIGHT_PWM_MAX": 235,
    "ABSOLUTE_PWM_MIN": 90,
    "LEFT_KP_SPEED": 0.120,
    "LEFT_KI_SPEED": 0.035,
    "LEFT_KD_SPEED": 0.000,
    "LEFT_KFF_SPEED": 0.052,
    "RIGHT_KP_SPEED": 0.155,
    "RIGHT_KI_SPEED": 0.045,
    "RIGHT_KD_SPEED": 0.000,
    "RIGHT_KFF_SPEED": 0.068,
    "MAX_STRAIGHT_SPEED_TPS_BASE": 1500.0,
    "MAX_TURN_SPEED_TPS_BASE": 1900.0,
    "MIN_STRAIGHT_SPEED_TPS": 400.0,
    "MIN_TURN_SPEED_TPS": 500.0,
    "ENDPOINT_MIN_STRAIGHT_SPEED_TPS": 400.0,
    "ENDPOINT_MIN_TURN_SPEED_TPS": 500.0,
    "INTEGRAL_LIMIT": 140.0,
    "SPEED_FILTER_TAU_S": 0.060,
    "DERIVATIVE_FILTER_TAU_S": 0.080,
    "TURN_STOP_RATE_TOLERANCE_DPS": 3.0,
    "TURN_SETTLE_COUNT_REQUIRED": 6,
    "STRAIGHT_FINAL_YAW_TOLERANCE_DEG": 0.50,
    "STRAIGHT_FINAL_MIN_CORRECTION_TPS": 60.0,
    "STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED": 8,
    "PROGRESS_BALANCE_GAIN_TPS": 0.0,
    "MAX_PROGRESS_BALANCE_TPS": 0.0,
    "PROGRESS_BALANCE_YAW_GATE_DEG": 4.0,
    "POSITION_TOLERANCE_TICKS": 10,
    "POSITION_COMMAND_DEADBAND_TICKS": 10,
    "BIAS_DISABLE_REMAINING_TICKS": 650,
    "SPEED_STOP_TOLERANCE_TPS": 80.0,
    "TURN_TOLERANCE_DEG": 1.0,
    "TURN_ENCODER_TOLERANCE_TICKS": 180,
    "YAW_IGNORE_DEG": 0.15,
    "PROGRESS_SLIP_THRESHOLD": 0.55,
    "STRAIGHT_YAW_SLIP_THRESHOLD_DEG": 42.0,
    "STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS": 125.0,
    "SLIP_COUNT_LIMIT": 20,
    "TURN_WRONG_WAY_DEG": 8.0,
    "TURN_WRONG_WAY_COUNT_LIMIT": 16,
    "MAX_VALID_YAW_RATE_DPS": 300.0,
    "MAX_VALID_TURN_DELTA_DEG_PER_SAMPLE": 45.0,
    "MAX_VALID_HEADING_JUMP_DEG": 35.0,
    "STALL_PWM_THRESHOLD": 120,
    "STALL_TARGET_SPEED_TPS": 260.0,
    "STALL_MEASURED_SPEED_TPS": 70.0,
    "STALL_COUNT_LIMIT": 8,
    "MAX_RECOVERY_ATTEMPTS_PER_MOTION": 0,
    "RECOVERY_STOP_MS": 180,
    "RECOVERY_PULSE_MS": 170,
    "RECOVERY_SETTLE_MS": 180,
    "RECOVERY_PWM_LEFT": 180,
    "RECOVERY_PWM_RIGHT": 180,
    "RECOVERY_DERATE_FACTOR": 0.84,
    "MIN_SPEED_DERATE": 0.55,
    "IMU_YAW_SIGN": 1,
    "TURN_CONTROL_SIGN": 1,
    "YAW_CORRECTION_SIGN": 1,
}


PROFILE_LIMITS: dict[str, tuple[float, float]] = {
    "CELL_DISTANCE_MM": (50.0, 500.0),
    "LEFT_TICKS_PER_MM": (5.0, 200.0),
    "RIGHT_TICKS_PER_MM": (5.0, 200.0),
    "LEFT_LINEAR_SCALE": (0.6, 1.5),
    "RIGHT_LINEAR_SCALE": (0.6, 1.5),
    "FORWARD_DISTANCE_TICK_SCALE": (0.6, 1.5),
    "BACKWARD_DISTANCE_TICK_SCALE": (0.6, 1.5),
    "TURN_LEFT_DEG_SCALE": (0.7, 1.25),
    "TURN_RIGHT_DEG_SCALE": (0.7, 1.25),
    "KP_DISTANCE": (0.0, 5.0),
    "KP_YAW_STRAIGHT": (0.0, 100.0),
    "KI_YAW_STRAIGHT": (0.0, 50.0),
    "KD_YAW_STRAIGHT": (0.0, 50.0),
    "MAX_YAW_CORRECTION_TPS": (0.0, 1500.0),
    "YAW_INTEGRAL_LIMIT_TPS": (0.0, 1000.0),
    "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM": (0.0, 3.0),
    "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG": (0.0, 30.0),
    "YAW_RATE_FILTER_TAU_S": (0.001, 1.0),
    "KP_TURN_YAW": (0.0, 40.0),
    "KI_TURN_YAW": (0.0, 20.0),
    "KD_TURN_YAW": (0.0, 20.0),
    "TURN_BALANCE_KP_TPS_PER_MM": (0.0, 20.0),
    "TURN_CENTER_SPEED_KP_TPS_PER_MM_S": (0.0, 100.0),
    "MAX_TURN_BALANCE_TPS": (0.0, 500.0),
    "RIGHT_STRAIGHT_BIAS_TPS": (-400.0, 600.0),
    "LEFT_STRAIGHT_SOFTEN_TPS": (-200.0, 400.0),
    "RIGHT_TRACK_SLIP_BOOST_TPS": (0.0, 800.0),
    "MAX_RIGHT_SLIP_BOOST_TPS": (0.0, 800.0),
    "LEFT_PWM_MIN": (0, 255),
    "RIGHT_PWM_MIN": (0, 255),
    "LEFT_PWM_MAX": (0, 255),
    "RIGHT_PWM_MAX": (0, 255),
    "ABSOLUTE_PWM_MIN": (0, 255),
    "LEFT_KP_SPEED": (0.0, 1.0),
    "LEFT_KI_SPEED": (0.0, 0.5),
    "LEFT_KD_SPEED": (0.0, 0.5),
    "LEFT_KFF_SPEED": (0.0, 0.5),
    "RIGHT_KP_SPEED": (0.0, 1.0),
    "RIGHT_KI_SPEED": (0.0, 0.5),
    "RIGHT_KD_SPEED": (0.0, 0.5),
    "RIGHT_KFF_SPEED": (0.0, 0.5),
    "MAX_STRAIGHT_SPEED_TPS_BASE": (100.0, 3000.0),
    "MAX_TURN_SPEED_TPS_BASE": (100.0, 2500.0),
    "MIN_STRAIGHT_SPEED_TPS": (0.0, 1000.0),
    "MIN_TURN_SPEED_TPS": (0.0, 1000.0),
    "ENDPOINT_MIN_STRAIGHT_SPEED_TPS": (0.0, 500.0),
    "ENDPOINT_MIN_TURN_SPEED_TPS": (0.0, 500.0),
    "INTEGRAL_LIMIT": (0.0, 255.0),
    "SPEED_FILTER_TAU_S": (0.0, 1.0),
    "DERIVATIVE_FILTER_TAU_S": (0.0, 1.0),
    "TURN_STOP_RATE_TOLERANCE_DPS": (0.1, 50.0),
    "TURN_SETTLE_COUNT_REQUIRED": (1, 100),
    "STRAIGHT_FINAL_YAW_TOLERANCE_DEG": (0.1, 10.0),
    "STRAIGHT_FINAL_MIN_CORRECTION_TPS": (0.0, 500.0),
    "STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED": (1, 100),
    "PROGRESS_BALANCE_GAIN_TPS": (0.0, 500.0),
    "MAX_PROGRESS_BALANCE_TPS": (0.0, 500.0),
    "PROGRESS_BALANCE_YAW_GATE_DEG": (0.0, 30.0),
    "POSITION_TOLERANCE_TICKS": (10, 2000),
    "POSITION_COMMAND_DEADBAND_TICKS": (10, 2000),
    "BIAS_DISABLE_REMAINING_TICKS": (10, 5000),
    "SPEED_STOP_TOLERANCE_TPS": (0.0, 1000.0),
    "TURN_TOLERANCE_DEG": (0.2, 20.0),
    "TURN_ENCODER_TOLERANCE_TICKS": (10, 3000),
    "YAW_IGNORE_DEG": (0.0, 10.0),
    "PROGRESS_SLIP_THRESHOLD": (0.05, 2.0),
    "STRAIGHT_YAW_SLIP_THRESHOLD_DEG": (5.0, 90.0),
    "STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS": (10.0, 500.0),
    "SLIP_COUNT_LIMIT": (1, 100),
    "TURN_WRONG_WAY_DEG": (1.0, 45.0),
    "TURN_WRONG_WAY_COUNT_LIMIT": (1, 100),
    "MAX_VALID_YAW_RATE_DPS": (50.0, 2000.0),
    "MAX_VALID_TURN_DELTA_DEG_PER_SAMPLE": (5.0, 120.0),
    "MAX_VALID_HEADING_JUMP_DEG": (5.0, 120.0),
    "STALL_PWM_THRESHOLD": (0, 255),
    "STALL_TARGET_SPEED_TPS": (0.0, 1000.0),
    "STALL_MEASURED_SPEED_TPS": (0.0, 500.0),
    "STALL_COUNT_LIMIT": (1, 100),
    "MAX_RECOVERY_ATTEMPTS_PER_MOTION": (0, 20),
    "RECOVERY_STOP_MS": (0, 2000),
    "RECOVERY_PULSE_MS": (0, 2000),
    "RECOVERY_SETTLE_MS": (0, 2000),
    "RECOVERY_PWM_LEFT": (0, 255),
    "RECOVERY_PWM_RIGHT": (0, 255),
    "RECOVERY_DERATE_FACTOR": (0.1, 1.0),
    "MIN_SPEED_DERATE": (0.1, 1.0),
    "IMU_YAW_SIGN": (-1, 1),
    "TURN_CONTROL_SIGN": (-1, 1),
    "YAW_CORRECTION_SIGN": (-1, 1),
}


INTEGER_KEYS = {
    key for key, value in DEFAULT_CONTROL_PROFILE.items() if isinstance(value, int)
}


TUNING_ORDER: list[tuple[str, str]] = [
    (key, (
        "MANDATORY" if key in {"CELL_DISTANCE_MM", "LEFT_TICKS_PER_MM", "RIGHT_TICKS_PER_MM"}
        else "CRITICAL" if key in {"LEFT_LINEAR_SCALE", "RIGHT_LINEAR_SCALE", "FORWARD_DISTANCE_TICK_SCALE", "BACKWARD_DISTANCE_TICK_SCALE", "TURN_LEFT_DEG_SCALE", "TURN_RIGHT_DEG_SCALE"}
        else "NOT_SUGGESTED_AUTOTUNE" if key.startswith("STALL_") or key.startswith("RECOVERY_") or key in {"MAX_RECOVERY_ATTEMPTS_PER_MOTION", "MIN_SPEED_DERATE"}
        else "SUGGESTED_AUTOTUNE" if key in {
            "KP_DISTANCE", "KP_YAW_STRAIGHT", "KI_YAW_STRAIGHT",
            "KD_YAW_STRAIGHT", "MAX_YAW_CORRECTION_TPS",
            "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM",
            "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG",
            "KP_TURN_YAW", "KI_TURN_YAW", "KD_TURN_YAW",
            "TURN_BALANCE_KP_TPS_PER_MM", "TURN_CENTER_SPEED_KP_TPS_PER_MM_S",
            "MAX_TURN_BALANCE_TPS",
        }
        else "OPTIONAL"
    ))
    for key in DEFAULT_CONTROL_PROFILE
]


VERIFICATION_KEYS = (
    "CELL_DISTANCE_MM",
    "LEFT_TICKS_PER_MM",
    "RIGHT_TICKS_PER_MM",
    "LEFT_LINEAR_SCALE",
    "RIGHT_LINEAR_SCALE",
    "FORWARD_DISTANCE_TICK_SCALE",
    "BACKWARD_DISTANCE_TICK_SCALE",
    "TURN_LEFT_DEG_SCALE",
    "TURN_RIGHT_DEG_SCALE",
    "LEFT_KP_SPEED",
    "LEFT_KI_SPEED",
    "LEFT_KD_SPEED",
    "LEFT_KFF_SPEED",
    "RIGHT_KP_SPEED",
    "RIGHT_KI_SPEED",
    "RIGHT_KD_SPEED",
    "RIGHT_KFF_SPEED",
    "SPEED_FILTER_TAU_S",
    "DERIVATIVE_FILTER_TAU_S",
    "TURN_STOP_RATE_TOLERANCE_DPS",
    "TURN_SETTLE_COUNT_REQUIRED",
    "STRAIGHT_FINAL_YAW_TOLERANCE_DEG",
    "STRAIGHT_FINAL_MIN_CORRECTION_TPS",
    "STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED",
    "KP_YAW_STRAIGHT",
    "KI_YAW_STRAIGHT",
    "KD_YAW_STRAIGHT",
    "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM",
    "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG",
    "KP_TURN_YAW",
    "KI_TURN_YAW",
    "KD_TURN_YAW",
    "TURN_BALANCE_KP_TPS_PER_MM",
    "TURN_CENTER_SPEED_KP_TPS_PER_MM_S",
    "MAX_TURN_BALANCE_TPS",
)


class ProfileValidationError(ValueError):
    pass


def _coerce_number(key: str, value: Any) -> float | int:
    if isinstance(value, bool):
        raise ProfileValidationError(f"{key} must be numeric, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ProfileValidationError(f"{key} must be numeric") from exc
    if not math.isfinite(number):
        raise ProfileValidationError(f"{key} must be finite")
    low, high = PROFILE_LIMITS[key]
    if number < low or number > high:
        raise ProfileValidationError(f"{key}={number} outside [{low}, {high}]")
    return int(round(number)) if key in INTEGER_KEYS else number


def validated_updates(values: Mapping[str, Any]) -> dict[str, float | int]:
    unknown = sorted(set(values) - set(DEFAULT_CONTROL_PROFILE))
    if unknown:
        raise ProfileValidationError(f"unknown control keys: {', '.join(unknown)}")
    return {key: _coerce_number(key, value) for key, value in values.items()}


def load_control_profile(path: str) -> tuple[dict[str, float | int], dict[str, Any]]:
    profile = dict(DEFAULT_CONTROL_PROFILE)
    metadata: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "source": "bootstrap_defaults",
        "calibrated": False,
        "updated_at": None,
    }
    if not os.path.isfile(path):
        return profile, metadata

    try:
        with open(path, encoding="utf-8") as stream:
            document = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileValidationError(f"cannot read profile {path}: {exc}") from exc

    if document.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ProfileValidationError(
            f"unsupported profile schema {document.get('schema_version')!r}"
        )
    stored = document.get("profile")
    if not isinstance(stored, dict):
        raise ProfileValidationError("profile document must contain an object named 'profile'")
    profile.update(validated_updates(stored))
    metadata.update({
        "source": document.get("source", "persisted_profile"),
        "calibrated": bool(document.get("calibrated", False)),
        "updated_at": document.get("updated_at"),
        "notes": document.get("notes"),
    })
    return profile, metadata


def save_control_profile(
    path: str,
    profile: Mapping[str, Any],
    *,
    source: str,
    calibrated: bool,
    notes: str | None = None,
) -> dict[str, Any]:
    complete = dict(DEFAULT_CONTROL_PROFILE)
    complete.update(validated_updates(profile))
    document = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "source": str(source),
        "calibrated": bool(calibrated),
        "updated_at": datetime.now(UTC).isoformat(),
        "notes": notes,
        "profile": complete,
    }
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".robot-control-", suffix=".json.tmp", dir=directory
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(document, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return document


def corrected_ticks_per_mm(
    *,
    current_left: float,
    current_right: float,
    commanded_mm: float,
    actual_mm: float,
    wheel: str = "both",
) -> dict[str, float]:
    values = (current_left, current_right, commanded_mm, actual_mm)
    if not all(math.isfinite(float(value)) for value in values):
        raise ProfileValidationError("distance calibration values must be finite")
    if commanded_mm <= 0 or actual_mm <= 0:
        raise ProfileValidationError("commanded_mm and actual_mm must be greater than zero")
    wheel = str(wheel).strip().lower()
    if wheel not in {"both", "left", "right"}:
        raise ProfileValidationError("wheel must be 'both', 'left', or 'right'")
    ratio = float(commanded_mm) / float(actual_mm)
    result = {
        "ratio": ratio,
        "left_ticks_per_mm": float(current_left),
        "right_ticks_per_mm": float(current_right),
    }
    if wheel in {"both", "left"}:
        result["left_ticks_per_mm"] = float(current_left) * ratio
    if wheel in {"both", "right"}:
        result["right_ticks_per_mm"] = float(current_right) * ratio
    validated_updates({
        "LEFT_TICKS_PER_MM": result["left_ticks_per_mm"],
        "RIGHT_TICKS_PER_MM": result["right_ticks_per_mm"],
    })
    return result


def median_distance_ratio(samples: Iterable[Mapping[str, Any]]) -> float:
    ratios: list[float] = []
    for sample in samples:
        commanded = float(sample["commanded_mm"])
        actual = float(sample["actual_mm"])
        if not math.isfinite(commanded) or not math.isfinite(actual) or commanded <= 0 or actual <= 0:
            raise ProfileValidationError("all calibration samples must contain positive finite distances")
        ratios.append(commanded / actual)
    if not ratios:
        raise ProfileValidationError("at least one calibration sample is required")
    ratios.sort()
    middle = len(ratios) // 2
    return ratios[middle] if len(ratios) % 2 else (ratios[middle - 1] + ratios[middle]) / 2.0
