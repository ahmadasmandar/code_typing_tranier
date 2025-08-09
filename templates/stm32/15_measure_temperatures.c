/* Extracted from help_functions.c
 * Function: measure_temperatures()
 * Purpose: Read multiple temperature sensors and format a JSON object, then TX via UART DMA.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "stm32xx_hal.h" // replace with your series header

// externs/placeholders expected from the project environment
// extern UART_HandleTypeDef huart2;
// float TMP1075_Get_Temperature_Celsius(uint8_t addr);
// int print_number_or_float(UART_HandleTypeDef *huart, float val, const char *label,
//                           int width, int prec, const char *suffix,
//                           char *out, size_t out_sz, int also_print);

void measure_temperatures(uint8_t num, char *json_out, size_t out_size,
                          uint8_t temp_sens_counter, uint8_t *temp_addresses)
{
    if (!json_out || out_size==0 || !temp_addresses) return;

    char json_output[256];
    int offset = 0;
    offset += snprintf(json_output + offset, sizeof(json_output) - offset, "{");

    /* Read temperatures from all sensors */
    for (uint8_t i = 0; i < num; ++i) {
        for (uint8_t j = 0; j < temp_sens_counter; ++j) {
            uint8_t addr = temp_addresses[j];
            float temperature = TMP1075_Get_Temperature_Celsius(addr);
            static char id_str[4];

            /* Map sensor address to meaningful name */
            const char *key;
            switch (addr) {
                case 73: key = "temp_system"; break;
                case 72: key = "temp_drivers"; break;
                case 75: key = "temp_motor_x"; break;
                case 79: key = "temp_motor_y"; break;
                default:
                    snprintf(id_str, sizeof(id_str), "%u", addr);
                    key = id_str; break;
            }

            /* Format temperature value */
            char val_str[16];
            print_number_or_float(&huart2, temperature, "", 3, 1, "",
                                  val_str, sizeof(val_str), 0);

            /* Append to JSON */
            offset += snprintf(json_output + offset, sizeof(json_output) - offset,
                               "\"%s\":%s,", key, val_str);

            HAL_Delay(10);
        }
    }

    /* Close JSON object (replace possible trailing comma with brace) */
    if (offset>1 && json_output[offset-1]==',') {
        json_output[offset-1] = '}';
        json_output[offset] = '\0';
    } else {
        offset += snprintf(json_output + offset, sizeof(json_output) - offset, "}");
    }

    /* Copy to caller's buffer with safety */
    strncpy(json_out, json_output, out_size - 1);
    json_out[out_size - 1] = '\0';

    HAL_UART_Transmit_DMA(&huart2, (uint8_t *)json_out, strlen(json_out));
}
