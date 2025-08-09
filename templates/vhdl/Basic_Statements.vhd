--------------------------------------------------------------------------------
-- VHDL REFERENCE IMPLEMENTATION: BASIC STATEMENTS
--------------------------------------------------------------------------------
-- This file demonstrates various VHDL concepts including:
-- 1. Library declarations and package imports
-- 2. Entity and architecture definitions
-- 3. Signal declarations and assignments
-- 4. Process statements with sensitivity lists
-- 5. Sequential statements within processes (if, case)
-- 6. Concurrent statements outside processes
-- 7. Data-flow vs. Behavioral modeling styles
--------------------------------------------------------------------------------

-- Library declarations - Always include these at the top of your VHDL files
LIBRARY IEEE;                -- IEEE library contains standard packages
USE IEEE.std_logic_1164.ALL; -- Package for std_logic types and operations
USE IEEE.numeric_std.ALL;    -- Package for numeric operations

--------------------------------------------------------------------------------
-- ENTITY DECLARATION
--------------------------------------------------------------------------------
-- The entity defines the interface (inputs/outputs) of the design
-- This is the "black box" view of your circuit
--------------------------------------------------------------------------------
ENTITY Basic_Statements IS
       PORT
       (
              -- Standard control signals
              clk   : IN STD_LOGIC; -- System clock
              reset : IN STD_LOGIC; -- Active high reset

              -- Data signals with vector types
              a              : IN STD_LOGIC_VECTOR(3 DOWNTO 0); -- First input operand
              b              : IN STD_LOGIC_VECTOR(3 DOWNTO 0); -- Second input operand
              sel            : IN STD_LOGIC_VECTOR(1 DOWNTO 0); -- Selector
              D0, D1, D2, D3 : IN STD_LOGIC;                    -- Data inputs
              result         : OUT STD_LOGIC_VECTOR(3 DOWNTO 0) -- Output result
       );
END ENTITY Basic_Statements;

--------------------------------------------------------------------------------
-- ARCHITECTURE DECLARATION
--------------------------------------------------------------------------------
-- The architecture describes the behavior or structure of the entity
-- This example demonstrates both data-flow and behavioral modeling styles
--------------------------------------------------------------------------------
ARCHITECTURE Behavioral OF Basic_Statements IS
       -- DECLARATION SECTION: Internal signals, constants, and components
       -- Signal declarations with initial values
       SIGNAL a_reg                          : STD_LOGIC_VECTOR(3 DOWNTO 0) := "0000";
       SIGNAL b_reg                          : STD_LOGIC_VECTOR(3 DOWNTO 0) := "0000";
       SIGNAL d1_int, d2_int, d3_int, d4_int : STD_LOGIC                    := 'X';
       SIGNAL sel_int                        : STD_LOGIC_VECTOR(1 DOWNTO 0) := "00";
       SIGNAL result_int                     : STD_LOGIC_VECTOR(3 DOWNTO 0) := "0000";
       SIGNAL dataout_int                    : STD_LOGIC                    := 'X';

       -- BEGIN-END SECTION: Contains concurrent statements and processes
