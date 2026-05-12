#!/usr/bin/env python3
"""
UniCore Cloud Module 4: 统一调度器
====================================
整合 Gist、WebDAV、P2P，提供统一的云端同步接口
"""

import os
import time
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncBackend(Enum):
    """同步后端类型"""
    GITHUB_GIST = "github_gist"
    WEBDAV = "webdav"
    P2P = "p2p"
    AUTO = "auto"


@dataclass
class SyncTask:
    """同步任务"""
    task_id: str
    data_type: str
    data: Any
    backend: SyncBackend = SyncBackend.AUTO
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Any = None


class SyncScheduler:
    """统一同步调度器"""
    
    def __init__(self):
        self.github_gist = None
        self.webdav = None
        self.p2p = None
        self.task_queue: List[SyncTask] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self._config = {}
    
    def configure_github(self, token: str, username: str):
        """配置 GitHub Gist"""
        try:
            sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            from gist.gist_sync import GitHubGistSync
            self.github_gist = GitHubGistSync(token, username)
            self._config['github'] = {'username': username}
            logger.info("✅ GitHub Gist 已配置")
        except ImportError as e:
            logger.warning(f"⚠️  GitHub Gist 模块未安装: {e}")
    
    def configure_webdav(self, host: str, username: str, password: str):
        """配置 WebDAV"""
        try:
            sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            from webdav.webdav_sync import WebDAVClient
            self.webdav = WebDAVClient(host, username, password)
            self._config['webdav'] = {'host': host, 'username': username}
            logger.info("✅ WebDAV 已配置")
        except ImportError as e:
            logger.warning(f"⚠️  WebDAV 模块未安装: {e}")
    
    def configure_nutstore(self, username: str, password: str):
        """配置坚果云"""
        try:
            sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            from webdav.webdav_sync import NutstoreSync
            self.webdav = NutstoreSync(username, password)
            self._config['nutstore'] = {'username': username}
            logger.info("✅ 坚果云 WebDAV 已配置")
        except ImportError as e:
            logger.warning(f"⚠️  坚果云模块未安装: {e}")
    
    def configure_p2p(self, signaling_url: str):
        """配置 P2P"""
        try:
            sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            from p2p.p2p_webrtc import UniCoreP2P
            self.p2p = UniCoreP2P(signaling_url)
            self._config['p2p'] = {'signaling_url': signaling_url}
            logger.info("✅ P2P WebRTC 已配置")
        except ImportError as e:
            logger.warning(f"⚠️  P2P 模块未安装: {e}")
    
    def _select_backend(self, task: SyncTask) -> SyncBackend:
        """选择最佳后端"""
        if task.backend != SyncBackend.AUTO:
            return task.backend
        
        if self.github_gist and task.data_type in ['config', 'task', 'message', 'backup']:
            return SyncBackend.GITHUB_GIST
        
        if self.webdav and task.data_type in ['file', 'large_data', 'binary']:
            return SyncBackend.WEBDAV
        
        if self.p2p and task.data_type in ['realtime', 'message', 'stream']:
            return SyncBackend.P2P
        
        if self.github_gist:
            return SyncBackend.GITHUB_GIST
        
        return SyncBackend.GITHUB_GIST
    
    def add_task(self, data_type: str, data: Any, backend: SyncBackend = SyncBackend.AUTO, priority: int = 0) -> str:
        """添加同步任务"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = SyncTask(
            task_id=task_id,
            data_type=data_type,
            data=data,
            backend=backend,
            priority=priority
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        logger.info(f"📝 添加任务: {task_id} ({data_type})")
        
        self.executor.submit(self._execute_task, task)
        
        return task_id
    
    def _execute_task(self, task: SyncTask):
        """执行同步任务"""
        try:
            backend = self._select_backend(task)
            task.status = "syncing"
            
            if backend == SyncBackend.GITHUB_GIST and self.github_gist:
                result = self.github_gist.sync_data(task.data_type, task.data)
                task.result = result
                logger.info(f"✅ Gist 同步完成: {task.task_id}")
            
            elif backend == SyncBackend.WEBDAV and self.webdav:
                filename = f"{task.data_type}_{task.task_id}"
                success = self.webdav.upload_data(task.data_type, filename, task.data)
                task.result = success
                logger.info(f"✅ WebDAV 同步完成: {task.task_id}")
            
            elif backend == SyncBackend.P2P and self.p2p:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.p2p.send_message(json.dumps(task.data)))
                loop.close()
                task.result = True
                logger.info(f"✅ P2P 消息发送完成: {task.task_id}")
            
            task.status = "completed"
        
        except Exception as e:
            task.status = f"failed: {str(e)}"
            logger.error(f"❌ 同步失败: {task.task_id} - {e}")
    
    def sync_now(self, data_type: str, data: Any) -> Optional[str]:
        """立即同步"""
        future = self.executor.submit(self.add_task, data_type, data)
        return future.result()
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        for task in self.task_queue:
            if task.task_id == task_id:
                return task.status
        return None
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待处理任务"""
        return [
            {
                "task_id": t.task_id,
                "data_type": t.data_type,
                "status": t.status,
                "priority": t.priority
            }
            for t in self.task_queue
            if t.status == "pending"
        ]
    
    def clear_completed_tasks(self):
        """清理已完成任务"""
        self.task_queue = [t for t in self.task_queue if t.status not in ["completed", "failed"]]


