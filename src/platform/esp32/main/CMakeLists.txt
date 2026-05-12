cmake_minimum_required(VERSION 3.5)

project(unicore_esp32)

set(COMPONENT_ADD_INCLUDEDIRS "")

set(COMPONENT_REQUIRES esp_timer esp_system freertos)

register_component()

target_add_binary_data(${COMPONENT_TARGET} "unicore.wasm" TEXT)

set_source_files_properties(unicore.wasm PROPERTIES HEADER_FILE_ONLY TRUE)

idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "."
    REQUIRES esp_timer esp_system freertos
)
