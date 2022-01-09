import datetime


class TimerState(object):
    def __init__(self):
        self.started_at: datetime.datetime = datetime.datetime.now()
        self.running: bool = False
        self.time: int = 0

    def __dict__(self):
        return {"running": self.running,
                "time": self.time,
                "startedAt": self.started_at.strftime("%Y-%m-%dT%H:%M:%S%f")[:-3] + "Z"}
