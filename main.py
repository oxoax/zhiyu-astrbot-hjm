from astrbot.api.all import *
from astrbot.api.event import filter, AstrMessageEvent
import aiohttp
import tempfile
import os


@register("zhiyu-astrbot-hjm", "知鱼", "随机哈基米语音的AstrBot插件", "1.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "http://api.ocoa.cn/api/hjm.php?type=audio"

    @filter.regex(r".*哈基米.*")
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
                        pass
        except Exception as e:
            pass
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
