// UniCore 安全包装层 - Rust实现
// 内存安全、FFI绑定、错误处理

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::error::Error;
use std::fmt;

/// 统一错误类型
#[derive(Debug, Clone)]
pub enum UniError {
    OutOfBounds,
    InvalidOpcode,
    DivisionByZero,
    StackOverflow,
    StackUnderflow,
    NullPointer,
    PermissionDenied,
    ResourceNotFound,
    SystemCallFailed(String),
    Unknown(String),
}

impl fmt::Display for UniError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::OutOfBounds => write!(f, "Memory access out of bounds"),
            Self::InvalidOpcode => write!(f, "Invalid instruction opcode"),
            Self::DivisionByZero => write!(f, "Division by zero"),
            Self::StackOverflow => write!(f, "Stack overflow"),
            Self::StackUnderflow => write!(f, "Stack underflow"),
            Self::NullPointer => write!(f, "Null pointer dereference"),
            Self::PermissionDenied => write!(f, "Permission denied"),
            Self::ResourceNotFound => write!(f, "Resource not found"),
            Self::SystemCallFailed(msg) => write!(f, "System call failed: {}", msg),
            Self::Unknown(msg) => write!(f, "Unknown error: {}", msg),
        }
    }
}

impl Error for UniError {}

pub type Result<T> = std::result::Result<T, UniError>;

/// 安全的寄存器包装器
#[derive(Debug, Clone)]
pub struct SafeRegister {
    value: u64,
    max_value: u64,
}

impl SafeRegister {
    pub fn new(value: u64, max: u64) -> Self {
        Self { value, max_value: max }
    }

    pub fn get(&self) -> u64 { self.value }

    pub fn set(&mut self, v: u64) -> Result<()> {
        if v > self.max_value {
            return Err(UniError::OutOfBounds);
        }
        self.value = v;
        Ok(())
    }

    pub fn add(&mut self, v: u64) -> Result<()> {
        self.set(self.value.checked_add(v).ok_or(UniError::Overflow)?)
    }
}

/// 安全的内存管理器
pub struct SafeMemory {
    data: Vec<u8>,
    allocated: Arc<Mutex<HashMap<usize, usize>>>, // addr -> size
    size: usize,
}

impl SafeMemory {
    pub fn new(size: usize) -> Self {
        Self {
            data: vec![0; size],
            allocated: Arc::new(Mutex::new(HashMap::new())),
            size,
        }
    }

    pub fn read(&self, addr: usize, len: usize) -> Result<Vec<u8>> {
        if addr + len > self.size {
            return Err(UniError::OutOfBounds);
        }
        Ok(self.data[addr..addr + len].to_vec())
    }

    pub fn write(&mut self, addr: usize, data: &[u8]) -> Result<()> {
        if addr + data.len() > self.size {
            return Err(UniError::OutOfBounds);
        }
        self.data[addr..addr + data.len()].copy_from_slice(data);
        Ok(())
    }

    pub fn alloc(&mut self, size: usize) -> Result<usize> {
        let mut allocated = self.allocated.lock().unwrap();
        
        // 简单的首次适配分配
        let mut addr = 0;
        while addr + size <= self.size {
            let mut available = true;
            for (a, s) in allocated.iter() {
                if addr < *a + s && addr + size > *a {
                    addr = *a + s;
                    available = false;
                    break;
                }
            }
            if available {
                allocated.insert(addr, size);
                return Ok(addr);
            }
        }
        Err(UniError::OutOfBounds)
    }

    pub fn free(&mut self, addr: usize) -> Result<()> {
        let mut allocated = self.allocated.lock().unwrap();
        allocated.remove(&addr);
        Ok(())
    }
}

/// 安全调用接口
pub trait SafeCall {
    fn call(&self, args: &[u64]) -> Result<u64>;
}

/// FFI绑定到Zig核心
pub struct ZigBridge {
    core_ptr: *mut std::ffi::c_void,
}

impl ZigBridge {
    pub fn new(core_ptr: *mut std::ffi::c_void) -> Self {
        Self { core_ptr }
    }

    pub fn execute(&self, opcode: u8, operands: &[u64]) -> Result<u64> {
        unsafe {
            // 调用Zig核心
            let result = self.call_zig_function(opcode, operands);
            result
        }
    }

    unsafe fn call_zig_function(&self, _opcode: u8, _operands: &[u64]) -> Result<u64> {
        // FFI调用
        Ok(0)
    }
}

/// 并行任务调度器
pub struct TaskScheduler {
    tasks: Arc<Mutex<Vec<Task>>>,
    max_workers: usize,
}

#[derive(Debug, Clone)]
pub struct Task {
    pub id: u64,
    pub entry: usize,
    pub args: Vec<u64>,
}

impl TaskScheduler {
    pub fn new(max_workers: usize) -> Self {
        Self {
            tasks: Arc::new(Mutex::new(Vec::new())),
            max_workers,
        }
    }

    pub fn spawn(&self, entry: usize, args: Vec<u64>) -> Result<u64> {
        let mut tasks = self.tasks.lock().unwrap();
        let id = tasks.len() as u64 + 1;
        tasks.push(Task { id, entry, args });
        Ok(id)
    }

    pub fn join(&self, id: u64) -> Result<()> {
        let tasks = self.tasks.lock().unwrap();
        if tasks.iter().any(|t| t.id == id) {
            Ok(())
        } else {
            Err(UniError::ResourceNotFound)
        }
    }
}

/// 协议契约验证器
pub struct ContractValidator {
    rules: Arc<Mutex<Vec<ContractRule>>>,
}

#[derive(Debug, Clone)]
pub struct ContractRule {
    pub permission: String,
    pub max_calls: Option<u64>,
    pub timeout_ms: u64,
    pub calls_made: u64,
}

impl ContractValidator {
    pub fn new() -> Self {
        Self {
            rules: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn add_rule(&self, rule: ContractRule) {
        let mut rules = self.rules.lock().unwrap();
        rules.push(rule);
    }

    pub fn validate(&self, permission: &str) -> Result<()> {
        let rules = self.rules.lock().unwrap();
        if let Some(rule) = rules.iter().find(|r| r.permission == permission) {
            if let Some(max) = rule.max_calls {
                if rule.calls_made >= max {
                    return Err(UniError::PermissionDenied);
                }
            }
            Ok(())
        } else {
            Err(UniError::PermissionDenied)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_safe_memory() {
        let mut mem = SafeMemory::new(1024);
        mem.write(0, &[1, 2, 3, 4]).unwrap();
        let data = mem.read(0, 4).unwrap();
        assert_eq!(data, vec![1, 2, 3, 4]);
    }

    #[test]
    fn test_safe_register() {
        let mut reg = SafeRegister::new(10, 100);
        assert_eq!(reg.get(), 10);
        reg.add(5).unwrap();
        assert_eq!(reg.get(), 15);
        assert!(reg.set(200).is_err());
    }

    #[test]
    fn test_task_scheduler() {
        let scheduler = TaskScheduler::new(4);
        let id = scheduler.spawn(0x100, vec![1, 2, 3]).unwrap();
        assert_eq!(id, 1);
        scheduler.join(id).unwrap();
    }
}
