{ config, lib, pkgs, ... }:

let
  calamaresConfig = self.packages.${config.nixpkgs.system}.setup-calamares-config;
in {
  options.alloy.calamares.enable = lib.mkEnableOption "Alloy Calamares configuration";

  config = lib.mkIf config.alloy.calamares.enable {
    environment.etc."calamares" = {
      source = "${calamaresConfig}/etc/calamares";
      mode = "0644";
    };
    environment.systemPackages = [ pkgs.calamares ];
    services.xserver.desktopManager.gnome.extraGSettingsOverrides = ''
      [org.gnome.shell]
      favorite-apps=['calamares.desktop']
    '';
  };
}