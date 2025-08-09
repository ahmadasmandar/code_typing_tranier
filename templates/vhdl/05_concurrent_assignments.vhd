-- 05_concurrent_assignments.vhd
-- Purpose: Demonstrate concurrent vs conditional/selected signal assignments

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity concurrent_demo is
  port (
    sel  : in  std_logic;
    a, b : in  std_logic_vector(3 downto 0);
    y    : out std_logic_vector(3 downto 0);
    z    : out std_logic_vector(3 downto 0)
  );
end entity;

architecture rtl of concurrent_demo is
begin
  -- Simple concurrent assignment
  z <= a xor b; -- XOR operator

  -- Conditional signal assignment (when-else)
  y <= a when sel = '1' else b;
end architecture;
