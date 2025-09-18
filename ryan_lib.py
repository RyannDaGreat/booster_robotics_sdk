import booster_robotics_sdk_python as B
from functools import partial
from time import sleep


def set_global(name, value):
    globals()[name] = value


def globalize_locals(func):
    """Decorator to make local variables global"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        for name, value in func.__code__.co_varnames[:func.__code__.co_argcount]:
            globals()[name] = locals()[name]
        return result
    return wrapper


@globalize_locals
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

        INITIALIZED = True

def tick(): sleep(.01)

# Mode control
def set_mode_custom (): return client.ChangeMode(B.RobotMode.kCustom ) #Goes limp allows for low level control
def set_mode_prepare(): return client.ChangeMode(B.RobotMode.kPrepare) #Needed before setting to custom
def set_mode_walking(): return client.ChangeMode(B.RobotMode.kWalking) #Needed before dancing
def set_mode_damping(): return client.ChangeMode(B.RobotMode.kDamping) #Damping mode

# Dance moves - must be in walking mode
def do_new_years_dance(): return client.Dance(B.DanceId.kNewYear)     #New Year dance
def do_nezha_dance():     return client.Dance(B.DanceId.kNezha)       #Nezha dance
def do_future_dance():    return client.Dance(B.DanceId.kTowardsFuture) #Towards Future dance
def stop_dance():         return client.Dance(B.DanceId.kStop)        #Stop dancing

# Movement control
def move(x=0.0, y=0.0, z=0.0): return client.Move(x, y, z)  # x=forward/back, y=left/right, z=rotate
def stop_movement(): return move(0, 0, 0)
def walk_forward(speed=0.8): return move(speed, 0, 0)
def walk_backward(speed=0.2): return move(-speed, 0, 0)
def walk_left(speed=0.2): return move(0, speed, 0)
def walk_right(speed=0.2): return move(0, -speed, 0)
def rotate_left(speed=0.2): return move(0, 0, speed)
def rotate_right(speed=0.2): return move(0, 0, -speed)

# Head control
def rotate_head(pitch=0.0, yaw=0.0): return client.RotateHead(pitch, yaw)
def head_look_down(): return rotate_head(1.0, 0.0)
def head_look_up(): return rotate_head(-0.3, 0.0)
def head_look_left(): return rotate_head(0.0, 0.785)  # 45 degrees
def head_look_right(): return rotate_head(0.0, -0.785)  # 45 degrees
def head_center(): return rotate_head(0.0, 0.0)

# Status queries
def get_mode():
    gm = B.GetModeResponse()
    res = client.GetMode(gm)
    if res == 0:
        return gm.mode
    return None

# Battery status (placeholder - needs topic discovery)
def get_battery_status():
    """Get battery status - NOT IMPLEMENTED YET
    Will return battery SOC, voltage, temperature when implemented
    """
    # TODO: Need to find the correct topic name for robot status
    # The infrastructure exists in C++ but needs Python bindings
    print("Battery status not yet implemented - needs topic discovery")
    return None

_init_communication()