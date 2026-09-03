#include "heart_frames.h"
#include <Arduino_LED_Matrix.h>
#include <vector>


Arduino_LED_Matrix matrix;


static const int MAX_FRAMES = 50;
static uint32_t animation_buf[MAX_FRAMES][5];
static int animation_frame_count = 0;
static bool animation_running = false;
static int  animation_current_frame = 0;
static unsigned long animation_next_time = 0;


struct PinEntry { const char *name; uint8_t pin; };
static const PinEntry kPins[] = {
    {"D21",LED_BUILTIN},{"D20",D20},{"D13",D13},{"D12",D12},
    {"D11",D11},{"D10",D10},{"D9",D9},{"D8",D8},
    {"D7",D7},{"D6",D6},{"D5",D5},{"D4",D4},
    {"D3",D3},{"D2",D2},{"D1",D1},{"D0",D0},
    {"A0",A0},{"A1",A1},{"A2",A2},{"A3",A3},{"A4",A4},{"A5",A5},
    {"LED3_R",LED_BUILTIN},{"LED3_G",LED_BUILTIN+1},{"LED3_B",LED_BUILTIN+2},
    {"LED4_R",LED_BUILTIN+3},{"LED4_G",LED_BUILTIN+4},{"LED4_B",LED_BUILTIN+5},
};

static int findIndex(const char *n) {
  for (size_t i = 0; i < sizeof(kPins)/sizeof(kPins[0]); i++)
    if (strcmp(kPins[i].name, n) == 0) return (int)i;
  return -1;
}

static bool isRobotReservedPinName(const char *n) {
  return strcmp(n, "D2") == 0 || strcmp(n, "D3") == 0 ||
         strcmp(n, "D4") == 0 || strcmp(n, "D5") == 0 ||
         strcmp(n, "D6") == 0 || strcmp(n, "D7") == 0 ||
         strcmp(n, "D8") == 0 || strcmp(n, "D9") == 0 ||
         strcmp(n, "D10") == 0 || strcmp(n, "D11") == 0;
}

void set_pin_by_name(String name, bool s) {
  if (isRobotReservedPinName(name.c_str())) return;
  int i = findIndex(name.c_str());
  if (i >= 0) digitalWrite(kPins[i].pin, s ? HIGH : LOW);
}

void draw(std::vector<uint8_t> frame) {
  if (!frame.empty()) matrix.draw(frame.data());
}

void load_frame(std::array<uint32_t,5> b) {
  if (animation_frame_count >= MAX_FRAMES) return;
  for (int i=0;i<5;i++) animation_buf[animation_frame_count][i] = b[i];
  animation_frame_count++;
}

void play_animation() {
  animation_current_frame = 0; animation_running = true; animation_next_time = millis();
}

void stop_animation() {
  animation_running = false; animation_frame_count = 0;
}


uint32_t reverse_bits(uint32_t x) {
  x = ((x >> 1) & 0x55555555) | ((x & 0x55555555) << 1);
  x = ((x >> 2) & 0x33333333) | ((x & 0x33333333) << 2);
  x = ((x >> 4) & 0x0F0F0F0F) | ((x & 0x0F0F0F0F) << 4);
  x = ((x >> 8) & 0x00FF00FF) | ((x & 0x00FF00FF) << 8);
  x = (x >> 16) | (x << 16);
  return x;
}

void matrixWrite(uint32_t frame[4]) {
  matrix.loadFrame(frame);
}

void animation_tick() {
  if (!animation_running || animation_frame_count == 0) return;
  unsigned long now = millis();
  if (now < animation_next_time) return;
  uint32_t frame[4];
  frame[0] = reverse_bits(animation_buf[animation_current_frame][0]);
  frame[1] = reverse_bits(animation_buf[animation_current_frame][1]);
  frame[2] = reverse_bits(animation_buf[animation_current_frame][2]);
  frame[3] = reverse_bits(animation_buf[animation_current_frame][3]);
  matrixWrite(frame);
  Bridge.notify("animation_progress", animation_current_frame);
  uint32_t interval = animation_buf[animation_current_frame][4];
  if (interval == 0) interval = 1;
  animation_next_time = now + interval;
  animation_current_frame++;
  if (animation_current_frame >= animation_frame_count) {
    animation_running = false; animation_frame_count = 0; animation_current_frame = 0;
  }
}

void wake_up() {
  matrix.loadSequence(HeartAnim); matrix.playSequence(); delay(1000); matrix.loadFrame(HeartStatic);
}

#include <Arduino.h>
#include <Wire.h>
#include <Arduino_RouterBridge.h>
#include <Adafruit_INA219.h>
#include <SparkFun_BNO080_Arduino_Library.h>
#include <math.h>
#include "control_core.h"


void stopMotorsRaw();
void updateIMU();
void updateBattery();
long readLeftTicks();
long readRightTicks();
void resetControllersKeepingTargets();
void clearCounters();
void clearMacro();





const int LEFT_EN  = 5;
const int LEFT_IN1 = 8;
const int LEFT_IN2 = 9;

const int RIGHT_EN  = 6;
const int RIGHT_IN1 = 10;
const int RIGHT_IN2 = 11;





const int LEFT_ENC_A  = 2;
const int LEFT_ENC_B  = 3;

const int RIGHT_ENC_A = 4;
const int RIGHT_ENC_B = 7;





const float DRIVE_WHEEL_DIAMETER_MM = 55.0f;
const float WHEEL_RADIUS_MM = DRIVE_WHEEL_DIAMETER_MM * 0.5f;
const float WHEEL_CIRCUMFERENCE_MM = PI * DRIVE_WHEEL_DIAMETER_MM;




const float LEFT_TICKS_PER_REV  = 6565.0f;
const float RIGHT_TICKS_PER_REV = 6565.0f;




const float AXLE_CENTER_DISTANCE_MM = 108.0f;
const float TRACK_CLEAR_GAP_MM = 88.0f;
const float TRACK_BELT_WIDTH_MM = 44.0f;
const float TRACK_WIDTH_MM = TRACK_CLEAR_GAP_MM + TRACK_BELT_WIDTH_MM;
const float ENCODER_TURN_SCALE = 1.000f;


















float LEFT_TICKS_PER_MM  = LEFT_TICKS_PER_REV  / WHEEL_CIRCUMFERENCE_MM; 
float RIGHT_TICKS_PER_MM = RIGHT_TICKS_PER_REV / WHEEL_CIRCUMFERENCE_MM; 





float CELL_DISTANCE_MM = 200.0f;

float LEFT_LINEAR_SCALE  = 1.000f;
float RIGHT_LINEAR_SCALE = 1.000f;



float FORWARD_DISTANCE_TICK_SCALE = 1.035197f;
float BACKWARD_DISTANCE_TICK_SCALE = 1.035197f;



float TURN_LEFT_DEG_SCALE  = 1.000000f;
float TURN_RIGHT_DEG_SCALE = 1.000000f;






const int LEFT_MOTOR_SIGN  = -1;
const int RIGHT_MOTOR_SIGN = 1;

const int LEFT_ENCODER_SIGN  = -1;
const int RIGHT_ENCODER_SIGN = 1;

int IMU_YAW_SIGN = 1;
int TURN_CONTROL_SIGN = 1;
int YAW_CORRECTION_SIGN = 1;








const unsigned long CONTROL_PERIOD_MS = 20;
const unsigned long BATTERY_PERIOD_MS = 200;
const unsigned long MOTION_TIMEOUT_MS = 55000;
const unsigned long MACRO_STEP_PAUSE_MS = 250;

const unsigned long HEADING_CAPTURE_MS = 260;
const unsigned long HEADING_CAPTURE_SAMPLE_DELAY_MS = 5;





int ABSOLUTE_PWM_MIN = 90;

int LEFT_PWM_MIN  = 140;
int RIGHT_PWM_MIN = 150;

int LEFT_PWM_MAX  = 225;
int RIGHT_PWM_MAX = 235;

float LEFT_KP_SPEED  = 0.120f;
float LEFT_KI_SPEED  = 0.035f;
float LEFT_KD_SPEED  = 0.000f;
float LEFT_KFF_SPEED = 0.052f;

float RIGHT_KP_SPEED  = 0.155f;
float RIGHT_KI_SPEED  = 0.045f;
float RIGHT_KD_SPEED  = 0.000f;
float RIGHT_KFF_SPEED = 0.068f;





float KP_DISTANCE = 0.95f;



float KP_YAW_STRAIGHT = 50.0f;


float KI_YAW_STRAIGHT = 3.0f;
float KD_YAW_STRAIGHT = 5.0f;
float MAX_YAW_CORRECTION_TPS = 200.0f;
float YAW_INTEGRAL_LIMIT_TPS = 80.0f;
float YAW_RATE_FILTER_TAU_S = 0.040f;

float KP_TURN_YAW = 14.00f;
float KI_TURN_YAW = 0.0f;
float KD_TURN_YAW = 1.10f;
float TURN_BALANCE_KP_TPS_PER_MM = 12.0f;
float TURN_CENTER_SPEED_KP_TPS_PER_MM_S = 20.0f;
float MAX_TURN_BALANCE_TPS = 100.0f;

float MAX_STRAIGHT_SPEED_TPS_BASE = 1500.0f;
float MAX_TURN_SPEED_TPS_BASE = 1900.0f;

float MIN_STRAIGHT_SPEED_TPS = 400.0f;
float MIN_TURN_SPEED_TPS = 500.0f;

float ENDPOINT_MIN_STRAIGHT_SPEED_TPS = 400.0f;
float ENDPOINT_MIN_TURN_SPEED_TPS = 500.0f;


float INTEGRAL_LIMIT = 140.0f;
float SPEED_FILTER_TAU_S = 0.060f;
float DERIVATIVE_FILTER_TAU_S = 0.080f;
float TURN_STOP_RATE_TOLERANCE_DPS = 3.0f;
int TURN_SETTLE_COUNT_REQUIRED = 6;
float STRAIGHT_FINAL_YAW_TOLERANCE_DEG = 0.50f;
float STRAIGHT_FINAL_MIN_CORRECTION_TPS = 60.0f;
int STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED = 8;








long POSITION_TOLERANCE_TICKS = 10;
long POSITION_COMMAND_DEADBAND_TICKS = 10;
long BIAS_DISABLE_REMAINING_TICKS = 650;

float SPEED_STOP_TOLERANCE_TPS = 80.0f;

float TURN_TOLERANCE_DEG = 1.0f;
long TURN_ENCODER_TOLERANCE_TICKS = 180;

float YAW_IGNORE_DEG = 0.15f;




float NOMINAL_MOTOR_VOLTAGE = 14.8f;





float RIGHT_STRAIGHT_BIAS_TPS = 0.0f;
float LEFT_STRAIGHT_SOFTEN_TPS = 0.0f;

float RIGHT_TRACK_SLIP_BOOST_TPS = 0.0f;
float MAX_RIGHT_SLIP_BOOST_TPS = 0.0f;





float PROGRESS_BALANCE_GAIN_TPS = 0.0f;
float MAX_PROGRESS_BALANCE_TPS = 0.0f;
float PROGRESS_BALANCE_YAW_GATE_DEG = 4.0f;

float PROGRESS_SLIP_THRESHOLD = 0.55f;

float STRAIGHT_YAW_SLIP_THRESHOLD_DEG = 42.0f;
float STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS = 125.0f;
int SLIP_COUNT_LIMIT = 20;







int STALL_PWM_THRESHOLD = 120;
float STALL_TARGET_SPEED_TPS = 260.0f;
float STALL_MEASURED_SPEED_TPS = 70.0f;
int STALL_COUNT_LIMIT = 8;

int MAX_RECOVERY_ATTEMPTS_PER_MOTION = 0;

unsigned long RECOVERY_STOP_MS = 180;
unsigned long RECOVERY_PULSE_MS = 170;
unsigned long RECOVERY_SETTLE_MS = 180;

int RECOVERY_PWM_LEFT = 180;
int RECOVERY_PWM_RIGHT = 180;

float RECOVERY_DERATE_FACTOR = 0.84f;
float MIN_SPEED_DERATE = 0.55f;





float TURN_WRONG_WAY_DEG = 8.0f;
int TURN_WRONG_WAY_COUNT_LIMIT = 16;

float MAX_VALID_YAW_RATE_DPS = 300.0f;
float MAX_VALID_TURN_DELTA_DEG_PER_SAMPLE = 45.0f;
float MAX_VALID_HEADING_JUMP_DEG = 35.0f;





Adafruit_INA219 ina219(0x40);
BNO080 bno080;




TwoWire *bno_wire = &Wire1;
uint8_t bno_i2c_address = 0x4A;
const unsigned long BNO_I2C_BYTE_WAIT_US = 1800;
const unsigned long BNO_UPDATE_BUDGET_US = 3500;
const unsigned long BNO_MIN_POLL_INTERVAL_US = 3000;
unsigned long last_bno_poll_us = 0;
unsigned long bno_empty_polls = 0;
unsigned long bno_short_reads = 0;
unsigned long bno_budget_hits = 0;

bool ina_ok = false;
bool bno_ok = false;

float battery_bus_v = 0.0f;
float battery_source_v = 0.0f;
float battery_current_ma = 0.0f;
float battery_power_mw = 0.0f;
float battery_percent_est = 0.0f;

float raw_imu_yaw_deg = 0.0f;
float robot_heading_deg = 0.0f;

float yaw_rate_deg_s = 0.0f;
bool yaw_rate_valid = false;
bool yaw_valid = false;

const unsigned long IMU_CONTROL_STALE_MS = 120;
unsigned long last_rotation_ms = 0;
unsigned long last_gyro_ms = 0;
unsigned long last_linear_accel_ms = 0;
unsigned long last_gravity_ms = 0;
uint8_t imu_rotation_accuracy = 0;
float imu_heading_accuracy_rad = 0.0f;

float last_imu_heading_for_rate_deg = 0.0f;
unsigned long last_imu_sample_ms = 0;
bool have_last_imu_rate_sample = false;

float imu_ax = 0.0f;
float imu_ay = 0.0f;
float imu_az = 0.0f;

float imu_gx = 0.0f;
float imu_gy = 0.0f;
float imu_gz = 0.0f;

float imu_gravity_x = 0.0f;
float imu_gravity_y = 0.0f;
float imu_gravity_z = 0.0f;

float imu_mx = 0.0f;
float imu_my = 0.0f;
float imu_mz = 0.0f;

unsigned long bno_samples = 0;
unsigned long rejected_yaw_rate_samples = 0;
unsigned long rejected_heading_jump_samples = 0;
unsigned long rejected_quaternion_samples = 0;

unsigned long last_battery_ms = 0;

static unsigned long _mpu_last_ms = 0;
static unsigned long _ina_last_ms = 0;
#define MPU_INTERVAL_MS     500
#define INA_INTERVAL_MS     2000

void sensor_tick() {
  unsigned long now = millis();
  
  if (bno_ok && (now - _mpu_last_ms >= MPU_INTERVAL_MS)) {
    _mpu_last_ms = now;
    std::vector<float> mpu_v = {imu_ax, imu_ay, imu_az, imu_gx, imu_gy, imu_gz};
    Bridge.notify("mpu6050_data", mpu_v);
  }

  if (ina_ok && (now - _ina_last_ms >= INA_INTERVAL_MS)) {
    _ina_last_ms = now;
    std::vector<float> ina_v = {battery_bus_v, 0.0f, battery_current_ma, battery_power_mw, battery_source_v};
    Bridge.notify("ina219_data", ina_v);
  }
}





volatile long left_ticks = 0;
volatile long right_ticks = 0;

volatile uint8_t left_last_state = 0;
volatile uint8_t right_last_state = 0;





enum MotionMode {
  MODE_IDLE,
  MODE_STRAIGHT,
  MODE_TURN_IMU,
  MODE_TURN_ENCODER,
  MODE_SPEED_TEST,
  MODE_RECOVERY,
  MODE_FAULT
};

enum MacroMode {
  MACRO_NONE,
  MACRO_MOVE_LEFT,
  MACRO_MOVE_RIGHT
};

enum PrimitiveHeadingResult {
  HEADING_RESULT_NONE,
  HEADING_RESULT_RUNNING,
  HEADING_RESULT_COMPLETED,
  HEADING_RESULT_STOPPED
};

MotionMode mode = MODE_IDLE;
MotionMode resume_mode_after_recovery = MODE_IDLE;

MacroMode macro_mode = MACRO_NONE;
int macro_step = 0;
unsigned long macro_next_step_ms = 0;

MesBotControl::WheelController left_ctrl;
MesBotControl::WheelController right_ctrl;
MesBotControl::HeadingController straight_heading_ctrl;
MesBotControl::HeadingController turn_heading_ctrl;




float pose_x_mm = 0.0f;
float pose_y_mm = 0.0f;
float pose_distance_mm = 0.0f;
float pose_heading_origin_deg = 0.0f;
float pose_last_heading_deg = 0.0f;
long pose_last_left_ticks = 0;
long pose_last_right_ticks = 0;




float straight_start_pose_x_mm = 0.0f;
float straight_start_pose_y_mm = 0.0f;
float straight_path_heading_deg = 0.0f;
float straight_cross_track_error_mm = 0.0f;
float straight_path_heading_offset_deg = 0.0f;
float STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM = 0.35f;
float STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG = 10.0f;

float target_yaw_deg = 0.0f;
float last_yaw_error_deg = 0.0f;



float step_start_yaw_deg = 0.0f;
float step_end_yaw_deg = 0.0f;
float step_requested_yaw_delta_deg = 0.0f;
float step_actual_yaw_delta_deg = 0.0f;
float step_final_yaw_error_deg = 0.0f;
bool step_end_heading_stable = false;
PrimitiveHeadingResult step_heading_result = HEADING_RESULT_NONE;
float step_requested_distance_mm = 0.0f;
float step_left_distance_mm = 0.0f;
float step_right_distance_mm = 0.0f;
float step_actual_distance_mm = 0.0f;
float step_distance_error_mm = 0.0f;
long step_encoder_start_left_ticks = 0;
long step_encoder_start_right_ticks = 0;




bool motion_result_notify_pending = false;
int motion_result_notify_code = 0;  

