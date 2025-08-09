-- 10_utils_pkg.vhd
-- Purpose: Utility package with helpful functions and types
-- Includes: ceil_log2, saturating add, parity

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package utils_pkg is
  function ceil_log2(n : natural) return natural;
  function sat_add(a, b : unsigned) return unsigned; -- saturate on overflow
  function parity(x : std_logic_vector) return std_logic; -- even parity
end package;

package body utils_pkg is
  function ceil_log2(n : natural) return natural is
    variable v : natural := 0;
    variable p : natural := 1;
  begin
    while p < n loop
      p := p * 2;
      v := v + 1;
    end loop;
    return v;
  end function;

  function sat_add(a, b : unsigned) return unsigned is
    variable res : unsigned(a'range);
    variable ext : unsigned(a'length downto 0);
  begin
    ext := ('0' & a) + ('0' & b);
    if ext(ext'high) = '1' then
      res := (others => '1');
    else
      res := ext(res'range);
    end if;
    return res;
  end function;

  function parity(x : std_logic_vector) return std_logic is
    variable p : std_logic := '0';
  begin
    for i in x'range loop
      p := p xor x(i);
    end loop;
    return p; -- '1' if odd number of '1's
  end function;
end package body;
