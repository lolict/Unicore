/**
 * UniCore 协议层
 * 契约、权限、资源调度、智能体通信
 */

class Contract {
    constructor(name, rules = []) {
        this.name = name;
        this.rules = rules;
        this.timestamp = Date.now();
        this.signatures = new Map();
    }

    add_rule(permission, constraints = {}) {
        this.rules.push({
            permission,
            ...constraints,
            granted: true
        });
    }

    validate(permission) {
        const rule = this.rules.find(r => r.permission === permission);
        if (!rule) {
            return { valid: false, reason: 'Permission not defined' };
        }
        if (!rule.granted) {
            return { valid: false, reason: 'Permission denied' };
        }
        if (rule.max_calls && rule.calls_made >= rule.max_calls) {
            return { valid: false, reason: 'Max calls exceeded' };
        }
        return { valid: true };
    }

    toJSON() {
        return {
            name: this.name,
            rules: this.rules,
            timestamp: this.timestamp,
            signatures: Array.from(this.signatures.entries())
        };
    }
}

class Agent {
    constructor(id, capabilities = []) {
        this.id = id;
        this.capabilities = capabilities;
        this.contracts = new Map();
        this.state = {};
        this.message_queue = [];
    }

    grant_contract(contract) {
        this.contracts.set(contract.name, contract);
    }

    revoke_contract(name) {
        this.contracts.delete(name);
    }

    can_perform(action) {
        for (const contract of this.contracts.values()) {
            const result = contract.validate(action);
            if (result.valid) return true;
        }
        return false;
    }

    send_message(to, message) {
        return {
            type: 'agent_message',
            from: this.id,
            to: to,
            content: message,
            timestamp: Date.now()
        };
    }

    receive_message(message) {
        this.message_queue.push(message);
        return this.process_message(message);
    }

    process_message(message) {
        // 消息处理逻辑
        return { processed: true, response: null };
    }
}

class AgentProtocol {
    constructor() {
        this.agents = new Map();
        this.contracts = new Map();
        this.message_log = [];
    }

    register_agent(agent) {
        this.agents.set(agent.id, agent);
    }

    unregister_agent(agent_id) {
        this.agents.delete(agent_id);
    }

    create_contract(name, participants, rules) {
        const contract = new Contract(name, rules);
        this.contracts.set(name, contract);
        
        for (const agent_id of participants) {
            const agent = this.agents.get(agent_id);
            if (agent) {
                agent.grant_contract(contract);
            }
        }
        
        return contract;
    }

    send_message(from_id, to_id, content) {
        const from = this.agents.get(from_id);
        const to = this.agents.get(to_id);
        
        if (!from || !to) {
            throw new Error('Agent not found');
        }

        const message = from.send_message(to_id, content);
        this.message_log.push(message);
        
        return to.receive_message(message);
    }

    broadcast(from_id, content) {
        const results = [];
        for (const [id, agent] of this.agents) {
            if (id !== from_id) {
                results.push(this.send_message(from_id, id, content));
            }
        }
        return results;
    }

    negotiate_contract(agent1_id, agent2_id, terms) {
        // 简化的契约协商
        const contract_name = `contract_${agent1_id}_${agent2_id}_${Date.now()}`;
        return this.create_contract(
            contract_name,
            [agent1_id, agent2_id],
            terms
        );
    }
}

class ResourceManager {
    constructor() {
        this.resources = new Map();
        this.locks = new Map();
        this.quotas = new Map();
    }

    register_resource(id, config = {}) {
        this.resources.set(id, {
            id,
            type: config.type || 'generic',
            capacity: config.capacity || Infinity,
            usage: 0,
            locked: false,
            owner: null
        });
    }

    allocate(resource_id, amount, requester_id) {
        const resource = this.resources.get(resource_id);
        if (!resource) {
            throw new Error('Resource not found');
        }
        if (resource.usage + amount > resource.capacity) {
            throw new Error('Insufficient capacity');
        }
        if (resource.locked && resource.owner !== requester_id) {
            throw new Error('Resource locked by another');
        }
        
        resource.usage += amount;
        return true;
    }

    release(resource_id, amount, requester_id) {
        const resource = this.resources.get(resource_id);
        if (!resource) {
            throw new Error('Resource not found');
        }
        resource.usage = Math.max(0, resource.usage - amount);
        return true;
    }