float turn_start_heading_deg = 0.0f;
float turn_requested_delta_deg = 0.0f;
float turn_abs_target_deg = 0.0f;
int turn_direction_sign = 1;
int turn_wrong_way_counter = 0;
int turn_settle_counter = 0;
int straight_final_settle_counter = 0;
bool straight_endpoint_aligning = false;

float turn_unwrapped_progress_deg = 0.0f;
float turn_last_heading_deg = 0.0f;
bool turn_accumulator_valid = false;
unsigned long rejected_turn_delta_samples = 0;




float turn_gyro_progress_deg = 0.0f;
float turn_encoder_progress_deg = 0.0f;
float turn_fused_progress_deg = 0.0f;
float turn_sensor_disagreement_deg = 0.0f;
float turn_balance_error_mm = 0.0f;
float turn_center_translation_mm = 0.0f;
float turn_center_speed_mm_s = 0.0f;
float turn_balance_correction_tps = 0.0f;
uint8_t turn_fusion_selected_pair = 0;

unsigned long last_control_ms = 0;
unsigned long motion_start_ms = 0;
float last_control_dt_ms = 0.0f;
float max_control_dt_ms = 0.0f;
unsigned long control_deadline_misses = 0;
unsigned long speed_test_end_ms = 0;
float speed_test_left_tps = 0.0f;
float speed_test_right_tps = 0.0f;

long motion_start_left_ticks = 0;
long motion_start_right_ticks = 0;
long motion_left_delta_ticks = 0;
long motion_right_delta_ticks = 0;

float speed_derate = 1.0f;

int left_stall_counter = 0;
int right_stall_counter = 0;
int slip_counter = 0;

int recovery_attempts_this_motion = 0;
int recovery_side = -1;
int recovery_phase = 0;
unsigned long recovery_phase_start_ms = 0;
int recovery_left_corrected_pwm = 0;
int recovery_right_corrected_pwm = 0;

unsigned long tune_version = 0;
String fault_reason = "";





int signInt(float x) {
  if (x > 0.0f) return 1;
  if (x < 0.0f) return -1;
  return 0;
}

float clampFloat(float x, float low, float high) {
  if (x < low) return low;
  if (x > high) return high;
  return x;
}

long clampLong(long x, long low, long high) {
  if (x < low) return low;
  if (x > high) return high;
  return x;
}

int clampInt(int x, int low, int high) {
  if (x < low) return low;
  if (x > high) return high;
  return x;
}

unsigned long clampUnsignedLong(unsigned long x, unsigned long low, unsigned long high) {
  if (x < low) return low;
  if (x > high) return high;
  return x;
}

float wrapAngleDeg(float angle) {
  while (angle > 180.0f) angle -= 360.0f;
  while (angle < -180.0f) angle += 360.0f;
  return angle;
}

float yawErrorDeg(float target, float current) {
  return wrapAngleDeg(target - current);
}

float quaternionToYawDeg(float w, float x, float y, float z) {
  float siny_cosp = 2.0f * (w * z + x * y);
  float cosy_cosp = 1.0f - 2.0f * (y * y + z * z);
  float yaw_rad = atan2f(siny_cosp, cosy_cosp);
  return yaw_rad * 180.0f / PI;
}

long maxLongAbs(long a, long b) {
  long aa = labs(a);
  long bb = labs(b);
  return aa > bb ? aa : bb;
}

float finishGateFromRemaining(long max_remaining_ticks) {
  if (max_remaining_ticks <= BIAS_DISABLE_REMAINING_TICKS) {
    return 0.0f;
  }

  float gate = ((float)(max_remaining_ticks - BIAS_DISABLE_REMAINING_TICKS)) / 1800.0f;
  return clampFloat(gate, 0.0f, 1.0f);
}

float headingGateFromRemaining(long max_remaining_ticks) {
  
  
  return max_remaining_ticks > POSITION_COMMAND_DEADBAND_TICKS ? 1.0f : 0.0f;
}

float endpointLimitedMaxStraightSpeed(float base_max_speed, long max_remaining_ticks) {
  
  
  const long ramp_ticks = 700;
  if (max_remaining_ticks >= ramp_ticks) {
    return base_max_speed;
  }

  if (max_remaining_ticks <= POSITION_COMMAND_DEADBAND_TICKS) {
    return 0.0f;
  }

  float low_speed = ENDPOINT_MIN_STRAIGHT_SPEED_TPS;
  float span = (float)(ramp_ticks - POSITION_COMMAND_DEADBAND_TICKS);
  float factor = (float)(max_remaining_ticks - POSITION_COMMAND_DEADBAND_TICKS) / span;
  factor = clampFloat(factor, 0.0f, 1.0f);

  return low_speed + factor * (base_max_speed - low_speed);
}

float endpointLimitedMinStraightSpeed(long max_remaining_ticks) {
  return max_remaining_ticks < 700
    ? ENDPOINT_MIN_STRAIGHT_SPEED_TPS
    : MIN_STRAIGHT_SPEED_TPS;
}

float endpointLimitedMinTurnSpeed(float remaining_deg) {
  if (remaining_deg < 18.0f) {
    return ENDPOINT_MIN_TURN_SPEED_TPS;
  }
  return MIN_TURN_SPEED_TPS;
}

long ticksForLeftDistance(float distance_mm) {
  
  
  float direction_scale = distance_mm < 0.0f
    ? BACKWARD_DISTANCE_TICK_SCALE : FORWARD_DISTANCE_TICK_SCALE;
  return MesBotControl::distanceMmToTicks(
    distance_mm * direction_scale, LEFT_LINEAR_SCALE, LEFT_TICKS_PER_MM
  );
}

long ticksForRightDistance(float distance_mm) {
  
  float direction_scale = distance_mm < 0.0f
    ? BACKWARD_DISTANCE_TICK_SCALE : FORWARD_DISTANCE_TICK_SCALE;
  return MesBotControl::distanceMmToTicks(
    distance_mm * direction_scale, RIGHT_LINEAR_SCALE, RIGHT_TICKS_PER_MM
  );
}

float progressFraction(long current_ticks, long start_ticks, long delta_ticks) {
  if (delta_ticks == 0) {
    return 1.0f;
  }

  return ((float)(current_ticks - start_ticks)) / ((float)delta_ticks);
}

float estimateBatteryPercent4S(float source_v) {
  if (source_v < 5.0f) {
    return 0.0f;
  }

  float cell_v = source_v / 4.0f;
  float pct = (cell_v - 3.30f) * 100.0f / (4.20f - 3.30f);

  return clampFloat(pct, 0.0f, 100.0f);
}

float batterySpeedDerate() {
  if (!ina_ok || battery_source_v < 5.0f) {
    return 1.0f;
  }

  float cell_v = battery_source_v / 4.0f;

  if (cell_v < 3.30f) return 0.55f;
  if (cell_v < 3.45f) return 0.68f;
  if (cell_v < 3.60f) return 0.82f;

  return 1.0f;
}

float maxStraightSpeedNow() {
  return MAX_STRAIGHT_SPEED_TPS_BASE * speed_derate * batterySpeedDerate();
}

float maxTurnSpeedNow() {
  return MAX_TURN_SPEED_TPS_BASE * speed_derate * batterySpeedDerate();
}

float speedCommandFromError(long error_ticks, float max_speed_tps, float min_speed_tps) {
  return MesBotControl::distanceSpeedTarget(
    error_ticks,
    KP_DISTANCE,
    POSITION_COMMAND_DEADBAND_TICKS,
    max_speed_tps,
    min_speed_tps
  );
}





int findValueSeparator(String payload, int key_pos) {
  int colon = payload.indexOf(':', key_pos);
  int equals = payload.indexOf('=', key_pos);

  if (colon < 0) return equals;
  if (equals < 0) return colon;

  return colon < equals ? colon : equals;
}

bool extractNumber(String payload, const char *key, float &value_out) {
  String quoted = String("\"") + String(key) + String("\"");

  int key_pos = payload.indexOf(quoted);

  if (key_pos < 0) {
    
    
    
    String bare = String(key);
    int search_from = 0;
    while (true) {
      int candidate = payload.indexOf(bare, search_from);
      if (candidate < 0) break;
      int after = candidate + bare.length();
      bool before_ok = candidate == 0 || payload[candidate - 1] == ',' ||
        payload[candidate - 1] == '{' || payload[candidate - 1] == ' ' ||
        payload[candidate - 1] == '\n' || payload[candidate - 1] == '\t';
      bool after_ok = after >= payload.length() || payload[after] == ':' ||
        payload[after] == '=' || payload[after] == ' ' ||
        payload[after] == '\t';
      if (before_ok && after_ok) {
        key_pos = candidate;
        break;
      }
      search_from = candidate + bare.length();
    }
  }

  if (key_pos < 0) {
    return false;
  }

  int sep = findValueSeparator(payload, key_pos);

  if (sep < 0) {
    return false;
  }

  int start = sep + 1;

  while (
    start < payload.length() &&
    (
      payload[start] == ' ' ||
      payload[start] == '\t' ||
      payload[start] == '"' ||
      payload[start] == '\''
    )
  ) {
    start++;
  }

  String tail = payload.substring(start);
  value_out = tail.toFloat();

  return true;
}

int applyFloatValue(String payload, const char *key, float &target, float low, float high) {
  float value;

  if (!extractNumber(payload, key, value)) {
    return 0;
  }

  target = clampFloat(value, low, high);
  return 1;
}

int applyLongValue(String payload, const char *key, long &target, long low, long high) {
  float value;

  if (!extractNumber(payload, key, value)) {
    return 0;
  }

  target = clampLong((long)lroundf(value), low, high);
  return 1;
}

int applyIntValue(String payload, const char *key, int &target, int low, int high) {
  float value;

  if (!extractNumber(payload, key, value)) {
    return 0;
  }

  target = clampInt((int)lroundf(value), low, high);
  return 1;
}

int applyULongValue(String payload, const char *key, unsigned long &target, unsigned long low, unsigned long high) {
  float value;

  if (!extractNumber(payload, key, value)) {
    return 0;
  }

  target = clampUnsignedLong((unsigned long)lroundf(value), low, high);
  return 1;
}





int decodeQuadrature(uint8_t previous, uint8_t current) {
  uint8_t transition = (previous << 2) | current;

  switch (transition) {
    case 0b0001:
    case 0b0111:
    case 0b1110:
    case 0b1000:
      return +1;

    case 0b0010:
    case 0b1011:
    case 0b1101:
    case 0b0100:
      return -1;

    default:
      return 0;
  }
}

void leftEncoderISR() {
  uint8_t current = (digitalRead(LEFT_ENC_A) << 1) | digitalRead(LEFT_ENC_B);
  int delta = decodeQuadrature(left_last_state, current);
  left_ticks += delta * LEFT_ENCODER_SIGN;
  left_last_state = current;
}

void rightEncoderISR() {
  uint8_t current = (digitalRead(RIGHT_ENC_A) << 1) | digitalRead(RIGHT_ENC_B);
  int delta = decodeQuadrature(right_last_state, current);
  right_ticks += delta * RIGHT_ENCODER_SIGN;
  right_last_state = current;
}

long readLeftTicks() {
  noInterrupts();
  long value = left_ticks;
  interrupts();
  return value;
}

long readRightTicks() {
  noInterrupts();
  long value = right_ticks;
  interrupts();
  return value;
}

void resetEncoderCounts() {
  noInterrupts();
  left_ticks = 0;
  right_ticks = 0;
  interrupts();

  left_last_state = (digitalRead(LEFT_ENC_A) << 1) | digitalRead(LEFT_ENC_B);
  right_last_state = (digitalRead(RIGHT_ENC_A) << 1) | digitalRead(RIGHT_ENC_B);
}

void updatePlanarOdometry() {
  long left_now = readLeftTicks();
  long right_now = readRightTicks();
  long left_delta_ticks = left_now - pose_last_left_ticks;
  long right_delta_ticks = right_now - pose_last_right_ticks;
  pose_last_left_ticks = left_now;
  pose_last_right_ticks = right_now;

  float direction_scale = 1.0f;
  if (left_delta_ticks < 0 && right_delta_ticks < 0) {
    direction_scale = BACKWARD_DISTANCE_TICK_SCALE;
  } else if (left_delta_ticks > 0 && right_delta_ticks > 0) {
    direction_scale = FORWARD_DISTANCE_TICK_SCALE;
  }
  float left_mm = ((float)left_delta_ticks) /
    (LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE * direction_scale);
  float right_mm = ((float)right_delta_ticks) /
    (RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE * direction_scale);
  float center_mm = 0.5f * (left_mm + right_mm);

  float heading_deg = pose_last_heading_deg;
  if (yaw_valid) {
    heading_deg = wrapAngleDeg(robot_heading_deg - pose_heading_origin_deg);
  }
  
  
  
  float heading_delta_deg = wrapAngleDeg(heading_deg - pose_last_heading_deg);
  float midpoint_heading_deg = wrapAngleDeg(
    pose_last_heading_deg + 0.5f * heading_delta_deg
  );
  float heading_rad = midpoint_heading_deg * PI / 180.0f;
  pose_x_mm += center_mm * cosf(heading_rad);
  pose_y_mm += center_mm * sinf(heading_rad);
  pose_distance_mm += fabsf(center_mm);
  pose_last_heading_deg = heading_deg;
}

void resetPlanarOdometry(bool capture_heading) {
  pose_x_mm = 0.0f;
  pose_y_mm = 0.0f;
  pose_distance_mm = 0.0f;
  if (capture_heading && yaw_valid) {
    pose_heading_origin_deg = robot_heading_deg;
  }
  pose_last_heading_deg = yaw_valid
    ? wrapAngleDeg(robot_heading_deg - pose_heading_origin_deg)
    : 0.0f;
  pose_last_left_ticks = readLeftTicks();
  pose_last_right_ticks = readRightTicks();
}

void resetPrimitiveEncodersPreservingPose() {
  updatePlanarOdometry();
  resetEncoderCounts();
  pose_last_left_ticks = 0;
  pose_last_right_ticks = 0;
}





void configureBnoReports() {
  
  
  bno080.enableRotationVector(10);
  bno080.enableLinearAccelerometer(10);
  bno080.enableGyro(10);
  bno080.enableGravity(40);
}

bool waitForBnoBytes(uint16_t required, unsigned long timeout_us) {
  unsigned long started_us = micros();
  while ((uint16_t)bno_wire->available() < required) {
    if ((unsigned long)(micros() - started_us) >= timeout_us) {
      return false;
    }
    delayMicroseconds(40);
  }
  return true;
}

void discardBnoWireBytes() {
  while (bno_wire->available() > 0) {
    bno_wire->read();
  }
}






uint16_t getBnoReadingBounded() {
  bno_wire->requestFrom(bno_i2c_address, (size_t)4);
  if (!waitForBnoBytes(4, BNO_I2C_BYTE_WAIT_US)) {
    discardBnoWireBytes();
    bno_empty_polls++;
    return 0;
  }

  for (uint8_t i = 0; i < 4; i++) {
    bno080.shtpHeader[i] = (uint8_t)bno_wire->read();
  }

  uint16_t packet_length =
    ((uint16_t)bno080.shtpHeader[1] << 8) | bno080.shtpHeader[0];
  packet_length &= ~(1U << 15);
  if (packet_length < 4) {
    return 0;
  }

  uint16_t bytes_remaining = packet_length - 4;
  uint16_t data_spot = 0;
  while (bytes_remaining > 0) {
    uint16_t payload_count = bytes_remaining;
    if (payload_count > (I2C_BUFFER_LENGTH - 4)) {
      payload_count = I2C_BUFFER_LENGTH - 4;
    }

    uint16_t request_count = payload_count + 4;
    bno_wire->requestFrom(bno_i2c_address, (size_t)request_count);
    if (!waitForBnoBytes(request_count, BNO_I2C_BYTE_WAIT_US)) {
      discardBnoWireBytes();
      bno_short_reads++;
      return 0;
    }

    
    for (uint8_t i = 0; i < 4; i++) {
      bno_wire->read();
    }
    for (uint16_t i = 0; i < payload_count; i++) {
      uint8_t incoming = (uint8_t)bno_wire->read();
      if (data_spot < MAX_PACKET_SIZE) {
        bno080.shtpData[data_spot] = incoming;
      }
      data_spot++;
    }
    bytes_remaining -= payload_count;
  }

  if (
    bno080.shtpHeader[2] == CHANNEL_REPORTS &&
    bno080.shtpData[0] == SHTP_REPORT_BASE_TIMESTAMP
  ) {
    return bno080.parseInputReport();
  }
  if (bno080.shtpHeader[2] == CHANNEL_CONTROL) {
    return bno080.parseCommandReport();
  }
  if (bno080.shtpHeader[2] == CHANNEL_GYRO) {
    return bno080.parseInputReport();
  }
  return 0;
}

