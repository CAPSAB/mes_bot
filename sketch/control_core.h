#pragma once

#include <Arduino.h>
#include <math.h>









namespace MesBotControl {

inline float clampValue(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

inline int signOf(float value) {
  if (value > 0.0f) return 1;
  if (value < 0.0f) return -1;
  return 0;
}

struct WheelController {
  long target_ticks = 0;
  long last_ticks = 0;
  float target_speed_tps = 0.0f;
  float raw_speed_tps = 0.0f;
  float measured_speed_tps = 0.0f;
  float integral = 0.0f;
  float last_measurement_tps = 0.0f;
  float filtered_derivative = 0.0f;
  float ff_term = 0.0f;
  float p_term = 0.0f;
  float i_term = 0.0f;
  float d_term = 0.0f;
  float unsaturated_pwm = 0.0f;
  bool saturated = false;
  int pwm = 0;
};

struct WheelPidConfig {
  float kp;
  float ki;
  float kd;
  float kff;
  int pwm_min;
  int pwm_max;
  float integral_limit_pwm;
  float speed_filter_tau_s;
  float derivative_filter_tau_s;
  float feedforward_scale;
};




inline int updateWheelPid(
  WheelController &state,
  long current_ticks,
  float dt_s,
  const WheelPidConfig &cfg
) {
  if (dt_s <= 0.0001f) return state.pwm;

  long delta_ticks = current_ticks - state.last_ticks;
  state.last_ticks = current_ticks;
  state.raw_speed_tps = ((float)delta_ticks) / dt_s;

  float speed_alpha = dt_s / (cfg.speed_filter_tau_s + dt_s);
  speed_alpha = clampValue(speed_alpha, 0.0f, 1.0f);
  state.measured_speed_tps += speed_alpha *
    (state.raw_speed_tps - state.measured_speed_tps);

  float raw_derivative =
    (state.measured_speed_tps - state.last_measurement_tps) / dt_s;
  state.last_measurement_tps = state.measured_speed_tps;
  float derivative_alpha = dt_s / (cfg.derivative_filter_tau_s + dt_s);
  derivative_alpha = clampValue(derivative_alpha, 0.0f, 1.0f);
  state.filtered_derivative += derivative_alpha *
    (raw_derivative - state.filtered_derivative);

  if (fabsf(state.target_speed_tps) < 0.5f) {
    state.integral = 0.0f;
    state.ff_term = state.p_term = state.i_term = state.d_term = 0.0f;
    state.unsaturated_pwm = 0.0f;
    state.saturated = false;
    state.pwm = 0;
    return 0;
  }

  float error_tps = state.target_speed_tps - state.measured_speed_tps;
  
  
  
  
  state.ff_term = cfg.feedforward_scale * (
    (float)signOf(state.target_speed_tps) * (float)cfg.pwm_min +
    cfg.kff * state.target_speed_tps
  );
  state.p_term = cfg.kp * error_tps;
  state.d_term = -cfg.kd * state.filtered_derivative;

  float candidate_integral = state.integral + cfg.ki * error_tps * dt_s;
  candidate_integral = clampValue(
    candidate_integral,
    -cfg.integral_limit_pwm,
    cfg.integral_limit_pwm
  );
  float candidate_output = state.ff_term + state.p_term +
    candidate_integral + state.d_term;

  
  
  bool high_saturated = candidate_output > (float)cfg.pwm_max;
  bool low_saturated = candidate_output < (float)-cfg.pwm_max;
  bool drives_farther =
    (high_saturated && error_tps > 0.0f) ||
    (low_saturated && error_tps < 0.0f);
  if (!drives_farther) state.integral = candidate_integral;

  state.i_term = state.integral;
  state.unsaturated_pwm = state.ff_term + state.p_term +
    state.i_term + state.d_term;
  state.saturated = fabsf(state.unsaturated_pwm) > (float)cfg.pwm_max;
  state.pwm = (int)lroundf(clampValue(
    state.unsaturated_pwm,
    (float)-cfg.pwm_max,
    (float)cfg.pwm_max
  ));
  return state.pwm;
}

struct HeadingController {
  float integral_tps = 0.0f;
  float filtered_yaw_rate_dps = 0.0f;
  float p_term_tps = 0.0f;
  float i_term_tps = 0.0f;
  float d_term_tps = 0.0f;
  float correction_tps = 0.0f;
  bool saturated = false;
};

struct HeadingPidConfig {
  float kp_tps_per_deg;
  float ki_tps_per_deg_s;
  float kd_tps_per_dps;
  float max_correction_tps;
  float integral_limit_tps;
  float yaw_rate_filter_tau_s;
  float error_deadband_deg;
};

inline void resetHeadingController(HeadingController &state) {
  state = HeadingController();
}



inline float updateHeadingPid(
  HeadingController &state,
  float error_deg,
  float yaw_rate_dps,
  float dt_s,
  bool enabled,
  const HeadingPidConfig &cfg
) {
  if (!enabled || dt_s <= 0.0001f) {
    resetHeadingController(state);
    return 0.0f;
  }

  float active_error =
    fabsf(error_deg) <= cfg.error_deadband_deg ? 0.0f : error_deg;
  float rate_alpha = dt_s / (cfg.yaw_rate_filter_tau_s + dt_s);
  rate_alpha = clampValue(rate_alpha, 0.0f, 1.0f);
  state.filtered_yaw_rate_dps += rate_alpha *
    (yaw_rate_dps - state.filtered_yaw_rate_dps);

  state.p_term_tps = cfg.kp_tps_per_deg * active_error;
  state.d_term_tps = -cfg.kd_tps_per_dps * state.filtered_yaw_rate_dps;

  float candidate_integral = state.integral_tps +
    cfg.ki_tps_per_deg_s * active_error * dt_s;
  candidate_integral = clampValue(
    candidate_integral,
    -cfg.integral_limit_tps,
    cfg.integral_limit_tps
  );
  float candidate_output =
    state.p_term_tps + candidate_integral + state.d_term_tps;
  bool high_saturated = candidate_output > cfg.max_correction_tps;
  bool low_saturated = candidate_output < -cfg.max_correction_tps;
  bool drives_farther =
    (high_saturated && active_error > 0.0f) ||
    (low_saturated && active_error < 0.0f);
  if (!drives_farther) state.integral_tps = candidate_integral;

  state.i_term_tps = state.integral_tps;
  float output = state.p_term_tps + state.i_term_tps + state.d_term_tps;
  state.saturated = fabsf(output) > cfg.max_correction_tps;
  state.correction_tps = clampValue(
    output,
    -cfg.max_correction_tps,
    cfg.max_correction_tps
  );
  return state.correction_tps;
}

inline long distanceMmToTicks(
  float distance_mm,
  float linear_scale,
  float ticks_per_mm
) {
  return lroundf(distance_mm * linear_scale * ticks_per_mm);
}

inline float distanceSpeedTarget(
  long error_ticks,
  float kp_tps_per_tick,
  long deadband_ticks,
  float max_speed_tps,
  float min_speed_tps
) {
  long absolute_error = labs(error_ticks);
  if (absolute_error <= deadband_ticks || max_speed_tps <= 0.0f) return 0.0f;
  float target = kp_tps_per_tick * (float)error_ticks;
  target = clampValue(target, -max_speed_tps, max_speed_tps);
  float minimum = fminf(fabsf(min_speed_tps), max_speed_tps);
  if (fabsf(target) < minimum) target = (float)signOf(target) * minimum;
  return target;
}

struct WheelSpeedTargets {
  float left_tps;
  float right_tps;
};

struct TurnFusionResult {
  float progress_deg;
  float max_disagreement_deg;
  uint8_t selected_pair; 
};




inline TurnFusionResult robustTurnFusion(
  float rotation_deg,
  float gyro_deg,
  float encoder_deg
) {
  float rotation_gyro_delta = fabsf(rotation_deg - gyro_deg);
  float rotation_encoder_delta = fabsf(rotation_deg - encoder_deg);
  float gyro_encoder_delta = fabsf(gyro_deg - encoder_deg);

  TurnFusionResult result;
  result.max_disagreement_deg = fmaxf(
    rotation_gyro_delta,
    fmaxf(rotation_encoder_delta, gyro_encoder_delta)
  );

  if (
    rotation_gyro_delta <= rotation_encoder_delta &&
    rotation_gyro_delta <= gyro_encoder_delta
  ) {
    result.progress_deg = 0.5f * (rotation_deg + gyro_deg);
    result.selected_pair = 0;
  } else if (rotation_encoder_delta <= gyro_encoder_delta) {
    result.progress_deg = 0.5f * (rotation_deg + encoder_deg);
    result.selected_pair = 1;
  } else {
    result.progress_deg = 0.5f * (gyro_deg + encoder_deg);
    result.selected_pair = 2;
  }
  return result;
}





inline WheelSpeedTargets balanceTurnTargets(
  WheelSpeedTargets base,
  int requested_direction_sign,
  float directed_left_progress_mm,
  float directed_right_progress_mm,
  float center_speed_mm_s,
  float left_ticks_per_mm,
  float right_ticks_per_mm,
  float kp_tps_per_mm,
  float center_speed_kp_tps_per_mm_s,
  float max_balance_tps,
  float max_wheel_speed_tps
) {
  if (left_ticks_per_mm <= 0.0f || right_ticks_per_mm <= 0.0f) return base;

  float progress_error_mm =
    directed_left_progress_mm - directed_right_progress_mm;
  float nominal_ticks_per_mm =
    0.5f * (left_ticks_per_mm + right_ticks_per_mm);
  float common_nominal_tps =
    (float)requested_direction_sign * kp_tps_per_mm * progress_error_mm -
    center_speed_kp_tps_per_mm_s * center_speed_mm_s;

  
  
  float left_base_mm_s = fabsf(base.left_tps / left_ticks_per_mm);
  float right_base_mm_s = fabsf(base.right_tps / right_ticks_per_mm);
  float safe_common_mm_s = 0.75f * fminf(left_base_mm_s, right_base_mm_s);
  float configured_common_mm_s =
    fabsf(max_balance_tps) / nominal_ticks_per_mm;
  float common_mm_s = common_nominal_tps / nominal_ticks_per_mm;
  float safe_limit_mm_s = fminf(configured_common_mm_s, safe_common_mm_s);
  common_mm_s = clampValue(common_mm_s, -safe_limit_mm_s, safe_limit_mm_s);

  WheelSpeedTargets result = {
    base.left_tps + common_mm_s * left_ticks_per_mm,
    base.right_tps + common_mm_s * right_ticks_per_mm
  };

  
  
  float peak_tps = fmaxf(fabsf(result.left_tps), fabsf(result.right_tps));
  if (peak_tps > max_wheel_speed_tps && peak_tps > 0.0f) {
    float scale = max_wheel_speed_tps / peak_tps;
    result.left_tps *= scale;
    result.right_tps *= scale;
  }
  return result;
}





inline WheelSpeedTargets normalizeTurnTargetsForWheelGeometry(
  WheelSpeedTargets nominal,
  float left_ticks_per_mm,
  float right_ticks_per_mm,
  float max_wheel_speed_tps
) {
  if (left_ticks_per_mm <= 0.0f || right_ticks_per_mm <= 0.0f) return nominal;
  float nominal_ticks_per_mm =
    0.5f * (left_ticks_per_mm + right_ticks_per_mm);
  WheelSpeedTargets result = {
    nominal.left_tps * left_ticks_per_mm / nominal_ticks_per_mm,
    nominal.right_tps * right_ticks_per_mm / nominal_ticks_per_mm
  };
  float peak_tps = fmaxf(fabsf(result.left_tps), fabsf(result.right_tps));
  if (peak_tps > max_wheel_speed_tps && peak_tps > 0.0f) {
    float scale = max_wheel_speed_tps / peak_tps;
    result.left_tps *= scale;
    result.right_tps *= scale;
  }
  return result;
}

struct StraightCascadeInput {
  long left_error_ticks;
  long right_error_ticks;
  float local_max_speed_tps;
  float local_min_speed_tps;
  float heading_gate;
  bool heading_valid;
  float yaw_error_deg;
  float yaw_rate_dps;
  float dt_s;
};

struct StraightCascadeConfig {
  float kp_distance_tps_per_tick;
  long distance_deadband_ticks;
  HeadingPidConfig heading_pid;
  int correction_sign;
};





inline WheelSpeedTargets straightCascadeTargets(
  const StraightCascadeInput &input,
  const StraightCascadeConfig &cfg,
  HeadingController &heading_state
) {
  float left_base = distanceSpeedTarget(
    input.left_error_ticks,
    cfg.kp_distance_tps_per_tick,
    cfg.distance_deadband_ticks,
    input.local_max_speed_tps,
    input.local_min_speed_tps
  );
  float right_base = distanceSpeedTarget(
    input.right_error_ticks,
    cfg.kp_distance_tps_per_tick,
    cfg.distance_deadband_ticks,
    input.local_max_speed_tps,
    input.local_min_speed_tps
  );
  float correction = updateHeadingPid(
    heading_state,
    input.yaw_error_deg,
    input.yaw_rate_dps,
    input.dt_s,
    input.heading_valid,
    cfg.heading_pid
  );
  correction *= input.heading_gate * (float)cfg.correction_sign;

  
  
  
  float non_reversing_limit = 0.45f * fminf(
    fabsf(left_base), fabsf(right_base)
  );
  correction = clampValue(
    correction, -non_reversing_limit, non_reversing_limit
  );

  WheelSpeedTargets result = {
    left_base - correction,
    right_base + correction
  };
  result.left_tps = clampValue(
    result.left_tps, -input.local_max_speed_tps, input.local_max_speed_tps
  );
  result.right_tps = clampValue(
    result.right_tps, -input.local_max_speed_tps, input.local_max_speed_tps
  );
  return result;
}

inline bool straightPositionComplete(
  long left_error_ticks,
  long right_error_ticks,
  long tolerance_ticks
) {
  return labs(left_error_ticks) <= tolerance_ticks &&
    labs(right_error_ticks) <= tolerance_ticks;
}




inline WheelSpeedTargets turnCascadeTargets(
  float yaw_error_deg,
  float yaw_rate_dps,
  float dt_s,
  float min_turn_speed_tps,
  float max_turn_speed_tps,
  int control_sign,
  const HeadingPidConfig &cfg,
  HeadingController &turn_state
) {
  float turn_tps = updateHeadingPid(
    turn_state,
    yaw_error_deg,
    yaw_rate_dps,
    dt_s,
    true,
    cfg
  ) * (float)control_sign;

  int requested_sign = signOf(yaw_error_deg * (float)control_sign);
  if (requested_sign != 0 && fabsf(turn_tps) < min_turn_speed_tps) {
    turn_tps = (float)requested_sign * min_turn_speed_tps;
  }
  turn_tps = clampValue(turn_tps, -max_turn_speed_tps, max_turn_speed_tps);

  WheelSpeedTargets result = {-turn_tps, turn_tps};
  return result;
}

inline bool updateTurnSettling(
  bool inside_tolerance,
  bool yaw_rate_valid,
  float yaw_rate_dps,
  float rate_tolerance_dps,
  int required_samples,
  int &settle_counter
) {
  bool rate_stopped = yaw_rate_valid && fabsf(yaw_rate_dps) <= rate_tolerance_dps;
  if (inside_tolerance) {
    settle_counter += rate_stopped ? 2 : 1;
  } else {
    settle_counter = 0;
  }
  return settle_counter >= required_samples;
}

}  
