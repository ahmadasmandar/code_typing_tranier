/* Extracted from help_functions.c
 * Function: parse_z_frame()
 * Purpose: Parse a JSON-like frame from USART and atomically update RemoteState_t.
 */
#include <string.h>
#include <stdint.h>
#include <stddef.h>

/* Placeholders you should adapt to your project */
// typedef struct {
//   char     position[32];
//   uint8_t  referenced;
//   uint8_t  busy;
//   uint8_t  back;
//   uint8_t  front;
//   uint8_t  speed;
// } RemoteState_t;
// extern RemoteState_t remoteState;
// void __disable_irq(void);
// void __enable_irq(void);

void parse_z_frame(const char *frame)
{
    RemoteState_t tmp = {0};

    /* p – Position ------------------------------------------------ */
    const char *tag = strstr(frame, "\"p\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        size_t n = 0;
        while (*tag && *tag != ',' && *tag != '}' && n < sizeof tmp.position - 1) {
            tmp.position[n++] = *tag++;
        }
        tmp.position[n] = '\0';
    }

    /* r – Referenced --------------------------------------------- */
    tag = strstr(frame, "\"r\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        tmp.referenced = (*tag == '1');
    }

    /* b – Busy ---------------------------------------------------- */
    tag = strstr(frame, "\"b\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        tmp.busy = (*tag == '1');
    }

    /* o – Back-Switch -------------------------------------------- */
    tag = strstr(frame, "\"o\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        tmp.back = (*tag == '1');
    }

    /* u – Front-Switch ------------------------------------------- */
    tag = strstr(frame, "\"u\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        tmp.front = (*tag == '1');
    }

    /* v – Speed --------------------------------------------------- */
    tag = strstr(frame, "\"v\":");
    if (tag) {
        tag += 3;
        while (*tag == ' ' || *tag == ':') ++tag;
        tmp.speed = (uint8_t)strtoul(tag, NULL, 10);
    }

    /* atomar übernehmen ------------------------------------------ */
    __disable_irq();
    remoteState = tmp;
    __enable_irq();
}
