#!/usr/bin/env python3
"""
UniCore Cloud Module 3: P2P WebRTC 通信模块
==============================================
支持：设备间直连通信、数据传输、信令服务
注意：WebRTC 主要用于浏览器环境，此模块提供信令服务器和连接管理
"""

import asyncio
import json
import logging
import uuid
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    TEXT = "text"
    DATA = "data"
    CONTROL = "control"
    HEARTBEAT = "heartbeat"


@dataclass
class Peer:
    """对等节点"""
    peer_id: str
    websocket: WebSocketServerProtocol
    room_id: str = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Room:
    """房间"""
    room_id: str
    peers: Dict[str, Peer] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    max_peers: int = 10


@dataclass
class SignalMessage:
    """信令消息"""
    type: MessageType
    sender_id: str
    target_id: str = None
    room_id: str = None
    payload: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SignalingServer:
    """WebRTC 信令服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.peers: Dict[str, Peer] = {}
        self.rooms: Dict[str, Room] = {}
        self.handlers: Dict[MessageType, List[Callable]] = {}
        self.running = False
        self._peer_locks: Dict[str, asyncio.Lock] = {}
    
    async def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)
    
    async def _get_peer_lock(self, peer_id: str) -> asyncio.Lock:
        """获取对等节点锁"""
        if peer_id not in self._peer_locks:
            self._peer_locks[peer_id] = asyncio.Lock()
        return self._peer_locks[peer_id]
    
    async def _broadcast_to_room(self, room: Room, message: SignalMessage, exclude: str = None):
        """广播消息到房间"""
        for peer_id, peer in room.peers.items():
            if peer_id != exclude:
                try:
                    await peer.websocket.send(json.dumps(asdict(message)))
                except Exception as e:
                    logger.error(f"广播失败 {peer_id}: {e}")
    
    async def _handle_offer(self, peer: Peer, message: SignalMessage):
        """处理 Offer"""
        if message.target_id and message.target_id in self.peers:
            target_peer = self.peers[message.target_id]
            forward_msg = SignalMessage(
                type=MessageType.OFFER,
                sender_id=peer.peer_id,
                target_id=target_peer.peer_id,
                payload=message.payload
            )
            await target_peer.websocket.send(json.dumps(asdict(forward_msg)))
            logger.info(f"转发 OFFER: {peer.peer_id} -> {target_peer.peer_id}")
    
    async def _handle_answer(self, peer: Peer, message: SignalMessage):
        """处理 Answer"""
        if message.target_id and message.target_id in self.peers:
            target_peer = self.peers[message.target_id]
            forward_msg = SignalMessage(
                type=MessageType.ANSWER,
                sender_id=peer.peer_id,
                target_id=target_peer.peer_id,
                payload=message.payload
            )
            await target_peer.websocket.send(json.dumps(asdict(forward_msg)))
            logger.info(f"转发 ANSWER: {peer.peer_id} -> {target_peer.peer_id}")
    
    async def _handle_ice_candidate(self, peer: Peer, message: SignalMessage):
        """处理 ICE Candidate"""
        if message.target_id and message.target_id in self.peers:
            target_peer = self.peers[message.target_id]
            forward_msg = SignalMessage(
                type=MessageType.ICE_CANDIDATE,
                sender_id=peer.peer_id,
                target_id=target_peer.peer_id,
                payload=message.payload
            )
            try:
                await target_peer.websocket.send(json.dumps(asdict(forward_msg)))
            except Exception as e:
                logger.error(f"ICE Candidate 转发失败: {e}")
    
    async def _handle_text_message(self, peer: Peer, message: SignalMessage):
        """处理文本消息"""
        if peer.room_id and peer.room_id in self.rooms:
            room = self.rooms[peer.room_id]
            await self._broadcast_to_room(room, message, exclude=peer.peer_id)
            logger.info(f"广播消息 from {peer.peer_id} in room {peer.room_id}")
    
    async def _handle_join_room(self, peer: Peer, room_id: str):
        """处理加入房间"""
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
        
        room = self.rooms[room_id]
        
        if len(room.peers) >= room.max_peers:
            await peer.websocket.send(json.dumps({
                "type": "error",
                "message": "Room is full"
            }))
            return
        
        room.peers[peer.peer_id] = peer
        peer.room_id = room_id
        
        await peer.websocket.send(json.dumps({
            "type": "joined",
            "room_id": room_id,
            "peer_count": len(room.peers),
            "peers": list(room.peers.keys())
        }))
        
        notify_msg = SignalMessage(
            type=MessageType.CONTROL,
            sender_id=peer.peer_id,
            payload={"action": "peer_joined", "peer_id": peer.peer_id}
        )
        await self._broadcast_to_room(room, notify_msg, exclude=peer.peer_id)
        
        logger.info(f"Peer {peer.peer_id} joined room {room_id}")
    
    async def _handle_leave_room(self, peer: Peer):
        """处理离开房间"""
        if peer.room_id and peer.room_id in self.rooms:
            room = self.rooms[peer.room_id]
            
            if peer.peer_id in room.peers:
                del room.peers[peer.peer_id]
            
            if len(room.peers) == 0:
                del self.rooms[peer.room_id]
            else:
                notify_msg = SignalMessage(
                    type=MessageType.CONTROL,
                    sender_id=peer.peer_id,
                    payload={"action": "peer_left", "peer_id": peer.peer_id}
                )
                await self._broadcast_to_room(room, notify_msg)
            
            peer.room_id = None
            logger.info(f"Peer {peer.peer_id} left room")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """处理连接"""
        peer_id = str(uuid.uuid4())[:8]
        peer = Peer(peer_id=peer_id, websocket=websocket)
        
        self.peers[peer_id] = peer
        
        await websocket.send(json.dumps({
            "type": "connected",
            "peer_id": peer_id,
            "server_time": datetime.now().isoformat()
        }))
        
        logger.info(f"新连接: {peer_id}")
        
        try:
            async for raw_message in websocket:
                try:
                    message_data = json.loads(raw_message)
                    msg_type = MessageType(message_data.get("type", "text"))
                    message = SignalMessage(
                        type=msg_type,
                        sender_id=peer_id,
                        payload=message_data.get("payload", {})
                    )
                    
                    if msg_type == MessageType.OFFER:
                        message.target_id = message_data.get("target_id")
                        await self._handle_offer(peer, message)
                    
                    elif msg_type == MessageType.ANSWER:
                        message.target_id = message_data.get("target_id")
                        await self._handle_answer(peer, message)
                    
                    elif msg_type == MessageType.ICE_CANDIDATE:
                        message.target_id = message_data.get("target_id")
                        await self._handle_ice_candidate(peer, message)
                    
                    elif msg_type == MessageType.TEXT:
                        message.room_id = peer.room_id
                        await self._handle_text_message(peer, message)
                    
                    elif msg_type == MessageType.CONTROL:
                        action = message_data.get("payload", {}).get("action")
                        
                        if action == "join_room":
                            await self._handle_join_room(peer, message_data.get("room_id"))
                        elif action == "leave_room":
                            await self._handle_leave_room(peer)
                        elif action == "heartbeat":
                            peer.last_seen = datetime.now()
                    
                    elif msg_type == MessageType.HEARTBEAT:
                        peer.last_seen = datetime.now()
                        await websocket.send(json.dumps({"type": "heartbeat_ack"}))
                    
                    if msg_type in self.handlers:
                        for handler in self.handlers[msg_type]:
                            await handler(peer, message)
                
                except json.JSONDecodeError:
                    logger.error(f"无效 JSON: {raw_message[:100]}")
                except Exception as e:
                    logger.error(f"消息处理错误: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._handle_leave_room(peer)
            
            if peer_id in self.peers:
                del self.peers[peer_id]
            
            logger.info(f"连接关闭: {peer_id}")
    
    async def cleanup_inactive(self):
        """清理不活跃连接"""
        while self.running:
            await asyncio.sleep(30)
            
            now = datetime.now()
            inactive_threshold = 300
            
            for peer_id, peer in list(self.peers.items()):
                inactive_time = (now - peer.last_seen).total_seconds()
                
                if inactive_time > inactive_threshold:
                    logger.info(f"清理不活跃连接: {peer_id}")
                    try:
                        await peer.websocket.close()
                    except:
                        pass
    
    async def start(self):
        """启动服务器"""
        self.running = True
        
        cleanup_task = asyncio.create_task(self.cleanup_inactive())
        
        logger.info(f"启动信令服务器: ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()


class UniCoreP2P:
    """UniCore P2P 通信管理器"""
    
    ICE_SERVERS = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
        {"urls": "stun:stun2.l.google.com:19302"}
    ]
    
    def __init__(self, signaling_url: str = "ws://localhost:8765"):
        self.signaling_url = signaling_url
        self.websocket = None
        self.peer_id = None
        self.connected_peers: Dict[str, Peer] = {}
        self.on_message_callback: Optional[Callable] = None
        self.on_peer_connected_callback: Optional[Callable] = None
        self.on_peer_disconnected_callback: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """连接到信令服务器"""
        try:
            self.websocket = await websockets.connect(self.signaling_url)
            
            welcome = json.loads(await self.websocket.recv())
            self.peer_id = welcome.get("peer_id")
            
            logger.info(f"连接到信令服务器成功，Peer ID: {self.peer_id}")
            
            asyncio.create_task(self._receive_messages())
            
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    async def _receive_messages(self):
        """接收消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "joined":
                    logger.info(f"加入房间: {data.get('room_id')}")
                
                elif msg_type == "peer_joined":
                    peer_id = data.get("peer_id")
                    logger.info(f"新对等节点: {peer_id}")
                    if self.on_peer_connected_callback:
                        await self.on_peer_connected_callback(peer_id)
                
                elif msg_type == "peer_left":
                    peer_id = data.get("peer_id")
                    logger.info(f"对等节点离开: {peer_id}")
                    if self.on_peer_disconnected_callback:
                        await self.on_peer_disconnected_callback(peer_id)
                
                elif msg_type == "text" and self.on_message_callback:
                    sender_id = data.get("sender_id")
                    payload = data.get("payload", {})
                    await self.on_message_callback(sender_id, payload)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("与信令服务器断开连接")
    
    async def send_message(self, message: str):
        """发送消息"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "text",
                "payload": {"content": message}
            }))
    
    async def create_offer(self, target_peer_id: str) -> Dict:
        """创建 WebRTC Offer"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "offer",
                "target_id": target_peer_id,
                "payload": {"sdp": "local_sdp", "type": "offer"}
            }))
        return {}
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()


