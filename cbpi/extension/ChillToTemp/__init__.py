import asyncio
from cbpi.api.step import CBPiStep, StepResult
from cbpi.api.timer import Timer
from cbpi.api import *
from cbpi.api.dataclasses import NotificationAction, NotificationType


@parameters([Property.Number(label="Temp", configurable=True,
                             description="Target temperature for cooldown. "
                                         "Notification will be send when temp is reached and Actor can be triggered"),
             Property.Number(label="Timer", configurable=True,
                             description="The time until step is forced finished"),
             Property.Sensor(label="Sensor", description="Sensor that is used during cooldown"),
             Property.Actor(label="Actor",
                            description="Actor can trigger a valve for the cooldown to target temperature"),
             Property.Actor(label="Secondary_Actor",
                            description="Actor can trigger a valve for the cooldown to target temperature"),
             Property.Number(label="Samples", configurable=True, default_value=5,
                             description="Number of samples that are in the desired range before finishing this step")
             ])
class Cooldown(CBPiStep):

    def __init__(self, cbpi, id, name, props, on_done):
        super().__init__(cbpi, id, name, props, on_done)
        self._samp_count = 0

    @action("Add 5 Minutes to Timer", [])
    async def add_timer(self):
        if self.timer._task != None:
            self.cbpi.notify(self.name, '5 Minutes added', NotificationType.INFO)
            await self.timer.add(300)
        else:
            self.cbpi.notify(self.name, 'Timer must be running to add time', NotificationType.WARNING)

    async def on_timer_done(self, timer):
        self.summary = ""
        self.cbpi.notify('CoolDown', 'Step finished', NotificationType.INFO)
        await self.next()

    async def on_timer_update(self, timer, seconds):
        self.summary = Timer.format_time(seconds)
        await self.push_update()

    async def on_start(self):
        if self.timer is None:
            self.timer = Timer(int(self.props.Timer) * 60, on_update=self.on_timer_update, on_done=self.on_timer_done)
        self.timer.start()

    async def on_stop(self):
        await self.timer.stop()
        self.summary = ""
        if self.props.Actor is not None:
            await self.actor_off(self.props.Actor)
        if self.props.Secondary_Actor is not None:
            await self.actor_off(self.props.Secondary_Actor)
        await self.push_update()

    async def reset(self):
        self.timer = Timer(int(self.props.Timer) * 60, on_update=self.on_timer_update, on_done=self.on_timer_done)
        self.cbpi.notify('CoolDown', "Timer was reset", NotificationType.INFO)

    async def run(self):
        if self.props.Actor is not None:
            await self.actor_on(self.props.Actor)
        if self.props.Secondary_Actor is not None:
            await self.actor_on(self.props.Secondary_Actor)
        self.cbpi.notify('CoolDown', "Step started", NotificationType.INFO)
        while True:
            await asyncio.sleep(1)
            if self.get_sensor_value(self.props.Sensor).get("value") <= float(self.props.Temp):
                self._samp_count += 1
            if self._samp_count >= int(self.props.Samples):
                self.cbpi.notify('CoolDown', "Desired temp was reached", NotificationType.INFO)
                break
        return StepResult.DONE


def setup(cbpi):
    '''
    This method is called by the server during startup
    Here you need to register your plugins at the server

    :param cbpi: the cbpi core
    :return:
    '''
    cbpi.plugin.register("Cooldown", Cooldown)
