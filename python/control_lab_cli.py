

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request


def request_json(base_url: str, path: str, method: str = "GET", payload=None):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"MES-BOT app is unavailable: {exc.reason}") from exc


def parse_assignment(text: str) -> tuple[str, int | float]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("expected KEY=NUMBER")
    key, raw = text.split("=", 1)
    key = key.strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid numeric value in {text!r}") from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise argparse.ArgumentTypeError(f"control value must be numeric in {text!r}")
    return key, value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:7000",
        help="running MES-BOT web service (default: %(default)s)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("profile", help="show persisted controller profile")
    commands.add_parser("state", help="show live MCU controller state")

    set_parser = commands.add_parser("set", help="apply and persist verified values")
    set_parser.add_argument("assignment", nargs="+", type=parse_assignment)
    set_parser.add_argument("--calibrated", action="store_true")
    set_parser.add_argument("--notes")

    distance = commands.add_parser(
        "calibrate-distance", help="apply one measured distance correction"
    )
    distance.add_argument("--actual-mm", type=float, required=True)
    distance.add_argument("--commanded-mm", type=float, default=200.0)
    distance.add_argument("--wheel", choices=("both", "left", "right"), default="both")

    speed_test = commands.add_parser(
        "speed-test", help="run isolated inner wheel-speed loops (bench/HIL only)"
    )
    speed_test.add_argument("--left-tps", type=float, required=True)
    speed_test.add_argument("--right-tps", type=float, required=True)
    speed_test.add_argument("--duration-ms", type=int, required=True)
    speed_test.add_argument(
        "--confirm-safe-test", action="store_true", required=True,
        help="confirm robot is lifted/secured as appropriate and STOP is available",
    )

    capture = commands.add_parser(
        "capture", help="capture low-rate control telemetry as JSON Lines"
    )
    capture.add_argument("--seconds", type=float, required=True)
    capture.add_argument("--period", type=float, default=0.2)
    capture.add_argument("--output", type=pathlib.Path, required=True)
    return parser


def run_capture(base_url: str, seconds: float, period: float, output: pathlib.Path):
    if seconds <= 0:
        raise ValueError("seconds must be greater than zero")
    if period < 0.15:
        raise ValueError("period must be at least 0.15 s to avoid overloading Router Bridge")
    output.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + seconds
    samples = 0
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        while time.monotonic() < deadline:
            cycle_start = time.monotonic()
            state = request_json(base_url, "/robot_state")
            record = {
                "captured_at": datetime.now(UTC).isoformat(),
                "sample": samples,
                "telemetry": state,
            }
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")
            stream.flush()
            samples += 1
            time.sleep(max(0.0, period - (time.monotonic() - cycle_start)))
    return {"ok": True, "samples": samples, "output": str(output.resolve())}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "profile":
        result = request_json(args.base_url, "/robot_control_profile")
    elif args.command == "state":
        result = request_json(args.base_url, "/robot_state")
    elif args.command == "set":
        result = request_json(
            args.base_url,
            "/robot_control_profile",
            "POST",
            {
                "values": dict(args.assignment),
                "source": "control_lab_cli",
                "calibrated": args.calibrated,
                "notes": args.notes,
            },
        )
    elif args.command == "calibrate-distance":
        result = request_json(
            args.base_url,
            "/robot_calibrate_distance",
            "POST",
            {
                "actual_mm": args.actual_mm,
                "commanded_mm": args.commanded_mm,
                "wheel": args.wheel,
            },
        )
    elif args.command == "speed-test":
        result = request_json(
            args.base_url,
            "/robot_speed_test",
            "POST",
            {
                "left_tps": args.left_tps,
                "right_tps": args.right_tps,
                "duration_ms": args.duration_ms,
                "confirm_safe_test": args.confirm_safe_test,
            },
        )
    else:
        result = run_capture(
            args.base_url, args.seconds, args.period, args.output
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as exc:
        print(f"control-lab error: {exc}", file=sys.stderr)
        raise SystemExit(2)