void updateIMU() {
  if (!bno_ok) return;

  unsigned long poll_now_us = micros();
  if (
    last_bno_poll_us != 0 &&
    (unsigned long)(poll_now_us - last_bno_poll_us) < BNO_MIN_POLL_INTERVAL_US
  ) {
    return;
  }
  last_bno_poll_us = poll_now_us;

  
  
  unsigned long update_started_us = micros();
  for (uint8_t packet = 0; packet < 12; packet++) {
    uint16_t report = getBnoReadingBounded();
    if (report == 0) break;

    unsigned long now = millis();
    bno_samples++;

    if (report == SENSOR_REPORTID_ROTATION_VECTOR) {
      float qi = bno080.getQuatI();
      float qj = bno080.getQuatJ();
      float qk = bno080.getQuatK();
      float qr = bno080.getQuatReal();
      float norm = sqrtf(qr * qr + qi * qi + qj * qj + qk * qk);

      if (norm > 0.25f && norm < 1.75f) {
        qr /= norm;
        qi /= norm;
        qj /= norm;
        qk /= norm;
        raw_imu_yaw_deg = quaternionToYawDeg(qr, qi, qj, qk);
        
        
        
        robot_heading_deg = wrapAngleDeg(
          (IMU_YAW_SIGN * raw_imu_yaw_deg) + 180.0f
        );
        imu_rotation_accuracy = bno080.getQuatAccuracy();
        imu_heading_accuracy_rad = bno080.getQuatRadianAccuracy();
        last_rotation_ms = now;
        yaw_valid = true;
      } else {
        rejected_quaternion_samples++;
      }
    } else if (report == SENSOR_REPORTID_LINEAR_ACCELERATION) {
      imu_ax = bno080.getLinAccelX();
      imu_ay = bno080.getLinAccelY();
      imu_az = bno080.getLinAccelZ();
      last_linear_accel_ms = now;
    } else if (report == SENSOR_REPORTID_GYROSCOPE) {
      imu_gx = bno080.getGyroX();
      imu_gy = bno080.getGyroY();
      imu_gz = bno080.getGyroZ();
      
      
      yaw_rate_deg_s =
        (float)IMU_YAW_SIGN * imu_gz * 57.2957795f;
      last_gyro_ms = now;
      yaw_rate_valid = true;
    } else if (report == SENSOR_REPORTID_GRAVITY) {
      imu_gravity_x = bno080.getGravityX();
      imu_gravity_y = bno080.getGravityY();
      imu_gravity_z = bno080.getGravityZ();
      last_gravity_ms = now;
    }

    if ((unsigned long)(micros() - update_started_us) >= BNO_UPDATE_BUDGET_US) {
      bno_budget_hits++;
      break;
    }
  }

  unsigned long now = millis();
  yaw_valid = last_rotation_ms != 0 &&
    now - last_rotation_ms <= IMU_CONTROL_STALE_MS;
  yaw_rate_valid = last_gyro_ms != 0 &&
    now - last_gyro_ms <= IMU_CONTROL_STALE_MS;
}

bool imuFreshForControl() {
  return bno_ok && yaw_valid && yaw_rate_valid;
}

void updateBattery() {
  if (!ina_ok) return;

  unsigned long now = millis();

  if (now - last_battery_ms < BATTERY_PERIOD_MS) {
    return;
  }

  last_battery_ms = now;

  float bus_v = ina219.getBusVoltage_V();
  float shunt_mv = ina219.getShuntVoltage_mV();
  float current_ma = ina219.getCurrent_mA();
  float power_mw = ina219.getPower_mW();

  battery_bus_v = bus_v;
  battery_source_v = bus_v + (shunt_mv / 1000.0f);
  battery_current_ma = current_ma;
  battery_power_mw = power_mw;
  battery_percent_est = estimateBatteryPercent4S(battery_source_v);
}

float batteryCompensationScale() {
  if (!ina_ok || battery_source_v < 5.0f) {
    return 1.0f;
  }

  float scale = NOMINAL_MOTOR_VOLTAGE / battery_source_v;
  return clampFloat(scale, 0.90f, 1.30f);
}

bool captureStableHeading(float &heading_out) {
  stopMotorsRaw();
  
  
  
  const uint8_t required_samples = 5;
  const unsigned long timeout_ms = 180;
  unsigned long start = millis();
  unsigned long observed_rotation_ms = 0;
  float sin_sum = 0.0f;
  float cos_sum = 0.0f;
  uint8_t samples = 0;

  while (millis() - start < timeout_ms) {
    updateIMU();
    updateBattery();
    if (
      yaw_valid && yaw_rate_valid &&
      fabsf(yaw_rate_deg_s) <= TURN_STOP_RATE_TOLERANCE_DPS &&
      last_rotation_ms != 0 && last_rotation_ms != observed_rotation_ms
    ) {
      observed_rotation_ms = last_rotation_ms;
      float radians = robot_heading_deg * DEG_TO_RAD;
      sin_sum += sinf(radians);
      cos_sum += cosf(radians);
      samples++;
      if (samples >= required_samples) {
        heading_out = wrapAngleDeg(atan2f(sin_sum, cos_sum) * RAD_TO_DEG);
        return true;
      }
    }
    delay(2);
  }

  heading_out = robot_heading_deg;
  return false;
}





void stopMotorsRaw() {
  analogWrite(LEFT_EN, 0);
  analogWrite(RIGHT_EN, 0);

  digitalWrite(LEFT_IN1, LOW);
  digitalWrite(LEFT_IN2, LOW);

  digitalWrite(RIGHT_IN1, LOW);
  digitalWrite(RIGHT_IN2, LOW);

  left_ctrl.pwm = 0;
  right_ctrl.pwm = 0;
}

void writeOneMotorRaw(int en, int in1, int in2, int pwm) {
  pwm = constrain(pwm, -255, 255);

  if (pwm > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
    analogWrite(en, pwm);
  } else if (pwm < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
    analogWrite(en, -pwm);
  } else {
    analogWrite(en, 0);
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }
}

void writeLeftCorrectedPWM(int corrected_pwm) {
  left_ctrl.pwm = corrected_pwm;
  writeOneMotorRaw(
    LEFT_EN,
    LEFT_IN1,
    LEFT_IN2,
    corrected_pwm * LEFT_MOTOR_SIGN
  );
}

void writeRightCorrectedPWM(int corrected_pwm) {
  right_ctrl.pwm = corrected_pwm;
  writeOneMotorRaw(
    RIGHT_EN,
    RIGHT_IN1,
    RIGHT_IN2,
    corrected_pwm * RIGHT_MOTOR_SIGN
  );
}

int applyDeadbandAndLimit(
  int pwm,
  int pwm_min,
  int pwm_max,
  float target_speed_tps,
  bool moving_endpoint_ramp
) {
  pwm = constrain(pwm, -pwm_max, pwm_max);

  int desired_sign = signInt(target_speed_tps);

  if (desired_sign == 0) {
    return 0;
  }

  
  
  
  if (desired_sign > 0 && pwm < 0) pwm = 0;
  if (desired_sign < 0 && pwm > 0) pwm = 0;

  return constrain(pwm, -pwm_max, pwm_max);
}

void writeMotors(
  int left_pwm,
  int right_pwm,
  bool moving_endpoint_ramp = false
) {
  float scale = batteryCompensationScale();

  left_pwm = (int)(left_pwm * scale);
  right_pwm = (int)(right_pwm * scale);

  left_pwm = applyDeadbandAndLimit(
    left_pwm,
    LEFT_PWM_MIN,
    LEFT_PWM_MAX,
    left_ctrl.target_speed_tps,
    moving_endpoint_ramp
  );

  right_pwm = applyDeadbandAndLimit(
    right_pwm,
    RIGHT_PWM_MIN,
    RIGHT_PWM_MAX,
    right_ctrl.target_speed_tps,
    moving_endpoint_ramp
  );

  writeLeftCorrectedPWM(left_pwm);
  writeRightCorrectedPWM(right_pwm);
}





int updatePIDForSide(int side, long current_ticks, float dt_sec) {
  MesBotControl::WheelController &state = side == 0 ? left_ctrl : right_ctrl;
  MesBotControl::WheelPidConfig config = {
    side == 0 ? LEFT_KP_SPEED : RIGHT_KP_SPEED,
    side == 0 ? LEFT_KI_SPEED : RIGHT_KI_SPEED,
    side == 0 ? LEFT_KD_SPEED : RIGHT_KD_SPEED,
    side == 0 ? LEFT_KFF_SPEED : RIGHT_KFF_SPEED,
    side == 0 ? LEFT_PWM_MIN : RIGHT_PWM_MIN,
    side == 0 ? LEFT_PWM_MAX : RIGHT_PWM_MAX,
    INTEGRAL_LIMIT,
    SPEED_FILTER_TAU_S,
    DERIVATIVE_FILTER_TAU_S,
    1.0f  
  };
  return MesBotControl::updateWheelPid(state, current_ticks, dt_sec, config);
}

void resetControllersKeepingTargets() {
  long l = readLeftTicks();
  long r = readRightTicks();

  left_ctrl.last_ticks = l;
  right_ctrl.last_ticks = r;

  left_ctrl.measured_speed_tps = 0.0f;
  right_ctrl.measured_speed_tps = 0.0f;
  left_ctrl.raw_speed_tps = 0.0f;
  right_ctrl.raw_speed_tps = 0.0f;

  left_ctrl.target_speed_tps = 0.0f;
  right_ctrl.target_speed_tps = 0.0f;

  left_ctrl.integral = 0.0f;
  right_ctrl.integral = 0.0f;

  left_ctrl.last_measurement_tps = 0.0f;
  right_ctrl.last_measurement_tps = 0.0f;
  left_ctrl.filtered_derivative = 0.0f;
  right_ctrl.filtered_derivative = 0.0f;

  left_ctrl.ff_term = 0.0f;
  right_ctrl.ff_term = 0.0f;
  left_ctrl.p_term = 0.0f;
  right_ctrl.p_term = 0.0f;
  left_ctrl.i_term = 0.0f;
  right_ctrl.i_term = 0.0f;
  left_ctrl.d_term = 0.0f;
  right_ctrl.d_term = 0.0f;
  left_ctrl.unsaturated_pwm = 0.0f;
  right_ctrl.unsaturated_pwm = 0.0f;
  left_ctrl.saturated = false;
  right_ctrl.saturated = false;

  left_ctrl.pwm = 0;
  right_ctrl.pwm = 0;
}

void zeroMotionCountersForNewPrimitive() {
  
  
  resetPrimitiveEncodersPreservingPose();

  left_ctrl.target_ticks = 0;
  right_ctrl.target_ticks = 0;

  motion_start_left_ticks = 0;
  motion_start_right_ticks = 0;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;

  resetControllersKeepingTargets();
  step_requested_distance_mm = 0.0f;
  step_left_distance_mm = 0.0f;
  step_right_distance_mm = 0.0f;
  step_actual_distance_mm = 0.0f;
  step_distance_error_mm = 0.0f;
  step_encoder_start_left_ticks = 0;
  step_encoder_start_right_ticks = 0;
  MesBotControl::resetHeadingController(straight_heading_ctrl);
  MesBotControl::resetHeadingController(turn_heading_ctrl);
}

void captureStepDistanceOutcome(long left_ticks, long right_ticks) {
  float direction_scale = step_requested_distance_mm < 0.0f
    ? BACKWARD_DISTANCE_TICK_SCALE : FORWARD_DISTANCE_TICK_SCALE;
  step_left_distance_mm = ((float)(left_ticks - step_encoder_start_left_ticks)) /
    (LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE * direction_scale);
  step_right_distance_mm = ((float)(right_ticks - step_encoder_start_right_ticks)) /
    (RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE * direction_scale);
  step_actual_distance_mm = 0.5f *
    (step_left_distance_mm + step_right_distance_mm);
  step_distance_error_mm =
    step_requested_distance_mm - step_actual_distance_mm;
}





String macroName() {
  if (macro_mode == MACRO_NONE) return "NONE";
  if (macro_mode == MACRO_MOVE_LEFT) return "MOVE_LEFT";
  if (macro_mode == MACRO_MOVE_RIGHT) return "MOVE_RIGHT";
  return "UNKNOWN";
}

const char *stepHeadingResultName() {
  if (step_heading_result == HEADING_RESULT_RUNNING) return "RUNNING";
  if (step_heading_result == HEADING_RESULT_COMPLETED) return "COMPLETED";
  if (step_heading_result == HEADING_RESULT_STOPPED) return "STOPPED";
  return "NONE";
}

void beginStepHeadingReference(float start_yaw_deg, float requested_delta_deg) {
  step_start_yaw_deg = start_yaw_deg;
  step_end_yaw_deg = start_yaw_deg;
  step_requested_yaw_delta_deg = requested_delta_deg;
  step_actual_yaw_delta_deg = 0.0f;
  step_final_yaw_error_deg = requested_delta_deg;
  step_end_heading_stable = false;
  step_heading_result = HEADING_RESULT_RUNNING;
}

void closeAndRebaseStepHeading(int result) {
  
  
  
  float end_heading = robot_heading_deg;
  bool stable = captureStableHeading(end_heading);
  step_end_yaw_deg = end_heading;
  step_actual_yaw_delta_deg = wrapAngleDeg(
    step_end_yaw_deg - step_start_yaw_deg
  );
  step_final_yaw_error_deg = yawErrorDeg(target_yaw_deg, step_end_yaw_deg);
  step_end_heading_stable = stable;
  step_heading_result = (PrimitiveHeadingResult)result;

  
  
  
  
  last_yaw_error_deg = step_final_yaw_error_deg;
}

void clearMacro() {
  macro_mode = MACRO_NONE;
  macro_step = 0;
  macro_next_step_ms = 0;
}

void scheduleNextMacroStep() {
  if (macro_mode != MACRO_NONE) {
    macro_next_step_ms = millis() + MACRO_STEP_PAUSE_MS;
  }
}





void enterFault(String reason) {
  MotionMode failed_mode = mode;
  fault_reason = reason;
  mode = MODE_FAULT;
  clearMacro();
  stopMotorsRaw();

  
  long l = readLeftTicks();
  long r = readRightTicks();
  if (failed_mode == MODE_STRAIGHT) {
    captureStepDistanceOutcome(l, r);
  }
  left_ctrl.target_ticks = l;
  right_ctrl.target_ticks = r;
  motion_start_left_ticks = l;
  motion_start_right_ticks = r;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;

  resetControllersKeepingTargets();
  motion_result_notify_code = 1;
  motion_result_notify_pending = true;
}

void clearCounters() {
  left_stall_counter = 0;
  right_stall_counter = 0;
  slip_counter = 0;
  turn_wrong_way_counter = 0;
  turn_settle_counter = 0;
  straight_final_settle_counter = 0;
  straight_endpoint_aligning = false;
}

void beginRecovery(int side, String reason) {
  recovery_attempts_this_motion++;

  if (recovery_attempts_this_motion > MAX_RECOVERY_ATTEMPTS_PER_MOTION) {
    enterFault("recovery_disabled_or_too_many_recoveries:" + reason);
    return;
  }

  resume_mode_after_recovery = mode;
  recovery_side = side;
  recovery_phase = 0;
  recovery_phase_start_ms = millis();

  int left_dir = signInt(left_ctrl.target_speed_tps);
  int right_dir = signInt(right_ctrl.target_speed_tps);

  if (left_dir == 0) left_dir = 1;
  if (right_dir == 0) right_dir = 1;

  recovery_left_corrected_pwm = 0;
  recovery_right_corrected_pwm = 0;

  if (side == 0) {
    recovery_left_corrected_pwm = -left_dir * RECOVERY_PWM_LEFT;
  } else if (side == 1) {
    recovery_right_corrected_pwm = -right_dir * RECOVERY_PWM_RIGHT;
  } else {
    recovery_left_corrected_pwm = -left_dir * RECOVERY_PWM_LEFT;
    recovery_right_corrected_pwm = -right_dir * RECOVERY_PWM_RIGHT;
  }

  speed_derate *= RECOVERY_DERATE_FACTOR;
  if (speed_derate < MIN_SPEED_DERATE) {
    speed_derate = MIN_SPEED_DERATE;
  }

  clearCounters();
  stopMotorsRaw();

  mode = MODE_RECOVERY;
}

void runRecoveryControl() {
  unsigned long now = millis();

  if (recovery_phase == 0) {
    stopMotorsRaw();

    if (now - recovery_phase_start_ms >= RECOVERY_STOP_MS) {
      recovery_phase = 1;
      recovery_phase_start_ms = now;
    }

    return;
  }

  if (recovery_phase == 1) {
    if (recovery_side == 0 || recovery_side == 2) {
      writeLeftCorrectedPWM(recovery_left_corrected_pwm);
    } else {
      writeLeftCorrectedPWM(0);
    }

    if (recovery_side == 1 || recovery_side == 2) {
      writeRightCorrectedPWM(recovery_right_corrected_pwm);
    } else {
      writeRightCorrectedPWM(0);
    }

    if (now - recovery_phase_start_ms >= RECOVERY_PULSE_MS) {
      recovery_phase = 2;
      recovery_phase_start_ms = now;
      stopMotorsRaw();
    }

    return;
  }

  if (recovery_phase == 2) {
    stopMotorsRaw();

    if (now - recovery_phase_start_ms >= RECOVERY_SETTLE_MS) {
      resetControllersKeepingTargets();
      clearCounters();

      mode = resume_mode_after_recovery;
      last_control_ms = millis();
    }

    return;
  }
}

bool monitorMotorStallAndSlip() {
  unsigned long now = millis();

  if (now - motion_start_ms < 600) {
    return false;
  }

  bool left_target_active = fabsf(left_ctrl.target_speed_tps) >= STALL_TARGET_SPEED_TPS;
  bool right_target_active = fabsf(right_ctrl.target_speed_tps) >= STALL_TARGET_SPEED_TPS;

  bool left_pwm_high = abs(left_ctrl.pwm) >= STALL_PWM_THRESHOLD;
  bool right_pwm_high = abs(right_ctrl.pwm) >= STALL_PWM_THRESHOLD;

  bool left_speed_low = fabsf(left_ctrl.measured_speed_tps) <= STALL_MEASURED_SPEED_TPS;
  bool right_speed_low = fabsf(right_ctrl.measured_speed_tps) <= STALL_MEASURED_SPEED_TPS;

  if (left_target_active && left_pwm_high && left_speed_low) {
    left_stall_counter++;
  } else if (left_stall_counter > 0) {
    left_stall_counter--;
  }

  if (right_target_active && right_pwm_high && right_speed_low) {
    right_stall_counter++;
  } else if (right_stall_counter > 0) {
    right_stall_counter--;
  }

  if (left_stall_counter >= STALL_COUNT_LIMIT) {
    beginRecovery(0, "left_stall");
    return true;
  }

  if (right_stall_counter >= STALL_COUNT_LIMIT) {
    beginRecovery(1, "right_stall");
    return true;
  }

  if (mode == MODE_STRAIGHT) {
    long l = readLeftTicks();
    long r = readRightTicks();

    float lp = progressFraction(l, motion_start_left_ticks, motion_left_delta_ticks);
    float rp = progressFraction(r, motion_start_right_ticks, motion_right_delta_ticks);
    float progress_diff = lp - rp;

    bool progress_slip = fabsf(progress_diff) > PROGRESS_SLIP_THRESHOLD;
    bool yaw_slip = false;

    if (yaw_valid) {
      float ye = yawErrorDeg(target_yaw_deg, robot_heading_deg);

      if (fabsf(ye) > STRAIGHT_YAW_SLIP_THRESHOLD_DEG) {
        yaw_slip = true;
      }

      if (yaw_rate_valid && fabsf(yaw_rate_deg_s) > STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS) {
        yaw_slip = true;
      }
    }

    if (progress_slip || yaw_slip) {
      slip_counter++;
    } else if (slip_counter > 0) {
      slip_counter--;
    }

    if (slip_counter >= SLIP_COUNT_LIMIT) {
      beginRecovery(2, "slip_or_yaw_error");
      return true;
    }
  }

  return false;
}





