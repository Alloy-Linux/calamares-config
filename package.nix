{ pkgs ? import <nixpkgs> {} }:

with pkgs; 

stdenv.mkDerivation {
  pname = "setup-calamares-config";
  version = "0.1";

  src = ./calamares;

  installPhase = ''
    mkdir -p $out/etc/calamares
    cp -r branding config modules $out/etc/calamares/
  '';

  meta = with lib; {
    description = "Calamares config, branding, and modules for Alloy Linux";
    homepage = "https://github.com/Alloy-Linux";
    license = licenses.gpl3;
    maintainers = [ maintainers.miyu ];
    platforms = platforms.linux;
  };
}