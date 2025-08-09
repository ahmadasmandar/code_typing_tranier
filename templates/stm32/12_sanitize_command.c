/* Extracted from help_functions.c
 * Function: sanitize_command()
 * Purpose:
 *   1) Remove leading CR/LF from a command buffer
 *   2) If the cleaned command ends with "Z#" and doesn't start with '>', prepend '>'
 */
#include <string.h>
#include <stddef.h>

void sanitize_command(char *cmd, size_t buf_size)
{
    if (!cmd || buf_size==0) return;

    // 1) Trim leading CR/LF
    size_t skip = strspn(cmd, "\r\n");
    if (skip) {
        memmove(cmd, cmd + skip, strlen(cmd + skip) + 1);
    }

    // 2) Check for Z# at the end and prepend '>' if missing
    size_t len = strnlen(cmd, buf_size);
    if (len >= 2 && cmd[len - 1] == '#' && cmd[len - 2] == 'Z' && cmd[0] != '>') {
        if (len + 1 < buf_size) {
            memmove(cmd + 1, cmd, len + 1);  // include terminator
            cmd[0] = '>';
        }
    }
}
