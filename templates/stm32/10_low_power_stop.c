/* STM32 HAL template: Low-power STOP mode with EXTI wakeup
 * Practice: Enter STOP, wake on button (PA0), reconfigure clocks.
 */
#include "stm32xx_hal.h"

static void MX_GPIO_Init(void);
void SystemClock_Config(void);
void SystemClock_ReConfig_AfterStop(void);

int main(void)
{
  HAL_Init();
  SystemClock_Config();
  MX_GPIO_Init();

  while(1){
    // prepare wakeup on PA0 falling edge
    HAL_SuspendTick();
    HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
    HAL_ResumeTick();

    SystemClock_ReConfig_AfterStop();

    // indicate wake
    for (int i=0;i<3;i++){ HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5); HAL_Delay(100); }
  }
}

void SystemClock_ReConfig_AfterStop(void)
{
  // Re-enable PLL/HSE as per your board. Stub for brevity.
}

static void MX_GPIO_Init(void)
{
  __HAL_RCC_GPIOA_CLK_ENABLE();
  GPIO_InitTypeDef g={0};
  g.Pin = GPIO_PIN_5; g.Mode = GPIO_MODE_OUTPUT_PP; g.Pull = GPIO_NOPULL; g.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &g);

  g.Pin = GPIO_PIN_0; g.Mode = GPIO_MODE_IT_FALLING; g.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOA, &g);
  HAL_NVIC_SetPriority(EXTI0_IRQn,2,0);
  HAL_NVIC_EnableIRQ(EXTI0_IRQn);
}

void EXTI0_IRQHandler(void){ HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_0); }
void HAL_GPIO_EXTI_Callback(uint16_t pin){ if(pin==GPIO_PIN_0){ /* nothing */ } }

void SystemClock_Config(void){ /* device specific */ }
