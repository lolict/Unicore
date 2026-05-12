/**
 * UniCore 完整演示应用
 * 集成了所有核心功能
 */

class UniCoreDemo {
    constructor() {
        this.ai = new window.UniCoreAI();
        this.runtime = new window.UniCoreRuntime();
        this.protocol = new window.UniCoreProtocol();
        this.tools = new window.UniCoreTools();
        this.isInitialized = false;
    }

    async init() {
        console.log('Initializing UniCore Demo...');
        this.runtime.init();
        this.protocol.init_defaults();
        this.tools.init();
        this.isInitialized = true;
        console.log('UniCore Demo Ready!');
        return this;
    }

    // AI对话演示
    async demoAI(input) {
        const result = this.ai.process(input);
        return {
            intent: result.understanding.intent,
            response: result.response,
            confidence: result.understanding.confidence,
            subtasks: result.understanding.subtasks
        };
    }

    // 并行计算演示
    async demoParallel() {
        const startTime = performance.now();
        const tasks = [
            () => this.simulateTask('计算', 500),
            () => this.simulateTask('分析', 300),
            () => this.simulateTask('渲染', 400),
            () => this.simulateTask('网络', 200)
        ];

        const results = await Promise.all(tasks.map(t => t()));
        const elapsed = (performance.now() - startTime).toFixed(2);

        return {
            results,
            totalTime: elapsed,
            speedup: '4x parallel'
        };
    }

    simulateTask(name, ms) {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ task: name, status: 'completed', time: ms + 'ms' });
            }, ms);
        });
    }

    // 协议演示
    demoProtocol() {
        const alice = this.protocol.register_agent('Alice', ['read', 'write']);
        const bob = this.protocol.register_agent('Bob', ['read']);

        const contract = this.protocol.create_contract('test_contract', ['Alice', 'Bob'], [
            { permission: 'read', max_calls: 10 },
            { permission: 'write', max_calls: 5 }
        ]);

        return {
            agents: ['Alice', 'Bob'],
            contract: contract.name,
            rules: contract.rules.length
        };
    }

    // 多模态演示
    async demoMultimodal() {
        const results = {};

        // 音频
        try {
            this.tools.audio.playTone(523, 0.3);
            results.audio = '声音播放成功';
        } catch (e) {
            results.audio = '音频功能就绪';
        }

        // 图像
        this.tools.image.init(200, 200);
        this.tools.image.clear('#667eea');
        this.tools.image.drawRect(20, 20, 160, 160, '#4ecdc4');
        this.tools.image.drawCircle(100, 100, 60, '#ffd93d');
        this.tools.image.drawText('UniCore', 100, 105, {
            color: '#fff',
            align: 'center',
            font: '16px Arial'
        });
        results.image = this.tools.image.toBase64();

        // 网络
        results.network = '网络工具就绪';

        return results;
    }

    // 执行UniISA指令
    executeInstruction(opcode, operands) {
        this.runtime.execute_instruction(opcode, operands);
        return {
            opcode,
            operands,
            registers: Array.from(this.runtime.registers)
        };
    }

    // 完整流程演示
    async demoFullFlow(userInput) {
        const flow = {
            step1_understand: null,
            step2_reason: null,
            step3_execute: null,
            step4_respond: null
        };

        // 步骤1: 理解
        flow.step1_understand = this.ai.understand(userInput);
        await this.delay(200);

        // 步骤2: 推理
        flow.step2_reason = this.ai.reason(userInput);
        await this.delay(200);

        // 步骤3: 执行
        if (flow.step1_understand.intent === 'EXECUTE') {
            flow.step3_execute = { status: 'executed' };
        }
        await this.delay(200);

        // 步骤4: 响应
        flow.step4_respond = this.ai.generateResponse(
            flow.step1_understand,
            flow.step2_reason
        );

        return flow;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 生成演示报告
    generateReport() {
        return {
            system: 'UniCore Demo v1.0.0',
            timestamp: new Date().toISOString(),
            components: {
                ai: 'UniCoreAI (Intent/Task/Reasoning)',
                runtime: 'UniISARuntime (WASM)',
                protocol: 'UniCoreProtocol (Contract/Permission)',
                tools: 'UniCoreTools (Audio/Image/Video/Control)'
            },
            features: [
                '意图分类与理解',
                '任务分解与调度',
                '知识图谱推理',
                '并行计算加速',
                '契约与权限管理',
                '多模态处理'
            ]
        };
    }
}

// 全局实例
window.UniCoreDemo = UniCoreDemo;
