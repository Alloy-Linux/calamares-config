{ pkgs ? import <nixpkgs> {} }:


with pkgs; 

stdenv.mkDerivation {
  pname = "setup-calamares-config";
  version = "0.1";

  src = fetchFromGitHub {
    owner = "Alloy-Linux";
    repo = "calamares-config";
    rev = "00128800c5038a89797fbe358e771f30e7d15243"; 
    hash = "sha256-c7N405riX3ujT4PnLW8N70BNHINaNKBblwSQ+vUucHw="; 
  };

  dontBuild = true;
  dontConfigure = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/etc/calamares

    cp -r $src/* $out/etc/calamares/
    runHook postInstall
  '';

  meta = with lib; {
    description = "Unpack calamares config to etc";
    homepage = "https://github.com/Alloy-Linux";
    license = licenses.gpl3;
    maintainers = [ maintainers.miyu ];
    platforms = platforms.linux;
  };
}