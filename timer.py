import asyncio
import logging
import sys, time

import pykeybasebot.types.chat1 as chat1
from pykeybasebot import Bot

logging.basicConfig(level=logging.DEBUG)

if "win32" in sys.platform:
    # Windows specific event-loop policy
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()  # type: ignore
    )


helptext = """
`This bot is used to start a timer. It shows in minutes:seconds format.`\n `To use the bot, just type 
'!timer 15min 2sec' to start 15 minutes 2 seconds timer or '!timer 10' to start 10 minutes timer.` \n
`You can also stop the timer using '!timer stop'.`\n 
`Note that trial version supports only upto 60 minutes.`
"""


def extract_time(msg_parts):
    try:
        if len(msg_parts) == 1:
            return 1, int(msg_parts[0]) * 60
        total_time = 0
        i = 0
        mt = 0
        while i < len(msg_parts):
            if msg_parts[i + 1] == 'sec' or msg_parts[i + 1] == 'seconds' or msg_parts[i + 1] == 'second':
                total_time += int(msg_parts[i])
            elif msg_parts[i + 1] == 'min' or msg_parts[i + 1] == 'minutes' or msg_parts[i + 1] == 'minute':
                total_time += int(msg_parts[i]) * 60
            else:
                raise Exception
            i += 2
    except Exception as e:
        print(e)
        return -1, 0
    if total_time >= 3600:
        mt = 2
    elif total_time >= 60:
        mt = 1
    else:
        mt = 0
    return mt, total_time


channel_msg = {}


def format_msg(msg):
    if not msg[0].isdigit():
        return msg
    i, k = 0, 0
    lm = len(msg)
    fmsg = ''
    while i < lm:
        if msg[i].isdigit():
            fmsg = fmsg + ' '
            k = i
            while i < lm and msg[i].isdigit():
                i = i + 1
            fmsg = fmsg + msg[k:i] + ' '
            continue
        fmsg = fmsg + msg[i]
        i = i + 1
    return fmsg.split()


async def handler(bot, event):
    if event.msg.content.type_name != chat1.MessageTypeStrings.TEXT.value:
        return

    before = "--[ `"
    after = "` ]--"

    msg = str(event.msg.content.text.body).lower()
    msg_parts = msg.split(" ")

    if msg_parts[0] == "!timer":
        channel = event.msg.channel

        if len(msg_parts) == 1:
            await bot.chat.send(channel, "`Please specify time.`")
        elif msg_parts[1] == 'help':
            await bot.chat.send(channel, helptext)
        elif msg_parts[1] == 'stop':
            command = {"method": "unpin", "params": {"options": {"message_id": channel_msg[str(channel)][-1], "channel": channel.to_dict()}}}
            await bot.chat.execute(command)
            await bot.chat.execute({"method": "delete", "params": {"options": {"channel": channel.to_dict(), "message_id": channel_msg[str(channel)][-1]}}})
        elif msg_parts[1] == 'commands':
            command = {"method": "listcommands", "params": {"options": {"channel": channel.to_dict()}}}
            await bot.chat.execute(command)
        else:
            msg_parts = format_msg(msg[7:])
            mt, total_time = extract_time(msg_parts)
            st = time.time()
            ed = st + int(total_time)

            if mt == -1:
                await bot.chat.send(channel, "`Please use correct format. For help, use !timer help`")
            elif mt == 2:
                await bot.chat.send(channel, "`Time period is more than an hour. Please upgrade or set lesser time period.`")
            else:
                ft = ''
                if mt == 0:
                    ft = '%S'
                else:
                    ft = '%M:%S'

                result = await bot.chat.send(channel, f"{before}{time.strftime(ft, time.gmtime(ed - time.time()))}{after}")
                msg_id = result.message_id

                if str(channel) in channel_msg:
                    channel_msg[str(channel)].append(msg_id)
                else:
                    channel_msg[str(channel)] = [msg_id]
                diff = ed - time.time()

                command = {"method": "pin", "params": {"options": {"message_id": msg_id, "channel": channel.to_dict()}}}

                await bot.chat.execute(command)

                while diff > 0:
                    sst = time.time()
                    await bot.chat.edit(channel, msg_id,
                                        f"{before}{time.strftime(ft, time.gmtime(diff))}{after}")

                    await asyncio.sleep(1 - time.time() + sst)
                    diff = ed - time.time()
                command = {"method": "unpin", "params": {
                    "options": {"message_id": msg_id, "channel": channel.to_dict()}}}
                await bot.chat.execute(command)


listen_options = {
    "local": False,
    "wallet": False,
    "dev": True,
    "hide-exploding": False,
    "convs": True,
    "filter_channel": None,
    "filter_channels": None,
}

bot = Bot(
    # you don't need to pass in a username or paperkey if you're already logged in
    handler=handler
)

asyncio.run(bot.start(listen_options))
