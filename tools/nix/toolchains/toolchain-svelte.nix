# This function returns a attrset of `devenv` modules
# which can be passed to `mkShell`.
{
  self,
  lib,
  pkgs,
  pkgsPinned,
  ...
}:
{
  svelte = [
    {
      packages = [
        pkgsPinned.nodejs
        pkgsPinned.pnpm
      ];
    }
  ];
}
