--------------------------------------------------------------------------------
-- VHDL REFERENCE IMPLEMENTATION: VHDL OPERATORS
--------------------------------------------------------------------------------
-- This file demonstrates various VHDL operators including:
-- 1. Logical operators (and, or, nand, nor, xor, xnor)
-- 2. Relational operators (=, /=, <, <=, >, >=)
-- 3. Shift operators (sll, srl, sla, sra, rol, ror)
-- 4. Adding operators (+, -, &)
-- 5. Sign operators (+, -)
-- 6. Multiplying operators (*, /, mod, rem)
-- 7. Miscellaneous operators (**, abs, not)
--------------------------------------------------------------------------------

-- Library declarations
LIBRARY IEEE;
USE IEEE.std_logic_1164.ALL;
USE IEEE.numeric_std.ALL;  -- Required for shift operators and numerical operations

--------------------------------------------------------------------------------
-- ENTITY DECLARATION
--------------------------------------------------------------------------------
ENTITY Vhdl_Operators IS
       PORT (
              -- Control signals
              clk   : IN STD_LOGIC;
              reset : IN STD_LOGIC;
              
              -- Input operands
              a     : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
              b     : IN STD_LOGIC_VECTOR(7 DOWNTO 0);
              c     : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
              d     : IN STD_LOGIC_VECTOR(3 DOWNTO 0);
              
              -- Output results for different operator types
              logical_result    : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
              relational_result : OUT STD_LOGIC;
              shift_result      : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
              adding_result     : OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
              mult_result       : OUT STD_LOGIC_VECTOR(7 DOWNTO 0);
              misc_result       : OUT STD_LOGIC_VECTOR(7 DOWNTO 0)
       );
END ENTITY Vhdl_Operators;

--------------------------------------------------------------------------------
-- ARCHITECTURE DECLARATION
--------------------------------------------------------------------------------
ARCHITECTURE Behavioral OF Vhdl_Operators IS
       -- Internal signals for demonstration
       SIGNAL a_reg, b_reg           : STD_LOGIC_VECTOR(7 DOWNTO 0) := (OTHERS => '0');
       SIGNAL c_reg, d_reg           : STD_LOGIC_VECTOR(3 DOWNTO 0) := (OTHERS => '0');
       SIGNAL op_select              : STD_LOGIC_VECTOR(2 DOWNTO 0) := "000";
       
       -- Signal declarations for type conversions
       SIGNAL a_unsigned : UNSIGNED(7 DOWNTO 0);
       SIGNAL b_unsigned : UNSIGNED(7 DOWNTO 0);
       SIGNAL a_signed   : SIGNED(7 DOWNTO 0);
       
       -- Integer versions for mod and rem operations
       SIGNAL int_a      : INTEGER;
       SIGNAL int_b      : INTEGER := 0;
       
       -- Constants for demonstration
       CONSTANT SHIFT_AMOUNT         : INTEGER := 2;
       
