/* STM32 HAL template: SPI loopback/echo
 * Practice: SPI init, transmit/receive, buffer compare.
 */
#include <string.h>
#include <stdio.h>
#include "stm32xx_hal.h"

SPI_HandleTypeDef hspi1;
UART_HandleTypeDef huart2;

int __io_putchar(int ch){ HAL_UART_Transmit(&huart2,(uint8_t*)&ch,1,HAL_MAX_DELAY); return ch; }

static void MX_SPI1_Init(void)
{
  __HAL_RCC_SPI1_CLK_ENABLE();
  hspi1.Instance = SPI1;
  hspi1.Init.Mode = SPI_MODE_MASTER;
  hspi1.Init.Direction = SPI_DIRECTION_2LINES;
  hspi1.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi1.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi1.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi1.Init.NSS = SPI_NSS_SOFT;
  hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_16;
  hspi1.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi1.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi1.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  HAL_SPI_Init(&hspi1);
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
  MX_SPI1_Init();

  uint8_t tx[8] = {1,2,3,4,5,6,7,8};
  uint8_t rx[8] = {0};

  HAL_SPI_TransmitReceive(&hspi1, tx, rx, sizeof(tx), HAL_MAX_DELAY);
  if (memcmp(tx, rx, sizeof(tx))==0) printf("SPI OK\r\n");
  else printf("SPI mismatch\r\n");

  while(1){ HAL_Delay(1000); }
}

static void MX_GPIO_Init(void){ __HAL_RCC_GPIOA_CLK_ENABLE(); }
void SystemClock_Config(void){ /* device specific */ }