void finishStraightMotionCleanly() {
  
  
  stopMotorsRaw();
  long l = readLeftTicks();
  long r = readRightTicks();

  captureStepDistanceOutcome(l, r);
  left_ctrl.target_ticks = l;
  right_ctrl.target_ticks = r;

  motion_start_left_ticks = l;
  motion_start_right_ticks = r;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;

  stopMotorsRaw();
  closeAndRebaseStepHeading(HEADING_RESULT_COMPLETED);
  mode = MODE_IDLE;
  resetControllersKeepingTargets();
  clearCounters();

  motion_result_notify_code = 0;
  motion_result_notify_pending = true;

  scheduleNextMacroStep();
}

void finishTurnMotionCleanly() {
  long l = readLeftTicks();
  long r = readRightTicks();

  left_ctrl.target_ticks = l;
  right_ctrl.target_ticks = r;

  stopMotorsRaw();
  closeAndRebaseStepHeading(HEADING_RESULT_COMPLETED);
  mode = MODE_IDLE;
  resetControllersKeepingTargets();
  clearCounters();

  motion_result_notify_code = 0;
  motion_result_notify_pending = true;

  scheduleNextMacroStep();
}

void finishSpeedTestCleanly() {
  long l = readLeftTicks();
  long r = readRightTicks();
  left_ctrl.target_ticks = l;
  right_ctrl.target_ticks = r;
  motion_start_left_ticks = l;
  motion_start_right_ticks = r;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;
  mode = MODE_IDLE;
  speed_test_end_ms = 0;
  speed_test_left_tps = 0.0f;
  speed_test_right_tps = 0.0f;
  stopMotorsRaw();
  resetControllersKeepingTargets();
  clearCounters();
  motion_result_notify_code = 0;
  motion_result_notify_pending = true;
}





void runStraightControl(float dt_sec) {
  long l = readLeftTicks();
  long r = readRightTicks();

  long left_error_ticks = left_ctrl.target_ticks - l;
  long right_error_ticks = right_ctrl.target_ticks - r;

  
  
  
  float left_remaining_fraction = motion_left_delta_ticks == 0 ? 0.0f :
    ((float)left_error_ticks) / ((float)motion_left_delta_ticks);
  float right_remaining_fraction = motion_right_delta_ticks == 0 ? 0.0f :
    ((float)right_error_ticks) / ((float)motion_right_delta_ticks);
  float center_remaining_fraction =
    0.5f * (left_remaining_fraction + right_remaining_fraction);
  long average_target_ticks =
    (labs(motion_left_delta_ticks) + labs(motion_right_delta_ticks)) / 2L;
  long center_remaining_ticks = lroundf(
    center_remaining_fraction * (float)average_target_ticks
  );

  if (!imuFreshForControl()) {
    enterFault("imu_stale_during_straight");
    return;
  }
  int travel_sign = motion_left_delta_ticks < 0 ? -1 : 1;
  float step_dx_mm = pose_x_mm - straight_start_pose_x_mm;
  float step_dy_mm = pose_y_mm - straight_start_pose_y_mm;
  float path_heading_rad = straight_path_heading_deg * DEG_TO_RAD;
  straight_cross_track_error_mm =
    -step_dx_mm * sinf(path_heading_rad) +
     step_dy_mm * cosf(path_heading_rad);
  straight_path_heading_offset_deg = clampFloat(
    -((float)travel_sign) * STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM *
      straight_cross_track_error_mm,
    -STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG,
     STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG
  );
  float trajectory_target_yaw_deg = wrapAngleDeg(
    target_yaw_deg + straight_path_heading_offset_deg
  );
  float yaw_error = yawErrorDeg(trajectory_target_yaw_deg, robot_heading_deg);
  last_yaw_error_deg = yaw_error;

  if (center_remaining_ticks <= POSITION_COMMAND_DEADBAND_TICKS) {
    
    
    finishStraightMotionCleanly();
    return;
  }

  float positive_remaining_fraction = fmaxf(center_remaining_fraction, 0.0f);
  long left_common_error_ticks = travel_sign * lroundf(
    positive_remaining_fraction * (float)labs(motion_left_delta_ticks)
  );
  long right_common_error_ticks = travel_sign * lroundf(
    positive_remaining_fraction * (float)labs(motion_right_delta_ticks)
  );
  long max_remaining_ticks = maxLongAbs(
    left_common_error_ticks, right_common_error_ticks
  );

  float heading_gate = headingGateFromRemaining(max_remaining_ticks);

  float base_max_speed = maxStraightSpeedNow();
  float local_max_speed = endpointLimitedMaxStraightSpeed(base_max_speed, max_remaining_ticks);
  float local_min_speed = endpointLimitedMinStraightSpeed(max_remaining_ticks);

  MesBotControl::StraightCascadeInput straight_input = {
    left_common_error_ticks, right_common_error_ticks,
    local_max_speed, local_min_speed,
    heading_gate,
    true, yaw_error, yaw_rate_deg_s, dt_sec
  };
  MesBotControl::StraightCascadeConfig straight_config = {
    KP_DISTANCE,
    POSITION_COMMAND_DEADBAND_TICKS,
    {
      KP_YAW_STRAIGHT,
      KI_YAW_STRAIGHT,
      KD_YAW_STRAIGHT,
      MAX_YAW_CORRECTION_TPS,
      YAW_INTEGRAL_LIMIT_TPS,
      YAW_RATE_FILTER_TAU_S,
      YAW_IGNORE_DEG
    },
    YAW_CORRECTION_SIGN
  };
  MesBotControl::WheelSpeedTargets straight_targets =
    MesBotControl::straightCascadeTargets(
      straight_input, straight_config, straight_heading_ctrl
    );
  left_ctrl.target_speed_tps = straight_targets.left_tps;
  right_ctrl.target_speed_tps = straight_targets.right_tps;

  int left_pwm = updatePIDForSide(0, l, dt_sec);
  int right_pwm = updatePIDForSide(1, r, dt_sec);

  writeMotors(left_pwm, right_pwm, true);

  if (monitorMotorStallAndSlip()) {
    return;
  }
}





void updateTurnAccumulator() {
  if (!yaw_valid) {
    return;
  }

  if (!turn_accumulator_valid) {
    turn_last_heading_deg = robot_heading_deg;
    turn_unwrapped_progress_deg = 0.0f;
    turn_accumulator_valid = true;
    return;
  }

  float delta = wrapAngleDeg(robot_heading_deg - turn_last_heading_deg);
  turn_unwrapped_progress_deg += delta;
  turn_last_heading_deg = robot_heading_deg;
}

void runTurnIMUControl(float dt_sec) {
  long l = readLeftTicks();
  long r = readRightTicks();

  updateTurnAccumulator();

  if (!imuFreshForControl()) {
    enterFault("imu_stale_during_turn");
    return;
  }

  
  
  float left_turn_mm = ((float)(l - motion_start_left_ticks)) /
    (LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE);
  float right_turn_mm = ((float)(r - motion_start_right_ticks)) /
    (RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE);
  turn_encoder_progress_deg =
    ((right_turn_mm - left_turn_mm) / TRACK_WIDTH_MM) * 180.0f / PI;

  
  
  turn_gyro_progress_deg += yaw_rate_deg_s * dt_sec;

  MesBotControl::TurnFusionResult turn_fusion =
    MesBotControl::robustTurnFusion(
      turn_unwrapped_progress_deg,
      turn_gyro_progress_deg,
      turn_encoder_progress_deg
    );
  turn_fused_progress_deg = turn_fusion.progress_deg;
  turn_sensor_disagreement_deg = turn_fusion.max_disagreement_deg;
  turn_fusion_selected_pair = turn_fusion.selected_pair;

  float signed_progress_deg =
    turn_fused_progress_deg * (float)turn_direction_sign;
  float remaining_signed_deg =
    turn_requested_delta_deg - turn_fused_progress_deg;
  float remaining_abs_deg = fabsf(remaining_signed_deg);

  last_yaw_error_deg = remaining_signed_deg;

  bool inside_turn_tolerance = remaining_abs_deg <= TURN_TOLERANCE_DEG;
  if (inside_turn_tolerance) {
    left_ctrl.target_speed_tps = 0.0f;
    right_ctrl.target_speed_tps = 0.0f;
    stopMotorsRaw();
    resetControllersKeepingTargets();

    if (MesBotControl::updateTurnSettling(
      inside_turn_tolerance,
      yaw_rate_valid,
      yaw_rate_deg_s,
      TURN_STOP_RATE_TOLERANCE_DPS,
      TURN_SETTLE_COUNT_REQUIRED,
      turn_settle_counter
    )) {
      finishTurnMotionCleanly();
    }
    return;
  }

  turn_settle_counter = 0;

  if (signed_progress_deg < -TURN_WRONG_WAY_DEG) {
    turn_wrong_way_counter++;
  } else if (turn_wrong_way_counter > 0) {
    turn_wrong_way_counter--;
  }

  if (turn_wrong_way_counter >= TURN_WRONG_WAY_COUNT_LIMIT) {
    enterFault("turn_wrong_way");
    return;
  }

  float max_turn_speed = maxTurnSpeedNow();
  float local_min_turn_speed = endpointLimitedMinTurnSpeed(remaining_abs_deg);

  MesBotControl::HeadingPidConfig turn_pid = {
    KP_TURN_YAW,
    KI_TURN_YAW,
    KD_TURN_YAW,
    max_turn_speed,
    0.0f,
    YAW_RATE_FILTER_TAU_S,
    0.0f
  };
  MesBotControl::WheelSpeedTargets turn_targets =
    MesBotControl::turnCascadeTargets(
      remaining_signed_deg,
      yaw_rate_deg_s,
      dt_sec,
      local_min_turn_speed,
      max_turn_speed,
      TURN_CONTROL_SIGN,
      turn_pid,
      turn_heading_ctrl
    );

  const float left_effective_ticks_per_mm =
    LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE;
  const float right_effective_ticks_per_mm =
    RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE;
  turn_targets = MesBotControl::normalizeTurnTargetsForWheelGeometry(
    turn_targets,
    left_effective_ticks_per_mm,
    right_effective_ticks_per_mm,
    max_turn_speed
  );

  float directed_left_progress_mm =
    -((float)turn_direction_sign) * left_turn_mm;
  float directed_right_progress_mm =
    ((float)turn_direction_sign) * right_turn_mm;
  turn_balance_error_mm =
    directed_left_progress_mm - directed_right_progress_mm;
  turn_center_translation_mm = 0.5f * (left_turn_mm + right_turn_mm);
  turn_center_speed_mm_s = 0.5f * (
    left_ctrl.measured_speed_tps / left_effective_ticks_per_mm +
    right_ctrl.measured_speed_tps / right_effective_ticks_per_mm
  );
  MesBotControl::WheelSpeedTargets unbalanced_turn_targets = turn_targets;
  turn_targets = MesBotControl::balanceTurnTargets(
    turn_targets,
    turn_direction_sign,
    directed_left_progress_mm,
    directed_right_progress_mm,
    turn_center_speed_mm_s,
    left_effective_ticks_per_mm,
    right_effective_ticks_per_mm,
    TURN_BALANCE_KP_TPS_PER_MM,
    TURN_CENTER_SPEED_KP_TPS_PER_MM_S,
    MAX_TURN_BALANCE_TPS,
    max_turn_speed
  );
  turn_balance_correction_tps =
    turn_targets.left_tps - unbalanced_turn_targets.left_tps;
  left_ctrl.target_speed_tps = turn_targets.left_tps;
  right_ctrl.target_speed_tps = turn_targets.right_tps;

  int left_pwm = updatePIDForSide(0, l, dt_sec);
  int right_pwm = updatePIDForSide(1, r, dt_sec);

  writeMotors(left_pwm, right_pwm);
  if (monitorMotorStallAndSlip()) {
    return;
  }
}





void runTurnEncoderControl(float dt_sec) {
  long l = readLeftTicks();
  long r = readRightTicks();

  long left_error_ticks = left_ctrl.target_ticks - l;
  long right_error_ticks = right_ctrl.target_ticks - r;

  float max_turn_speed = maxTurnSpeedNow();

  float left_speed_cmd = speedCommandFromError(
    left_error_ticks,
    max_turn_speed,
    MIN_TURN_SPEED_TPS
  );

  float right_speed_cmd = speedCommandFromError(
    right_error_ticks,
    max_turn_speed,
    MIN_TURN_SPEED_TPS
  );

  left_ctrl.target_speed_tps = left_speed_cmd;
  right_ctrl.target_speed_tps = right_speed_cmd;

  int left_pwm = updatePIDForSide(0, l, dt_sec);
  int right_pwm = updatePIDForSide(1, r, dt_sec);

  writeMotors(left_pwm, right_pwm);
  if (monitorMotorStallAndSlip()) {
    return;
  }

  bool left_done =
    labs(left_error_ticks) <= TURN_ENCODER_TOLERANCE_TICKS &&
    fabsf(left_ctrl.measured_speed_tps) <= SPEED_STOP_TOLERANCE_TPS;

  bool right_done =
    labs(right_error_ticks) <= TURN_ENCODER_TOLERANCE_TICKS &&
    fabsf(right_ctrl.measured_speed_tps) <= SPEED_STOP_TOLERANCE_TPS;

  if (left_done && right_done) {
    finishTurnMotionCleanly();
  }
}





void prepareNewMotionAfterEncoderReset() {
  fault_reason = "";
  recovery_attempts_this_motion = 0;
  speed_derate = 1.0f;
  clearCounters();
  resetControllersKeepingTargets();

  motion_start_left_ticks = readLeftTicks();
  motion_start_right_ticks = readRightTicks();

  motion_start_ms = millis();
  last_control_ms = millis();
  last_control_dt_ms = 0.0f;
  max_control_dt_ms = 0.0f;
  control_deadline_misses = 0;
}

void runSpeedTestControl(float dt_sec) {
  if (millis() >= speed_test_end_ms) {
    finishSpeedTestCleanly();
    return;
  }

  long l = readLeftTicks();
  long r = readRightTicks();
  left_ctrl.target_speed_tps = speed_test_left_tps;
  right_ctrl.target_speed_tps = speed_test_right_tps;

  int left_pwm = updatePIDForSide(0, l, dt_sec);
  int right_pwm = updatePIDForSide(1, r, dt_sec);
  writeMotors(left_pwm, right_pwm);
  monitorMotorStallAndSlip();
}

String startStraightDistance(float distance_mm) {
  if (mode != MODE_IDLE && mode != MODE_FAULT) {
    return "busy";
  }

  motion_result_notify_pending = false;

  float captured_heading = robot_heading_deg;

  if (!captureStableHeading(captured_heading)) {
    enterFault("imu_heading_capture_failed");
    return "imu_heading_capture_failed";
  }

  target_yaw_deg = captured_heading;
  last_yaw_error_deg = 0.0f;
  beginStepHeadingReference(captured_heading, 0.0f);

  zeroMotionCountersForNewPrimitive();

  straight_start_pose_x_mm = pose_x_mm;
  straight_start_pose_y_mm = pose_y_mm;
  straight_path_heading_deg = wrapAngleDeg(
    captured_heading - pose_heading_origin_deg
  );
  straight_cross_track_error_mm = 0.0f;
  straight_path_heading_offset_deg = 0.0f;

  step_requested_distance_mm = distance_mm;

  long l = readLeftTicks();
  long r = readRightTicks();

  long left_delta = ticksForLeftDistance(distance_mm);
  long right_delta = ticksForRightDistance(distance_mm);

  left_ctrl.target_ticks = l + left_delta;
  right_ctrl.target_ticks = r + right_delta;

  motion_left_delta_ticks = left_delta;
  motion_right_delta_ticks = right_delta;

  prepareNewMotionAfterEncoderReset();

  step_encoder_start_left_ticks = motion_start_left_ticks;
  step_encoder_start_right_ticks = motion_start_right_ticks;

  mode = MODE_STRAIGHT;

  String out = "startStraightDistance: distance_mm=";
  out += String(distance_mm, 1);

  out += " left_delta=";
  out += String(left_delta);

  out += " right_delta=";
  out += String(right_delta);

  out += " captured_heading=";
  out += String(captured_heading, 2);

  out += " target_heading=";
  out += String(target_yaw_deg, 2);

  out += " yaw_valid=";
  out += yaw_valid ? "1" : "0";

  return out;
}

