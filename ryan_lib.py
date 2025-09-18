import booster_robotics_sdk_python as B
from functools import partial
from time import sleep
from easydict import EasyDict
import rp


def set_global(name, value):
    globals()[name] = value


@rp.globalize_locals
def _init_communication() -> None:
    if not "INITIALIZED" in globals():
        B.ChannelFactory.Instance().Init(0)

        # low_cmd_publisher = B1LowCmdPublisher()
        # low_cmd_publisher.InitChannel()
        # low_cmd = LowCmd()

        client = B.B1LocoClient()
        client.Init()

        handler = partial(set_global, "low_state")  # Low Level State
        low_state_subscriber = B.B1LowStateSubscriber(handler)
        low_state_subscriber.InitChannel()

        # Battery state subscriber
        battery_handler = partial(set_global, "battery_state")
        # RobotStatusSubscriber would subscribe to battery data topic
        set_global("battery_state", EasyDict(soc=None, voltage=None, temperature=None))

        # Low-level joint control setup
        low_cmd_publisher = B.B1LowCmdPublisher()
        low_cmd_publisher.InitChannel()
        motor_cmds = [B.MotorCmd() for _ in range(B.B1JointCnt)]
        set_global("low_cmd_publisher", low_cmd_publisher)
        set_global("motor_cmds", motor_cmds)

        INITIALIZED = True

def tick(): sleep(.01)

# Mode control
def set_mode_custom (): return client.ChangeMode(B.RobotMode.kCustom ) # Goes limp, allows low level control
def set_mode_prepare(): return client.ChangeMode(B.RobotMode.kPrepare) # Stand ready position
def set_mode_walking(): return client.ChangeMode(B.RobotMode.kWalking) # For movement and dancing
def set_mode_damping(): return client.ChangeMode(B.RobotMode.kDamping) # Damped/compliant mode

def set_mode_custom_stiff():
    # Get current positions from low_state before switching modes
    if 'low_state' in globals() and globals()['low_state']:
        for i in range(B.B1JointCnt):
            if i < len(globals()['low_state'].motor_state_serial):
                globals()['motor_cmds'][i].q = globals()['low_state'].motor_state_serial[i].q  # Hold current position
            globals()['motor_cmds'][i].kp, globals()['motor_cmds'][i].kd, globals()['motor_cmds'][i].weight = 350.0, 7.5, 1.0
            globals()['motor_cmds'][i].dq, globals()['motor_cmds'][i].tau = 0.0, 0.0
    result = client.ChangeMode(B.RobotMode.kCustom)
    # Send stiff commands immediately after mode change
    low_cmd = B.LowCmd(); low_cmd.cmd_type = B.SERIAL; low_cmd.motor_cmd = globals()['motor_cmds']; globals()['low_cmd_publisher'].Write(low_cmd)
    return result

# Dance moves - must be in walking mode
def do_new_years_dance(): return client.Dance(B.DanceId.kNewYear      ) # New Year dance
def do_nezha_dance    (): return client.Dance(B.DanceId.kNezha        ) # Nezha dance
def do_future_dance   (): return client.Dance(B.DanceId.kTowardsFuture) # Towards Future dance
def stop_dance        (): return client.Dance(B.DanceId.kStop         ) # Stop dancing

# Movement control - must be in walking mode
def move(x=0.0, y=0.0, z=0.0): return client.Move(x, y, z) # x=forward/back, y=left/right, z=rotate
def stop_movement(): return move(0, 0, 0)
def walk_forward (speed=0.8): return move(speed, 0, 0 )
def walk_backward(speed=0.2): return move(-speed, 0, 0)
def walk_left    (speed=0.2): return move(0, speed, 0 )
def walk_right   (speed=0.2): return move(0, -speed, 0)
def rotate_left  (speed=0.2): return move(0, 0, speed )
def rotate_right (speed=0.2): return move(0, 0, -speed)

# Head control - works in walking and prepare modes
def rotate_head(pitch=0.0, yaw=0.0): return client.RotateHead(pitch, yaw)
def head_look_down (): return rotate_head(1.0, 0.0   )
def head_look_up   (): return rotate_head(-0.3, 0.0  )
def head_look_left (): return rotate_head(0.0, 0.785 )  # 45 degrees
def head_look_right(): return rotate_head(0.0, -0.785)  # 45 degrees
def head_center    (): return rotate_head(0.0, 0.0   )

# Status queries
def get_mode():
    gm = B.GetModeResponse()
    res = client.GetMode(gm)
    if res == 0:
        return gm.mode
    return None

