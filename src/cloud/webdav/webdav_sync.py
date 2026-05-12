#!/usr/bin/env python3
"""
UniCore Cloud Module 2: WebDAV 坚果云集成
==========================================
支持：坚果云、OwnCloud、NextCloud 等 WebDAV 协议网盘
功能：文件同步、增量备份、冲突处理
"""

import os
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    size: int
    modified: str
    is_dir: bool


class WebDAVClient:
    """WebDAV 客户端"""
    
    NS = {
        'd': 'DAV:',
        'oc': 'http://owncloud.org/ns'
    }
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({
            'User-Agent': 'UniCore/1.0'
        })
    
    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """发起请求"""
        url = f"{self.host}{path}"
        response = self.session.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response
    
    def propfind(self, path: str = '/', depth: int = 1) -> List[FileInfo]:
        """列出目录内容"""
        url = f"{self.host}{path}"
        headers = {'Depth': str(depth)}
        
        body = '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:allprop/></d:propfind>'
        
        response = self.session.request('PROPFIND', url, headers=headers, data=body)
        
        files = []
        if response.status_code in (200, 207):
            root = ET.fromstring(response.content)
            for resp in root.findall('.//d:response', self.NS):
                href = resp.find('d:href', self.NS)
                if href is not None:
                    file_path = href.text
                    props = resp.find('.//d:propstat/d:prop', self.NS)
                    
                    if props is not None:
                        resource_type = props.find('d:resourcetype', self.NS)
                        is_dir = resource_type is not None and len(resource_type) > 0
                        
                        getcontentlength = props.find('d:getcontentlength', self.NS)
                        getlastmodified = props.find('d:getlastmodified', self.NS)
                        
                        size = int(getcontentlength.text) if getcontentlength is not None else 0
                        modified = getlastmodified.text if getlastmodified is not None else ''
                        
                        files.append(FileInfo(
                            path=file_path,
                            name=os.path.basename(file_path.rstrip('/')),
                            size=size,
                            modified=modified,
                            is_dir=is_dir
                        ))
        
        return files
    
    def upload(self, remote_path: str, content: bytes) -> bool:
        """上传文件"""
        url = f"{self.host}{remote_path}"
        headers = {'Content-Type': 'application/octet-stream'}
        
        response = self.session.put(url, data=content, headers=headers)
        return response.status_code in (200, 201, 204)
    
    def download(self, remote_path: str) -> Optional[bytes]:
        """下载文件"""
        url = f"{self.host}{remote_path}"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.content
        return None
    
    def delete(self, remote_path: str) -> bool:
        """删除文件/目录"""
        url = f"{self.host}{remote_path}"
        response = self.session.delete(url)
        return response.status_code in (200, 204)
    
    def mkdir(self, remote_path: str) -> bool:
        """创建目录"""
        url = f"{self.host}{remote_path}"
        headers = {'Content-Type': 'application/xml'}
        body = '<?xml version="1.0"?><d:mkcol xmlns:d="DAV:"/>'
        
        response = self.session.request('MKCOL', url, headers=headers, data=body)
        return response.status_code in (200, 201, 405)
    
    def exists(self, remote_path: str) -> bool:
        """检查文件是否存在"""
        url = f"{self.host}{remote_path}"
        response = self.session.head(url)
        return response.status_code == 200