String startTurnDegrees(float delta_deg) {
  if (mode != MODE_IDLE && mode != MODE_FAULT) {
    return "busy";
  }

  motion_result_notify_pending = false;

  
  
  
  float captured_heading = robot_heading_deg;
  String reset_reason = "";

  if (!resetImuReferenceForTurnInternal(captured_heading, reset_reason)) {
    enterFault(reset_reason);
    return reset_reason;
  }

  zeroMotionCountersForNewPrimitive();

  turn_start_heading_deg = captured_heading;
  turn_requested_delta_deg = delta_deg;
  turn_abs_target_deg = fabsf(delta_deg);
  turn_direction_sign = signInt(delta_deg);

  if (turn_direction_sign == 0) {
    turn_direction_sign = 1;
  }

  turn_unwrapped_progress_deg = 0.0f;
  turn_gyro_progress_deg = 0.0f;
  turn_encoder_progress_deg = 0.0f;
  turn_fused_progress_deg = 0.0f;
  turn_sensor_disagreement_deg = 0.0f;
  turn_balance_error_mm = 0.0f;
  turn_center_translation_mm = 0.0f;
  turn_center_speed_mm_s = 0.0f;
  turn_balance_correction_tps = 0.0f;
  turn_fusion_selected_pair = 0;
  turn_last_heading_deg = captured_heading;
  turn_accumulator_valid = true;
  turn_wrong_way_counter = 0;
  rejected_turn_delta_samples = 0;

  target_yaw_deg = wrapAngleDeg(captured_heading + delta_deg);
  last_yaw_error_deg = yawErrorDeg(target_yaw_deg, captured_heading);
  beginStepHeadingReference(captured_heading, delta_deg);

  float wheel_arc_mm = turn_abs_target_deg * PI / 180.0f *
    (TRACK_WIDTH_MM * 0.5f);
  motion_left_delta_ticks = ticksForLeftDistance(
    -((float)turn_direction_sign) * wheel_arc_mm
  );
  motion_right_delta_ticks = ticksForRightDistance(
    ((float)turn_direction_sign) * wheel_arc_mm
  );
  left_ctrl.target_ticks = readLeftTicks() + motion_left_delta_ticks;
  right_ctrl.target_ticks = readRightTicks() + motion_right_delta_ticks;

  prepareNewMotionAfterEncoderReset();

  mode = MODE_TURN_IMU;

  String out = "startTurnDegrees: IMU_REFERENCE_RESET_DIRECTION_LOCKED_UNWRAPPED delta_deg=";
  out += String(delta_deg, 1);

  out += " captured_heading=";
  out += String(captured_heading, 2);

  out += " target_heading=";
  out += String(target_yaw_deg, 2);

  out += " direction=";
  out += String(turn_direction_sign);

  out += " abs_target=";
  out += String(turn_abs_target_deg, 2);

  out += " imu_reference_reset=1";

  return out;
}

String start_speed_test(String payload) {
  if (mode != MODE_IDLE && mode != MODE_FAULT) {
    return "busy";
  }

  motion_result_notify_pending = false;

  float left_tps = 0.0f;
  float right_tps = 0.0f;
  float duration_ms_value = 0.0f;
  if (!extractNumber(payload, "left_tps", left_tps) ||
      !extractNumber(payload, "right_tps", right_tps) ||
      !extractNumber(payload, "duration_ms", duration_ms_value)) {
    return "speed_test_invalid_payload";
  }

  left_tps = clampFloat(left_tps, -1000.0f, 1000.0f);
  right_tps = clampFloat(right_tps, -1000.0f, 1000.0f);
  unsigned long duration_ms = clampUnsignedLong(
    (unsigned long)lroundf(duration_ms_value), 200, 5000
  );
  if (fabsf(left_tps) < 1.0f && fabsf(right_tps) < 1.0f) {
    return "speed_test_zero_targets";
  }

  clearMacro();
  zeroMotionCountersForNewPrimitive();
  prepareNewMotionAfterEncoderReset();
  speed_test_left_tps = left_tps;
  speed_test_right_tps = right_tps;
  speed_test_end_ms = millis() + duration_ms;
  mode = MODE_SPEED_TEST;

  String out = "start_speed_test: left_tps=";
  out += String(left_tps, 1);
  out += " right_tps=";
  out += String(right_tps, 1);
  out += " duration_ms=";
  out += String(duration_ms);
  return out;
}

void advanceMacroIfReady() {
  if (macro_mode == MACRO_NONE) {
    return;
  }

  if (mode != MODE_IDLE) {
    return;
  }

  if (millis() < macro_next_step_ms) {
    return;
  }

  if (macro_mode == MACRO_MOVE_LEFT) {
    if (macro_step == 0) {
      macro_step = 1;
      startTurnDegrees(90.0f * TURN_LEFT_DEG_SCALE);
      return;
    }

    if (macro_step == 1) {
      macro_step = 2;
      startStraightDistance(CELL_DISTANCE_MM);
      return;
    }

    if (macro_step == 2) {
      macro_step = 3;
      startTurnDegrees(-90.0f * TURN_RIGHT_DEG_SCALE);
      return;
    }

    clearMacro();
    return;
  }

  if (macro_mode == MACRO_MOVE_RIGHT) {
    if (macro_step == 0) {
      macro_step = 1;
      startTurnDegrees(-90.0f * TURN_RIGHT_DEG_SCALE);
      return;
    }

    if (macro_step == 1) {
      macro_step = 2;
      startStraightDistance(CELL_DISTANCE_MM);
      return;
    }

    if (macro_step == 2) {
      macro_step = 3;
      startTurnDegrees(90.0f * TURN_LEFT_DEG_SCALE);
      return;
    }

    clearMacro();
    return;
  }
}





void controlLoop() {
  updateIMU();
  updateBattery();

  advanceMacroIfReady();

  unsigned long now = millis();

  if (now - last_control_ms < CONTROL_PERIOD_MS) {
    return;
  }

  unsigned long dt_ms = now - last_control_ms;
  float dt_sec = dt_ms / 1000.0f;
  last_control_ms = now;
  last_control_dt_ms = (float)dt_ms;
  if (last_control_dt_ms > max_control_dt_ms) {
    max_control_dt_ms = last_control_dt_ms;
  }
  if (dt_ms > CONTROL_PERIOD_MS + (CONTROL_PERIOD_MS / 2)) {
    control_deadline_misses++;
  }

  if (dt_sec <= 0.0f) {
    return;
  }

  updatePlanarOdometry();

  if (mode == MODE_IDLE || mode == MODE_FAULT) {
    return;
  }

  if (mode == MODE_RECOVERY) {
    runRecoveryControl();
    return;
  }

  if (now - motion_start_ms > MOTION_TIMEOUT_MS) {
    enterFault("motion_timeout");
    return;
  }

  if (mode == MODE_STRAIGHT) {
    runStraightControl(dt_sec);
  } else if (mode == MODE_TURN_IMU) {
    runTurnIMUControl(dt_sec);
  } else if (mode == MODE_TURN_ENCODER) {
    runTurnEncoderControl(dt_sec);
  } else if (mode == MODE_SPEED_TEST) {
    runSpeedTestControl(dt_sec);
  }
}





String init_robot() {
  Wire1.begin();
  Wire1.setClock(400000);

  delay(700);

  ina_ok = false;
  bno_ok = false;
  yaw_valid = false;
  yaw_rate_valid = false;
  last_rotation_ms = 0;
  last_gyro_ms = 0;
  last_linear_accel_ms = 0;
  last_gravity_ms = 0;
  have_last_imu_rate_sample = false;

  rejected_yaw_rate_samples = 0;
  rejected_heading_jump_samples = 0;
  rejected_quaternion_samples = 0;
  rejected_turn_delta_samples = 0;

  stopMotorsRaw();

  unsigned long init_start_ms = millis();

  for (int attempt = 0; attempt < 4; attempt++) {
    if (!ina_ok) {
      ina_ok = ina219.begin(&Wire1);
      if (ina_ok) {
        ina219.setCalibration_32V_2A();
      }
    }

    if (!bno_ok) {
      if (bno080.begin(0x4A, Wire1)) {
        bno_ok = true;
        bno_wire = &Wire1;
        bno_i2c_address = 0x4A;
      } else if (bno080.begin(0x4B, Wire1)) {
        bno_ok = true;
        bno_wire = &Wire1;
        bno_i2c_address = 0x4B;
      } else {
        Wire.begin();
        Wire.setClock(400000);
        if (bno080.begin(0x4A, Wire)) {
          bno_ok = true;
          bno_wire = &Wire;
          bno_i2c_address = 0x4A;
        } else if (bno080.begin(0x4B, Wire)) {
          bno_ok = true;
          bno_wire = &Wire;
          bno_i2c_address = 0x4B;
        }
      }

      if (bno_ok) {
        last_bno_poll_us = 0;
        configureBnoReports();
        delay(250);
      }
    }

    unsigned long warmup_start_ms = millis();

    while (millis() - warmup_start_ms < 900) {
      updateIMU();
      updateBattery();

      if (ina_ok && bno_ok && yaw_valid) {
        break;
      }

      delay(10);
    }

    if (ina_ok && bno_ok && yaw_valid) {
      break;
    }

    delay(250);

    if (millis() - init_start_ms > 6500) {
      break;
    }
  }

  if (yaw_valid) {
    target_yaw_deg = robot_heading_deg;
    last_yaw_error_deg = 0.0f;
    resetPlanarOdometry(true);
  }

  String out = "init_robot_bounded: INA219=";
  out += ina_ok ? "OK" : "NOT_FOUND";

  out += " | BNO080=";
  out += bno_ok ? "OK" : "NOT_FOUND";

  out += " | yaw_valid=";
  out += yaw_valid ? "1" : "0";

  out += " | left_cell_ticks=";
  out += String(ticksForLeftDistance(CELL_DISTANCE_MM));

  out += " | right_cell_ticks=";
  out += String(ticksForRightDistance(CELL_DISTANCE_MM));

  out += " | robot_heading_deg=";
  out += String(robot_heading_deg, 2);

  out += " | target_yaw_deg=";
  out += String(target_yaw_deg, 2);

  out += " | battery_v=";
  out += String(battery_source_v, 3);

  out += " | battery_percent_est=";
  out += String(battery_percent_est, 1);

  out += " | init_time_ms=";
  out += String(millis() - init_start_ms);

  return out;
}

String zero_pose() {
  stopMotorsRaw();
  updatePlanarOdometry();
  resetEncoderCounts();
  pose_last_left_ticks = 0;
  pose_last_right_ticks = 0;

  left_ctrl.target_ticks = 0;
  right_ctrl.target_ticks = 0;

  motion_start_left_ticks = 0;
  motion_start_right_ticks = 0;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;

  resetControllersKeepingTargets();
  clearCounters();
  clearMacro();

  float stable_heading = robot_heading_deg;

  bool heading_stable = captureStableHeading(stable_heading);
  if (heading_stable) {
    target_yaw_deg = stable_heading;
    robot_heading_deg = stable_heading;
  }

  resetPlanarOdometry(true);
  MesBotControl::resetHeadingController(straight_heading_ctrl);
  MesBotControl::resetHeadingController(turn_heading_ctrl);

  turn_start_heading_deg = robot_heading_deg;
  turn_requested_delta_deg = 0.0f;
  turn_abs_target_deg = 0.0f;
  turn_direction_sign = 1;
  turn_unwrapped_progress_deg = 0.0f;
  turn_gyro_progress_deg = 0.0f;
  turn_encoder_progress_deg = 0.0f;
  turn_fused_progress_deg = 0.0f;
  turn_sensor_disagreement_deg = 0.0f;
  turn_balance_error_mm = 0.0f;
  turn_center_translation_mm = 0.0f;
  turn_center_speed_mm_s = 0.0f;
  turn_balance_correction_tps = 0.0f;
  turn_fusion_selected_pair = 0;
  turn_last_heading_deg = robot_heading_deg;
  turn_accumulator_valid = true;

  last_yaw_error_deg = 0.0f;
  step_start_yaw_deg = stable_heading;
  step_end_yaw_deg = stable_heading;
  step_requested_yaw_delta_deg = 0.0f;
  step_actual_yaw_delta_deg = 0.0f;
  step_final_yaw_error_deg = 0.0f;
  step_end_heading_stable = heading_stable;
  step_heading_result = HEADING_RESULT_NONE;
  step_requested_distance_mm = 0.0f;
  step_left_distance_mm = 0.0f;
  step_right_distance_mm = 0.0f;
  step_actual_distance_mm = 0.0f;
  step_distance_error_mm = 0.0f;
  step_encoder_start_left_ticks = 0;
  step_encoder_start_right_ticks = 0;
  recovery_attempts_this_motion = 0;
  speed_derate = 1.0f;
  fault_reason = "";

  mode = MODE_IDLE;
  stopMotorsRaw();

  String out = "zero_pose: encoders reset, stable heading captured, heading=";
  out += String(robot_heading_deg, 2);
  out += " target_yaw=";
  out += String(target_yaw_deg, 2);

  return out;
}










bool resetImuReferenceForTurnInternal(float &stable_heading_out, String &reason_out) {
  stopMotorsRaw();

  have_last_imu_rate_sample = false;
  yaw_rate_deg_s = 0.0f;
  yaw_rate_valid = false;

  turn_unwrapped_progress_deg = 0.0f;
  turn_gyro_progress_deg = 0.0f;
  turn_encoder_progress_deg = 0.0f;
  turn_fused_progress_deg = 0.0f;
  turn_sensor_disagreement_deg = 0.0f;
  turn_balance_error_mm = 0.0f;
  turn_center_translation_mm = 0.0f;
  turn_center_speed_mm_s = 0.0f;
  turn_balance_correction_tps = 0.0f;
  turn_fusion_selected_pair = 0;
  turn_last_heading_deg = robot_heading_deg;
  turn_accumulator_valid = false;
  turn_wrong_way_counter = 0;
  rejected_turn_delta_samples = 0;

  float stable_heading = robot_heading_deg;

  if (!captureStableHeading(stable_heading)) {
    reason_out = "imu_heading_capture_failed";
    return false;
  }

  robot_heading_deg = stable_heading;
  target_yaw_deg = stable_heading;
  last_yaw_error_deg = 0.0f;

  turn_start_heading_deg = stable_heading;
  turn_requested_delta_deg = 0.0f;
  turn_abs_target_deg = 0.0f;
  turn_direction_sign = 1;
  turn_unwrapped_progress_deg = 0.0f;
  turn_gyro_progress_deg = 0.0f;
  turn_encoder_progress_deg = 0.0f;
  turn_fused_progress_deg = 0.0f;
  turn_sensor_disagreement_deg = 0.0f;
  turn_balance_error_mm = 0.0f;
  turn_center_translation_mm = 0.0f;
  turn_center_speed_mm_s = 0.0f;
  turn_balance_correction_tps = 0.0f;
  turn_fusion_selected_pair = 0;
  turn_last_heading_deg = stable_heading;
  turn_accumulator_valid = true;

  resetControllersKeepingTargets();
  clearCounters();

  stable_heading_out = stable_heading;
  reason_out = "";
  return true;
}

String reset_imu_reference() {
  float stable_heading = robot_heading_deg;
  String reason = "";

  if (!resetImuReferenceForTurnInternal(stable_heading, reason)) {
    return "reset_imu_reference: " + reason;
  }

  String out = "reset_imu_reference: heading=";
  out += String(stable_heading, 2);
  out += " target_yaw=";
  out += String(target_yaw_deg, 2);
  out += " yaw_rate_reset=1 turn_accumulator_reset=1";

  return out;
}

String settle_robot() {
  stopMotorsRaw();

  float stable_heading = robot_heading_deg;
  String reason = "";

  if (!resetImuReferenceForTurnInternal(stable_heading, reason)) {
    return "settle_robot: " + reason;
  }

  String out = "settle_robot: heading=";
  out += String(robot_heading_deg, 2);
  out += " target_yaw=";
  out += String(target_yaw_deg, 2);
  out += " imu_reference_reset=1";

  return out;
}

String stop_robot() {
  bool stopped_straight = mode == MODE_STRAIGHT;
  stopMotorsRaw();
  if (step_heading_result != HEADING_RESULT_RUNNING) {
    beginStepHeadingReference(robot_heading_deg, 0.0f);
  }
  closeAndRebaseStepHeading(HEADING_RESULT_STOPPED);
  mode = MODE_IDLE;
  fault_reason = "";
  clearMacro();

  
  long l = readLeftTicks();
  long r = readRightTicks();
  if (stopped_straight) {
    captureStepDistanceOutcome(l, r);
  }
  left_ctrl.target_ticks = l;
  right_ctrl.target_ticks = r;
  motion_start_left_ticks = l;
  motion_start_right_ticks = r;
  motion_left_delta_ticks = 0;
  motion_right_delta_ticks = 0;

  resetControllersKeepingTargets();
  clearCounters();

  motion_result_notify_code = 2;
  motion_result_notify_pending = true;

  return "stop_robot: OK";
}

String move_forward() {
  clearMacro();
  return startStraightDistance(CELL_DISTANCE_MM);
}

String move_backward() {
  clearMacro();
  return startStraightDistance(-CELL_DISTANCE_MM);
}




String move_relative_mm(String payload) {
  float distance_mm = 0.0f;
  if (!extractNumber(payload, "distance_mm", distance_mm)) {
    return "move_relative_mm: invalid_payload";
  }
  if (fabsf(distance_mm) < 2.0f || fabsf(distance_mm) > 100.0f) {
    return "move_relative_mm: outside_safe_range_2_to_100_mm";
  }
  clearMacro();
  return startStraightDistance(distance_mm);
}

String turn_relative_deg(String payload) {
  float degrees = 0.0f;
  if (!extractNumber(payload, "degrees", degrees)) {
    return "turn_relative_deg: invalid_payload";
  }
  if (fabsf(degrees) < 0.5f || fabsf(degrees) > 90.0f) {
    return "turn_relative_deg: outside_safe_range_0_5_to_90_deg";
  }
  clearMacro();
  return startTurnDegrees(degrees);
}

String move_left() {
  if (mode != MODE_IDLE) {
    return "busy";
  }

  macro_mode = MACRO_MOVE_LEFT;
  macro_step = 0;
  macro_next_step_ms = millis();

  return "move_left: queued turn_CCW_forward_turn_CW";
}

String move_right() {
  if (mode != MODE_IDLE) {
    return "busy";
  }

  macro_mode = MACRO_MOVE_RIGHT;
  macro_step = 0;
  macro_next_step_ms = millis();

  return "move_right: queued turn_CW_forward_turn_CCW";
}

