import os
import aiohttp
from urllib.parse import urlparse
from typing import Dict, Any
import uuid

async def get_url(api_config: Dict[str, Any], cache_folder: str) -> str:
    """
    处理API管道流程，返回直接URL或下载文件的本地路径。
    
    Args:
        api_config: 包含'url'和'pipeline'的API配置
        cache_folder: 下载文件的缓存文件夹
        
    Returns:
        直接URL或下载文件的本地路径
    """
    url = api_config["url"]
    pipeline_steps = api_config["pipeline"].split(" | ")
    
    async with aiohttp.ClientSession() as session:
        current_data = None
        current_url = url
        
        for step in pipeline_steps:
            if step == "fetch":
                # 请求URL
                async with session.get(current_url, allow_redirects=True) as response:
                    if response.status != 200:
                        raise Exception(f"获取URL失败: {current_url}, 状态码: {response.status}")
                    
                    # 尝试解析为JSON
                    try:
                        current_data = await response.json()
                    except:
                        # 如果不是JSON，使用响应的URL
                        current_url = str(response.url)
                        current_data = None
            
            elif step == "direct_url":
                # 直接返回当前URL
                return current_url
            
            elif step == "download_url":
                # 下载当前URL并返回文件路径
                # 如果缓存文件夹不存在，创建它
                os.makedirs(cache_folder, exist_ok=True)
                
                # 解析URL以获取文件扩展名
                parsed_url = urlparse(current_url)
                file_ext = os.path.splitext(parsed_url.path)[1]
                if not file_ext:
                    file_ext = ".mp4" if "video" in current_url.lower() else ".jpg"
                
                # 生成唯一文件名
                filename = f"{uuid.uuid4()}{file_ext}"
                filepath = os.path.join(cache_folder, filename)
                
                # 下载文件
                async with session.get(current_url, allow_redirects=True) as response:
                    if response.status != 200:
                        raise Exception(f"下载文件失败: {current_url}, 状态码: {response.status}")
                    
                    with open(filepath, 'wb') as file:
                        file.write(await response.read())
                    
                    return filepath
            
            else:
                # 对于任何其他步骤，从当前数据中提取字段
                if current_data is None:
                    raise Exception(f"没有数据可以提取'{step}'")
                
                if isinstance(current_data, dict) and step in current_data:
                    value = current_data[step]
                    
                    # 如果值是字符串并且看起来像URL，更新当前URL
                    if isinstance(value, str) and (value.startswith("http://") or value.startswith("https://")):
                        current_url = value
                        current_data = None
                    else:
                        # 否则，更新当前数据用于下一步
                        current_data = value
                else:
                    raise Exception(f"在响应中找不到键'{step}': {current_data}")
    
    raise Exception("管道流程未以direct_url或download_url结束")