    lock(resource_id, owner_id) {
        const resource = this.resources.get(resource_id);
        if (!resource) {
            throw new Error('Resource not found');
        }
        if (resource.locked) {
            throw new Error('Already locked');
        }
        resource.locked = true;
        resource.owner = owner_id;
        this.locks.set(resource_id, owner_id);
    }

    unlock(resource_id, owner_id) {
        const resource = this.resources.get(resource_id);
        if (!resource) {
            throw new Error('Resource not found');
        }
        if (this.locks.get(resource_id) !== owner_id) {
            throw new Error('Not the lock owner');
        }
        resource.locked = false;
        resource.owner = null;
        this.locks.delete(resource_id);
    }

    set_quota(resource_id, requester_id, quota) {
        this.quotas.set(`${resource_id}_${requester_id}`, quota);
    }

    check_quota(resource_id, requester_id, amount) {
        const key = `${resource_id}_${requester_id}`;
        const quota = this.quotas.get(key);
        if (quota === undefined) return true;
        return amount <= quota;
    }
}

class PermissionSystem {
    constructor() {
        this.permissions = new Map();
        this.roles = new Map();
        this.user_permissions = new Map();
    }

    define_permission(name, description, constraints = {}) {
        this.permissions.set(name, {
            name,
            description,
            constraints
        });
    }

    create_role(name, permissions) {
        this.roles.set(name, new Set(permissions));
    }

    grant(user_id, permission) {
        if (!this.user_permissions.has(user_id)) {
            this.user_permissions.set(user_id, new Set());
        }
        this.user_permissions.get(user_id).add(permission);
    }

    revoke(user_id, permission) {
        const perms = this.user_permissions.get(user_id);
        if (perms) {
            perms.delete(permission);
        }
    }

    has_permission(user_id, permission) {
        const perms = this.user_permissions.get(user_id);
        return perms ? perms.has(permission) : false;
    }

    check(user_id, permission) {
        if (this.has_permission(user_id, permission)) {
            return { allowed: true };
        }
        
        // 检查角色权限
        for (const [role, perms] of this.roles) {
            if (perms.has(permission) && this.has_role(user_id, role)) {
                return { allowed: true };
            }
        }
        
        return { allowed: false, reason: 'Permission denied' };
    }

    has_role(user_id, role) {
        return false; // 简化实现
    }
}

class UniCoreProtocol {
    constructor() {
        this.agent_protocol = new AgentProtocol();
        this.resource_manager = new ResourceManager();
        this.permission_system = new PermissionSystem();
        this.event_bus = new EventEmitter();
    }

    // 初始化默认权限
    init_defaults() {
        this.permission_system.define_permission('read', 'Read access');
        this.permission_system.define_permission('write', 'Write access');
        this.permission_system.define_permission('execute', 'Execute programs');
        this.permission_system.define_permission('admin', 'Administrative access');
    }

    // 注册智能体
    register_agent(id, capabilities = []) {
        const agent = new Agent(id, capabilities);
        this.agent_protocol.register_agent(agent);
        return agent;
    }

    // 创建契约
    create_contract(name, participants, rules) {
        return this.agent_protocol.create_contract(name, participants, rules);
    }

    // 消息通信
    send_message(from, to, content) {
        return this.agent_protocol.send_message(from, to, content);
    }

    // 资源管理
    register_resource(id, config) {
        this.resource_manager.register_resource(id, config);
    }

    allocate(resource_id, amount, requester_id) {
        return this.resource_manager.allocate(resource_id, amount, requester_id);
    }
}

class EventEmitter {
    constructor() {
        this.events = new Map();
    }

    on(event, handler) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        this.events.get(event).push(handler);
    }

    off(event, handler) {
        const handlers = this.events.get(event);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        const handlers = this.events.get(event);
        if (handlers) {
            for (const handler of handlers) {
                handler(data);
            }
        }
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Contract, Agent, AgentProtocol, ResourceManager,
        PermissionSystem, UniCoreProtocol, EventEmitter
    };
}

if (typeof window !== 'undefined') {
    window.UniCoreProtocol = UniCoreProtocol;
    window.Contract = Contract;
    window.Agent = Agent;
    window.AgentProtocol = AgentProtocol;
    window.ResourceManager = ResourceManager;
    window.PermissionSystem = PermissionSystem;
    window.EventEmitter = EventEmitter;
}
