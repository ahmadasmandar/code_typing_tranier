/* STM32 HAL template: Timer PWM duty ramp
 * Practice: TIM PWM init, CCR update.
 */
#include "stm32xx_hal.h"

TIM_HandleTypeDef htim3; // example timer

static void MX_TIM3_Init(void)
{
  __HAL_RCC_TIM3_CLK_ENABLE();
  TIM_OC_InitTypeDef sConfig = {0};

  htim3.Instance = TIM3;
  htim3.Init.Prescaler = 7999;   // adjust for your clock
  htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim3.Init.Period = 999;
  htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  HAL_TIM_PWM_Init(&htim3);

  sConfig.OCMode = TIM_OCMODE_PWM1;
  sConfig.Pulse = 0;
  sConfig.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfig.OCFastMode = TIM_OCFAST_DISABLE;
  HAL_TIM_PWM_ConfigChannel(&htim3, &sConfig, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
}

void SystemClock_Config(void);
static void MX_GPIO_Init(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();
  MX_TIM3_Init();

  uint32_t duty = 0;
  while (1) {
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, duty);
    duty = (duty + 50) % 1000;
    HAL_Delay(50);
  }
}

static void MX_GPIO_Init(void)
{
  __HAL_RCC_GPIOA_CLK_ENABLE();
  // Configure alternate function pin for TIM3 CH1 as needed
}

void SystemClock_Config(void) { /* device specific */ }