String set_values(String payload) {
  int applied = 0;

  applied += applyFloatValue(payload, "CELL_DISTANCE_MM", CELL_DISTANCE_MM, 50.0f, 500.0f);

  
  
  applied += applyFloatValue(payload, "LEFT_TICKS_PER_MM",  LEFT_TICKS_PER_MM,  5.0f, 200.0f);
  applied += applyFloatValue(payload, "RIGHT_TICKS_PER_MM", RIGHT_TICKS_PER_MM, 5.0f, 200.0f);

  applied += applyFloatValue(payload, "LEFT_LINEAR_SCALE", LEFT_LINEAR_SCALE, 0.600f, 1.500f);
  applied += applyFloatValue(payload, "RIGHT_LINEAR_SCALE", RIGHT_LINEAR_SCALE, 0.600f, 1.500f);
  applied += applyFloatValue(payload, "FORWARD_DISTANCE_TICK_SCALE", FORWARD_DISTANCE_TICK_SCALE, 0.600f, 1.500f);
  applied += applyFloatValue(payload, "BACKWARD_DISTANCE_TICK_SCALE", BACKWARD_DISTANCE_TICK_SCALE, 0.600f, 1.500f);

  applied += applyFloatValue(payload, "TURN_LEFT_DEG_SCALE", TURN_LEFT_DEG_SCALE, 0.700f, 1.250f);
  applied += applyFloatValue(payload, "TURN_RIGHT_DEG_SCALE", TURN_RIGHT_DEG_SCALE, 0.700f, 1.250f);

  applied += applyFloatValue(payload, "KP_DISTANCE", KP_DISTANCE, 0.000f, 5.000f);
  applied += applyFloatValue(payload, "KP_YAW_STRAIGHT", KP_YAW_STRAIGHT, 0.000f, 100.000f);
  applied += applyFloatValue(payload, "KI_YAW_STRAIGHT", KI_YAW_STRAIGHT, 0.000f, 50.000f);
  applied += applyFloatValue(payload, "KD_YAW_STRAIGHT", KD_YAW_STRAIGHT, 0.000f, 50.000f);
  applied += applyFloatValue(payload, "MAX_YAW_CORRECTION_TPS", MAX_YAW_CORRECTION_TPS, 0.0f, 1500.0f);
  applied += applyFloatValue(payload, "YAW_INTEGRAL_LIMIT_TPS", YAW_INTEGRAL_LIMIT_TPS, 0.0f, 1000.0f);
  applied += applyFloatValue(payload, "STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM", STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM, 0.0f, 3.0f);
  applied += applyFloatValue(payload, "STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG", STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG, 0.0f, 30.0f);
  applied += applyFloatValue(payload, "YAW_RATE_FILTER_TAU_S", YAW_RATE_FILTER_TAU_S, 0.001f, 1.0f);
  applied += applyFloatValue(payload, "KP_TURN_YAW", KP_TURN_YAW, 0.000f, 40.000f);
  applied += applyFloatValue(payload, "KI_TURN_YAW", KI_TURN_YAW, 0.000f, 20.000f);
  applied += applyFloatValue(payload, "KD_TURN_YAW", KD_TURN_YAW, 0.000f, 20.000f);
  applied += applyFloatValue(payload, "TURN_BALANCE_KP_TPS_PER_MM", TURN_BALANCE_KP_TPS_PER_MM, 0.000f, 20.000f);
  applied += applyFloatValue(payload, "TURN_CENTER_SPEED_KP_TPS_PER_MM_S", TURN_CENTER_SPEED_KP_TPS_PER_MM_S, 0.000f, 100.000f);
  applied += applyFloatValue(payload, "MAX_TURN_BALANCE_TPS", MAX_TURN_BALANCE_TPS, 0.000f, 500.000f);

  applied += applyFloatValue(payload, "RIGHT_STRAIGHT_BIAS_TPS", RIGHT_STRAIGHT_BIAS_TPS, -400.0f, 600.0f);
  applied += applyFloatValue(payload, "LEFT_STRAIGHT_SOFTEN_TPS", LEFT_STRAIGHT_SOFTEN_TPS, -200.0f, 400.0f);
  applied += applyFloatValue(payload, "RIGHT_TRACK_SLIP_BOOST_TPS", RIGHT_TRACK_SLIP_BOOST_TPS, 0.0f, 800.0f);
  applied += applyFloatValue(payload, "MAX_RIGHT_SLIP_BOOST_TPS", MAX_RIGHT_SLIP_BOOST_TPS, 0.0f, 800.0f);

  applied += applyIntValue(payload, "LEFT_PWM_MIN", LEFT_PWM_MIN, 0, 255);
  applied += applyIntValue(payload, "RIGHT_PWM_MIN", RIGHT_PWM_MIN, 0, 255);
  applied += applyIntValue(payload, "LEFT_PWM_MAX", LEFT_PWM_MAX, 0, 255);
  applied += applyIntValue(payload, "RIGHT_PWM_MAX", RIGHT_PWM_MAX, 0, 255);
  applied += applyIntValue(payload, "ABSOLUTE_PWM_MIN", ABSOLUTE_PWM_MIN, 0, 255);

  applied += applyFloatValue(payload, "LEFT_KP_SPEED", LEFT_KP_SPEED, 0.000f, 1.000f);
  applied += applyFloatValue(payload, "LEFT_KI_SPEED", LEFT_KI_SPEED, 0.000f, 0.500f);
  applied += applyFloatValue(payload, "LEFT_KD_SPEED", LEFT_KD_SPEED, 0.000f, 0.500f);
  applied += applyFloatValue(payload, "LEFT_KFF_SPEED", LEFT_KFF_SPEED, 0.000f, 0.500f);

  applied += applyFloatValue(payload, "RIGHT_KP_SPEED", RIGHT_KP_SPEED, 0.000f, 1.000f);
  applied += applyFloatValue(payload, "RIGHT_KI_SPEED", RIGHT_KI_SPEED, 0.000f, 0.500f);
  applied += applyFloatValue(payload, "RIGHT_KD_SPEED", RIGHT_KD_SPEED, 0.000f, 0.500f);
  applied += applyFloatValue(payload, "RIGHT_KFF_SPEED", RIGHT_KFF_SPEED, 0.000f, 0.500f);

  applied += applyFloatValue(payload, "MAX_STRAIGHT_SPEED_TPS_BASE", MAX_STRAIGHT_SPEED_TPS_BASE, 100.0f, 3000.0f);
  applied += applyFloatValue(payload, "MAX_TURN_SPEED_TPS_BASE", MAX_TURN_SPEED_TPS_BASE, 100.0f, 2500.0f);

  applied += applyFloatValue(payload, "MIN_STRAIGHT_SPEED_TPS", MIN_STRAIGHT_SPEED_TPS, 0.0f, 1000.0f);
  applied += applyFloatValue(payload, "MIN_TURN_SPEED_TPS", MIN_TURN_SPEED_TPS, 0.0f, 1000.0f);

  applied += applyFloatValue(payload, "ENDPOINT_MIN_STRAIGHT_SPEED_TPS", ENDPOINT_MIN_STRAIGHT_SPEED_TPS, 0.0f, 500.0f);
  applied += applyFloatValue(payload, "ENDPOINT_MIN_TURN_SPEED_TPS", ENDPOINT_MIN_TURN_SPEED_TPS, 0.0f, 500.0f);

  applied += applyFloatValue(payload, "INTEGRAL_LIMIT", INTEGRAL_LIMIT, 0.0f, 1000.0f);
  applied += applyFloatValue(payload, "SPEED_FILTER_TAU_S", SPEED_FILTER_TAU_S, 0.0f, 1.0f);
  applied += applyFloatValue(payload, "DERIVATIVE_FILTER_TAU_S", DERIVATIVE_FILTER_TAU_S, 0.0f, 1.0f);
  applied += applyFloatValue(payload, "TURN_STOP_RATE_TOLERANCE_DPS", TURN_STOP_RATE_TOLERANCE_DPS, 0.1f, 50.0f);
  applied += applyIntValue(payload, "TURN_SETTLE_COUNT_REQUIRED", TURN_SETTLE_COUNT_REQUIRED, 1, 100);
  applied += applyFloatValue(payload, "STRAIGHT_FINAL_YAW_TOLERANCE_DEG", STRAIGHT_FINAL_YAW_TOLERANCE_DEG, 0.1f, 10.0f);
  applied += applyFloatValue(payload, "STRAIGHT_FINAL_MIN_CORRECTION_TPS", STRAIGHT_FINAL_MIN_CORRECTION_TPS, 0.0f, 500.0f);
  applied += applyIntValue(payload, "STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED", STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED, 1, 100);

  applied += applyFloatValue(payload, "PROGRESS_BALANCE_GAIN_TPS", PROGRESS_BALANCE_GAIN_TPS, 0.0f, 500.0f);
  applied += applyFloatValue(payload, "MAX_PROGRESS_BALANCE_TPS", MAX_PROGRESS_BALANCE_TPS, 0.0f, 500.0f);
  applied += applyFloatValue(payload, "PROGRESS_BALANCE_YAW_GATE_DEG", PROGRESS_BALANCE_YAW_GATE_DEG, 0.0f, 30.0f);

  applied += applyLongValue(payload, "POSITION_TOLERANCE_TICKS", POSITION_TOLERANCE_TICKS, 10, 2000);
  applied += applyLongValue(payload, "POSITION_COMMAND_DEADBAND_TICKS", POSITION_COMMAND_DEADBAND_TICKS, 10, 2000);
  applied += applyLongValue(payload, "BIAS_DISABLE_REMAINING_TICKS", BIAS_DISABLE_REMAINING_TICKS, 10, 5000);

  applied += applyFloatValue(payload, "SPEED_STOP_TOLERANCE_TPS", SPEED_STOP_TOLERANCE_TPS, 0.0f, 1000.0f);

  applied += applyFloatValue(payload, "TURN_TOLERANCE_DEG", TURN_TOLERANCE_DEG, 0.2f, 20.0f);
  applied += applyLongValue(payload, "TURN_ENCODER_TOLERANCE_TICKS", TURN_ENCODER_TOLERANCE_TICKS, 10, 3000);

  applied += applyFloatValue(payload, "YAW_IGNORE_DEG", YAW_IGNORE_DEG, 0.0f, 10.0f);

  applied += applyFloatValue(payload, "PROGRESS_SLIP_THRESHOLD", PROGRESS_SLIP_THRESHOLD, 0.05f, 2.0f);
  applied += applyFloatValue(payload, "STRAIGHT_YAW_SLIP_THRESHOLD_DEG", STRAIGHT_YAW_SLIP_THRESHOLD_DEG, 5.0f, 90.0f);
  applied += applyFloatValue(payload, "STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS", STRAIGHT_YAW_RATE_SLIP_THRESHOLD_DPS, 10.0f, 500.0f);
  applied += applyIntValue(payload, "SLIP_COUNT_LIMIT", SLIP_COUNT_LIMIT, 1, 100);

  applied += applyFloatValue(payload, "TURN_WRONG_WAY_DEG", TURN_WRONG_WAY_DEG, 1.0f, 45.0f);
  applied += applyIntValue(payload, "TURN_WRONG_WAY_COUNT_LIMIT", TURN_WRONG_WAY_COUNT_LIMIT, 1, 100);

  applied += applyFloatValue(payload, "MAX_VALID_YAW_RATE_DPS", MAX_VALID_YAW_RATE_DPS, 50.0f, 2000.0f);
  applied += applyFloatValue(payload, "MAX_VALID_TURN_DELTA_DEG_PER_SAMPLE", MAX_VALID_TURN_DELTA_DEG_PER_SAMPLE, 5.0f, 120.0f);
  applied += applyFloatValue(payload, "MAX_VALID_HEADING_JUMP_DEG", MAX_VALID_HEADING_JUMP_DEG, 5.0f, 120.0f);

  applied += applyIntValue(payload, "STALL_PWM_THRESHOLD", STALL_PWM_THRESHOLD, 0, 255);
  applied += applyFloatValue(payload, "STALL_TARGET_SPEED_TPS", STALL_TARGET_SPEED_TPS, 0.0f, 1000.0f);
  applied += applyFloatValue(payload, "STALL_MEASURED_SPEED_TPS", STALL_MEASURED_SPEED_TPS, 0.0f, 500.0f);
  applied += applyIntValue(payload, "STALL_COUNT_LIMIT", STALL_COUNT_LIMIT, 1, 100);

  applied += applyIntValue(payload, "MAX_RECOVERY_ATTEMPTS_PER_MOTION", MAX_RECOVERY_ATTEMPTS_PER_MOTION, 0, 20);

  applied += applyULongValue(payload, "RECOVERY_STOP_MS", RECOVERY_STOP_MS, 0, 2000);
  applied += applyULongValue(payload, "RECOVERY_PULSE_MS", RECOVERY_PULSE_MS, 0, 2000);
  applied += applyULongValue(payload, "RECOVERY_SETTLE_MS", RECOVERY_SETTLE_MS, 0, 2000);

  applied += applyIntValue(payload, "RECOVERY_PWM_LEFT", RECOVERY_PWM_LEFT, 0, 255);
  applied += applyIntValue(payload, "RECOVERY_PWM_RIGHT", RECOVERY_PWM_RIGHT, 0, 255);

  applied += applyFloatValue(payload, "RECOVERY_DERATE_FACTOR", RECOVERY_DERATE_FACTOR, 0.10f, 1.00f);
  applied += applyFloatValue(payload, "MIN_SPEED_DERATE", MIN_SPEED_DERATE, 0.10f, 1.00f);

  applied += applyIntValue(payload, "IMU_YAW_SIGN", IMU_YAW_SIGN, -1, 1);
  applied += applyIntValue(payload, "TURN_CONTROL_SIGN", TURN_CONTROL_SIGN, -1, 1);
  applied += applyIntValue(payload, "YAW_CORRECTION_SIGN", YAW_CORRECTION_SIGN, -1, 1);

  if (applied > 0) {
    tune_version++;
  }

  String out = "set_values: applied=";
  out += String(applied);
  out += " tune_version=";
  out += String(tune_version);

  return out;
}

