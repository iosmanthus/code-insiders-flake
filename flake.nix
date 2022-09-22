{
  description = "Nix Flake for Code Insider";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      meta = builtins.fromJSON (builtins.readFile ./meta.json);
      package = (pkgs.vscode.override {
        isInsiders = true;
      }).overrideAttrs (oldAttrs: rec {
        pname = "vscode-insiders";
        src = (builtins.fetchurl {
          url = meta.url;
          sha256 = meta.sha256;
        });
        version = meta.version;
      });
    in
    {
      overlays.default = final: prev: {
        vscode-insiders = package;
      };
      packages.${system}.vscode-insider = package;
      legacyPackages.${system}.vscode-insider = package;
    };
}
