from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
import aiohttp
import tempfile
import os
import asyncio


@register("zhiyu-astrbot-hjm", "知鱼", "一款随机哈基米语音的AstrBot插件", "2.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "http://api.ocoa.cn/api/hjm.php?type=audio"

    # 保持原有“包含哈基米就触发”的行为，但避免与“全员哈基米”新指令重复触发
    @filter.regex(r"^(?!\s*全员哈基米\s*$).*哈基米.*")
    async def wsde_handler(self, message: AstrMessageEvent):
        temp_path = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                            temp_path = temp_file.name
                            audio_content = await response.read()
                            temp_file.write(audio_content)
                        
                        chain = [Record.fromFileSystem(temp_path)]
                        yield message.chain_result(chain)
                    else:
                        yield message.plain_result("获取哈基米语音失败 请稍后重试")
        except Exception as e:
            yield message.plain_result(f"获取语音时出错：{str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.regex(r"^\s*全员哈基米\s*$")
    async def hjm_broadcast_all_groups(self, event: AiocqhttpMessageEvent):
        """管理员发送“全员哈基米”时：给所有群聊发送一段哈基米语音。"""
        temp_path = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    if response.status != 200:
                        yield event.plain_result("获取哈基米语音失败 请稍后重试")
                        return

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_path = temp_file.name
                        audio_content = await response.read()
                        temp_file.write(audio_content)

            # 仅编码一次，避免对每个群重复读取/编码文件
            record = Record.fromFileSystem(temp_path)
            bs64 = await record.convert_to_base64()
            payload = [{"type": "record", "data": {"file": f"base64://{bs64}"}}]

            groups = await event.bot.get_group_list()
            success = 0
            failed = 0
            for g in groups:
                gid = g.get("group_id")
                if gid is None:
                    continue
                try:
                    await event.bot.send_group_msg(group_id=int(gid), message=payload)
                    success += 1
                except Exception:
                    failed += 1
                # 简单限速，降低风控/频率限制风险
                await asyncio.sleep(0.2)

            yield event.plain_result(
                f"全员哈基米已发送：成功{success}个群，失败{failed}个群"
            )

        except Exception as e:
            yield event.plain_result(f"全员哈基米执行失败：{str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