BEGIN
       -- Register inputs on clock edge for synchronous operation
       input_reg : PROCESS (clk, reset)
       BEGIN
              IF (reset = '1') THEN
                     a_reg <= (OTHERS => '0');
                     b_reg <= (OTHERS => '0');
                     c_reg <= (OTHERS => '0');
                     d_reg <= (OTHERS => '0');
                     op_select <= "000";
              ELSIF rising_edge(clk) THEN
                     a_reg <= a;
                     b_reg <= b;
                     c_reg <= c;
                     d_reg <= d;
                     -- Cycle through operator selections
                     op_select <= op_select + "001";
              END IF;
       END PROCESS input_reg;
       
       -- Convert between types for arithmetic operations
       a_unsigned <= UNSIGNED(a_reg);
       b_unsigned <= UNSIGNED(b_reg);
       a_signed <= SIGNED(a_reg);
       
       -- Convert to integers for mod and rem operations
       int_a <= TO_INTEGER(a_unsigned);
       int_b <= TO_INTEGER(b_unsigned) WHEN b_unsigned > 0 ELSE 1; -- Avoid division by zero
       
       ----------------------------------------------------------------
       -- 1. LOGICAL OPERATORS DEMONSTRATION
       -- Precedence: lowest among all operators
       -- Operators: and, or, nand, nor, xor, xnor, not
       ----------------------------------------------------------------
       logical_ops : PROCESS (a_reg, b_reg, op_select)
       BEGIN
              CASE op_select(2 DOWNTO 0) IS
                     WHEN "000" =>
                            -- AND: Returns '1' if both operands are '1'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "10001000" (bitwise AND)
                            -- 
                            -- Truth table for AND:
                            -- a | b | a AND b
                            -- --+---+--------
                            -- 0 | 0 |   0
                            -- 0 | 1 |   0
                            -- 1 | 0 |   0
                            -- 1 | 1 |   1
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 1 0 0 0 1 0 0 0
                            logical_result <= a_reg AND b_reg;
                     WHEN "001" =>
                            -- OR: Returns '1' if either operand is '1'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "11101110" (bitwise OR)
                            -- 
                            -- Truth table for OR:
                            -- a | b | a OR b
                            -- --+---+-------
                            -- 0 | 0 |   0
                            -- 0 | 1 |   1
                            -- 1 | 0 |   1
                            -- 1 | 1 |   1
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 1 1 1 0 1 1 1 0
                            logical_result <= a_reg OR b_reg;
                     WHEN "010" =>
                            -- NAND: Returns '0' if both operands are '1', otherwise '1'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "01110111" (bitwise NAND)
                            -- 
                            -- Truth table for NAND:
                            -- a | b | a NAND b
                            -- --+---+---------
                            -- 0 | 0 |    1
                            -- 0 | 1 |    1
                            -- 1 | 0 |    1
                            -- 1 | 1 |    0
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 0 1 1 1 0 1 1 1
                            logical_result <= a_reg NAND b_reg;
                     WHEN "011" =>
                            -- NOR: Returns '1' if both operands are '0', otherwise '0'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "00010001" (bitwise NOR)
                            -- 
                            -- Truth table for NOR:
                            -- a | b | a NOR b
                            -- --+---+--------
                            -- 0 | 0 |    1
                            -- 0 | 1 |    0
                            -- 1 | 0 |    0
                            -- 1 | 1 |    0
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 0 0 0 1 0 0 0 1
                            logical_result <= a_reg NOR b_reg;
                     WHEN "100" =>
                            -- XOR: Returns '1' if operands are different, otherwise '0'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "01100110" (bitwise XOR)
                            -- 
                            -- Truth table for XOR:
                            -- a | b | a XOR b
                            -- --+---+--------
                            -- 0 | 0 |    0
                            -- 0 | 1 |    1
                            -- 1 | 0 |    1
                            -- 1 | 1 |    0
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 0 1 1 0 0 1 1 0
                            logical_result <= a_reg XOR b_reg;
                     WHEN "101" =>
                            -- XNOR: Returns '1' if operands are the same, otherwise '0'
                            -- Example: If a_reg = "10101010" and b_reg = "11001100"
                            -- Result: "10011001" (bitwise XNOR)
                            -- 
                            -- Truth table for XNOR:
                            -- a | b | a XNOR b
                            -- --+---+---------
                            -- 0 | 0 |    1
                            -- 0 | 1 |    0
                            -- 1 | 0 |    0
                            -- 1 | 1 |    1
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- b_reg:  1 1 0 0 1 1 0 0
                            -- Result: 1 0 0 1 1 0 0 1
                            logical_result <= a_reg XNOR b_reg;
                     WHEN "110" =>
                            -- NOT: Returns the complement of the operand
                            -- Example: If a_reg = "10101010"
                            -- Result: "01010101" (bitwise NOT)
                            -- 
                            -- Truth table for NOT:
                            -- a | NOT a
                            -- --+------
                            -- 0 |   1
                            -- 1 |   0
                            -- 
                            -- Bit-by-bit calculation:
                            -- a_reg:  1 0 1 0 1 0 1 0
                            -- Result: 0 1 0 1 0 1 0 1
                            logical_result <= NOT a_reg;
                     WHEN OTHERS =>
                            -- Default case
                            logical_result <= (OTHERS => 'X');
              END CASE;
       END PROCESS logical_ops;
       
       ----------------------------------------------------------------
       -- 2. RELATIONAL OPERATORS DEMONSTRATION
       -- Precedence: higher than logical operators
       -- Operators: =, /=, <, <=, >, >=
       ----------------------------------------------------------------
       relational_ops : PROCESS (a_reg, b_reg, op_select)
       BEGIN
              CASE op_select(2 DOWNTO 0) IS
                     WHEN "000" =>
                            -- Equality (=): Returns TRUE if operands are equal
                            -- Example: If a_reg = "00001010" and b_reg = "00001010"
                            -- Result: '1' (TRUE because values are identical)
                            -- Example: If a_reg = "00001010" and b_reg = "00001011"
                            -- Result: '0' (FALSE because values differ)
                            relational_result <= '1' WHEN (a_reg = b_reg) ELSE '0';
                     WHEN "001" =>
                            -- Inequality (/=): Returns TRUE if operands are not equal
                            -- Example: If a_reg = "00001010" and b_reg = "00001011"
                            -- Result: '1' (TRUE because values differ)
                            -- Example: If a_reg = "00001010" and b_reg = "00001010"
                            -- Result: '0' (FALSE because values are identical)
                            relational_result <= '1' WHEN (a_reg /= b_reg) ELSE '0';
                     WHEN "010" =>
                            -- Less than (<): Returns TRUE if left operand is less than right operand
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00001111" (decimal 15)
                            -- Result: '1' (TRUE because 10 < 15)
                            -- Example: If a_reg = "00001111" (decimal 15) and b_reg = "00001010" (decimal 10)
                            -- Result: '0' (FALSE because 15 is not < 10)
                            relational_result <= '1' WHEN (a_unsigned < b_unsigned) ELSE '0';
                     WHEN "011" =>
                            -- Less than or equal (<=): Returns TRUE if left operand is less than or equal to right operand
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00001111" (decimal 15)
                            -- Result: '1' (TRUE because 10 <= 15)
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00001010" (decimal 10)
                            -- Result: '1' (TRUE because 10 = 10, so 10 <= 10)
                            relational_result <= '1' WHEN (a_unsigned <= b_unsigned) ELSE '0';
                     WHEN "100" =>
                            -- Greater than (>): Returns TRUE if left operand is greater than right operand
                            relational_result <= '1' WHEN (a_unsigned > b_unsigned) ELSE '0';
                     WHEN "101" =>
                            -- Greater than or equal (>=): Returns TRUE if left operand is greater than or equal to right operand
                            relational_result <= '1' WHEN (a_unsigned >= b_unsigned) ELSE '0';
                     WHEN OTHERS =>
                            -- Default case
                            relational_result <= 'X';
              END CASE;
       END PROCESS relational_ops;
       
       ----------------------------------------------------------------
       -- 3. SHIFT OPERATORS DEMONSTRATION
       -- Precedence: higher than relational operators
       -- Operators: sll, srl, sla, sra, rol, ror
       -- Note: These operators require ieee.numeric_std package
       ----------------------------------------------------------------
       shift_ops : PROCESS (a_reg, op_select)
              VARIABLE a_unsigned_var : UNSIGNED(7 DOWNTO 0);
       BEGIN
              a_unsigned_var := UNSIGNED(a_reg);
              
              CASE op_select(2 DOWNTO 0) IS
                     WHEN "000" =>
                            -- SLL: Shift Left Logical
                            -- Shifts bits left, filling with zeros from right
                            -- Example: If a_reg = "10010101"
                            -- Shift amount = 2
                            -- Result: "01010100" (bits shifted left, zeros added on right)
                            -- 
                            -- Original:  1 0 0 1 0 1 0 1
                            -- Shift:     ← ← ← ← ← ← ← ←
                            -- Result:    0 1 0 1 0 1 0 0
                            shift_result <= STD_LOGIC_VECTOR(a_unsigned_var SLL SHIFT_AMOUNT);
                     WHEN "001" =>
                            -- SRL: Shift Right Logical
                            -- Shifts bits right, filling with zeros from left
                            -- Example: If a_reg = "10010101"
                            -- Shift amount = 3
                            -- Result: "00010010" (bits shifted right, zeros added on left)
                            -- 
                            -- Original:  1 0 0 1 0 1 0 1
                            -- Shift:     → → → → → → → →
                            -- Result:    0 0 0 1 0 0 1 0
                            shift_result <= STD_LOGIC_VECTOR(a_unsigned_var SRL SHIFT_AMOUNT);
                     WHEN "010" =>
                            -- SLA: Shift Left Arithmetic
                            -- Similar to SLL but preserves sign bit for signed values
                            -- Example: If a_reg = "10010101" (negative in 2's complement)
                            -- Shift amount = 3
                            -- Result: "10101000" (sign bit preserved, zeros added on right)
                            -- 
                            -- Original:  1 0 0 1 0 1 0 1
                            -- Shift:     - ← ← ← ← ← ← ←
                            -- Result:    1 0 1 0 1 0 0 0
                            shift_result <= STD_LOGIC_VECTOR(SHIFT_LEFT(a_signed, SHIFT_AMOUNT));
                     WHEN "011" =>
                            -- SRA: Shift Right Arithmetic
                            -- Shifts bits right, replicating sign bit (leftmost bit)
                            -- Example: If a_reg = "10010101" (negative in 2's complement)
                            -- Shift amount = 2
                            -- Result: "11100101" (sign bit replicated on left)
                            -- 
                            -- Original:  1 0 0 1 0 1 0 1
                            -- Shift:     → → → → → → → →
                            -- Result:    1 1 1 0 0 1 0 1
                            shift_result <= STD_LOGIC_VECTOR(SHIFT_RIGHT(a_signed, SHIFT_AMOUNT));
                     WHEN "100" =>
                            -- ROL: Rotate Left
                            -- Rotates bits left, wrapping around (no bits lost)
                            -- Example: If a_reg = "10100011"
                            -- Rotate amount = 2
                            -- Result: "10001110" (leftmost bits wrap to rightmost positions)
                            -- 
                            -- Original:  1 0 1 0 0 0 1 1
                            -- Rotate:    ↖ ← ← ← ← ← ← ↙
                            -- Result:    1 0 0 0 1 1 1 0
                            shift_result <= STD_LOGIC_VECTOR(ROTATE_LEFT(a_unsigned_var, SHIFT_AMOUNT));
                     WHEN "101" =>
                            -- ROR: Rotate Right
                            -- Rotates bits right, wrapping around (no bits lost)
                            -- Example: If a_reg = "10100011"
                            -- Rotate amount = 2
                            -- Result: "11101000" (rightmost bits wrap to leftmost positions)
                            -- 
                            -- Original:  1 0 1 0 0 0 1 1
                            -- Rotate:    ↘ → → → → → → ↗
                            -- Result:    1 1 1 0 1 0 0 0
                            shift_result <= STD_LOGIC_VECTOR(ROTATE_RIGHT(a_unsigned_var, SHIFT_AMOUNT));
                     WHEN OTHERS =>
                            -- Default case
                            shift_result <= (OTHERS => 'X');
              END CASE;
       END PROCESS shift_ops;
       
       ----------------------------------------------------------------
       -- 4. ADDING OPERATORS DEMONSTRATION
       -- Precedence: higher than shift operators
       -- Operators: +, -, & (concatenation)
       ----------------------------------------------------------------
       adding_ops : PROCESS (a_reg, b_reg, c_reg, d_reg, op_select)
       BEGIN
              CASE op_select(1 DOWNTO 0) IS
                     WHEN "00" =>
                            -- Addition (+): Adds two operands
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00000101" (decimal 5)
                            -- Result: "0000000000001111" (decimal 15)
                            -- 
                            -- Binary addition:
                            --   00001010 (10)
                            -- + 00000101 (5)
                            -- = 00001111 (15)
                            adding_result <= STD_LOGIC_VECTOR(RESIZE(a_unsigned + b_unsigned, 16));
                     WHEN "01" =>
                            -- Subtraction (-): Subtracts right operand from left operand
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00000101" (decimal 5)
                            -- Result: "0000000000000101" (decimal 5)
                            -- 
                            -- Binary subtraction:
                            --   00001010 (10)
                            -- - 00000101 (5)
                            -- = 00000101 (5)
                            adding_result <= STD_LOGIC_VECTOR(RESIZE(a_unsigned - b_unsigned, 16));
                     WHEN "10" =>
                            -- Concatenation (&): Joins two or more bit vectors
                            -- Example: If a_reg = "10101010" and b_reg = "11110000"
                            -- Result: "1010101011110000" (a_reg followed by b_reg)
                            -- 
                            -- a_reg:  10101010
                            -- b_reg:  11110000
                            -- Result: 1010101011110000
                            adding_result <= a_reg & b_reg;
                     WHEN OTHERS =>
                            -- More concatenation examples
                            -- Example: If c_reg = "1100" and d_reg = "0011"
                            -- Result: "11000000001100000" (c_reg & "0000" & d_reg & "0000")
                            -- 
                            -- c_reg:   1100
                            -- zeros:   0000
                            -- d_reg:   0011
                            -- zeros:   0000
                            -- Result:  1100000000110000
                            adding_result <= c_reg & "0000" & d_reg & "0000";
              END CASE;
       END PROCESS adding_ops;
       
       ----------------------------------------------------------------
       -- 5 & 6. SIGN AND MULTIPLYING OPERATORS DEMONSTRATION
       -- Sign operators (unary): +, -
       -- Multiplying operators: *, /, mod, rem
       -- Precedence: higher than adding operators
       ----------------------------------------------------------------
       mult_ops : PROCESS (a_unsigned, b_unsigned, int_a, int_b, op_select)
              VARIABLE result_var : INTEGER;
       BEGIN
              CASE op_select(2 DOWNTO 0) IS
                     WHEN "000" =>
                            -- Unary plus (+): Identity operation
                            -- Example: If a_reg = "00001010" (decimal 10)
                            -- Result: "00001010" (unchanged, remains decimal 10)
                            -- 
                            -- This is simply the identity operation that returns the same value
                            mult_result <= STD_LOGIC_VECTOR(+a_unsigned);
                     WHEN "001" =>
                            -- Unary minus (-): Negation
                            -- Example: If a_reg = "00001010" (decimal 10 as unsigned, or decimal 10 as signed)
                            -- Result: "11110110" (2's complement of 10 = -10 in signed representation)
                            -- 
                            -- Two's complement negation:
                            -- 1. Invert all bits:        00001010 → 11110101
                            -- 2. Add 1:                  11110101 + 1 = 11110110
                            mult_result <= STD_LOGIC_VECTOR(-a_signed);
                     WHEN "010" =>
                            -- Multiplication (*): Multiplies two operands
                            -- Example: If a_reg = "00000011" (decimal 3) and b_reg = "00000101" (decimal 5)
                            -- Result: "00001111" (decimal 15)
                            -- 
                            -- Binary multiplication:
                            --   00000011 (3)
                            -- × 00000101 (5)
                            -- = 00001111 (15)
                            mult_result <= STD_LOGIC_VECTOR(RESIZE(a_unsigned * b_unsigned(3 DOWNTO 0), 8));
                     WHEN "011" =>
                            -- Division (/): Divides left operand by right operand
                            -- Example: If a_reg = "00001010" (decimal 10) and b_reg = "00000011" (decimal 3)
                            -- Result: "00000011" (decimal 3, fractional part truncated)
                            -- 
                            -- Integer division:
                            -- 10 ÷ 3 = 3.333... → 3 (truncated)
                            mult_result <= STD_LOGIC_VECTOR(a_unsigned / b_unsigned) WHEN b_unsigned > 0 ELSE (OTHERS => '1');
                     WHEN "100" =>
                            -- Modulus (mod): Returns remainder with same sign as divisor
                            -- Key difference from rem: sign follows the divisor
                            -- 
                            -- Examples from Table 6.6:
                            -- 8 mod 5 = 3    (8 = 1×5 + 3, remainder is 3)
                            -- -8 mod 5 = 2   (sign follows divisor, which is positive)
                            -- 8 mod -5 = -2  (sign follows divisor, which is negative)
                            -- -8 mod -5 = -3 (sign follows divisor, which is negative)
                            result_var := int_a MOD int_b;
                            mult_result <= STD_LOGIC_VECTOR(TO_UNSIGNED(result_var, 8));
                     WHEN "101" =>
                            -- Remainder (rem): Returns remainder with same sign as dividend
                            -- Key difference from mod: sign follows the dividend
                            -- 
                            -- Examples from Table 6.6:
                            -- 8 rem 5 = 3    (8 = 1×5 + 3, remainder is 3)
                            -- -8 rem 5 = -3  (sign follows dividend, which is negative)
                            -- 8 rem -5 = 3   (sign follows dividend, which is positive)
                            -- -8 rem -5 = -3 (sign follows dividend, which is negative)
                            result_var := int_a REM int_b;
                            mult_result <= STD_LOGIC_VECTOR(TO_UNSIGNED(ABS(result_var), 8));
                     WHEN OTHERS =>
                            -- Default case
                            mult_result <= (OTHERS => 'X');
              END CASE;
       END PROCESS mult_ops;
       
       ----------------------------------------------------------------
       -- 7. MISCELLANEOUS OPERATORS DEMONSTRATION
       -- Operators: abs, **
       ----------------------------------------------------------------
       misc_ops : PROCESS (a_signed, b_unsigned, op_select)
              VARIABLE result_var : INTEGER;
       BEGIN
              CASE op_select(1 DOWNTO 0) IS
                     WHEN "00" =>
                            -- ABS: Returns absolute value of the operand
                            -- Example: If a_signed = "11111011" (decimal -5 in 2's complement)
                            -- Result: "00000101" (decimal 5)
                            -- 
                            -- For negative numbers, ABS performs 2's complement:
                            -- 1. Original value:       11111011 (-5)
                            -- 2. Invert all bits:      00000100
                            -- 3. Add 1:               00000101 (5)
                            -- 
                            -- For positive numbers, ABS returns the same value:
                            -- If a_signed = "00000101" (decimal 5)
                            -- Result: "00000101" (unchanged)
                            misc_result <= STD_LOGIC_VECTOR(RESIZE(UNSIGNED(ABS(a_signed)), 8));
                     WHEN "01" =>
                            -- Exponentiation (**): Raises left operand to power of right operand
                            -- Example: If a_unsigned = "00000010" (decimal 2) and b_unsigned = "00000011" (decimal 3)
                            -- Result: "00001000" (decimal 8, because 2³ = 8)
                            -- 
                            -- Calculation:
                            -- 2³ = 2 × 2 × 2 = 8
                            -- 
                            -- Another example: If a_unsigned = "00000011" (decimal 3) and b_unsigned = "00000010" (decimal 2)
                            -- Result: "00001001" (decimal 9, because 3² = 9)
                            -- 
                            -- Note: Limited to small values to avoid overflow
                            result_var := TO_INTEGER(a_unsigned) ** TO_INTEGER(b_unsigned(2 DOWNTO 0));
                            misc_result <= STD_LOGIC_VECTOR(TO_UNSIGNED(result_var, 8));
                     WHEN OTHERS =>
                            -- Default case
                            misc_result <= (OTHERS => 'X');
              END CASE;
       END PROCESS misc_ops;

       ----------------------------------------------------------------
       -- ADDITIONAL EXAMPLES OF CONCATENATION OPERATOR
       -- These are for demonstration only and not connected to outputs
       ----------------------------------------------------------------
       concatenation_examples : PROCESS (a_reg, b_reg, c_reg)
              -- Examples similar to Listing 6.1 in the chapter
              VARIABLE A_val, B_val : STD_LOGIC_VECTOR(3 DOWNTO 0);
              VARIABLE C_val : STD_LOGIC_VECTOR(5 DOWNTO 0);
              VARIABLE D_val : STD_LOGIC_VECTOR(7 DOWNTO 0);
       BEGIN
              -- Initialize with input values for demonstration
              A_val := c_reg;
              B_val := d_reg;
              
              -- Examples of concatenation operator
              C_val := A_val & "00";           -- Append "00" to A_val
              C_val := "11" & B_val;           -- Prepend "11" to B_val
              C_val := '1' & A_val & '0';      -- Surround A_val with bits
              D_val := "0001" & C_val(3 DOWNTO 0); -- Combine with slices
              D_val := A_val & B_val;          -- Combine two vectors
       END PROCESS concatenation_examples;

END ARCHITECTURE Behavioral;
