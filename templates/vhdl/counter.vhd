library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter is
    Port ( clk   : in  STD_LOGIC;
           reset : in  STD_LOGIC;
           q     : out UNSIGNED(7 downto 0));
end counter;

architecture Behavioral of counter is
    signal cnt : UNSIGNED(7 downto 0) := (others => '0');
begin
    process(clk, reset)
    begin
        if reset = '1' then
            cnt <= (others => '0');
        elsif rising_edge(clk) then
            cnt <= cnt + 1;
        end if;
    end process;
    q <= cnt;
end Behavioral;
