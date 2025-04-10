from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from .utils.config_manager import load_config
from .utils.message_adapter import upload_file
import aiohttp
import asyncio
import json
import logging

upload_file(self, event: AstrMessageEvent, path: str, name: str = None, folder_name: str = '/')

@register("astrbot_plugin_showme_xjj", "drdon1234", "随机小姐姐视频", "1.0", "https://github.com/drdon1234/astrbot_plugin_showme_xjj")
class randomXJJPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.config = load_config()

    async def get_random_media(self, media_type="video"):
        if media_type == "video":
            api_list = self.config["api"]["video_api"]
        elif media_type == "picture":
            api_list = self.config["api"]["picture_api"]
        else:
            raise ValueError(f"不支持的媒体类型: {media_type}")
    
        api_config = random.choice(api_list)
        cache_folder = self.config["download"]["cache_folder"]
        result = await get_url(api_config, cache_folder)
    
        return result
    
    @filter.command("xjj视频")
    async def moyu_daily(self, event: AstrMessageEvent):
        cache_folder = Path(self.config['output']['cache_folder'])
        cache_folder.mkdir(exist_ok=True, parents=True)
        try:
            video_url = await get_random_media("video")
            print(f"随机视频: {video_url}")
        except Exception as e:
            print(f"获取视频失败: {e}")

    @filter.command("xjj图片")
    async def moyu_daily(self, event: AstrMessageEvent):
        try:
            picture_url = await get_random_media("picture")
            print(f"随机图片: {picture_url}")
        except Exception as e:
            print(f"获取图片失败: {e}")

    
    
    async def terminate(self):
        pass
