-- 03_process_sensitivity.vhd
-- Purpose: Demonstrate combinational vs clocked processes and proper sensitivity lists

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity proc_sens_demo is
  port (
    clk   : in  std_logic;
    a, b  : in  std_logic_vector(3 downto 0);
    sum_c : out std_logic_vector(3 downto 0);
    sum_s : out std_logic_vector(3 downto 0)
  );
end entity;

architecture rtl of proc_sens_demo is
  signal r_reg : std_logic_vector(3 downto 0) := (others => '0');
begin
  -- Combinational process: all inputs in sensitivity list
  comb: process(a, b)
    variable tmp : unsigned(3 downto 0);
  begin
    tmp := unsigned(a) + unsigned(b);
    sum_c <= std_logic_vector(tmp);
  end process;

  -- Clocked process: only clk in sensitivity list
  seq: process(clk)
  begin
    if rising_edge(clk) then
      r_reg <= a xor b; -- sequential logic
    end if;
  end process;

  sum_s <= r_reg; -- concurrent assignment
end architecture;