BEGIN
       ----------------------------------------------------------------
       -- 1. CONCURRENT SIGNAL ASSIGNMENT (Data-flow style)
       -- Executes whenever signals on the right-hand side change
       -- This statement is outside any process, so it's concurrent
       ----------------------------------------------------------------
       -- Example: If a = "1010" and b = "1100"
       -- Result: "1000" (bitwise AND: 1&1=1, 0&1=0, 1&0=0, 0&0=0)
       -- 
       -- Bit-by-bit calculation:
       -- a:      1 0 1 0
       -- b:      1 1 0 0
       -- result: 1 0 0 0
       -- 
       -- This statement is evaluated automatically whenever a or b changes
       -- No process or sensitivity list is needed for concurrent statements
       result <= a AND b; -- Bitwise AND operation

       ----------------------------------------------------------------
       -- 2. CONDITIONAL SIGNAL ASSIGNMENT (Data-flow style)
       -- Similar to if-elsif-else structure but in concurrent form
       -- Evaluates conditions in order until one is true
       ----------------------------------------------------------------
       -- Example 1: If a_reg = "0000"
       -- Result: '1' (first condition is true, others not evaluated)
       -- 
       -- Example 2: If a_reg = "0001" and b_reg = "1111"
       -- Result: '0' (first condition false, second condition true)
       -- 
       -- Example 3: If a_reg = "1100" and b_reg = "0000"
       -- Result: 'U' (first and second conditions false, third true)
       -- 
       -- Example 4: If a_reg = "0101" and b_reg = "0101"
       -- Result: 'X' (all conditions false, default value assigned)
       -- 
       -- The conditions are evaluated in order (top to bottom)
       -- Once a true condition is found, its value is assigned
       result_int <=
              '1' WHEN (a_reg = "0000") ELSE -- First condition
              '0' WHEN (b_reg = "1111") ELSE -- Second condition
              'U' WHEN (a_reg = "1100") ELSE -- Third condition
              'X';                           -- Default value

       ----------------------------------------------------------------
       -- 3. SELECTED SIGNAL ASSIGNMENT (Data-flow style)
       -- Similar to case statement but in concurrent form
       -- Selection based on exact match of sel_int value
       ----------------------------------------------------------------
       -- Example 1: If sel_int = "00" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Result: dataout_int = '1' (d1_int is selected)
       -- 
       -- Example 2: If sel_int = "01" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Result: dataout_int = '0' (d2_int is selected)
       -- 
       -- Example 3: If sel_int = "10" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Result: dataout_int = '1' (d3_int is selected)
       -- 
       -- Example 4: If sel_int = "11" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Result: dataout_int = '0' (d4_int is selected)
       -- 
       -- Example 5: If sel_int = "ZZ" (invalid value)
       -- Result: dataout_int = 'X' (OTHERS case is selected)
       -- 
       -- This implements a 4-to-1 multiplexer in a concurrent form
       -- The selection is based on exact match of sel_int value
       WITH sel_int SELECT
              dataout_int <=
              d1_int WHEN "00", -- When sel_int is "00"
              d2_int WHEN "01", -- When sel_int is "01"
              d3_int WHEN "10", -- When sel_int is "10"
              d4_int WHEN "11", -- When sel_int is "11"
              'X' WHEN OTHERS;  -- Default for any other value

       ----------------------------------------------------------------
       -- 4. PROCESS WITH IF STATEMENT (Behavioral style)
       -- Process is a concurrent statement containing sequential statements
       -- The sensitivity list (signals in parentheses) determines when process executes
       ----------------------------------------------------------------
       -- Example 1: If sel_int = "00" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Process execution:
       --   1. Process triggered when any signal in sensitivity list changes
       --   2. First IF condition (sel_int = "00") is TRUE
       --   3. mux_out is assigned d1_int value ('1')
       --   4. Other conditions are not evaluated
       -- 
       -- Example 2: If sel_int = "01" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Process execution:
       --   1. First IF condition (sel_int = "00") is FALSE
       --   2. First ELSIF condition (sel_int = "01") is TRUE
       --   3. mux_out is assigned d2_int value ('0')
       --   4. Other conditions are not evaluated
       -- 
       -- Example 3: If sel_int = "XX" (invalid value)
       -- Process execution:
       --   1. All conditions are FALSE
       --   2. mux_out retains its previous value
       --   3. This can create a latch in hardware (generally undesirable)
       -- 
       -- Key differences from concurrent statements:
       -- 1. Sequential execution (top to bottom)
       -- 2. Only executes when signals in sensitivity list change
       -- 3. Variables are local and updated immediately with :=
       if_process : PROCESS (d1_int, d2_int, d3_int, d4_int, sel_int) IS
              -- Variables are local to the process and use := for assignment
              -- This variable demonstrates the concept but is not used in output
              -- (kept for educational purposes)
       BEGIN
              -- IF statement: Sequential statement for conditional execution
              IF sel_int = "00" THEN
                     -- First condition: sel_int equals "00"
                     -- Signal assignment could be done here instead of using variable
                     -- Example: dataout_int <= d1_int;
              ELSIF sel_int = "01" THEN
                     -- Second condition: sel_int equals "01"
              ELSIF sel_int = "10" THEN
                     -- Third condition: sel_int equals "10"
              ELSIF sel_int = "11" THEN
                     -- Fourth condition: sel_int equals "11"
              END IF;
              -- Note: Variable assignments use := while signal assignments use <=
       END PROCESS if_process;

       ----------------------------------------------------------------
       -- 5. PROCESS WITH CASE STATEMENT (Behavioral style)
       -- Case statement provides a cleaner way to implement multiplexers
       -- compared to multiple if-elsif statements
       ----------------------------------------------------------------
       -- Example 1: If sel_int = "00" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Process execution:
       --   1. Process triggered when any signal in sensitivity list changes
       --   2. CASE evaluates sel_int value ("00")
       --   3. Matching branch is executed (WHEN "00")
       --   4. Output signal could be assigned d1_int value ('1')
       -- 
       -- Example 2: If sel_int = "01" and d1_int = '1', d2_int = '0', d3_int = '1', d4_int = '0'
       -- Process execution:
       --   1. CASE evaluates sel_int value ("01")
       --   2. Matching branch is executed (WHEN "01")
       --   3. Output signal could be assigned d2_int value ('0')
       -- 
       -- Example 3: If sel_int = "UU" (invalid value)
       -- Process execution:
       --   1. No exact match for "UU"
       --   2. WHEN OTHERS branch is executed
       --   3. Output signal could be assigned 'X'
       -- 
       -- Key differences from IF-ELSIF:
       -- 1. All possible values must be covered (WHEN OTHERS is required for synthesis)
       -- 2. Only exact matches are evaluated (no relational operators like < or >)
       -- 3. More efficient hardware implementation for multiplexers
       -- 4. Prevents unintentional latches by covering all cases
       case_process : PROCESS (d1_int, d2_int, d3_int, d4_int, sel_int) IS
              -- This process demonstrates CASE statement structure
              -- In a real design, you would assign to an output signal
       BEGIN
              -- CASE statement: Evaluates expression and executes matching branch
              CASE sel_int IS
                     WHEN "00"   => 
                            -- When sel_int is "00"
                            -- Example: dataout_int <= d1_int;
                     WHEN "01"   => 
                            -- When sel_int is "01"
                            -- Example: dataout_int <= d2_int;
                     WHEN "10"   => 
                            -- When sel_int is "10"
                            -- Example: dataout_int <= d3_int;
                     WHEN "11"   => 
                            -- When sel_int is "11"
                            -- Example: dataout_int <= d4_int;
                     WHEN OTHERS => 
                            -- Default case (required for synthesis)
                            -- Example: dataout_int <= 'X';
              END CASE;
              -- The WHEN OTHERS clause is good practice to avoid latches
       END PROCESS case_process;

       ----------------------------------------------------------------
       -- 6. SYNCHRONOUS PROCESS (Behavioral style)
       -- Demonstrates proper clock and reset handling for registers
       ----------------------------------------------------------------
       -- Example 1: Reset condition
       -- If reset = '1' (regardless of clock)
       -- Process execution:
       --   1. First IF condition is TRUE
       --   2. All registers are cleared (a_reg and b_reg set to "0000")
       --   3. ELSIF part is not evaluated
       -- 
       -- Example 2: Clock edge with data
       -- If reset = '0', clk has rising edge, a = "1010", b = "0101"
       -- Process execution:
       --   1. First IF condition is FALSE
       --   2. ELSIF condition checks for rising clock edge
       --   3. On rising edge, a_reg is assigned value of a ("1010")
       --   4. On same edge, b_reg is assigned value of b ("0101")
       -- 
       -- Example 3: No clock edge
       -- If reset = '0', clk is stable or falling
       -- Process execution:
       --   1. First IF condition is FALSE
       --   2. ELSIF condition is FALSE (no rising edge)
       --   3. No assignments are made, registers keep previous values
       -- 
       -- Key concepts of synchronous design:
       -- 1. All registers update simultaneously on clock edge
       -- 2. Reset provides a known starting state
       -- 3. Between clock edges, register values remain stable
       -- 4. This creates predictable timing behavior essential for digital circuits
       sync_process : PROCESS (clk, reset)
       BEGIN
              IF (reset = '1') THEN
                     -- Synchronous reset - Clear all registers
                     -- The OTHERS keyword is a convenient way to set all bits
                     -- Example: "0000" for a 4-bit vector
                     a_reg <= (OTHERS => '0'); -- OTHERS keyword assigns all bits
                     b_reg <= (OTHERS => '0');
              ELSIF rising_edge(clk) THEN -- Function to detect rising clock edge
                     -- Register inputs on clock edge
                     -- This creates a delay of one clock cycle between input and register
                     -- Example: If a = "1010" at clock edge, a_reg becomes "1010" after the edge
                     a_reg <= a; -- Signal assignment within process
                     b_reg <= b;
              END IF;
       END PROCESS sync_process;

END ARCHITECTURE Behavioral;