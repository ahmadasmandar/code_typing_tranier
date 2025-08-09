/* STM32 HAL template: I2C bus scan
 * Practice: I2C init, HAL_I2C_IsDeviceReady across 0..127.
 */
#include <stdio.h>
#include "stm32xx_hal.h"

I2C_HandleTypeDef hi2c1;
UART_HandleTypeDef huart2;

int __io_putchar(int ch){ HAL_UART_Transmit(&huart2,(uint8_t*)&ch,1,HAL_MAX_DELAY); return ch; }

static void MX_I2C1_Init(void)
{
  __HAL_RCC_I2C1_CLK_ENABLE();
  hi2c1.Instance = I2C1;
  hi2c1.Init.Timing = 0x00707CBB; // example timing
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  HAL_I2C_Init(&hi2c1);
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
  MX_I2C1_Init();

  for(;;){
    for (uint16_t addr=1; addr<127; ++addr){
      if (HAL_I2C_IsDeviceReady(&hi2c1, addr<<1, 1, 5) == HAL_OK){
        printf("Found I2C 0x%02X\r\n", (unsigned)addr);
      }
    }
    HAL_Delay(2000);
  }
}

static void MX_GPIO_Init(void){ __HAL_RCC_GPIOB_CLK_ENABLE(); }
void SystemClock_Config(void){ /* device specific */ }
