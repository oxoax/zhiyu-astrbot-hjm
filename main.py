from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
import aiohttp
import tempfile
import os
import brotli


@register("zhiyu-astrbot-hjm", "知鱼", "一款随机哈基米语音的AstrBot插件", "2.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "http://api.ocoa.cn/api/hjm.php?type=audio"

    @filter.regex(r".*哈基米.*")
    async def wsde_handler(self, message: AstrMessageEvent):
        temp_path = None
        try:
            headers = {"Accept-Encoding": "identity"}
            async with aiohttp.ClientSession(auto_decompress=False) as session:
                async with session.get(self.api_url, headers=headers) as response:
                    if response.status == 200:
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".mp3"
                        ) as temp_file:
                            temp_path = temp_file.name
                            audio_content = await response.read()
                            if (
                                response.headers.get("Content-Encoding", "").lower()
                                == "br"
                            ):
                                audio_content = brotli.decompress(audio_content)
                            temp_file.write(audio_content)

                        chain = [Record.fromFileSystem(temp_path)]
                        yield message.chain_result(chain)
                    else:
                        yield message.plain_result(
                            f"获取哈基米语音失败（HTTP {response.status}）请稍后重试"
                        )
        except Exception as e:
            yield message.plain_result(f"获取语音时出错：{str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
