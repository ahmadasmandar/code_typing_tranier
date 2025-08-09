-- 04_if_case_when.vhd
-- Purpose: Examples of if-elsif-else, case-when, and with-select/when-else

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity control_examples is
  port (
    sel  : in  std_logic_vector(1 downto 0);
    a, b : in  std_logic_vector(7 downto 0);
    y1   : out std_logic_vector(7 downto 0);
    y2   : out std_logic_vector(7 downto 0);
    y3   : out std_logic_vector(7 downto 0)
  );
end entity;

architecture rtl of control_examples is
begin
  -- if / elsif / else
  process(sel, a, b)
  begin
    if sel = "00" then
      y1 <= a;
    elsif sel = "01" then
      y1 <= b;
    else
      y1 <= (others => '0');
    end if;
  end process;

  -- case / when
  process(sel, a, b)
  begin
    case sel is
      when "00" => y2 <= a and b; -- logical operator AND
      when "01" => y2 <= a or  b; -- logical operator OR
      when "10" => y2 <= a xor b; -- logical operator XOR
      when others => y2 <= (others => '0');
    end case;
  end process;

  -- with-select (selected signal assignment)
  with sel select
    y3 <= a + b when "00",  -- arithmetic operator + (unsigned interpretation depends on context)
          a - b when "01",
          a    when others;
end architecture;
