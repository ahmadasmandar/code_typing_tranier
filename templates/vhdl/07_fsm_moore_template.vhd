-- 07_fsm_moore_template.vhd
-- Purpose: Moore FSM skeleton (separate next-state logic and state register)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

type state_t is (S0, S1, S2);

entity moore_fsm is
  port (
    clk, rst : in  std_logic;
    i        : in  std_logic;
    o        : out std_logic
  );
end entity;

architecture rtl of moore_fsm is
  signal st, st_n : state_t := S0;
begin
  -- state register
  process(clk)
  begin
    if rising_edge(clk) then
      if rst='1' then st <= S0; else st <= st_n; end if;
    end if;
  end process;

  -- next-state logic
  process(st, i)
  begin
    st_n <= st; -- default
    case st is
      when S0 => if i='1' then st_n <= S1; end if;
      when S1 => if i='1' then st_n <= S2; else st_n <= S0; end if;
      when S2 => if i='0' then st_n <= S0; end if;
    end case;
  end process;

  -- Moore output depends on current state only
  o <= '1' when st = S2 else '0';
end architecture;