class NutstoreSync:
    """坚果云同步引擎"""
    
    def __init__(self, username: str, password: str):
        self.client = WebDAVClient(
            host="https://dav.jianguoyun.com/dav/",
            username=username,
            password=password
        )
        self.base_path = "/UniCore"
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """确保基础目录存在"""
        if not self.client.exists(self.base_path):
            self.client.mkdir(self.base_path)
            logger.info(f"✅ 创建基础目录: {self.base_path}")
    
    def _compute_hash(self, content: bytes) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content).hexdigest()[:16]
    
    def _get_sync_path(self, category: str, filename: str) -> str:
        """获取同步路径"""
        return f"{self.base_path}/{category}/{filename}"
    
    def _ensure_category_dir(self, category: str):
        """确保分类目录存在"""
        dir_path = f"{self.base_path}/{category}"
        if not self.client.exists(dir_path):
            self.client.mkdir(dir_path)
    
    def upload_data(self, category: str, filename: str, data: Any) -> bool:
        """上传数据（JSON）"""
        import json
        
        self._ensure_category_dir(category)
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        remote_path = self._get_sync_path(category, filename)
        
        success = self.client.upload(remote_path, content.encode('utf-8'))
        
        if success:
            logger.info(f"✅ 上传数据: {remote_path}")
        
        return success
    
    def download_data(self, category: str, filename: str) -> Optional[Any]:
        """下载数据"""
        import json
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        remote_path = self._get_sync_path(category, filename)
        content = self.client.download(remote_path)
        
        if content:
            return json.loads(content.decode('utf-8'))
        return None
    
    def list_category(self, category: str) -> List[FileInfo]:
        """列出分类下的文件"""
        dir_path = f"{self.base_path}/{category}"
        return self.client.propfind(dir_path, depth=1)
    
    def sync_file(self, category: str, local_path: str) -> bool:
        """同步本地文件"""
        import shutil
        
        filename = os.path.basename(local_path)
        remote_path = self._get_sync_path(category, filename)
        
        with open(local_path, 'rb') as f:
            content = f.read()
        
        return self.client.upload(remote_path, content)
    
    def backup_with_version(self, category: str, data: Any, max_versions: int = 5) -> str:
        """带版本控制的备份"""
        import json
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_file = f"version_{timestamp}.json"
        
        version_data = {
            "timestamp": timestamp,
            "data": data,
            "hash": self._compute_hash(json.dumps(data, sort_keys=True).encode())
        }
        
        remote_path = self._get_sync_path(category, version_file)
        content = json.dumps(version_data, indent=2, ensure_ascii=False)
        
        self.client.upload(remote_path, content.encode('utf-8'))
        
        self._cleanup_old_versions(category, max_versions)
        
        return remote_path
    
    def _cleanup_old_versions(self, category: str, max_versions: int):
        """清理旧版本"""
        files = self.list_category(category)
        json_files = [f for f in files if f.name.startswith('version_') and f.name.endswith('.json')]
        
        if len(json_files) > max_versions:
            json_files.sort(key=lambda f: f.modified, reverse=True)
            
            for old_file in json_files[max_versions:]:
                file_path = f"{self.base_path}/{category}/{old_file.name}"
                self.client.delete(file_path)
                logger.info(f"🗑️  删除旧版本: {old_file.name}")
    
    def get_latest_backup(self, category: str) -> Optional[Dict]:
        """获取最新备份"""
        files = self.list_category(category)
        json_files = [f for f in files if f.name.startswith('version_') and f.name.endswith('.json')]
        
        if json_files:
            json_files.sort(key=lambda f: f.modified, reverse=True)
            latest = json_files[0]
            
            remote_path = f"{self.base_path}/{category}/{latest.name}"
            content = self.client.download(remote_path)
            
            if content:
                return json.loads(content.decode('utf-8'))
        
        return None
    
    def sync_directory(self, category: str, local_dir: str) -> Dict[str, bool]:
        """同步整个目录"""
        results = {}
        
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                results[local_path] = self.sync_file(category, local_path)
        
        return results
    
    def create_sync_index(self, category: str, data: Dict) -> bool:
        """创建同步索引"""
        index_filename = f"{category}_index.json"
        
        index_data = {
            "category": category,
            "updated": datetime.now().isoformat(),
            "files": data
        }
        
        return self.upload_data("_index", index_filename, index_data)


def create_nutstore_sync(username: str, password: str) -> NutstoreSync:
    """创建坚果云同步实例"""
    return NutstoreSync(username, password)


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════╗
║    UniCore Cloud Module 2: WebDAV / 坚果云 Sync        ║
╚════════════════════════════════════════════════════════╝

支持的 WebDAV 服务：
✅ 坚果云 (dav.jianguoyun.com)
✅ OwnCloud
✅ NextCloud
✅ Seafile
✅ 其他 WebDAV 协议服务

使用方法：
1. 配置坚果云账号:
   export NUTSTORE_USER="your_email@email.com"
   export NUTSTORE_PASS="your_password"

2. 在代码中使用:
   from webdav_sync import NutstoreSync
   
   sync = NutstoreSync("email", "password")
   
   # 上传数据
   sync.upload_data("config", "settings", {"key": "value"})
   
   # 下载数据
   data = sync.download_data("config", "settings")
   
   # 带版本备份
   sync.backup_with_version("data", {"important": "data"}, max_versions=5)

其他 WebDAV 服务：
OwnCloud:   https://your-server/remote.php/dav/files/user/
NextCloud:  https://your-server/remote.php/dav/files/user/
""")

    user = os.environ.get('NUTSTORE_USER', '__USER__')
    if user.startswith('__'):
        print("\n⚠️  请设置坚果云账号")
        print("   export NUTSTORE_USER=\"your@email.com\"")
        print("   export NUTSTORE_PASS=\"password\"")
    else:
        print(f"\n✅ WebDAV 同步模块就绪！")
        print(f"   用户: {user}")


if __name__ == "__main__":
    demo()
