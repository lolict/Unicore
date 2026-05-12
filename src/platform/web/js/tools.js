/**
 * UniCore 工具层
 * 音频、视频、图像、控制等多媒体处理
 */

class AudioTool {
    constructor() {
        this.context = null;
        this.gainNode = null;
    }

    init() {
        if (typeof window !== 'undefined' && window.AudioContext) {
            this.context = new window.AudioContext();
            this.gainNode = this.context.createGain();
            this.gainNode.connect(this.context.destination);
        }
    }

    playTone(frequency, duration = 1) {
        if (!this.context) return;
        
        const oscillator = this.context.createOscillator();
        oscillator.type = 'sine';
        oscillator.frequency.value = frequency;
        
        const gain = this.context.createGain();
        gain.gain.setValueAtTime(0.5, this.context.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.context.currentTime + duration);
        
        oscillator.connect(gain);
        gain.connect(this.context.destination);
        
        oscillator.start();
        oscillator.stop(this.context.currentTime + duration);
    }

    playSequence(notes) {
        let time = this.context.currentTime;
        for (const note of notes) {
            this.playNoteAt(note.frequency, note.duration, time);
            time += note.duration;
        }
    }

    playNoteAt(freq, duration, startTime) {
        const osc = this.context.createOscillator();
        const gain = this.context.createGain();
        
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.3, startTime);
        gain.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
        
        osc.connect(gain);
        gain.connect(this.context.destination);
        
        osc.start(startTime);
        osc.stop(startTime + duration);
    }

    async recognize(blob) {
        // 简化的语音识别
        return { text: '[识别结果]', confidence: 0.9 };
    }

    synthesize(text) {
        // 简化的TTS
        return { audio: null, duration: text.length * 0.1 };
    }
}

class ImageTool {
    constructor() {
        this.canvas = null;
        this.ctx = null;
    }

    init(width = 512, height = 512) {
        if (typeof document !== 'undefined') {
            this.canvas = document.createElement('canvas');
            this.canvas.width = width;
            this.canvas.height = height;
            this.ctx = this.canvas.getContext('2d');
        }
    }

    draw(drawFunc) {
        if (!this.ctx) return;
        drawFunc(this.ctx, this.canvas);
    }

    clear(color = '#000000') {
        if (!this.ctx) return;
        this.ctx.fillStyle = color;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    drawText(text, x, y, options = {}) {
        if (!this.ctx) return;
        const {
            font = '20px Arial',
            color = '#ffffff',
            align = 'start',
            baseline = 'alphabetic'
        } = options;
        
        this.ctx.font = font;
        this.ctx.fillStyle = color;
        this.ctx.textAlign = align;
        this.ctx.textBaseline = baseline;
        this.ctx.fillText(text, x, y);
    }

    drawRect(x, y, w, h, color = '#ffffff') {
        if (!this.ctx) return;
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, w, h);
    }

    drawCircle(x, y, r, color = '#ffffff') {
        if (!this.ctx) return;
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, r, 0, Math.PI * 2);
        this.ctx.fill();
    }

    async generate(prompt, style = 'realistic') {
        // 模拟图像生成
        this.clear('#4a90d9');
        this.drawText(`AI Generated: ${prompt}`, 256, 256, {
            font: '24px Arial',
            color: '#ffffff',
            align: 'center'
        });
        return this.canvas.toDataURL('image/png');
    }

    toBase64() {
        if (!this.canvas) return null;
        return this.canvas.toDataURL('image/png');
    }

    async loadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    }

    resize(img, maxWidth, maxHeight) {
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth) {
            height = (maxWidth / width) * height;
            width = maxWidth;
        }
        if (height > maxHeight) {
            width = (maxHeight / height) * width;
            height = maxHeight;
        }
        
        this.init(width, height);
        this.ctx.drawImage(img, 0, 0, width, height);
        return this.canvas;
    }
}

class VideoTool {
    constructor() {
        this.recorder = null;
        this.frames = [];
    }

    async capture(canvas) {
        const frame = canvas.toDataURL('image/png');
        this.frames.push(frame);
        return frame;
    }

    async encode(fps = 30) {
        // 简化视频编码
        return {
            frames: this.frames.length,
            fps,
            duration: this.frames.length / fps,
            url: this.frames[0]
        };
    }

