from astrbot.api.event import AstrMessageEvent
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageAdapter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_type = self.config["platform"]["type"]
        self.http_host = self.config["platform"]["http_host"]
        self.http_port = self.config["platform"]["http_port"]
        self.api_token = self.config["platform"]["api_token"]

    def get_headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        return headers

    async def get_group_root_files(self, group_id: str) -> Dict[str, Any]:
        url = f"http://{self.http_host}:{self.http_port}/get_group_root_files"
        payload = {"group_id": group_id}
        headers = self.get_headers()

        logger.debug(f"发送给消息平台-> {payload}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"获取群文件根目录失败，状态码: {response.status}, 错误信息: {error_text}")

                res = await response.json()
                if res["status"] != "ok":
                    raise Exception(f"获取群文件根目录失败，状态码: {res['status']}\n完整消息: {str(res)}")

                return res["data"]

    async def create_group_file_folder(self, group_id: str, folder_name: str) -> Optional[str]:
        url = f"http://{self.http_host}:{self.http_port}/create_group_file_folder"

        if self.platform_type == 'napcat':
            payload = {
                "group_id": group_id,
                "folder_name": folder_name
            }
        elif self.platform_type == 'llonebot':
            payload = {
                "group_id": group_id,
                "name": folder_name
            }
        elif self.platform_type == 'lagrange':
            payload = {
                "group_id": group_id,
                "name": folder_name,
                "parent_id": "/"
            }
        else:
            raise Exception("消息平台配置有误, 只能是'napcat', 'llonebot'或'lagrange'")

        headers = self.get_headers()
        logger.debug(f"发送给消息平台-> {payload}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"创建群文件夹失败，状态码: {response.status}, 错误信息: {error_text}")

                res = await response.json()
                logger.debug(f"消息平台返回-> {res}")

                if res["status"] != "ok":
                    raise Exception(f"创建群文件夹失败，状态码: {res['status']}\n完整消息: {str(res)}")

                try:
                    return res["data"]["folder_id"]
                except Exception:
                    return None

    async def get_group_folder_id(self, group_id: str, folder_name: str = '/') -> str:
        if folder_name == '/':
            return '/'

        data = await self.get_group_root_files(group_id)
        for folder in data.get('folders', []):
            if folder.get('folder_name') == folder_name:
                return folder.get('folder_id')

        folder_id = await self.create_group_file_folder(group_id, folder_name)
        if folder_id is None:
            data = await self.get_group_root_files(group_id)
            for folder in data.get('folders', []):
                if folder.get('folder_name') == folder_name:
                    return folder.get('folder_id')
            return "/"

        return folder_id

    async def upload_file(self, event: AstrMessageEvent, path: str, name: str = None, folder_name: str = '/') -> Dict[str, Any]:
        # 检测是否为网络链接
        is_url = path.startswith(('http://', 'https://'))
        temp_file = None
        
        try:
            if is_url:
                # 处理网络链接 - 下载到临时文件
                await event.send(event.plain_result(f"正在从网络下载文件，请稍候..."))
                temp_dir = Path(tempfile.gettempdir()) / "astrbot_downloads"
                temp_dir.mkdir(exist_ok=True)
                
                # 生成临时文件
                temp_file = temp_dir / f"{uuid.uuid4()}"
                
                # 下载文件
                async with aiohttp.ClientSession() as session:
                    async with session.get(path) as response:
                        response.raise_for_status()
                        content_type = response.headers.get('Content-Type', '')
                        
                        # 根据Content-Type推断文件扩展名
                        if 'image' in content_type:
                            if 'jpeg' in content_type or 'jpg' in content_type:
                                temp_file = temp_file.with_suffix('.jpg')
                            elif 'png' in content_type:
                                temp_file = temp_file.with_suffix('.png')
                            else:
                                temp_file = temp_file.with_suffix('.img')
                        elif 'video' in content_type:
                            if 'mp4' in content_type:
                                temp_file = temp_file.with_suffix('.mp4')
                            else:
                                temp_file = temp_file.with_suffix('.video')
                        else:
                            # 从URL中提取扩展名
                            url_path = urlparse(path).path
                            if '.' in url_path:
                                extension = Path(url_path).suffix
                                if extension:
                                    temp_file = temp_file.with_suffix(extension)
                        
                        # 保存文件内容
                        with open(temp_file, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
                
                # 使用临时文件路径
                file_path = temp_file
                
                # 从URL中提取文件名，如果name未提供
                if name is None:
                    url_path = urlparse(path).path
                    file_name = url_path.split('/')[-1] or "downloaded_file"
                    # 确保文件名与临时文件的后缀匹配
                    file_name = f"{Path(file_name).stem}{temp_file.suffix}"
                else:
                    file_name = f"{name}{temp_file.suffix}"
            else:
                # 处理本地文件路径
                file_path = Path(path)
                if not file_path.exists():
                    raise FileNotFoundError(f"文件不存在: {path}")
                
                # 确定文件名
                if name is None:
                    file_name = file_path.name
                else:
                    file_name = f"{name}{file_path.suffix}"
            
            # 发送上传通知
            await event.send(event.plain_result(f"发送 {file_name} 中，请稍候..."))
            
            # 上传文件
            is_private = event.is_private_chat()
            target_id = event.get_sender_id() if is_private else event.get_group_id()
            url_type = "upload_private_file" if is_private else "upload_group_file"
            url = f"http://{self.http_host}:{self.http_port}/{url_type}"
            
            payload = {
                "file": str(file_path),
                "name": file_name,
                "user_id" if is_private else "group_id": target_id
            }
            
            if not is_private:
                payload["folder_id"] = await self.get_group_folder_id(target_id, folder_name)
            
            try:
                headers = self.get_headers()
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        res = await response.json()
                        
                        if res["status"] != "ok":
                            result = {"success": False, "error": res.get("message")}
                        else:
                            result = {"success": True, "data": res.get("data")}
            except Exception as e:
                result = {"success": False, "error": str(e)}
                logger.warning(f"文件上传失败: {e}")
            
            if result["success"]:
                successes = [result["data"]]
                errors = []
            else:
                successes = []
                errors = [result["error"]]
                logger.warning(f"文件上传失败: {result['error']}")
            
            return {
                "total": 1,
                "success_count": len(successes),
                "failed_count": len(errors),
                "details": {
                    "successes": successes,
                    "errors": errors
                }
            }
        
        except Exception as e:
            logger.error(f"上传处理异常: {e}")
            return {
                "total": 1,
                "success_count": 0,
                "failed_count": 1,
                "details": {
                    "successes": [],
                    "errors": [str(e)]
                }
            }
        finally:
            # 如果使用了临时文件，尝试清理它
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")
