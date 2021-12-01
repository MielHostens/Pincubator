#!/usr/bin/env python
from pushsafer import *

init("gHIXO4mnMUAcsKfTJieY")

def  alert_message(message):
    Client("").send_message(message=message,
                            title="Pincubator ALERT",
                            device="a",  # all
                            sound="0",  # empty default otherwise 0-62
                            vibration="3",  # 1-3
                            icon="1",
                            url="https://cayenne.mydevices.com/cayenne/dashboard/arduino/b9b7f620-49c8-11eb-8779-7d56e82df461",
                            urltitle="",
                            time2live="3600",
                            priority="2",  # -2-2
                            picture1="",
                            picture2="",
                            picture3="",
                            expire="3600",
                            retry="3600",
                            answer=0)

def  start_message():
    Client("").send_message(message="Pincubator started",
                            title="Setup finished",
                            device="a",  # all
                            sound="8",  # empty default otherwise 0-62
                            vibration="3",  # 1-3
                            icon="1",
                            url="https://cayenne.mydevices.com/cayenne/dashboard/arduino/b9b7f620-49c8-11eb-8779-7d56e82df461",
                            urltitle="",
                            time2live="3600",
                            priority="2",  # -2-2
                            picture1="",
                            picture2="",
                            picture3="",
                            expire="2",
                            retry="3600",
                            answer=0)