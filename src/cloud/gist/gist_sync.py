#!/usr/bin/env python3
"""
UniCore Cloud Module 1: GitHub Gist 数据同步
============================================
使用 GitHub Gist 作为云端数据存储
支持：数据同步、版本管理、多设备共享
"""

import requests
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GistMetadata:
    """Gist 元数据"""
    gist_id: str
    filename: str
    created_at: str
    updated_at: str
    description: str
    version: int


@dataclass
class SyncRecord:
    """同步记录"""
    timestamp: str
    action: str
    data_hash: str
    success: bool
    message: str


class GitHubGistSync:
    """GitHub Gist 同步引擎"""
    
    GIST_INDEX_FILE = "unicore_index.json"
    
    def __init__(self, token: str, username: str = None):
        self.token = token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._index_cache = {}
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发起请求"""
        response = self.session.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return response
    
    def list_gists(self, page: int = 1, per_page: int = 100) -> List[Dict]:
        """列出所有 Gist"""
        url = f"{self.base_url}/gists"
        params = {"page": page, "per_page": per_page}
        response = self._make_request("GET", url, params=params)
        return response.json()
    
    def get_gist(self, gist_id: str) -> Optional[Dict]:
        """获取 Gist 详情"""
        url = f"{self.base_url}/gists/{gist_id}"
        try:
            response = self._make_request("GET", url)
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def create_gist(self, filename: str, content: str, description: str = "") -> Dict:
        """创建 Gist"""
        url = f"{self.base_url}/gists"
        data = {
            "description": description or f"UniCore Data - {filename}",
            "public": False,
            "files": {
                filename: {"content": content}
            }
        }
        response = self._make_request("POST", url, json=data)
        return response.json()
    
    def update_gist(self, gist_id: str, filename: str, content: str) -> Dict:
        """更新 Gist"""
        url = f"{self.base_url}/gists/{gist_id}"
        data = {
            "files": {
                filename: {"content": content}
            }
        }
        response = self._make_request("PATCH", url, json=data)
        return response.json()
    
    def delete_gist(self, gist_id: str) -> bool:
        """删除 Gist"""
        url = f"{self.base_url}/gists/{gist_id}"
        self._make_request("DELETE", url)
        return True
    
    # ==================== UniCore 特定功能 ====================
    
    def _compute_hash(self, data: Any) -> str:
        """计算数据哈希"""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_or_create_index(self) -> Dict:
        """获取或创建索引文件"""
        gists = self.list_gists()
        
        for gist in gists:
            if self.GIST_INDEX_FILE in gist.get("files", {}):
                data = self.get_gist(gist["id"])
                if data:
                    content = data["files"][self.GIST_INDEX_FILE]["content"]
                    return json.loads(content)
        
        index = {"version": 1, "entries": [], "last_sync": None}
        self.create_gist(self.GIST_INDEX_FILE, json.dumps(index, indent=2, ensure_ascii=False), "UniCore Data Index")
        return index
    
    def sync_data(self, data_type: str, data: Dict, tags: List[str] = None) -> str:
        """同步数据到云端"""
        timestamp = datetime.now().isoformat()
        filename = f"{data_type}_{int(time.time())}.json"
        
        record = {
            "type": data_type,
            "timestamp": timestamp,
            "data": data,
            "hash": self._compute_hash(data),
            "tags": tags or []
        }
        
        description = f"UniCore {data_type} | {timestamp}"
        gist = self.create_gist(
            filename=filename,
            content=json.dumps(record, indent=2, ensure_ascii=False),
            description=description
        )
        
        self._update_index(gist["id"], filename, data_type)
        
        logger.info(f"✅ 同步数据: {data_type} -> {gist['id']}")
        return gist["id"]
    
    def _update_index(self, gist_id: str, filename: str, data_type: str):
        """更新索引"""
        index = self._get_or_create_index()
        index["entries"].append({
            "gist_id": gist_id,
            "filename": filename,
            "type": data_type,
            "synced_at": datetime.now().isoformat()
        })
        index["last_sync"] = datetime.now().isoformat()
        
        gists = self.list_gists()
        for gist in gists:
            if self.GIST_INDEX_FILE in gist.get("files", {}):
                self.update_gist(gist["id"], self.GIST_INDEX_FILE, json.dumps(index, indent=2, ensure_ascii=False))
                break
    
    def get_data(self, gist_id: str) -> Optional[Dict]:
        """获取指定 Gist 数据"""
        data = self.get_gist(gist_id)
        if data and "files" in data:
            for filename, file_info in data["files"].items():
                if filename.endswith(".json"):
                    return json.loads(file_info["content"])
        return None
    
    def get_latest_by_type(self, data_type: str) -> Optional[Dict]:
        """获取指定类型的最新数据"""
        index = self._get_or_create_index()
        
        matching = [
            entry for entry in index.get("entries", [])
            if entry.get("type") == data_type
        ]
        
        if matching:
            latest = matching[-1]
            return self.get_data(latest["gist_id"])
        
        return None
    
    def sync_dataframe(self, data_type: str, data_list: List[Dict]) -> List[str]:
        """批量同步数据"""
        gist_ids = []
        for data in data_list:
            gid = self.sync_data(data_type, data)
            gist_ids.append(gid)
        return gist_ids
    
    def get_sync_history(self, data_type: str = None, limit: int = 50) -> List[Dict]:
        """获取同步历史"""
        index = self._get_or_create_index()
        entries = index.get("entries", [])
        
        if data_type:
            entries = [e for e in entries if e.get("type") == data_type]
        
        return entries[-limit:]
    
    def create_backup(self, data: Dict, backup_name: str = None) -> str:
        """创建备份"""
        name = backup_name or f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{name}.json"
        
        backup_data = {
            "backup_name": name,
            "created_at": datetime.now().isoformat(),
            "data": data,
            "version": "1.0"
        }
        
        gist = self.create_gist(
            filename=filename,
            content=json.dumps(backup_data, indent=2, ensure_ascii=False),
            description=f"UniCore Backup - {name}"
        )
        
        logger.info(f"✅ 创建备份: {name} -> {gist['id']}")
        return gist["id"]
    
    def restore_backup(self, gist_id: str) -> Optional[Dict]:
        """恢复备份"""
        data = self.get_data(gist_id)
        if data and "data" in data:
            return data["data"]
        return None


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════╗
║    UniCore Cloud Module 1: GitHub Gist Sync            ║
╚════════════════════════════════════════════════════════╝

功能：
✅ 创建/读取/更新 Gist
✅ 数据同步到云端
✅ 版本管理和备份
✅ 多设备数据共享

使用方法：
1. 设置 GitHub Token:
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

2. 在代码中使用:
   from gist_sync import GitHubGistSync
   
   sync = GitHubGistSync(token="your_token", username="lolict")
   
   # 同步数据
   gist_id = sync.sync_data("config", {"setting": "value"})
   
   # 获取数据
   data = sync.get_latest_by_type("config")
""")

    token = "__GITHUB_TOKEN__"
    if token.startswith("__"):
        print("\n⚠️  请设置您的 GitHub Token")
        print("   export GITHUB_TOKEN=\"ghp_xxx...\"")
    else:
        sync = GitHubGistSync(token)
        print(f"\n✅ GitHub Gist 同步模块就绪！")


if __name__ == "__main__":
    demo()
