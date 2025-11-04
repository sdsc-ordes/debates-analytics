# This function returns a attrset of `devenv` modules
# which can be passed to `mkShell`.
{
  self,
  lib,
  pkgs,
  ...
}:
{
  svelte = [
    {
      # TODO: Copy everything from `dac-portal` toolchain.nix "frontend"
      packages = [ ];
    }
  ];
}
