import asyncio
from cbpi.api.step import CBPiStep, StepResult
from cbpi.api.timer import Timer
from cbpi.api import *
import logging


@parameters([Property.Number(label="Upper Bound in Minutes", description="The time after which this step will conclude,"
                                                                         " regardless of the current temp",
                             configurable=True),
             Property.Number(label="Temp", configurable=True),
             Property.Sensor(label="Sensor"),
             Property.Kettle(label="Kettle"),
             Property.Actor(label="Chiller Primary Pump"),
             Property.Actor(label="Secondary Pump")])
class ChillStep(CBPiStep):

    def __init__(self, cbpi, id, name, props, on_done):
        super().__init__(cbpi, id, name, props, on_done)
        self.sample_streak = 0

    async def on_timer_done(self, timer):
        self.summary = ""
        self.cbpi.notify("Step Temp Wasn't Reached!", "Good luck:(", timeout=None)
        # turns pump off at finish
        await self.actor_off(int(self.prime_pump))
        if self.sec_pump is not None:
            await self.actor_off(int(self.sec_pump))
        await self.next()

    async def on_timer_update(self, timer, seconds):
        self.summary = Timer.format_time(seconds)
        await self.push_update()

    async def on_start(self):
        if self.timer is None:
            self.timer = Timer(int(self.props.Timer) * 60, on_update=self.on_timer_update, on_done=self.on_timer_done)
        self.summary = "Waiting for Target Temp"
        await self.push_update()

    async def on_stop(self):
        self.summary = ""
        await self.push_update()

    async def reset(self):
        self.summary = ""
        self.timer = Timer(int(self.props.Timer) * 60, on_update=self.on_timer_update, on_done=self.on_timer_done)

    async def run(self):
        while True:
            # Check if Target Temp has been reached
            if self.get_kettle_temp(self.kettle) <= float(self.temp):
                self.sample_streak += 1
                # Checks if Target Amount of Samples is reached
                if self.sample_streak == self.Samples:
                    self.cbpi.notify("Yeast Pitch Temp Reached!", "Move to fermentation tank", timeout=None)
                    # turns pump off at finish
                    await self.actor_off(int(self.prime_pump))
                    if self.sec_pump is not None:
                        await self.actor_off(int(self.sec_pump))
                    await self.next()
            else:
                # Nullifies The samples streak
                self.sample_streak = 0


def setup(cbpi):
    '''
    This method is called by the server during startup 
    Here you need to register your plugins at the server

    :param cbpi: the cbpi core 
    :return: 
    '''

    cbpi.plugin.register("ChillStep", ChillStep)

