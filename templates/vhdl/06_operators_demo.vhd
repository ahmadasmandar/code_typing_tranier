-- 06_operators_demo.vhd
-- Purpose: Showcase VHDL operators: logical, relational, shift, arithmetic (with numeric_std)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity operators_demo is
  port (
    a, b   : in  std_logic_vector(7 downto 0);
    y_and  : out std_logic_vector(7 downto 0);
    y_cmp  : out std_logic;  -- a > b
    y_sll  : out std_logic_vector(7 downto 0);
    y_add  : out std_logic_vector(7 downto 0)
  );
end entity;

architecture rtl of operators_demo is
begin
  -- logical AND
  y_and <= a and b;

  -- relational comparison (convert to unsigned)
  y_cmp <= '1' when unsigned(a) > unsigned(b) else '0';

  -- shift left logical
  y_sll <= std_logic_vector(shift_left(unsigned(a), 1));

  -- arithmetic addition
  y_add <= std_logic_vector(unsigned(a) + unsigned(b));
end architecture;
