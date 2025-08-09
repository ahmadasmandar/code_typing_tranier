/* Extracted from help_functions.c
 * Function: delay_us()
 * Purpose: Busy-wait a precise number of microseconds using a running timer.
 */
#include "stm32xx_hal.h" // replace with correct series header

// extern TIM_HandleTypeDef htim9; // provide your timer instance

void delay_us(uint16_t microseconds)
{
    uint16_t startTick = __HAL_TIM_GET_COUNTER(&htim9);
    uint16_t endTick   = (uint16_t)(startTick + microseconds) % (htim9.Init.Period + 1); /* Handle overflow */

    if (endTick < startTick) { /* Handle timer wraparound */
        while (__HAL_TIM_GET_COUNTER(&htim9) >= startTick) {
            /* Wait for counter to wrap around */
        }
    }
    while (__HAL_TIM_GET_COUNTER(&htim9) < endTick) {
        /* Wait until target tick is reached */
    }
}
