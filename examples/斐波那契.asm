; UniCore 示例程序 - 斐波那契数列
; 计算前10个斐波那契数

MOVI R1, 0       ; F(0) = 0
MOVI R2, 1       ; F(1) = 1
MOVI R3, 10      ; 计算10个数
MOVI R4, 0       ; 计数器

loop:
STORE R1, [R4]   ; 存储 F(n)
ADD R5, R1, R2   ; temp = F(n) + F(n+1)
MOV R1, R2       ; F(n) = F(n+1)
MOV R2, R5       ; F(n+1) = temp
ADDI R4, R4, 1  ; 计数器++
CMP R4, R3       ; 比较计数器和上限
JNE loop         ; 如果还没到10个，继续

HALT             ; 结束