# Robot state control
def lie_down(): return client.LieDown()  # Makes robot lie down
def get_up  (): return client.GetUp  ()  # Makes robot stand up from lying position

# Arm/hand control (if robot has arms)
def wave_hand    (): return client.WaveHand    (B.kHandOpen ) # Wave hand open
def wave_hand_close(): return client.WaveHand  (B.kHandClose) # Wave hand close
def handshake_start(): return client.Handshake (B.kHandOpen ) # Start handshake motion
def handshake_end  (): return client.Handshake (B.kHandClose) # End handshake motion

# Joint control helpers
def _set_joints_stiff(*joints):
    for j in joints: globals()['motor_cmds'][j].kp, globals()['motor_cmds'][j].kd, globals()['motor_cmds'][j].weight = 350.0, 7.5, 1.0
    low_cmd = B.LowCmd(); low_cmd.cmd_type = B.SERIAL; low_cmd.motor_cmd = globals()['motor_cmds']; globals()['low_cmd_publisher'].Write(low_cmd)

def _set_joints_limp(*joints):
    for j in joints: globals()['motor_cmds'][j].kp, globals()['motor_cmds'][j].kd, globals()['motor_cmds'][j].weight = 0.0, 0.1, 1.0
    low_cmd = B.LowCmd(); low_cmd.cmd_type = B.SERIAL; low_cmd.motor_cmd = globals()['motor_cmds']; globals()['low_cmd_publisher'].Write(low_cmd)

# Joint control - must be in custom mode
def right_arm_hold(): _set_joints_stiff(B.kRightShoulderPitch, B.kRightShoulderRoll, B.kRightElbowPitch, B.kRightElbowYaw)
def right_arm_limp(): _set_joints_limp (B.kRightShoulderPitch, B.kRightShoulderRoll, B.kRightElbowPitch, B.kRightElbowYaw)
def left_arm_hold (): _set_joints_stiff(B.kLeftShoulderPitch, B.kLeftShoulderRoll, B.kLeftElbowPitch, B.kLeftElbowYaw)
def left_arm_limp (): _set_joints_limp (B.kLeftShoulderPitch, B.kLeftShoulderRoll, B.kLeftElbowPitch, B.kLeftElbowYaw)
def right_leg_hold(): _set_joints_stiff(B.kRightHipPitch, B.kRightHipRoll, B.kRightHipYaw, B.kRightKneePitch, B.kCrankUpRight, B.kCrankDownRight)
def right_leg_limp(): _set_joints_limp (B.kRightHipPitch, B.kRightHipRoll, B.kRightHipYaw, B.kRightKneePitch, B.kCrankUpRight, B.kCrankDownRight)
def left_leg_hold (): _set_joints_stiff(B.kLeftHipPitch, B.kLeftHipRoll, B.kLeftHipYaw, B.kLeftKneePitch, B.kCrankUpLeft, B.kCrankDownLeft)
def left_leg_limp (): _set_joints_limp (B.kLeftHipPitch, B.kLeftHipRoll, B.kLeftHipYaw, B.kLeftKneePitch, B.kCrankUpLeft, B.kCrankDownLeft)
def ankles_hold   (): _set_joints_stiff(B.kCrankUpLeft, B.kCrankDownLeft, B.kCrankUpRight, B.kCrankDownRight)
def ankles_limp   (): _set_joints_limp (B.kCrankUpLeft, B.kCrankDownLeft, B.kCrankUpRight, B.kCrankDownRight)
def head_hold     (): _set_joints_stiff(B.kHeadYaw, B.kHeadPitch)
def head_limp     (): _set_joints_limp (B.kHeadYaw, B.kHeadPitch)
def hip_hold      (): _set_joints_stiff(B.kLeftHipPitch, B.kLeftHipRoll, B.kLeftHipYaw, B.kRightHipPitch, B.kRightHipRoll, B.kRightHipYaw)
def hip_limp      (): _set_joints_limp (B.kLeftHipPitch, B.kLeftHipRoll, B.kLeftHipYaw, B.kRightHipPitch, B.kRightHipRoll, B.kRightHipYaw)
def waist_hold    (): _set_joints_stiff(B.kWaist)
def waist_limp    (): _set_joints_limp (B.kWaist)

# Battery data: access global battery_state
# battery_state.soc - State of charge percentage
# battery_state.voltage - Battery voltage in volts
# battery_state.temperature - Battery temperature in celsius

_init_communication()
