-- 02_signals_variables_casting.vhd
-- Purpose: Show difference between signals and variables inside processes and numeric_std casting
-- Notes:
-- - Variables update immediately within a process; signals schedule an event after the process
-- - Use signed/unsigned for arithmetic; cast with to_unsigned/to_signed and std_logic_vector(...)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity sig_var_demo is
  port (
    clk  : in  std_logic;
    a    : in  std_logic_vector(7 downto 0);
    b    : in  std_logic_vector(7 downto 0);
    y    : out std_logic_vector(7 downto 0)
  );
end entity;

architecture rtl of sig_var_demo is
  signal s_acc : unsigned(7 downto 0) := (others => '0');
begin
  process(clk)
    variable v_tmp : unsigned(7 downto 0);
  begin
    if rising_edge(clk) then
      -- Cast inputs to unsigned for arithmetic
      v_tmp := unsigned(a) + unsigned(b);
      -- variable visible immediately here
      if v_tmp > 100 then
        s_acc <= v_tmp - 10; -- signal scheduled update
      else
        s_acc <= v_tmp + 10;
      end if;
    end if;
  end process;

  y <= std_logic_vector(s_acc);
end architecture;
