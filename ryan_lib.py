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

# Joint control - must be in custom mode
def set_joint_gains(joint_id, kp, kd, position=None):
    """Set joint stiffness gains and optional target position"""
    if position is not None:
        motor_cmds[joint_id].q = position
    motor_cmds[joint_id].kp = kp
    motor_cmds[joint_id].kd = kd
    motor_cmds[joint_id].dq = 0.0
    motor_cmds[joint_id].tau = 0.0
    motor_cmds[joint_id].weight = 1.0

def set_joint_stiff(joint_id, position=0.0):
    """Lock joint at specific position with high stiffness"""
    set_joint_gains(joint_id, kp=350.0, kd=7.5, position=position)

def set_joint_limp(joint_id):
    """Make joint compliant/loose with low stiffness"""
    set_joint_gains(joint_id, kp=0.0, kd=0.1)

def send_joint_commands():
    """Send current motor commands to robot - call after setting joints"""
    low_cmd = B.LowCmd()
    low_cmd.cmd_type = B.SERIAL
    low_cmd.motor_cmd = motor_cmds
    low_cmd_publisher.Write(low_cmd)

# Body part control - must be in custom mode
def freeze_right_arm():
    set_joint_stiff(B.kRightShoulderPitch)
    set_joint_stiff(B.kRightShoulderRoll)
    set_joint_stiff(B.kRightElbowPitch)
    set_joint_stiff(B.kRightElbowYaw)
    send_joint_commands()

def limp_right_arm():
    set_joint_limp(B.kRightShoulderPitch)
    set_joint_limp(B.kRightShoulderRoll)
    set_joint_limp(B.kRightElbowPitch)
    set_joint_limp(B.kRightElbowYaw)
    send_joint_commands()

def freeze_left_arm():
    set_joint_stiff(B.kLeftShoulderPitch)
    set_joint_stiff(B.kLeftShoulderRoll)
    set_joint_stiff(B.kLeftElbowPitch)
    set_joint_stiff(B.kLeftElbowYaw)
    send_joint_commands()

def limp_left_arm():
    set_joint_limp(B.kLeftShoulderPitch)
    set_joint_limp(B.kLeftShoulderRoll)
    set_joint_limp(B.kLeftElbowPitch)
    set_joint_limp(B.kLeftElbowYaw)
    send_joint_commands()

def freeze_right_leg():
    set_joint_stiff(B.kRightHipPitch)
    set_joint_stiff(B.kRightHipRoll)
    set_joint_stiff(B.kRightHipYaw)
    set_joint_stiff(B.kRightKneePitch)
    set_joint_stiff(B.kCrankUpRight)
    set_joint_stiff(B.kCrankDownRight)
    send_joint_commands()

def limp_right_leg():
    set_joint_limp(B.kRightHipPitch)
    set_joint_limp(B.kRightHipRoll)
    set_joint_limp(B.kRightHipYaw)
    set_joint_limp(B.kRightKneePitch)
    set_joint_limp(B.kCrankUpRight)
    set_joint_limp(B.kCrankDownRight)
    send_joint_commands()

def freeze_left_leg():
    set_joint_stiff(B.kLeftHipPitch)
    set_joint_stiff(B.kLeftHipRoll)
    set_joint_stiff(B.kLeftHipYaw)
    set_joint_stiff(B.kLeftKneePitch)
    set_joint_stiff(B.kCrankUpLeft)
    set_joint_stiff(B.kCrankDownLeft)
    send_joint_commands()

def limp_left_leg():
    set_joint_limp(B.kLeftHipPitch)
    set_joint_limp(B.kLeftHipRoll)
    set_joint_limp(B.kLeftHipYaw)
    set_joint_limp(B.kLeftKneePitch)
    set_joint_limp(B.kCrankUpLeft)
    set_joint_limp(B.kCrankDownLeft)
    send_joint_commands()

def freeze_ankles():
    set_joint_stiff(B.kCrankUpLeft)
    set_joint_stiff(B.kCrankDownLeft)
    set_joint_stiff(B.kCrankUpRight)
    set_joint_stiff(B.kCrankDownRight)
    send_joint_commands()

def limp_ankles():
    set_joint_limp(B.kCrankUpLeft)
    set_joint_limp(B.kCrankDownLeft)
    set_joint_limp(B.kCrankUpRight)
    set_joint_limp(B.kCrankDownRight)
    send_joint_commands()

def freeze_head():
    set_joint_stiff(B.kHeadYaw)
    set_joint_stiff(B.kHeadPitch)
    send_joint_commands()

def limp_head():
    set_joint_limp(B.kHeadYaw)
    set_joint_limp(B.kHeadPitch)
    send_joint_commands()

def freeze_hip():
    set_joint_stiff(B.kLeftHipPitch)
    set_joint_stiff(B.kLeftHipRoll)
    set_joint_stiff(B.kLeftHipYaw)
    set_joint_stiff(B.kRightHipPitch)
    set_joint_stiff(B.kRightHipRoll)
    set_joint_stiff(B.kRightHipYaw)
    send_joint_commands()

def limp_hip():
    set_joint_limp(B.kLeftHipPitch)
    set_joint_limp(B.kLeftHipRoll)
    set_joint_limp(B.kLeftHipYaw)
    set_joint_limp(B.kRightHipPitch)
    set_joint_limp(B.kRightHipRoll)
    set_joint_limp(B.kRightHipYaw)
    send_joint_commands()

def freeze_waist():
    set_joint_stiff(B.kWaist)
    send_joint_commands()

def limp_waist():
    set_joint_limp(B.kWaist)
    send_joint_commands()

# Battery data: access global battery_state
# battery_state.soc - State of charge percentage
# battery_state.voltage - Battery voltage in volts
# battery_state.temperature - Battery temperature in celsius

_init_communication()
