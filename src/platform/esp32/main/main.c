#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_timer.h"

#define UNICORE_WASM_SIZE 49152
#define UNICORE_STACK_SIZE 8192
#define UNICORE_HEAP_SIZE 65536

static uint8_t wasm_memory[UNICORE_HEAP_SIZE];
static uint8_t wasm_stack[UNICORE_STACK_SIZE];
static uint8_t wasm_binary[UNICORE_WASM_SIZE];

typedef struct {
    uint32_t registers[32];
    uint32_t pc;
    uint32_t sp;
    uint32_t running;
} unicore_state_t;

static unicore_state_t unicore_state;

void unicore_init(void) {
    memset(&unicore_state, 0, sizeof(unicore_state_t));
    memset(wasm_memory, 0, UNICORE_HEAP_SIZE);
    unicore_state.sp = (uint32_t)wasm_stack + UNICORE_STACK_SIZE;
    unicore_state.running = 1;
    printf("[UniCore] ESP32 Runtime Initialized\n");
}

int unicore_load_wasm(const uint8_t *data, size_t len) {
    if (len > UNICORE_WASM_SIZE) {
        printf("[UniCore] Error: WASM binary too large\n");
        return -1;
    }
    memcpy(wasm_binary, data, len);
    printf("[UniCore] Loaded %d bytes of WASM\n", len);
    return 0;
}

void unicore_execute(void) {
    printf("[UniCore] Starting execution...\n");
    unicore_state.running = 1;
    
    while (unicore_state.running && unicore_state.pc < UNICORE_WASM_SIZE) {
        uint8_t opcode = wasm_binary[unicore_state.pc];
        
        switch (opcode) {
            case 0x00: // NOP
                break;
            case 0x01: // ADD
                if (unicore_state.registers[2] < 32) {
                    unicore_state.registers[unicore_state.registers[2]] = 
                        unicore_state.registers[unicore_state.registers[0]] + 
                        unicore_state.registers[unicore_state.registers[1]];
                }
                break;
            case 0x30: // JMP
                unicore_state.pc = unicore_state.registers[0];
                break;
            case 0x33: // HALT
                unicore_state.running = 0;
                break;
            default:
                printf("[UniCore] Unknown opcode: 0x%02x\n", opcode);
                break;
        }
        
        unicore_state.pc++;
    }
    
    printf("[UniCore] Execution finished\n");
}

void unicore_task(void *pvParameters) {
    unicore_init();
    
    while (1) {
        if (unicore_state.running) {
            unicore_execute();
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void) {
    printf("\n========================================\n");
    printf("   UniCore ESP32 Runtime v1.0.0\n");
    printf("========================================\n\n");
    
    unicore_init();
    
    xTaskCreate(&unicore_task, "unicore", 8192, NULL, 5, NULL);
    
    printf("[UniCore] System started successfully\n");
}
