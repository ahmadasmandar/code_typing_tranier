/* STM32 HAL template: GPIO EXTI button toggles LED
 * Practice: GPIO input, EXTI interrupt, ISR toggles LED.
 */
#include "stm32xx_hal.h" // replace with stm32f4xx_hal.h, etc.

static void MX_GPIO_Init(void);
void SystemClock_Config(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  while (1) { __WFI(); }
}

void EXTI0_IRQHandler(void)
{
  HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_0);
}

void HAL_GPIO_EXTI_Callback(uint16_t pin)
{
  if (pin == GPIO_PIN_0) {
    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
  }
}

static void MX_GPIO_Init(void)
{
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_SYSCFG_CLK_ENABLE();

  GPIO_InitTypeDef g = {0};
  g.Pin = GPIO_PIN_5; g.Mode = GPIO_MODE_OUTPUT_PP; g.Pull = GPIO_NOPULL; g.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &g);

  g.Pin = GPIO_PIN_0; g.Mode = GPIO_MODE_IT_FALLING; g.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOA, &g);

  HAL_NVIC_SetPriority(EXTI0_IRQn, 2, 0);
  HAL_NVIC_EnableIRQ(EXTI0_IRQn);
}

void SystemClock_Config(void) { /* device specific */ }
