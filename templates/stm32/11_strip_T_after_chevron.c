/* Extracted from help_functions.c
 * Function: strip_T_after_chevron()
 * Purpose: If a command starts with ">T", remove the 'T' (e.g. ">TMA..." -> ">MA...")
 */
#include <string.h>
#include <stddef.h>

void strip_T_after_chevron(char *buf)
{
    // If buffer is at least 3 chars and buf[0]== '>' and buf[1] == 'T', remove that 'T'
    if (!buf) return;
    if (buf[0] == '>' && buf[1] == 'T') {
        // Move tail (starting at buf[2]) one position to the left, including the terminator
        size_t tail_len = strlen(buf + 2) + 1;
        memmove(&buf[1], &buf[2], tail_len);
    }
}
