/* STM32 HAL template: RTC time/date read
 * Practice: RTC init and printing time.
 */
#include <stdio.h>
#include "stm32xx_hal.h"

RTC_HandleTypeDef hrtc;
UART_HandleTypeDef huart2;

int __io_putchar(int ch){ HAL_UART_Transmit(&huart2,(uint8_t*)&ch,1,HAL_MAX_DELAY); return ch; }

static void MX_RTC_Init(void)
{
  __HAL_RCC_RTC_ENABLE();
  hrtc.Instance = RTC;
  hrtc.Init.HourFormat = RTC_HOURFORMAT_24;
  hrtc.Init.AsynchPrediv = 127;
  hrtc.Init.SynchPrediv = 255;
  hrtc.Init.OutPut = RTC_OUTPUT_DISABLE;
  HAL_RTC_Init(&hrtc);
}

static void MX_USART2_UART_Init(void)
{
  __HAL_RCC_USART2_CLK_ENABLE();
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  HAL_UART_Init(&huart2);
}

void SystemClock_Config(void);
static void MX_GPIO_Init(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_USART2_UART_Init();
  MX_RTC_Init();

  RTC_TimeTypeDef t; RTC_DateTypeDef d;
  while(1){
    HAL_RTC_GetTime(&hrtc, &t, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, &d, RTC_FORMAT_BIN);
    printf("%02u:%02u:%02u %02u/%02u/20%02u\r\n", t.Hours, t.Minutes, t.Seconds, d.Date, d.Month, d.Year);
    HAL_Delay(1000);
  }
}

static void MX_GPIO_Init(void){ /* clocks as needed */ }
void SystemClock_Config(void){ /* device specific */ }
