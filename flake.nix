{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05"; 

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.setup-calamares-config = pkgs.callPackage ./package.nix {};

      nixosConfigurations.custom-iso = nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          "${nixpkgs}/nixos/modules/installer/cd-dvd/installation-cd-graphical-gnome.nix"

          ({ pkgs, ... }: {
            environment.systemPackages = [
              pkgs.calamares 
              self.packages.${system}.setup-calamares-config
            ];

            users.users.nixos = {
              isNormalUser = true;
              extraGroups = [ "wheel" "networkmanager" ];
            };
          }) 
        ];
      };
    };
} # nix build .#nixosConfigurations.custom-iso.config.system.build.isoImage