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

          ({ pkgs, lib, ... }: {
            services.displayManager.autoLogin = lib.mkForce {
              enable = true;
              user = "alloy";
            };

            # testing.
            boot.readOnlyNixStore = false;
            boot.loader.grub.useOSProber = true;

            environment.systemPackages = [
              pkgs.calamares
              pkgs.calamares-nixos-extensions
              self.packages.${system}.setup-calamares-config
            ];

            system.activationScripts.calamares-config = ''
              mkdir -p /etc/calamares
              cp -rf ${self.packages.${system}.setup-calamares-config}/etc/calamares/* /etc/calamares/
              chmod -R +w /etc/calamares
            '';

            systemd.services.calamares-autorun = {
              wantedBy = [ "graphical.target" ];
              after = [ "display-manager.service" ];
              serviceConfig = {
                ExecStart = "${pkgs.calamares}/bin/calamares -d";
                User = "alloy";
                Type = "simple";
                Environment = "DISPLAY=:0";
              };
            };

            environment.etc."xdg/autostart/calamares.desktop".source = let
              desktopFile = pkgs.writeText "calamares.desktop" ''
                [Desktop Entry]
                Type=Application
                Name=Calamares Installer
                Exec=${pkgs.calamares}/bin/calamares -d
                Terminal=false
                X-GNOME-Autostart-enabled=true
                X-GNOME-Autostart-Delay=5
              '';
            in desktopFile;

            users.users.alloy = {
              isNormalUser = true;
              extraGroups = [ "wheel" "networkmanager" "video" ];
            };


            security.sudo.wheelNeedsPassword = false;
            networking.networkmanager.enable = true;
          })
        ];
      };
    };
} # nix build .#nixosConfigurations.custom-iso.config.system.build.isoImage
