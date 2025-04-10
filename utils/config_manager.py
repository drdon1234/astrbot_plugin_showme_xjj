import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, Any, Union, List

logger = logging.getLogger(__name__)

def parse_pipeline(pipeline_str: str) -> List[str]:
    """将管道字符串解析为操作步骤列表"""
    if not pipeline_str:
        return []
    
    return [step.strip() for step in pipeline_str.split('|')]

def load_api_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
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
