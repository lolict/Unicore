; UniCore 示例程序 - 阶乘计算
; 计算 5! = 120

MOVI R1, 5       ; n = 5
MOVI R2, 1       ; result = 1

loop:
MUL R2, R2, R1   ; result *= n
ADDI R1, R1, -1  ; n--
CMP R1, R0       ; 比较 n 和 0
JNE loop         ; 如果 n > 0，继续

; R2 现在是 120 (5!)
HALT             ; 结束
