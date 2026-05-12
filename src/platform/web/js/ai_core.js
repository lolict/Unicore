/**
 * UniCore AI层 - JavaScript实现
 * 意图理解、任务分解、知识推理
 */

class IntentClassifier {
    constructor() {
        this.INTENT_PATTERNS = {
            QUERY: ['什么', '怎么', '如何', '为什么', '多少', 'who', 'what', 'how', 'why'],
            EXECUTE: ['执行', '运行', '开始', '做', 'run', 'start', 'do'],
            CREATE: ['创建', '生成', '新建', '写', 'create', 'generate', 'new'],
            LEARN: ['学习', '教我', '告诉', '解释', 'learn', 'teach', 'explain'],
            CONTROL: ['控制', '开关', '调节', '设置', 'control', 'set', 'adjust'],
        };
        this.confidence_threshold = 0.6;
    }

    classify(text) {
        const scores = {};
        for (const intent in this.INTENT_PATTERNS) {
            scores[intent] = 0;
            for (const pattern of this.INTENT_PATTERNS[intent]) {
                if (text.toLowerCase().includes(pattern.toLowerCase())) {
                    scores[intent] += 1;
                }
            }
        }

        const total = Object.values(scores).reduce((a, b) => a + b, 0);
        if (total === 0) return { intent: 'UNKNOWN', confidence: 0 };

        for (const intent in scores) {
            scores[intent] /= total;
        }

        const bestIntent = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);
        return { intent: bestIntent, confidence: scores[bestIntent] };
    }
}

class TaskDecomposer {
    constructor() {
        this.parallelKeywords = ['同时', '并行', '一起'];
    }

    decompose(task) {
        const subtasks = [];
        const parts = task.split(/[，,。. ]+/).filter(p => p.trim());

        let i = 0;
        for (const part of parts) {
            if (part.trim()) {
                const isParallel = this.parallelKeywords.some(k => task.includes(k));
                subtasks.push({
                    id: i,
                    description: part.trim(),
                    dependencies: isParallel ? [] : [i - 1],
                    parallel: isParallel && i > 0
                });
                i++;
            }
        }

        return subtasks;
    }
}

class EmbeddingModel {
    constructor(dim = 128) {
        this.dim = dim;
        this.vocab = {};
    }

    encode(text) {
        const words = Array.from(text);
        const vector = new Array(this.dim).fill(0);

        for (let i = 0; i < words.length; i++) {
            const char = words[i];
            let vec = this.vocab[char];
            if (!vec) {
                vec = Array.from({ length: this.dim }, (_, j) => 
                    Math.sin(char.charCodeAt(0) * (j + 1) / this.dim)
                );
                this.vocab[char] = vec;
            }
            for (let j = 0; j < this.dim; j++) {
                vector[j] += vec[j] / words.length;
            }
        }

        const norm = Math.sqrt(vector.reduce((a, b) => a + b * b, 0));
        if (norm > 0) {
            for (let i = 0; i < this.dim; i++) {
                vector[i] /= norm;
            }
        }

        return vector;
    }

    cosineSimilarity(a, b) {
        const dot = a.reduce((sum, val, i) => sum + val * b[i], 0);
        const normA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
        const normB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
        if (normA * normB === 0) return 0;
        return dot / (normA * normB);
    }
}

class ReasoningEngine {
    constructor() {
        this.rules = [];
        this.facts = {};
    }

    addRule(condition, action) {
        this.rules.push({ condition, action, pattern: new RegExp(condition) });
    }

    addFact(key, value) {
        this.facts[key] = value;
    }

    forwardChain(query) {
        for (const rule of this.rules) {
            if (rule.pattern.test(query)) {
                return rule.action;
            }
        }
        return null;
    }

    backwardChain(goal) {
        return this.rules.some(r => r.action === goal);
    }
}

class UniCoreAI {
    constructor() {
        this.intentClassifier = new IntentClassifier();
        this.taskDecomposer = new TaskDecomposer();
        this.embeddingModel = new EmbeddingModel();
        this.reasoningEngine = new ReasoningEngine();
        this.knowledgeGraph = new KnowledgeGraph();
        
        this.init();
    }

    init() {
        this.knowledgeGraph.addNode('system', { type: 'system', name: 'UniCore' });
        this.knowledgeGraph.addNode('platform', { type: 'platform', name: 'multi-platform' });
        this.knowledgeGraph.addEdge('system', 'platform', 'runs_on');
        
        this.reasoningEngine.addRule('价格', '返回价格信息');
        this.reasoningEngine.addRule('搜索', '执行搜索操作');
        this.reasoningEngine.addRule('创建', '执行创建操作');
    }

    understand(inputText) {
        const { intent, confidence } = this.intentClassifier.classify(inputText);
        const subtasks = this.taskDecomposer.decompose(inputText);

        return {
            text: inputText,
            intent,
            confidence,
            subtasks,
            embedding: this.embeddingModel.encode(inputText)
        };
    }

    reason(query) {
        const result = this.reasoningEngine.forwardChain(query);
        const kgResult = this.knowledgeGraph.query(query);

        return {
            result,
            knowledge: kgResult,
            reasoningSteps: []
        };
    }

    process(inputText) {
        const understanding = this.understand(inputText);
        const reasoning = this.reason(inputText);

        return {
            understanding,
            reasoning,
            response: this.generateResponse(understanding, reasoning)
        };
    }

    generateResponse(understanding, reasoning) {
        const responses = {
            QUERY: '我正在分析您的问题...',
            EXECUTE: '好的，正在执行您的命令...',
            CREATE: '正在为您创建...',
            LEARN: '让我来为您解释...',
            CONTROL: '正在控制设备...',
            UNKNOWN: '我不确定您的意图，请重新描述。'
        };

        return responses[understanding.intent] || responses.UNKNOWN;
    }
}

class KnowledgeGraph {
    constructor() {
        this.nodes = new Map();
        this.edges = [];
    }

    addNode(id, data) {
        this.nodes.set(id, data);
    }

    addEdge(fromId, toId, relation) {
        this.edges.push({ from: fromId, to: toId, relation });
    }

    query(nodeId) {
        const node = this.nodes.get(nodeId);
        const relations = this.edges.filter(e => e.from === nodeId).map(e => ({
            target: e.to,
            relation: e.relation,
            targetData: this.nodes.get(e.to)
        }));

        return { node, relations };
    }

    infer(start, end) {
        const visited = new Set();
        const queue = [[start, [start]]];

        while (queue.length > 0) {
            const [node, path] = queue.shift();
            if (node === end) return path;
            if (visited.has(node)) continue;
            visited.add(node);

            for (const edge of this.edges) {
                if (edge.from === node && !visited.has(edge.to)) {
                    queue.push([edge.to, [...path, edge.to]]);
                }
            }
        }

        return null;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UniCoreAI, IntentClassifier, TaskDecomposer, KnowledgeGraph };
}

if (typeof window !== 'undefined') {
    window.UniCoreAI = UniCoreAI;
    window.IntentClassifier = IntentClassifier;
    window.TaskDecomposer = TaskDecomposer;
    window.KnowledgeGraph = KnowledgeGraph;
}
