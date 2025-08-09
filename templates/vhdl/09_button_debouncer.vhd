-- 09_button_debouncer.vhd
-- Purpose: Synchronizer + debounce filter for a push button
-- Notes: Two flip-flop synchronizer, then counter-based stable detection

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity button_debouncer is
  generic (
    CNT_MAX : natural := 50000 -- adjust to clock speed and desired debounce time
  );
  port (
    clk   : in  std_logic;
    rst   : in  std_logic;
    btn_i : in  std_logic; -- asynchronous button input
    btn_o : out std_logic  -- debounced, synchronized output
  );
end entity;

architecture rtl of button_debouncer is
  signal s1, s2 : std_logic := '0';
  signal cnt    : unsigned(31 downto 0) := (others => '0');
  signal stable : std_logic := '0';
begin
  -- 2FF synchronizer
  process(clk)
  begin
    if rising_edge(clk) then
      s1 <= btn_i;
      s2 <= s1;
    end if;
  end process;

  -- Debounce counter
  process(clk)
  begin
    if rising_edge(clk) then
      if rst='1' then
        cnt <= (others => '0');
        stable <= '0';
      else
        if s2 = stable then
          cnt <= (others => '0');
        else
          if cnt = to_unsigned(CNT_MAX, cnt'length) then
            stable <= s2;
            cnt <= (others => '0');
          else
            cnt <= cnt + 1;
          end if;
        end if;
      end if;
    end if;
  end process;

  btn_o <= stable;
end architecture;
