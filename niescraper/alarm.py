import asyncio
import importlib.resources

import aioconsole
from playsound import playsound

import niescraper.resources


async def play_alarm():
    with importlib.resources.path(niescraper.resources, 'alarm.mp3') as alarm_file:
        while asyncio.get_running_loop().is_running():
            playsound(alarm_file, False)
            await asyncio.sleep(0.5)


async def play_alarm_until_input_async():
    alarm_task = asyncio.create_task(play_alarm())
    await aioconsole.ainput("Please press Enter to acknowledge alarm...")
    alarm_task.cancel()


def play_alarm_until_input():
    asyncio.run(play_alarm_until_input_async())
