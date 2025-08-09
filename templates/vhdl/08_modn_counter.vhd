-- 08_modn_counter.vhd
-- Purpose: Parameterizable mod-N counter with enable and synchronous reset

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity modn_counter is
  generic (
    N : natural := 10 -- modulus
  );
  port (
    clk : in  std_logic;
    rst : in  std_logic; -- synchronous active-high
    en  : in  std_logic;
    q   : out unsigned(31 downto 0)
  );
end entity;

architecture rtl of modn_counter is
  signal cnt : unsigned(31 downto 0) := (others => '0');
begin
  process(clk)
  begin
    if rising_edge(clk) then
      if rst='1' then
        cnt <= (others => '0');
      elsif en='1' then
        if to_integer(cnt) = N-1 then
          cnt <= (others => '0');
        else
          cnt <= cnt + 1;
        end if;
      end if;
    end if;
  end process;
  q <= cnt;
end architecture;
