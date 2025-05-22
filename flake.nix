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
      bootstrap = rpypkgs.lib.${system}.mkRPythonDerivation {
        entrypoint = "zaddy.py";
        binName = "zaddyc";
        optLevel = "2";
      } {
        pname = "zaddy";
        version = "2025.4";
        src = ./rzaddy;
      };
      mk = desc: binName: let
        src = pkgs.stdenv.mkDerivation {
          name = "${binName}-src";
          src = ./.;
          installPhase = ''
            mkdir $out/
            ${bootstrap}/bin/zaddyc < ${desc} > $out/src.py
          '';
        };
      in rpypkgs.lib.${system}.mkRPythonDerivation {
        entrypoint = "src.py";
        inherit binName;
        optLevel = "2";
      } {
        pname = "zaddy";
        version = "2025.4";
        inherit src;
      };
    in {
      packages = rec {
        default = zaddyc;
        zaddyc = mk "zaddy.zaddy" "zaddyc";
        jsonc = mk "json.zaddy" "jsonc";
        sexpc = mk "sexp.zaddy" "sexpc";
        bfc = mk "bf.zaddy" "bfc";
      };
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          gdb
        ];
      };
    });
}
