{
  description = "A collection of metacompiling programs";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rpypkgs = {
      url = "github:rpypkgs/rpypkgs";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs = { self, nixpkgs, flake-utils, rpypkgs }:
    flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      zaddy = rpypkgs.lib.${system}.mkRPythonDerivation {
        entrypoint = "zzc.py";
        binName = "zzc";
        optLevel = "2";
      } {
        pname = "zaddy";
        version = "2025.4";
        src = ./rzaddy;
      };
    in {
      packages = {
        inherit zaddy;
        default = zaddy;
      };
      devShells.default = pkgs.mkShell {
        packages = [ ];
      };
    });
}