String get_state() {
  updatePlanarOdometry();
  long l = readLeftTicks();
  long r = readRightTicks();

  long left_error = left_ctrl.target_ticks - l;
  long right_error = right_ctrl.target_ticks - r;

  float left_progress = progressFraction(l, motion_start_left_ticks, motion_left_delta_ticks);
  float right_progress = progressFraction(r, motion_start_right_ticks, motion_right_delta_ticks);

  float turn_signed_progress = turn_fused_progress_deg * (float)turn_direction_sign;
  float turn_remaining = turn_abs_target_deg - turn_signed_progress;
  float straight_distance_scale = step_requested_distance_mm < 0.0f
    ? BACKWARD_DISTANCE_TICK_SCALE : FORWARD_DISTANCE_TICK_SCALE;
  float left_distance_mm = ((float)l) /
    (LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE * straight_distance_scale);
  float right_distance_mm = ((float)r) /
    (RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE * straight_distance_scale);
  float average_distance_mm = 0.5f * (left_distance_mm + right_distance_mm);
  float pose_heading_deg = yaw_valid
    ? wrapAngleDeg(robot_heading_deg - pose_heading_origin_deg)
    : 0.0f;
  unsigned long now_ms = millis();
  unsigned long rotation_age_ms = last_rotation_ms == 0
    ? 0xFFFFFFFFUL : now_ms - last_rotation_ms;
  unsigned long gyro_age_ms = last_gyro_ms == 0
    ? 0xFFFFFFFFUL : now_ms - last_gyro_ms;

  String out = "{";

  out += "\"mode\":";
  if (mode == MODE_IDLE) out += "\"IDLE\"";
  else if (mode == MODE_STRAIGHT) out += "\"STRAIGHT\"";
  else if (mode == MODE_TURN_IMU) out += "\"TURN_IMU\"";
  else if (mode == MODE_TURN_ENCODER) out += "\"TURN_ENCODER\"";
  else if (mode == MODE_SPEED_TEST) out += "\"SPEED_TEST\"";
  else if (mode == MODE_RECOVERY) out += "\"RECOVERY\"";
  else if (mode == MODE_FAULT) out += "\"FAULT\"";

  out += ",\"macro_mode\":\"";
  out += macroName();
  out += "\"";

  out += ",\"macro_step\":";
  out += String(macro_step);

  out += ",\"fault_reason\":\"";
  out += fault_reason;
  out += "\"";

  out += ",\"left_ticks\":";
  out += String(l);

  out += ",\"right_ticks\":";
  out += String(r);

  out += ",\"left_distance_mm\":";
  out += String(left_distance_mm, 3);
  out += ",\"right_distance_mm\":";
  out += String(right_distance_mm, 3);
  out += ",\"average_distance_mm\":";
  out += String(average_distance_mm, 3);

  out += ",\"pose_x_mm\":";
  out += String(pose_x_mm, 3);
  out += ",\"pose_y_mm\":";
  out += String(pose_y_mm, 3);
  out += ",\"pose_distance_mm\":";
  out += String(pose_distance_mm, 3);
  out += ",\"straight_cross_track_error_mm\":";
  out += String(straight_cross_track_error_mm, 3);
  out += ",\"straight_path_heading_offset_deg\":";
  out += String(straight_path_heading_offset_deg, 3);
  out += ",\"pose_heading_deg\":";
  out += String(pose_heading_deg, 3);

  out += ",\"left_target\":";
  out += String(left_ctrl.target_ticks);

  out += ",\"right_target\":";
  out += String(right_ctrl.target_ticks);

  out += ",\"left_error\":";
  out += String(left_error);

  out += ",\"right_error\":";
  out += String(right_error);

  out += ",\"left_progress\":";
  out += String(left_progress, 4);

  out += ",\"right_progress\":";
  out += String(right_progress, 4);

  out += ",\"progress_diff\":";
  out += String(left_progress - right_progress, 4);

  out += ",\"left_speed_tps\":";
  out += String(left_ctrl.measured_speed_tps, 1);

  out += ",\"right_speed_tps\":";
  out += String(right_ctrl.measured_speed_tps, 1);

  out += ",\"left_raw_speed_tps\":";
  out += String(left_ctrl.raw_speed_tps, 1);

  out += ",\"right_raw_speed_tps\":";
  out += String(right_ctrl.raw_speed_tps, 1);

  out += ",\"left_target_speed_tps\":";
  out += String(left_ctrl.target_speed_tps, 1);

  out += ",\"right_target_speed_tps\":";
  out += String(right_ctrl.target_speed_tps, 1);

  out += ",\"left_pwm\":";
  out += String(left_ctrl.pwm);

  out += ",\"right_pwm\":";
  out += String(right_ctrl.pwm);

  out += ",\"left_ff_term\":";
  out += String(left_ctrl.ff_term, 3);
  out += ",\"left_p_term\":";
  out += String(left_ctrl.p_term, 3);
  out += ",\"left_i_term\":";
  out += String(left_ctrl.i_term, 3);
  out += ",\"left_d_term\":";
  out += String(left_ctrl.d_term, 3);
  out += ",\"left_unsaturated_pwm\":";
  out += String(left_ctrl.unsaturated_pwm, 3);
  out += ",\"left_saturated\":";
  out += left_ctrl.saturated ? "true" : "false";

  out += ",\"right_ff_term\":";
  out += String(right_ctrl.ff_term, 3);
  out += ",\"right_p_term\":";
  out += String(right_ctrl.p_term, 3);
  out += ",\"right_i_term\":";
  out += String(right_ctrl.i_term, 3);
  out += ",\"right_d_term\":";
  out += String(right_ctrl.d_term, 3);
  out += ",\"right_unsaturated_pwm\":";
  out += String(right_ctrl.unsaturated_pwm, 3);
  out += ",\"right_saturated\":";
  out += right_ctrl.saturated ? "true" : "false";

  out += ",\"straight_heading_p_tps\":";
  out += String(straight_heading_ctrl.p_term_tps, 3);
  out += ",\"straight_heading_i_tps\":";
  out += String(straight_heading_ctrl.i_term_tps, 3);
  out += ",\"straight_heading_d_tps\":";
  out += String(straight_heading_ctrl.d_term_tps, 3);
  out += ",\"straight_heading_correction_tps\":";
  out += String(straight_heading_ctrl.correction_tps, 3);
  out += ",\"turn_heading_p_tps\":";
  out += String(turn_heading_ctrl.p_term_tps, 3);
  out += ",\"turn_heading_i_tps\":";
  out += String(turn_heading_ctrl.i_term_tps, 3);
  out += ",\"turn_heading_d_tps\":";
  out += String(turn_heading_ctrl.d_term_tps, 3);
  out += ",\"turn_heading_correction_tps\":";
  out += String(turn_heading_ctrl.correction_tps, 3);

  out += ",\"raw_imu_yaw_deg\":";
  out += String(raw_imu_yaw_deg, 2);

  out += ",\"robot_heading_deg\":";
  out += String(robot_heading_deg, 2);

  out += ",\"target_yaw_deg\":";
  out += String(target_yaw_deg, 2);

  out += ",\"yaw_error_deg\":";
  out += String(last_yaw_error_deg, 2);

  out += ",\"step_heading_result\":\"";
  out += stepHeadingResultName();
  out += "\"";
  out += ",\"step_start_yaw_deg\":";
  out += String(step_start_yaw_deg, 2);
  out += ",\"step_end_yaw_deg\":";
  out += String(step_end_yaw_deg, 2);
  out += ",\"step_requested_yaw_delta_deg\":";
  out += String(step_requested_yaw_delta_deg, 2);
  out += ",\"step_actual_yaw_delta_deg\":";
  out += String(step_actual_yaw_delta_deg, 2);
  out += ",\"step_final_yaw_error_deg\":";
  out += String(step_final_yaw_error_deg, 2);
  out += ",\"step_requested_distance_mm\":";
  out += String(step_requested_distance_mm, 3);
  out += ",\"step_left_distance_mm\":";
  out += String(step_left_distance_mm, 3);
  out += ",\"step_right_distance_mm\":";
  out += String(step_right_distance_mm, 3);
  out += ",\"step_actual_distance_mm\":";
  out += String(step_actual_distance_mm, 3);
  out += ",\"step_distance_error_mm\":";
  out += String(step_distance_error_mm, 3);
  out += ",\"step_end_heading_stable\":";
  out += step_end_heading_stable ? "true" : "false";

  out += ",\"yaw_rate_deg_s\":";
  out += String(yaw_rate_deg_s, 2);

  out += ",\"yaw_valid\":";
  out += yaw_valid ? "true" : "false";

  out += ",\"yaw_rate_valid\":";
  out += yaw_rate_valid ? "true" : "false";

  out += ",\"imu_rotation_age_ms\":";
  out += String(rotation_age_ms);
  out += ",\"imu_gyro_age_ms\":";
  out += String(gyro_age_ms);
  out += ",\"imu_rotation_accuracy\":";
  out += String(imu_rotation_accuracy);
  out += ",\"imu_heading_accuracy_rad\":";
  out += String(imu_heading_accuracy_rad, 5);

  out += ",\"rejected_yaw_rate_samples\":";
  out += String(rejected_yaw_rate_samples);

  out += ",\"rejected_heading_jump_samples\":";
  out += String(rejected_heading_jump_samples);

  out += ",\"rejected_quaternion_samples\":";
  out += String(rejected_quaternion_samples);

  out += ",\"turn_start_heading_deg\":";
  out += String(turn_start_heading_deg, 2);

  out += ",\"turn_requested_delta_deg\":";
  out += String(turn_requested_delta_deg, 2);

  out += ",\"turn_abs_target_deg\":";
  out += String(turn_abs_target_deg, 2);

  out += ",\"turn_direction_sign\":";
  out += String(turn_direction_sign);

  out += ",\"turn_unwrapped_progress_deg\":";
  out += String(turn_unwrapped_progress_deg, 2);

  out += ",\"turn_gyro_progress_deg\":";
  out += String(turn_gyro_progress_deg, 2);

  out += ",\"turn_encoder_progress_deg\":";
  out += String(turn_encoder_progress_deg, 2);

  out += ",\"turn_fused_progress_deg\":";
  out += String(turn_fused_progress_deg, 2);

  out += ",\"turn_sensor_disagreement_deg\":";
  out += String(turn_sensor_disagreement_deg, 2);
  out += ",\"turn_fusion_selected_pair\":";
  out += String(turn_fusion_selected_pair);
  out += ",\"turn_balance_error_mm\":";
  out += String(turn_balance_error_mm, 2);
  out += ",\"turn_center_translation_mm\":";
  out += String(turn_center_translation_mm, 2);
  out += ",\"turn_center_speed_mm_s\":";
  out += String(turn_center_speed_mm_s, 2);
  out += ",\"turn_balance_correction_tps\":";
  out += String(turn_balance_correction_tps, 2);

  out += ",\"turn_signed_progress_deg\":";
  out += String(turn_signed_progress, 2);

  out += ",\"turn_remaining_deg\":";
  out += String(turn_remaining, 2);

  out += ",\"turn_wrong_way_counter\":";
  out += String(turn_wrong_way_counter);

  out += ",\"rejected_turn_delta_samples\":";
  out += String(rejected_turn_delta_samples);

  out += ",\"ina_ok\":";
  out += ina_ok ? "true" : "false";

  out += ",\"bno_ok\":";
  out += bno_ok ? "true" : "false";

  out += ",\"imu_ax\":";
  out += String(imu_ax, 4);
  out += ",\"imu_ay\":";
  out += String(imu_ay, 4);
  out += ",\"imu_az\":";
  out += String(imu_az, 4);
  out += ",\"imu_gx\":";
  out += String(imu_gx, 4);
  out += ",\"imu_gy\":";
  out += String(imu_gy, 4);
  out += ",\"imu_gz\":";
  out += String(imu_gz, 4);

  out += ",\"battery_v\":";
  out += String(battery_source_v, 3);

  out += ",\"battery_percent_est\":";
  out += String(battery_percent_est, 1);

  out += ",\"current_ma\":";
  out += String(battery_current_ma, 1);

  out += ",\"power_mw\":";
  out += String(battery_power_mw, 1);

  out += ",\"bno_samples\":";
  out += String(bno_samples);
  out += ",\"bno_empty_polls\":";
  out += String(bno_empty_polls);
  out += ",\"bno_short_reads\":";
  out += String(bno_short_reads);
  out += ",\"bno_budget_hits\":";
  out += String(bno_budget_hits);

  out += ",\"left_stall_counter\":";
  out += String(left_stall_counter);

  out += ",\"right_stall_counter\":";
  out += String(right_stall_counter);

  out += ",\"slip_counter\":";
  out += String(slip_counter);

  out += ",\"recovery_attempts\":";
  out += String(recovery_attempts_this_motion);

  out += ",\"recovery_side\":";
  out += String(recovery_side);

  out += ",\"speed_derate\":";
  out += String(speed_derate, 3);

  out += ",\"tune_version\":";
  out += String(tune_version);

  out += ",\"control_period_ms\":";
  out += String(CONTROL_PERIOD_MS);
  out += ",\"last_control_dt_ms\":";
  out += String(last_control_dt_ms, 2);
  out += ",\"max_control_dt_ms\":";
  out += String(max_control_dt_ms, 2);
  out += ",\"control_deadline_misses\":";
  out += String(control_deadline_misses);
  out += ",\"straight_endpoint_aligning\":";
  out += straight_endpoint_aligning ? "true" : "false";

  out += ",\"speed_test_left_tps\":";
  out += String(speed_test_left_tps, 1);
  out += ",\"speed_test_right_tps\":";
  out += String(speed_test_right_tps, 1);

  out += ",\"CELL_DISTANCE_MM\":";
  out += String(CELL_DISTANCE_MM, 2);

  
  out += ",\"LEFT_TICKS_PER_REV\":";
  out += String(LEFT_TICKS_PER_REV, 1);
  out += ",\"RIGHT_TICKS_PER_REV\":";
  out += String(RIGHT_TICKS_PER_REV, 1);

  out += ",\"LEFT_TICKS_PER_MM\":";
  out += String(LEFT_TICKS_PER_MM, 5);

  out += ",\"RIGHT_TICKS_PER_MM\":";
  out += String(RIGHT_TICKS_PER_MM, 5);

  out += ",\"LEFT_LINEAR_SCALE\":";
  out += String(LEFT_LINEAR_SCALE, 4);

  out += ",\"RIGHT_LINEAR_SCALE\":";
  out += String(RIGHT_LINEAR_SCALE, 4);

  out += ",\"FORWARD_DISTANCE_TICK_SCALE\":";
  out += String(FORWARD_DISTANCE_TICK_SCALE, 6);

  out += ",\"BACKWARD_DISTANCE_TICK_SCALE\":";
  out += String(BACKWARD_DISTANCE_TICK_SCALE, 6);

  out += ",\"TURN_LEFT_DEG_SCALE\":";
  out += String(TURN_LEFT_DEG_SCALE, 4);

  out += ",\"TURN_RIGHT_DEG_SCALE\":";
  out += String(TURN_RIGHT_DEG_SCALE, 4);

  out += ",\"left_cell_ticks\":";
  out += String(ticksForLeftDistance(CELL_DISTANCE_MM));

  out += ",\"right_cell_ticks\":";
  out += String(ticksForRightDistance(CELL_DISTANCE_MM));

  out += ",\"LEFT_PWM_MIN\":";
  out += String(LEFT_PWM_MIN);

  out += ",\"RIGHT_PWM_MIN\":";
  out += String(RIGHT_PWM_MIN);

  out += ",\"LEFT_PWM_MAX\":";
  out += String(LEFT_PWM_MAX);

  out += ",\"RIGHT_PWM_MAX\":";
  out += String(RIGHT_PWM_MAX);

  out += ",\"LEFT_KP_SPEED\":";
  out += String(LEFT_KP_SPEED, 4);

  out += ",\"LEFT_KI_SPEED\":";
  out += String(LEFT_KI_SPEED, 4);

  out += ",\"LEFT_KD_SPEED\":";
  out += String(LEFT_KD_SPEED, 4);

  out += ",\"LEFT_KFF_SPEED\":";
  out += String(LEFT_KFF_SPEED, 4);

  out += ",\"RIGHT_KP_SPEED\":";
  out += String(RIGHT_KP_SPEED, 4);

  out += ",\"RIGHT_KI_SPEED\":";
  out += String(RIGHT_KI_SPEED, 4);

  out += ",\"RIGHT_KD_SPEED\":";
  out += String(RIGHT_KD_SPEED, 4);

  out += ",\"RIGHT_KFF_SPEED\":";
  out += String(RIGHT_KFF_SPEED, 4);

  out += ",\"SPEED_FILTER_TAU_S\":";
  out += String(SPEED_FILTER_TAU_S, 4);

  out += ",\"DERIVATIVE_FILTER_TAU_S\":";
  out += String(DERIVATIVE_FILTER_TAU_S, 4);

  out += ",\"TURN_STOP_RATE_TOLERANCE_DPS\":";
  out += String(TURN_STOP_RATE_TOLERANCE_DPS, 3);

  out += ",\"TURN_SETTLE_COUNT_REQUIRED\":";
  out += String(TURN_SETTLE_COUNT_REQUIRED);
  out += ",\"STRAIGHT_FINAL_YAW_TOLERANCE_DEG\":";
  out += String(STRAIGHT_FINAL_YAW_TOLERANCE_DEG, 3);
  out += ",\"STRAIGHT_FINAL_MIN_CORRECTION_TPS\":";
  out += String(STRAIGHT_FINAL_MIN_CORRECTION_TPS, 2);
  out += ",\"STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED\":";
  out += String(STRAIGHT_FINAL_SETTLE_COUNT_REQUIRED);

  out += ",\"KP_DISTANCE\":";
  out += String(KP_DISTANCE, 4);

  out += ",\"KP_YAW_STRAIGHT\":";
  out += String(KP_YAW_STRAIGHT, 4);

  out += ",\"KI_YAW_STRAIGHT\":";
  out += String(KI_YAW_STRAIGHT, 4);

  out += ",\"KD_YAW_STRAIGHT\":";
  out += String(KD_YAW_STRAIGHT, 4);

  out += ",\"MAX_YAW_CORRECTION_TPS\":";
  out += String(MAX_YAW_CORRECTION_TPS, 2);
  out += ",\"STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM\":";
  out += String(STRAIGHT_CROSS_TRACK_KP_DEG_PER_MM, 4);
  out += ",\"STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG\":";
  out += String(STRAIGHT_CROSS_TRACK_MAX_HEADING_DEG, 2);

  out += ",\"YAW_INTEGRAL_LIMIT_TPS\":";
  out += String(YAW_INTEGRAL_LIMIT_TPS, 2);

  out += ",\"YAW_RATE_FILTER_TAU_S\":";
  out += String(YAW_RATE_FILTER_TAU_S, 4);

  out += ",\"KP_TURN_YAW\":";
  out += String(KP_TURN_YAW, 4);

  out += ",\"KI_TURN_YAW\":";
  out += String(KI_TURN_YAW, 4);

  out += ",\"KD_TURN_YAW\":";
  out += String(KD_TURN_YAW, 4);
  out += ",\"TURN_BALANCE_KP_TPS_PER_MM\":";
  out += String(TURN_BALANCE_KP_TPS_PER_MM, 4);
  out += ",\"TURN_CENTER_SPEED_KP_TPS_PER_MM_S\":";
  out += String(TURN_CENTER_SPEED_KP_TPS_PER_MM_S, 4);
  out += ",\"MAX_TURN_BALANCE_TPS\":";
  out += String(MAX_TURN_BALANCE_TPS, 2);

  out += ",\"MAX_STRAIGHT_SPEED_TPS_BASE\":";
  out += String(MAX_STRAIGHT_SPEED_TPS_BASE, 2);

  out += ",\"MAX_TURN_SPEED_TPS_BASE\":";
  out += String(MAX_TURN_SPEED_TPS_BASE, 2);

  out += ",\"RIGHT_STRAIGHT_BIAS_TPS\":";
  out += String(RIGHT_STRAIGHT_BIAS_TPS, 2);

  out += ",\"LEFT_STRAIGHT_SOFTEN_TPS\":";
  out += String(LEFT_STRAIGHT_SOFTEN_TPS, 2);

  out += ",\"RIGHT_TRACK_SLIP_BOOST_TPS\":";
  out += String(RIGHT_TRACK_SLIP_BOOST_TPS, 2);

  out += ",\"MAX_RIGHT_SLIP_BOOST_TPS\":";
  out += String(MAX_RIGHT_SLIP_BOOST_TPS, 2);

  out += ",\"MAX_RECOVERY_ATTEMPTS_PER_MOTION\":";
  out += String(MAX_RECOVERY_ATTEMPTS_PER_MOTION);

  out += ",\"MAX_VALID_HEADING_JUMP_DEG\":";
  out += String(MAX_VALID_HEADING_JUMP_DEG, 2);

  out += ",\"LEFT_MOTOR_SIGN\":";
  out += String(LEFT_MOTOR_SIGN);

  out += ",\"RIGHT_MOTOR_SIGN\":";
  out += String(RIGHT_MOTOR_SIGN);

  out += ",\"LEFT_ENCODER_SIGN\":";
  out += String(LEFT_ENCODER_SIGN);

  out += ",\"RIGHT_ENCODER_SIGN\":";
  out += String(RIGHT_ENCODER_SIGN);

  out += ",\"IMU_YAW_SIGN\":";
  out += String(IMU_YAW_SIGN);

  out += ",\"TURN_CONTROL_SIGN\":";
  out += String(TURN_CONTROL_SIGN);

  out += ",\"YAW_CORRECTION_SIGN\":";
  out += String(YAW_CORRECTION_SIGN);

  out += "}";

  return out;
}





