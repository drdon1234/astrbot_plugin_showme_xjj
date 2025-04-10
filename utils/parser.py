import os
import json
import logging
import aiohttp
import asyncio
import random
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


async def process_api_request(url: str, pipeline: List[str], cache_folder: str) -> Optional[str]:
    try:
        if not pipeline or pipeline[0] != "fetch":
            logger.error(f"管道必须以'fetch'开始，得到的是: {pipeline}")
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"无法获取API: {url}。状态码: {response.status}")
                    return None
                
                current_data = response
                
                for step in pipeline[1:]:
                    if step == "json":
                        if isinstance(current_data, aiohttp.ClientResponse):
                            try:
                                current_data = await current_data.json()
                            except json.JSONDecodeError:
                                logger.error(f"无法从API解析JSON: {url}")
                                return None
                        else:
                            logger.error(f"JSON解析需要ClientResponse对象，得到的是 {type(current_data)}")
                            return None
                    
                    elif step == "direct_url":
                        if isinstance(current_data, aiohttp.ClientResponse):
                            return url
                        elif isinstance(current_data, str):
                            return current_data
                        else:
                            logger.error(f"需要URL字符串或ClientResponse对象，得到的是 {type(current_data)}")
                            return None
                    
                    elif step == "download_url":
                        download_url = None
                        
                        if isinstance(current_data, aiohttp.ClientResponse):
                            download_url = url
                        elif isinstance(current_data, str):
                            download_url = current_data
                        
                        if download_url:
                            return await download_file(download_url, cache_folder)
                        else:
                            logger.error("没有有效的下载URL")
                            return None
                    
                    else:
                        if isinstance(current_data, dict) and step in current_data:
                            current_data = current_data[step]
                        else:
                            logger.error(f"无法从数据中提取'{step}'")
                            return None
                
                if isinstance(current_data, str) and (current_data.startswith('http://') or current_data.startswith('https://')):
                    return current_data
                
                logger.error("管道处理完成但没有生成URL")
                return None
    
    except Exception as e:
        logger.error(f"处理API {url}时出错: {str(e)}")
        return None

async def download_file(url: str, cache_folder: str) -> Optional[str]:
    try:
        os.makedirs(cache_folder, exist_ok=True)
        local_filename = os.path.basename(url.split('?')[0])
        
        if not local_filename:
            import hashlib
            hash_object = hashlib.md5(url.encode())
            local_filename = f"download_{hash_object.hexdigest()}"
        
        local_path = os.path.join(cache_folder, local_filename)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"下载文件失败: {url}。状态码: {response.status}")
                    return None
                
                with open(local_path, 'wb') as f:
                    chunk_size = 8192
                    while True:
                        chunk = await response.content.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
        
        return local_path
    
    except Exception as e:
        logger.error(f"下载文件 {url} 时出错: {str(e)}")
        return None

def parse_pipeline(pipeline_str: str) -> List[str]:
    """将管道字符串解析为操作步骤列表"""
    if not pipeline_str:
        return []
    
    return [step.strip() for step in pipeline_str.split('|')]

async def load_api_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    import yaml
    
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            
        platform_config = config.setdefault('platform', {})
        platform_config.setdefault('type', 'napcat')
        platform_config.setdefault('http_host', '127.0.0.1')
        platform_config.setdefault('http_port', 2333)
        platform_config.setdefault('api_token', '')
        
        api_config = config.setdefault('api', {})
        video_api = api_config.setdefault('video_api', [])
        picture_api = api_config.setdefault('picture_api', [])
        
        for api_entry in video_api:
            if isinstance(api_entry, dict) and 'pipeline' in api_entry:
                api_entry['pipeline_steps'] = parse_pipeline(api_entry['pipeline'])
                
        for api_entry in picture_api:
            if isinstance(api_entry, dict) and 'pipeline' in api_entry:
                api_entry['pipeline_steps'] = parse_pipeline(api_entry['pipeline'])
        
        download_config = config.setdefault('download', {})
        download_config.setdefault('cache_folder', '/app/sharedFolder')
        
        return config
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"配置文件格式错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"配置文件加载失败: {str(e)}")
        raise

async def get_random_video(config: Dict[str, Any]) -> Optional[str]:
    
    
    try:
        video_apis = config.get('api', {}).get('video_api', [])
        if not video_apis:
            logger.error("配置中没有视频API")
            return None
            
        api_entry = random.choice(video_apis)
        url = api_entry.get('url')
        pipeline_steps = api_entry.get('pipeline_steps')
        cache_folder = config.get('download', {}).get('cache_folder', '/app/sharedFolder')
        
        if not url or not pipeline_steps:
            logger.error("无效的API配置")
            return None
            
        return await process_api_request(url, pipeline_steps, cache_folder)
    except Exception as e:
        logger.error(f"获取随机视频时出错: {str(e)}")
        return None

async def get_random_picture(config: Dict[str, Any]) -> Optional[str]:
    try:
        picture_apis = config.get('api', {}).get('picture_api', [])
        if not picture_apis:
            logger.error("配置中没有图片API")
            return None
            
        api_entry = random.choice(picture_apis)
        url = api_entry.get('url')
        pipeline_steps = api_entry.get('pipeline_steps')
        cache_folder = config.get('download', {}).get('cache_folder', '/app/sharedFolder')
        
        if not url or not pipeline_steps:
            logger.error("无效的API配置")
            return None
            
        return await process_api_request(url, pipeline_steps, cache_folder)
    except Exception as e:
        logger.error(f"获取随机图片时出错: {str(e)}")
        return None
