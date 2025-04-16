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
      tmgl = pkgs.stdenv.mkDerivation {
        name = "tmg";
        version = "2022";
        src = pkgs.fetchFromGitHub {
          owner = "amakukha";
          repo = "tmg";
          rev = "bb8c6c3d2c8178416c0ff8d4b2f51e25f624d925";
          hash = "sha256-0NrE/RnbkLkxpoBz90hvs75rsn+n8fcPQmuAt7Udc4w=";
        };
        buildPhase = ''
          pushd src/
          bash build.sh
          popd
        '';
        installPhase = ''
          mkdir -p $out/bin/
          cp src/tmgl1 src/tmgl2 $out/bin/
        '';
      };
      tmg = pkgs.writeShellScriptBin "tmg" ''
        if [[ $# -ne 2 ]] then
          echo "Usage: $0 <input.t> <output>"
          exit 1
        fi
        d=$(mktemp -d)
        cp ${tmgl.src}/src/*.[ch] $d
        chmod +w $d/tmgl.h
        ${tmgl}/bin/tmgl1 $1 > $d/table.tmp
        ${tmgl}/bin/tmgl2 $d/table.tmp > $d/tmgl.h
        ${pkgs.stdenv.cc}/bin/cc -std=c99 -falign-functions=16 -O1 $d/tmga.c -o $2
      '';
      meta2 = rpypkgs.lib.${system}.mkRPythonDerivation {
        entrypoint = "rmeta2.py";
        binName = "rmeta2";
        optLevel = "2";
      } {
        pname = "rmeta2";
        version = "2025.4";
        src = ./rmeta2;
      };
    in {
      packages = {
        inherit tmg meta2;
      };
      devShells.default = pkgs.mkShell {
        packages = [ tmg meta2 ];
      };
    });
}