class UniCoreCloudManager:
    """UniCore 云端管理器"""
    
    def __init__(self):
        self.scheduler = SyncScheduler()
        self.config_file = "unicore_cloud_config.json"
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
                if 'github_token' in config:
                    self.scheduler.configure_github(
                        config['github_token'],
                        config.get('github_username', 'lolict')
                    )
                
                if 'nutstore' in config:
                    ns = config['nutstore']
                    self.scheduler.configure_nutstore(ns['username'], ns['password'])
                
                if 'webdav' in config:
                    wd = config['webdav']
                    self.scheduler.configure_webdav(wd['host'], wd['username'], wd['password'])
                
                if 'p2p' in config:
                    self.scheduler.configure_p2p(config['p2p']['signaling_url'])
                
                logger.info("✅ 加载云端配置")
    
    def save_config(self, config: Dict):
        """保存配置"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        self._load_config()
    
    def setup_interactive(self):
        """交互式配置"""
        print("""
╔════════════════════════════════════════════════════════╗
║    UniCore Cloud Manager - 交互式配置                ║
╚════════════════════════════════════════════════════════╝
""")
        
        config = {}
        
        use_github = input("是否使用 GitHub Gist 同步? (y/n): ").strip().lower() == 'y'
        if use_github:
            token = input("GitHub Token (ghp_xxx): ").strip()
            username = input("GitHub 用户名: ").strip()
            config['github_token'] = token
            config['github_username'] = username
            self.scheduler.configure_github(token, username)
        
        use_nutstore = input("是否使用坚果云 WebDAV? (y/n): ").strip().lower() == 'y'
        if use_nutstore:
            username = input("坚果云邮箱: ").strip()
            password = input("坚果云密码: ").strip()
            config['nutstore'] = {'username': username, 'password': password}
            self.scheduler.configure_nutstore(username, password)
        
        use_p2p = input("是否使用 P2P WebRTC? (y/n): ").strip().lower() == 'y'
        if use_p2p:
            url = input("信令服务器地址 (ws://localhost:8765): ").strip()
            config['p2p'] = {'signaling_url': url}
            self.scheduler.configure_p2p(url)
        
        self.save_config(config)
        print("\n✅ 配置已保存！")


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════╗
║    UniCore Cloud Manager - 统一调度器                ║
╚════════════════════════════════════════════════════════╝

已集成的模块：
1. GitHub Gist    - JSON 数据存储
2. WebDAV/坚果云  - 文件同步
3. P2P WebRTC     - 实时通信

使用示例：
""")

    manager = UniCoreCloudManager()
    
    print("""
# 添加同步任务
task_id = manager.sync_now("config", {"setting": "value"})

# 查看任务状态
status = manager.scheduler.get_task_status(task_id)

# 查看待处理任务
pending = manager.scheduler.get_pending_tasks()
""")


if __name__ == "__main__":
    demo()
