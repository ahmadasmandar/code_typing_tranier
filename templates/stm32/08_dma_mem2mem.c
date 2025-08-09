/* STM32 HAL template: DMA mem2mem transfer
 * Practice: DMA init, start, complete flag.
 */
#include <string.h>
#include <stdio.h>
#include "stm32xx_hal.h"

DMA_HandleTypeDef hdma;
UART_HandleTypeDef huart2;

int __io_putchar(int ch){ HAL_UART_Transmit(&huart2,(uint8_t*)&ch,1,HAL_MAX_DELAY); return ch; }

static void MX_DMA_Init(void)
{
  __HAL_RCC_DMA1_CLK_ENABLE();
  hdma.Instance = DMA1_Channel1; // example
  hdma.Init.Direction = DMA_MEMORY_TO_MEMORY;
  hdma.Init.PeriphInc = DMA_PINC_ENABLE;
  hdma.Init.MemInc = DMA_MINC_ENABLE;
  hdma.Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
  hdma.Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
  hdma.Init.Mode = DMA_NORMAL;
  hdma.Init.Priority = DMA_PRIORITY_LOW;
  HAL_DMA_Init(&hdma);
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
  MX_DMA_Init();

  uint32_t src[16];
  uint32_t dst[16];
  for (uint32_t i=0;i<16;i++) src[i]=i, dst[i]=0;

  HAL_DMA_Start(&hdma, (uint32_t)src, (uint32_t)dst, 16);
  while (HAL_DMA_PollForTransfer(&hdma, HAL_DMA_FULL_TRANSFER, HAL_MAX_DELAY) != HAL_OK) {}

  printf("DMA copied: %lu -> %lu\r\n", (unsigned long)src[5], (unsigned long)dst[5]);
  while(1){ HAL_Delay(1000);} 
}

static void MX_GPIO_Init(void){ /* clocks as needed */ }
void SystemClock_Config(void){ /* device specific */ }
