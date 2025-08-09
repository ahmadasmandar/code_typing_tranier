/* Extracted from help_functions.c
 * Function: Print_Time()
 * Purpose: Read RTC (DS3231_get) and transmit formatted timestamp via UART DMA
 */
#include <stdio.h>
#include <string.h>
#include "stm32xx_hal.h" // replace as needed

// externs (provided by your project)
// extern UART_HandleTypeDef huart2;
// typedef struct { uint8_t hour,min,sec,mday,mon,year; } DS_TIME;
// void DS3231_get(DS_TIME *t);

void Print_Time()
{
    DS_TIME new_get_time;
    char time_buffer[50];
    DS3231_get(&new_get_time);
    snprintf(time_buffer, sizeof(time_buffer),
             "D:%02u%02u%02u_%02u%02u%02u;",
             new_get_time.hour, new_get_time.min, new_get_time.sec,
             new_get_time.mday, new_get_time.mon, new_get_time.year);
    HAL_UART_Transmit_DMA(&huart2, (uint8_t *)time_buffer, strlen(time_buffer));
}