def run_signaling_server(host: str = "0.0.0.0", port: int = 8765):
    """运行信令服务器"""
    server = SignalingServer(host, port)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("服务器关闭")


def demo():
    """演示"""
    print("""
╔════════════════════════════════════════════════════════╗
║    UniCore Cloud Module 3: P2P WebRTC Communication  ║
╚════════════════════════════════════════════════════════╝

功能：
✅ WebRTC 信令服务器
✅ 房间管理
✅ 点对点消息传递
✅ ICE Candidate 转发

使用方法：

1. 启动信令服务器：
   python3 p2p_webrtc.py --server

2. 客户端连接：
   from p2p_webrtc import UniCoreP2P
   
   p2p = UniCoreP2P("ws://your-server:8765")
   await p2p.connect()
   
   # 发送消息
   await p2p.send_message("Hello P2P!")
   
   # 创建 WebRTC 连接
   await p2p.create_offer("target_peer_id")

WebRTC 连接流程：
1. Client A 创建 Offer -> Server
2. Server 转发 Offer -> Client B
3. Client B 创建 Answer -> Server
4. Server 转发 Answer -> Client A
5. A/B 交换 ICE Candidates
6. P2P 直连建立完成
""")

    print("\n💡 提示: WebRTC 主要用于浏览器环境")
    print("   Python 版本主要用于信令服务器和测试")
    print("   前端请使用 JavaScript WebRTC API")


if __name__ == "__main__":
    import sys
    
    if "--server" in sys.argv:
        run_signaling_server()
    else:
        demo()
