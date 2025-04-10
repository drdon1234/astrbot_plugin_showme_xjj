from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import aiohttp
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "https://dayu.qqsuu.cn/moyuribaoshipin/apis.php?type=json"


@register("astrbot_plugin_showme_xjj", "drdon1234", "随机小姐姐视频", "1.0", "https://github.com/drdon1234/astrbot_plugin_showme_xjj")
class randomXJJPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.http_host = "192.168.5.2"
        self.http_port = 13000
        self.api_token = ""

    def get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        return headers

    async def get_video_url(self, session):
        try:
            async with session.get(API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"API返回数据: {data}")
                    if data.get("code") == 200 and data.get("msg") == "success":
                        return data.get("data")
                return None
        except Exception as e:
            logger.error(f"获取视频URL时发生错误: {str(e)}")
            return None

    async def send_video(self, session, target_id, video_url, is_private, file_name="moyu_daily.mp4"):
        payload = {
            "user_id" if is_private else "group_id": target_id,
            "file": video_url,  # 视频URL
            "name": file_name   # 文件名
        }
        
        logger.info(f"发送视频请求体: {payload}")
        
        endpoint = "send_private_video" if is_private else "send_group_video"
        url = f"http://{self.http_host}:{self.http_port}/{endpoint}"
        
        headers = self.get_headers()
        
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return False, f"发送失败，HTTP状态码: {response.status}, 错误: {error_text}"
                
                res = await response.json()
                logger.info(f"发送视频响应: {res}")
                
                if res.get("status") != "ok":
                    return False, f"发送失败，API错误: {res.get('message', '未知错误')}"
                
                return True, "发送成功"
        except Exception as e:
            logger.error(f"发送视频时发生异常: {str(e)}")
            return False, f"发送异常: {str(e)}"

    @filter.command("摸鱼日报")
    async def moyu_command(self, event: AstrMessageEvent):
        yield event.plain_result("正在获取今日摸鱼日报视频...")

        async with aiohttp.ClientSession() as session:
            video_url = await self.get_video_url(session)
            if not video_url:
                yield event.plain_result("无法获取今日摸鱼日报视频，请稍后再试。")
                return
                
            is_private = event.is_private_chat()
            target_id = event.get_sender_id() if is_private else event.get_group_id()
            
            try:
                if hasattr(event, 'video_result'):
                    yield event.video_result(video_url)
                    logger.info(f"使用event.video_result发送视频: {video_url}")
                else:
                    success, message = await self.send_video(session, target_id, video_url, is_private)
                    if success:
                        yield event.plain_result("摸鱼日报视频已发送")
                        logger.info("视频发送成功")
                    else:
                        yield event.plain_result(f"发送视频失败: {message}\n视频链接: {video_url}")
                        logger.warning(f"发送视频失败: {message}")
            except Exception as e:
                logger.error(f"发送视频时出错: {str(e)}")
                yield event.plain_result(f"发送视频时出错: {str(e)}\n视频链接: {video_url}")

    async def terminate(self):
        pass