    clear() {
        this.frames = [];
    }
}

class ControlTool {
    constructor() {
        this.sensors = {
            accelerometer: { x: 0, y: 0, z: 0 },
            gyroscope: { x: 0, y: 0, z: 0 },
            light: 0,
            temperature: 25
        };
        this.outputs = {
            vibration: false,
            flashlight: false
        };
    }

    startSensor(name) {
        if (typeof DeviceMotionEvent !== 'undefined') {
            window.addEventListener('devicemotion', (e) => {
                if (e.accelerationIncludingGravity) {
                    this.sensors.accelerometer = {
                        x: e.accelerationIncludingGravity.x || 0,
                        y: e.accelerationIncludingGravity.y || 0,
                        z: e.accelerationIncludingGravity.z || 0
                    };
                }
            });
        }
    }

    getSensor(name) {
        return this.sensors[name] || null;
    }

    vibrate(pattern = [100]) {
        if (typeof navigator !== 'undefined' && navigator.vibrate) {
            navigator.vibrate(pattern);
        }
    }

    setFlashlight(on) {
        this.outputs.flashlight = on;
    }

    async getLocation() {
        return new Promise((resolve) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((pos) => {
                    resolve({
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude
                    });
                }, () => {
                    resolve({ latitude: 0, longitude: 0 });
                });
            } else {
                resolve({ latitude: 0, longitude: 0 });
            }
        });
    }
}

class FileTool {
    constructor() {
        this.files = new Map();
    }

    read(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    write(path, data) {
        this.files.set(path, data);
        return true;
    }

    readSync(path) {
        return this.files.get(path);
    }

    list(path) {
        return Array.from(this.files.keys()).filter(p => p.startsWith(path));
    }

    delete(path) {
        return this.files.delete(path);
    }
}

class NetworkTool {
    constructor() {
        this.connections = new Map();
    }

    async fetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body ? JSON.stringify(options.body) : undefined
            });
            return {
                status: response.status,
                data: await response.json().catch(() => response.text())
            };
        } catch (error) {
            return { error: error.message };
        }
    }

    async websocket(url, onMessage) {
        const ws = new WebSocket(url);
        
        ws.onopen = () => {
            this.connections.set(url, ws);
        };
        
        ws.onmessage = (event) => {
            onMessage(event.data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    }

    send(url, data) {
        const ws = this.connections.get(url);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
            return true;
        }
        return false;
    }
}

class UniCoreTools {
    constructor() {
        this.audio = new AudioTool();
        this.image = new ImageTool();
        this.video = new VideoTool();
        this.control = new ControlTool();
        this.file = new FileTool();
        this.network = new NetworkTool();
    }

    init() {
        this.audio.init();
        this.image.init();
        return this;
    }

    // 执行工具调用
    async execute(tool, action, params = {}) {
        const tool_obj = this[tool];
        if (!tool_obj) {
            throw new Error(`Unknown tool: ${tool}`);
        }

        const method = tool_obj[action];
        if (typeof method !== 'function') {
            throw new Error(`Unknown action: ${action}`);
        }

        return await method.apply(tool_obj, Object.values(params));
    }

    // 获取所有工具列表
    list() {
        return ['audio', 'image', 'video', 'control', 'file', 'network'];
    }

    // 获取工具能力
    capabilities(tool) {
        const capabilities = {
            audio: ['playTone', 'playSequence', 'recognize', 'synthesize'],
            image: ['generate', 'draw', 'clear', 'toBase64'],
            video: ['capture', 'encode'],
            control: ['startSensor', 'getSensor', 'vibrate', 'getLocation'],
            file: ['read', 'write', 'list', 'delete'],
            network: ['fetch', 'websocket', 'send']
        };
        return capabilities[tool] || [];
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AudioTool, ImageTool, VideoTool, ControlTool,
        FileTool, NetworkTool, UniCoreTools
    };
}

if (typeof window !== 'undefined') {
    window.UniCoreTools = UniCoreTools;
    window.AudioTool = AudioTool;
    window.ImageTool = ImageTool;
    window.VideoTool = VideoTool;
    window.ControlTool = ControlTool;
    window.FileTool = FileTool;
    window.NetworkTool = NetworkTool;
}
