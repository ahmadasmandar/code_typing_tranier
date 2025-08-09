-- 01_entity_arch_basics.vhd
-- Purpose: Minimal synthesizable VHDL design showing ENTITY/ARCHITECTURE, ports, clocked process
-- Notes:
-- - Uses IEEE libraries std_logic_1164 and numeric_std (recommended for arithmetic)
-- - Demonstrates a simple register with synchronous reset

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity reg_example is
  port(
    clk   : in  std_logic;              -- system clock
    rst   : in  std_logic;              -- synchronous active-high reset
    d_in  : in  std_logic_vector(7 downto 0); -- input data
    q_out : out std_logic_vector(7 downto 0)  -- registered output
  );
end entity;

architecture rtl of reg_example is
  signal q_reg : std_logic_vector(7 downto 0) := (others => '0');
begin
  q_out <= q_reg; -- concurrent assignment

  -- Clocked process: synchronous reset and register update
  process(clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        q_reg <= (others => '0');
      else
        q_reg <= d_in; -- register input
      end if;
    end if;
  end process;
end architecture;
