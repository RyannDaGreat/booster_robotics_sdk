import booster_robotics_sdk_python as B


def set_global(name, value):
    globals()[name] = value


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

def set_mode_custom (): return client.ChangeMode(B.RobotMode.kCustom ) #Goes limp allows for low level control
def set_mode_prepare(): return client.ChangeMode(B.RobotMode.kPrepare) #Needed before setting to custom
def set_mode_walking(): return client.ChangeMode(B.RobotMode.kWalking) #Needed before dancing

def do_new_years_dance(): return client.Dance(B.DanceId.kNewYear) #Must be in walking mode

_init_communication()