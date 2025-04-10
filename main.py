from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from .utils.config_manager import load_config
from .utils.message_adapter import MessageAdapter
from .utils.parser import get_url
from pathlib import Path
import aiohttp
import asyncio
import json
import random
import logging

@register("astrbot_plugin_showme_xjj", "drdon1234", "随机小姐姐美图短视频", "1.0")
class randomXJJPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.config = load_config(Path(__file__).parent / "config.yaml")
        self.uploader = MessageAdapter(self.config)

    async def get_random_media(self, event: AstrMessageEvent, media_type="video"):
        cache_folder = Path(self.config['download']['cache_folder'])
        cache_folder.mkdir(exist_ok=True, parents=True)
        if media_type == "video":
            text = "视频"
            ext = "mp4"
            api_list = self.config["api"]["video_api"]
        elif media_type == "picture":
            text = "图片"
            ext = "jpg"
            api_list = self.config["api"]["picture_api"]
        else:
            raise ValueError(f"不支持的媒体类型: {media_type}")
    
        api_config = random.choice(api_list)
        result = await get_url(api_config, cache_folder)
        try:
            await event.send(event.plain_result(f"xjj{text}正在赶来的路上，请接收..."))
            await self.uploader.upload_file(event, result, f"xjj{text}.{ext}")
        except Exception as e:
            await event.send(event.plain_result(f"获取随机视频失败: {e}"))
    
    @filter.command("xjj视频")
    async def random_video(self, event: AstrMessageEvent):
        await self.get_random_media(event, "video")

    @filter.command("xjj图片")
    async def random_picture(self, event: AstrMessageEvent):
        await self.get_random_media(event, "picture")

    async def terminate(self):
        pass
