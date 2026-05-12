; UniCore 示例 - 排序算法（冒泡排序）
; 对数组 [5, 3, 8, 1, 9, 2] 进行排序

MOVI R1, 6       ; 数组长度 n = 6
MOVI R2, 0       ; i = 0 (外循环计数器)

outer_loop:
MOVI R3, 0       ; j = 0 (内循环计数器)
MOVI R4, 0       ; swapped = 0

inner_loop:
; 比较 arr[j] 和 arr[j+1]
STORE R1, [R3]   ; temp = arr[j] (用R1临时存储)

; 如果 arr[j] <= arr[j+1]，跳过交换
ADDI R5, R3, 1   ; R5 = j + 1
LOAD R6, [R5]    ; R6 = arr[j+1]

; 计算偏移
MUL R7, R3, R1   ; R7 = j * 4
ADD R8, R7, R2   ; R8 = base + j*4

; 比较
CMP R1, R6
JLE skip_swap

; 交换 arr[j] 和 arr[j+1]
STORE R6, [R8]   ; arr[j] = arr[j+1]
ADDI R9, R8, 4   ; R9 = j + 1 的地址
STORE R1, [R9]   ; arr[j+1] = temp
MOVI R4, 1       ; swapped = 1

skip_swap:
ADDI R3, R3, 1   ; j++
SUB R10, R1, R3   ; R10 = n - j
CMP R10, R1
JGT inner_loop    ; 如果 j < n-1，继续内循环

CMP R4, R0       ; 检查 swapped
JNE outer_loop    ; 如果 swapped == 1，继续外循环

HALT             ; 排序完成
