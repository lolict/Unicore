// UniCore 统一指令集定义
// UniISA - UniCore Instruction Set Architecture

pub const WORD_SIZE: usize = 8;
pub const MAX_REGISTERS: usize = 32;
pub const STACK_SIZE: usize = 65536;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum OpCode {
    // 算术运算 (0x00-0x0F)
    NOP = 0x00,
    ADD = 0x01,
    SUB = 0x02,
    MUL = 0x03,
    DIV = 0x04,
    MOD = 0x05,
    INC = 0x06,
    DEC = 0x07,

    // 位运算 (0x10-0x1F)
    AND = 0x10,
    OR  = 0x11,
    NOT = 0x12,
    XOR = 0x13,
    SHL = 0x14,
    SHR = 0x15,

    // 比较运算 (0x20-0x2F)
    CMP = 0x20,
    JE  = 0x21,
    JNE = 0x22,
    JL  = 0x23,
    JLE = 0x24,
    JG  = 0x25,
    JGE = 0x26,

    // 控制流 (0x30-0x3F)
    JMP = 0x30,
    CALL = 0x31,
    RET  = 0x32,
    HALT = 0x33,

    // 内存操作 (0x40-0x4F)
    LOAD  = 0x40,
    STORE = 0x41,
    PUSH  = 0x42,
    POP   = 0x43,
   ALLOC = 0x44,
    FREE  = 0x45,

    // 并行操作 (0x50-0x5F)
    SPAWN = 0x50,
    SYNC  = 0x51,
    SEND  = 0x52,
    RECV  = 0x53,
    JOIN  = 0x54,

    // AI操作 (0x60-0x6F)
    INFER    = 0x60,
    EMBED    = 0x61,
    TOKENIZE = 0x62,
    ATTENTION = 0x63,

    // 多媒体 (0x70-0x7F)
    PLAY    = 0x70,
    RENDER  = 0x71,
    CAPTURE = 0x72,
    ENCODE  = 0x73,
    DECODE  = 0x74,

    // 系统调用 (0x80-0x8F)
    SYSCALL = 0x80,
    THREAD_CREATE = 0x81,
    THREAD_JOIN   = 0x82,
    MUTEX_LOCK    = 0x83,
    MUTEX_UNLOCK  = 0x84,

    // 扩展操作 (0xE0-0xFF)
    EXT0 = 0xE0,
    EXT1 = 0xE1,
    EXT2 = 0xE2,
    EXT3 = 0xE3,
}

#[derive(Debug, Clone)]
pub struct Instruction {
    pub opcode: OpCode,
    pub operands: Vec<Value>,
}

#[derive(Debug, Clone)]
pub enum Value {
    Imm(i64),
    ImmF(f64),
    Reg(usize),
    Mem(i64),
    Label(String),
}

#[derive(Debug, Clone)]
pub struct VMState {
    pub registers: [u64; MAX_REGISTERS],
    pub pc: usize,
    pub sp: usize,
    pub memory: Vec<u8>,
    pub running: bool,
}

impl VMState {
    pub fn new() -> Self {
        Self {
            registers: [0; MAX_REGISTERS],
            pc: 0,
            sp: STACK_SIZE,
            memory: vec![0; STACK_SIZE * 2],
            running: true,
        }
    }

    pub fn execute(&mut self, instr: &Instruction) -> Result<(), String> {
        match instr.opcode {
            OpCode::NOP => {},
            OpCode::ADD => self.execute_add(&instr.operands)?,
            OpCode::SUB => self.execute_sub(&instr.operands)?,
            OpCode::LOAD => self.execute_load(&instr.operands)?,
            OpCode::STORE => self.execute_store(&instr.operands)?,
            OpCode::JMP => self.execute_jmp(&instr.operands)?,
            OpCode::HALT => self.running = false,
            _ => return Err(format!("Unknown opcode: {:?}", instr.opcode)),
        }
        self.pc += 1;
        Ok(())
    }

    fn execute_add(&mut self, ops: &[Value]) -> Result<(), String> {
        if ops.len() < 3 {
            return Err("ADD requires 3 operands".to_string());
        }
        let a = self.get_value(&ops[0])?;
        let b = self.get_value(&ops[1])?;
        self.set_value(&ops[2], a + b)?;
        Ok(())
    }

    fn execute_sub(&mut self, ops: &[Value]) -> Result<(), String> {
        if ops.len() < 3 {
            return Err("SUB requires 3 operands".to_string());
        }
        let a = self.get_value(&ops[0])?;
        let b = self.get_value(&ops[1])?;
        self.set_value(&ops[2], a - b)?;
        Ok(())
    }

    fn execute_load(&mut self, ops: &[Value]) -> Result<(), String> {
        if ops.len() < 2 {
            return Err("LOAD requires 2 operands".to_string());
        }
        let addr = self.get_value(&ops[1])? as usize;
        let val = u64::from_le_bytes(self.memory[addr..addr+8].try_into().unwrap());
        self.set_value(&ops[0], val as i64 as u64)?;
        Ok(())
    }

    fn execute_store(&mut self, ops: &[Value]) -> Result<(), String> {
        if ops.len() < 2 {
            return Err("STORE requires 2 operands".to_string());
        }
        let val = self.get_value(&ops[0])?;
        let addr = self.get_value(&ops[1])? as usize;
        self.memory[addr..addr+8].copy_from_slice(&val.to_le_bytes());
        Ok(())
    }

    fn execute_jmp(&mut self, ops: &[Value]) -> Result<(), String> {
        if ops.is_empty() {
            return Err("JMP requires 1 operand".to_string());
        }
        let target = self.get_value(&ops[0])?;
        self.pc = target as usize;
        Ok(())
    }

    fn get_value(&self, v: &Value) -> Result<u64, String> {
        match v {
            Value::Imm(i) => Ok(*i as u64),
            Value::Reg(r) => Ok(self.registers[*r]),
            Value::Mem(off) => {
                let addr = (self.sp as i64 + off) as usize;
                Ok(u64::from_le_bytes(self.memory[addr..addr+8].try_into().unwrap()))
            }
            _ => Err("Unsupported value type".to_string()),
        }
    }

    fn set_value(&mut self, v: &Value, val: u64) -> Result<(), String> {
        match v {
            Value::Reg(r) => { self.registers[*r] = val; Ok(()) }
            Value::Mem(off) => {
                let addr = (self.sp as i64 + off) as usize;
                self.memory[addr..addr+8].copy_from_slice(&val.to_le_bytes());
                Ok(())
            }
            _ => Err("Cannot set this value type".to_string()),
        }
    }
}

impl Default for VMState {
    fn default() -> Self {
        Self::new()
    }
}

// 高级语言到UniISA的编译器接口
pub trait Compiler {
    fn compile(&self, source: &str) -> Result<Vec<Instruction>, String>;
}

// 反汇编器
pub fn disassemble(instr: &Instruction) -> String {
    format!("{:?} {:?}", instr.opcode, instr.operands)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vm_add() {
        let mut state = VMState::new();
        state.registers[0] = 5;
        state.registers[1] = 3;

        let instr = Instruction {
            opcode: OpCode::ADD,
            operands: vec![Value::Reg(0), Value::Reg(1), Value::Reg(2)],
        };

        state.execute(&instr).unwrap();
        assert_eq!(state.registers[2], 8);
    }

    #[test]
    fn test_vm_jmp() {
        let mut state = VMState::new();
        state.pc = 0;

        let instr = Instruction {
            opcode: OpCode::JMP,
            operands: vec![Value::Imm(100)],
        };

        state.execute(&instr).unwrap();
        assert_eq!(state.pc, 100);
    }
}