String get_motion_state() {
  long l = readLeftTicks();
  long r = readRightTicks();
  float straight_distance_scale = step_requested_distance_mm < 0.0f
    ? BACKWARD_DISTANCE_TICK_SCALE : FORWARD_DISTANCE_TICK_SCALE;
  float left_distance_mm = ((float)l) /
    (LEFT_TICKS_PER_MM * LEFT_LINEAR_SCALE * straight_distance_scale);
  float right_distance_mm = ((float)r) /
    (RIGHT_TICKS_PER_MM * RIGHT_LINEAR_SCALE * straight_distance_scale);
  float pose_heading_deg = yaw_valid
    ? wrapAngleDeg(robot_heading_deg - pose_heading_origin_deg)
    : pose_last_heading_deg;
  unsigned long now_ms = millis();
  unsigned long rotation_age_ms = last_rotation_ms == 0
    ? 0xFFFFFFFFUL : now_ms - last_rotation_ms;
  unsigned long gyro_age_ms = last_gyro_ms == 0
    ? 0xFFFFFFFFUL : now_ms - last_gyro_ms;

  String out;
  out.reserve(2300);
  out += "{\"mode\":\"";
  if (mode == MODE_IDLE) out += "IDLE";
  else if (mode == MODE_STRAIGHT) out += "STRAIGHT";
  else if (mode == MODE_TURN_IMU) out += "TURN_IMU";
  else if (mode == MODE_TURN_ENCODER) out += "TURN_ENCODER";
  else if (mode == MODE_SPEED_TEST) out += "SPEED_TEST";
  else if (mode == MODE_RECOVERY) out += "RECOVERY";
  else if (mode == MODE_FAULT) out += "FAULT";
  out += "\",\"macro_mode\":\"";
  out += macroName();
  out += "\",\"fault_reason\":\"";
  out += fault_reason;
  out += "\",\"left_ticks\":"; out += String(l);
  out += ",\"right_ticks\":"; out += String(r);
  out += ",\"left_target\":"; out += String(left_ctrl.target_ticks);
  out += ",\"right_target\":"; out += String(right_ctrl.target_ticks);
  out += ",\"left_distance_mm\":"; out += String(left_distance_mm, 2);
  out += ",\"right_distance_mm\":"; out += String(right_distance_mm, 2);
  out += ",\"average_distance_mm\":";
  out += String(0.5f * (left_distance_mm + right_distance_mm), 2);
  out += ",\"pose_x_mm\":"; out += String(pose_x_mm, 2);
  out += ",\"pose_y_mm\":"; out += String(pose_y_mm, 2);
  out += ",\"pose_distance_mm\":"; out += String(pose_distance_mm, 2);
  out += ",\"pose_heading_deg\":"; out += String(pose_heading_deg, 2);
  out += ",\"straight_cross_track_error_mm\":";
  out += String(straight_cross_track_error_mm, 2);
  out += ",\"straight_path_heading_offset_deg\":";
  out += String(straight_path_heading_offset_deg, 2);
  out += ",\"left_speed_tps\":"; out += String(left_ctrl.measured_speed_tps, 1);
  out += ",\"right_speed_tps\":"; out += String(right_ctrl.measured_speed_tps, 1);
  out += ",\"left_target_speed_tps\":"; out += String(left_ctrl.target_speed_tps, 1);
  out += ",\"right_target_speed_tps\":"; out += String(right_ctrl.target_speed_tps, 1);
  out += ",\"left_pwm\":"; out += String(left_ctrl.pwm);
  out += ",\"right_pwm\":"; out += String(right_ctrl.pwm);
  out += ",\"straight_heading_correction_tps\":";
  out += String(straight_heading_ctrl.correction_tps, 2);
  out += ",\"turn_heading_correction_tps\":";
  out += String(turn_heading_ctrl.correction_tps, 2);
  out += ",\"robot_heading_deg\":"; out += String(robot_heading_deg, 2);
  out += ",\"target_yaw_deg\":"; out += String(target_yaw_deg, 2);
  out += ",\"yaw_error_deg\":"; out += String(last_yaw_error_deg, 2);
  out += ",\"step_heading_result\":\"";
  out += stepHeadingResultName(); out += "\"";
  out += ",\"step_start_yaw_deg\":"; out += String(step_start_yaw_deg, 2);
  out += ",\"step_end_yaw_deg\":"; out += String(step_end_yaw_deg, 2);
  out += ",\"step_requested_yaw_delta_deg\":";
  out += String(step_requested_yaw_delta_deg, 2);
  out += ",\"step_actual_yaw_delta_deg\":";
  out += String(step_actual_yaw_delta_deg, 2);
  out += ",\"step_final_yaw_error_deg\":";
  out += String(step_final_yaw_error_deg, 2);
  out += ",\"step_requested_distance_mm\":";
  out += String(step_requested_distance_mm, 2);
  out += ",\"step_left_distance_mm\":";
  out += String(step_left_distance_mm, 2);
  out += ",\"step_right_distance_mm\":";
  out += String(step_right_distance_mm, 2);
  out += ",\"step_actual_distance_mm\":";
  out += String(step_actual_distance_mm, 2);
  out += ",\"step_distance_error_mm\":";
  out += String(step_distance_error_mm, 2);
  out += ",\"step_end_heading_stable\":";
  out += step_end_heading_stable ? "true" : "false";
  out += ",\"yaw_rate_deg_s\":"; out += String(yaw_rate_deg_s, 2);
  out += ",\"yaw_valid\":"; out += yaw_valid ? "true" : "false";
  out += ",\"yaw_rate_valid\":"; out += yaw_rate_valid ? "true" : "false";
  out += ",\"imu_rotation_age_ms\":"; out += String(rotation_age_ms);
  out += ",\"imu_gyro_age_ms\":"; out += String(gyro_age_ms);
  out += ",\"imu_rotation_accuracy\":"; out += String(imu_rotation_accuracy);
  out += ",\"bno_ok\":"; out += bno_ok ? "true" : "false";
  out += ",\"ina_ok\":"; out += ina_ok ? "true" : "false";
  out += ",\"battery_v\":"; out += String(battery_source_v, 3);
  out += ",\"battery_percent_est\":"; out += String(battery_percent_est, 1);
  out += ",\"turn_requested_delta_deg\":"; out += String(turn_requested_delta_deg, 2);
  out += ",\"turn_signed_progress_deg\":";
  out += String(turn_fused_progress_deg * (float)turn_direction_sign, 2);
  out += ",\"turn_rotation_progress_deg\":";
  out += String(turn_unwrapped_progress_deg, 2);
  out += ",\"turn_gyro_progress_deg\":";
  out += String(turn_gyro_progress_deg, 2);
  out += ",\"turn_encoder_progress_deg\":";
  out += String(turn_encoder_progress_deg, 2);
  out += ",\"turn_fused_progress_deg\":";
  out += String(turn_fused_progress_deg, 2);
  out += ",\"turn_sensor_disagreement_deg\":";
  out += String(turn_sensor_disagreement_deg, 2);
  out += ",\"turn_fusion_selected_pair\":";
  out += String(turn_fusion_selected_pair);
  out += ",\"turn_balance_error_mm\":";
  out += String(turn_balance_error_mm, 2);
  out += ",\"turn_center_translation_mm\":";
  out += String(turn_center_translation_mm, 2);
  out += ",\"turn_center_speed_mm_s\":";
  out += String(turn_center_speed_mm_s, 2);
  out += ",\"turn_balance_correction_tps\":";
  out += String(turn_balance_correction_tps, 2);
  out += ",\"turn_remaining_deg\":";
  out += String(turn_abs_target_deg -
    turn_fused_progress_deg * (float)turn_direction_sign, 2);
  out += ",\"control_period_ms\":"; out += String(CONTROL_PERIOD_MS);
  out += ",\"last_control_dt_ms\":"; out += String(last_control_dt_ms, 1);
  out += ",\"max_control_dt_ms\":"; out += String(max_control_dt_ms, 1);
  out += ",\"control_deadline_misses\":"; out += String(control_deadline_misses);
  out += ",\"straight_endpoint_aligning\":";
  out += straight_endpoint_aligning ? "true" : "false";
  out += ",\"CELL_DISTANCE_MM\":"; out += String(CELL_DISTANCE_MM, 2);
  out += ",\"LEFT_TICKS_PER_REV\":"; out += String(LEFT_TICKS_PER_REV, 1);
  out += ",\"RIGHT_TICKS_PER_REV\":"; out += String(RIGHT_TICKS_PER_REV, 1);
  out += ",\"LEFT_TICKS_PER_MM\":"; out += String(LEFT_TICKS_PER_MM, 5);
  out += ",\"RIGHT_TICKS_PER_MM\":"; out += String(RIGHT_TICKS_PER_MM, 5);
  out += ",\"LEFT_LINEAR_SCALE\":"; out += String(LEFT_LINEAR_SCALE, 4);
  out += ",\"RIGHT_LINEAR_SCALE\":"; out += String(RIGHT_LINEAR_SCALE, 4);
  out += ",\"FORWARD_DISTANCE_TICK_SCALE\":"; out += String(FORWARD_DISTANCE_TICK_SCALE, 6);
  out += ",\"BACKWARD_DISTANCE_TICK_SCALE\":"; out += String(BACKWARD_DISTANCE_TICK_SCALE, 6);
  out += ",\"IMU_YAW_SIGN\":"; out += String(IMU_YAW_SIGN);
  out += ",\"TURN_CONTROL_SIGN\":"; out += String(TURN_CONTROL_SIGN);
  out += ",\"YAW_CORRECTION_SIGN\":"; out += String(YAW_CORRECTION_SIGN);
  out += "}";
  return out;
}




String get_motion_guard() {
  String out;
  out.reserve(240);
  out += "{\"mode\":\"";
  if (mode == MODE_IDLE) out += "IDLE";
  else if (mode == MODE_STRAIGHT) out += "STRAIGHT";
  else if (mode == MODE_TURN_IMU) out += "TURN_IMU";
  else if (mode == MODE_TURN_ENCODER) out += "TURN_ENCODER";
  else if (mode == MODE_SPEED_TEST) out += "SPEED_TEST";
  else if (mode == MODE_RECOVERY) out += "RECOVERY";
  else if (mode == MODE_FAULT) out += "FAULT";
  out += "\",\"macro_mode\":\"";
  out += macroName();
  out += "\",\"fault_reason\":\"";
  out += fault_reason;
  out += "\",\"bno_ok\":";
  out += bno_ok ? "true" : "false";
  out += ",\"yaw_valid\":";
  out += yaw_valid ? "true" : "false";
  out += ",\"yaw_rate_valid\":";
  out += yaw_rate_valid ? "true" : "false";
  out += ",\"left_ticks\":";
  out += String(readLeftTicks());
  out += ",\"right_ticks\":";
  out += String(readRightTicks());
  out += "}";
  return out;
}



String get_status() {
  return get_state();
}

String move_20cm_forward() {
  return move_forward();
}

String move_20cm_backward() {
  return move_backward();
}

String turn_90_left() {
  clearMacro();
  return startTurnDegrees(90.0f * TURN_LEFT_DEG_SCALE);
}

String turn_90_right() {
  clearMacro();
  return startTurnDegrees(-90.0f * TURN_RIGHT_DEG_SCALE);
}
String raw_left_forward() {
  stopMotorsRaw();
  resetPrimitiveEncodersPreservingPose();
  left_ctrl.target_speed_tps = 300.0f;
  right_ctrl.target_speed_tps = 0.0f;
  writeLeftCorrectedPWM(160);
  delay(1200);
  stopMotorsRaw();

  String out = "raw_left_forward: left_ticks=";
  out += String(readLeftTicks());
  out += " right_ticks=";
  out += String(readRightTicks());
  return out;
}

String raw_left_backward() {
  stopMotorsRaw();
  resetPrimitiveEncodersPreservingPose();
  left_ctrl.target_speed_tps = -300.0f;
  right_ctrl.target_speed_tps = 0.0f;
  writeLeftCorrectedPWM(-160);
  delay(1200);
  stopMotorsRaw();

  String out = "raw_left_backward: left_ticks=";
  out += String(readLeftTicks());
  out += " right_ticks=";
  out += String(readRightTicks());
  return out;
}

String raw_right_forward() {
  stopMotorsRaw();
  resetPrimitiveEncodersPreservingPose();
  left_ctrl.target_speed_tps = 0.0f;
  right_ctrl.target_speed_tps = 300.0f;
  writeRightCorrectedPWM(160);
  delay(1200);
  stopMotorsRaw();

  String out = "raw_right_forward: left_ticks=";
  out += String(readLeftTicks());
  out += " right_ticks=";
  out += String(readRightTicks());
  return out;
}

String raw_right_backward() {
  stopMotorsRaw();
  resetPrimitiveEncodersPreservingPose();
  left_ctrl.target_speed_tps = 0.0f;
  right_ctrl.target_speed_tps = -300.0f;
  writeRightCorrectedPWM(-160);
  delay(1200);
  stopMotorsRaw();

  String out = "raw_right_backward: left_ticks=";
  out += String(readLeftTicks());
  out += " right_ticks=";
  out += String(readRightTicks());
  return out;
}





void setup() {
  Serial.begin(115200);

  pinMode(LEFT_EN, OUTPUT);
  pinMode(LEFT_IN1, OUTPUT);
  pinMode(LEFT_IN2, OUTPUT);

  pinMode(RIGHT_EN, OUTPUT);
  pinMode(RIGHT_IN1, OUTPUT);
  pinMode(RIGHT_IN2, OUTPUT);

  pinMode(LEFT_ENC_A, INPUT_PULLUP);
  pinMode(LEFT_ENC_B, INPUT_PULLUP);

  pinMode(RIGHT_ENC_A, INPUT_PULLUP);
  pinMode(RIGHT_ENC_B, INPUT_PULLUP);

  left_last_state = (digitalRead(LEFT_ENC_A) << 1) | digitalRead(LEFT_ENC_B);
  right_last_state = (digitalRead(RIGHT_ENC_A) << 1) | digitalRead(RIGHT_ENC_B);

  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_A), leftEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(LEFT_ENC_B), leftEncoderISR, CHANGE);

  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_A), rightEncoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(RIGHT_ENC_B), rightEncoderISR, CHANGE);

  stopMotorsRaw();

  matrix.begin();
  matrix.setGrayscaleBits(3);
  matrix.clear();
  matrix.loadSequence(HeartAnim);
  matrix.playSequence();
  delay(1000);
  matrix.clear();
  matrix.loadFrame(HeartStatic);

  for (auto &e : kPins) {
    if (isRobotReservedPinName(e.name)) continue;
    pinMode(e.pin, OUTPUT);
    digitalWrite(e.pin, HIGH);
  }

  
  Wire1.begin();
  Wire1.setClock(400000);
  delay(100);
  ina_ok = ina219.begin(&Wire1);
  if (ina_ok) {
    ina219.setCalibration_32V_2A();
  }
  bno_ok = bno080.begin(0x4A, Wire1);
  if (bno_ok) {
    bno_wire = &Wire1;
    bno_i2c_address = 0x4A;
  }
  if (!bno_ok) {
    bno_ok = bno080.begin(0x4B, Wire1);
    if (bno_ok) {
      bno_wire = &Wire1;
      bno_i2c_address = 0x4B;
    }
  }
  if (!bno_ok) {
    Wire.begin();
    Wire.setClock(400000);
    bno_ok = bno080.begin(0x4A, Wire);
    if (bno_ok) {
      bno_wire = &Wire;
      bno_i2c_address = 0x4A;
    }
  }
  if (!bno_ok) {
    bno_ok = bno080.begin(0x4B, Wire);
    if (bno_ok) {
      bno_wire = &Wire;
      bno_i2c_address = 0x4B;
    }
  }
  if (bno_ok) {
    last_bno_poll_us = 0;
    configureBnoReports();
  }

  resetPlanarOdometry(false);

  Bridge.begin();

  Bridge.provide("set_pin_by_name", set_pin_by_name);
  Bridge.provide("draw",            draw);
  Bridge.provide("load_frame",      load_frame);
  Bridge.provide("play_animation",  play_animation);
  Bridge.provide("stop_animation",  stop_animation);
  Bridge.provide("keyword_detected", wake_up);
  
  Bridge.provide("motor_forward", [](int d) { move_forward(); });
  Bridge.provide("motor_backward", [](int d) { move_backward(); });
  Bridge.provide("motor_left", [](int d) { turn_90_left(); });
  Bridge.provide("motor_right", [](int d) { turn_90_right(); });
  Bridge.provide("motor_stop", []() { stop_robot(); });
  
  Bridge.provide("read_mpu6050", []() {
    std::vector<float> v = {imu_ax, imu_ay, imu_az, imu_gx, imu_gy, imu_gz};
    return v;
  });
  
  
  Bridge.provide("read_imu", []() {
    std::vector<float> v = {imu_ax, imu_ay, imu_az, imu_gx, imu_gy, imu_gz};
    return v;
  });

  Bridge.provide("read_ina219", []() {
    std::vector<float> v = {battery_bus_v, 0.0f, battery_current_ma, battery_power_mw, battery_source_v};
    return v;
  });

  Bridge.provide("init_robot", init_robot);
  Bridge.provide("zero_pose", zero_pose);
  Bridge.provide("settle_robot", settle_robot);
  Bridge.provide("reset_imu_reference", reset_imu_reference);
  Bridge.provide("stop_robot", stop_robot);

  Bridge.provide("move_forward", move_forward);
  Bridge.provide("move_backward", move_backward);
  Bridge.provide("move_relative_mm", move_relative_mm);
  Bridge.provide("turn_relative_deg", turn_relative_deg);
  
  
  
  

  Bridge.provide("set_values", set_values);
  Bridge.provide("get_state", get_state);
  Bridge.provide("get_motion_state", get_motion_state);
  Bridge.provide("get_motion_guard", get_motion_guard);
  Bridge.provide("start_speed_test", start_speed_test);

  Bridge.provide("get_status", get_status);
  Bridge.provide("move_20cm_forward", move_20cm_forward);
  Bridge.provide("move_20cm_backward", move_20cm_backward);
  Bridge.provide("turn_90_left", turn_90_left);
  Bridge.provide("turn_90_right", turn_90_right);
  
  Bridge.provide("raw_left_forward", raw_left_forward);
  Bridge.provide("raw_left_backward", raw_left_backward);
  Bridge.provide("raw_right_forward", raw_right_forward);
  Bridge.provide("raw_right_backward", raw_right_backward);
  
  last_control_ms = millis();
  motion_start_ms = millis();
}

void loop() {
  controlLoop();
  
  
  
  
  bool sent_motion_result = false;
  if (motion_result_notify_pending && (mode == MODE_IDLE || mode == MODE_FAULT)) {
    if (fabsf(step_requested_distance_mm) > 0.001f) {
      captureStepDistanceOutcome(readLeftTicks(), readRightTicks());
    }
    int result_code = motion_result_notify_code;
    motion_result_notify_pending = false;
    Bridge.notify("robot_motion_complete", result_code);
    sent_motion_result = true;
  }

  if (!sent_motion_result && (mode == MODE_IDLE || mode == MODE_FAULT)) {
    animation_tick();
    sensor_tick();
  }
  delay(1);
}
