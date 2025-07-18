#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   SPDX-FileCopyrightText: 2022 Victor Fuentes <vmfuentes64@gmail.com>
#   SPDX-FileCopyrightText: 2019 Adriaan de Groot <groot@kde.org>
#   SPDX-License-Identifier: GPL-3.0-or-later
#
#   Calamares is Free Software: see the License-Identifier above.
#

import configparser
import libcalamares
import os
import subprocess
import re

import gettext

_ = gettext.translation(
    "calamares-python",
    localedir=libcalcalamares.utils.gettext_path(),
    languages=libcalamares.utils.gettext_languages(),
    fallback=True,
).gettext


cfghead = """# This file is generated by Calamares.
# Do not edit this file directly.
# Your changes will be overwritten.

{ config, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
    # Calamares-generated modules will be imported here
  ];

"""


def env_is_set(name):
    envValue = os.environ.get(name)
    return not (envValue is None or envValue == "")

def generateProxyStrings():
    proxyEnv = []
    if env_is_set('http_proxy'):
        proxyEnv.append('http_proxy={}'.format(os.environ.get('http_proxy')))
    if env_is_set('https_proxy'):
        proxyEnv.append('https_proxy={}'.format(os.environ.get('https_proxy')))
    if env_is_set('HTTP_PROXY'):
        proxyEnv.append('HTTP_PROXY={}'.format(os.environ.get('HTTP_PROXY')))
    if env_is_set('HTTPS_PROXY'):
        proxyEnv.append('HTTPS_PROXY={}'.format(os.environ.get('HTTPS_PROXY')))

    if len(proxyEnv) > 0:
        proxyEnv.insert(0, "env")

    return proxyEnv

def pretty_name():
    return _("Installing NixOS.")


status = pretty_name()


def pretty_status_message():
    return status


def copy_nixos_modules(root_mount_point):
    libcalamares.utils.debug("Copying NixOS modules to target system.")
    source_path = "/home/simon/Downloads/calamares-nixos-extensions/nix-source-files"
    destination_path = os.path.join(root_mount_point, "etc/nixos/calamares-modules")
    try:
        libcalamares.utils.host_env_process_output(
            ["mkdir", "-p", destination_path], None
        )
        libcalamares.utils.host_env_process_output(
            ["cp", "-r", source_path, destination_path], None
        )
        libcalamares.utils.debug(f"Successfully copied modules from {source_path} to {destination_path}")
    except subprocess.CalledProcessError as e:
        libcalamares.utils.error(f"Failed to copy NixOS modules: {e.output.decode('utf-8')}")
        raise


def run():
    """NixOS Configuration."""

    global status
    status = _("Configuring NixOS")
    libcalamares.job.setprogress(0.1)

    ngc_cfg = configparser.ConfigParser()
    ngc_cfg["Defaults"] = { "Kernel": "lts" }
    ngc_cfg.read("/etc/nixos-generate-config.conf")

    module_imports = []

    nixos_config_content = cfghead.replace("# Calamares-generated modules will be imported here",
                          "\n".join([f"    ./calamares-modules/{m}" for m in module_imports]))
    gs = libcalamares.globalstorage
    variables = dict()

    root_mount_point = gs.value("rootMountPoint")
    config = os.path.join(root_mount_point, "etc/nixos/configuration.nix")

    copy_nixos_modules(root_mount_point)
    fw_type = gs.value("firmwareType")
    bootdev = (
        "nodev"
        if gs.value("bootLoader") is None
        else gs.value("bootLoader")["installPath"]
    )

    for part in gs.value("partitions"):
        if (
            part["claimed"] is True
            and (part["fsName"] == "luks" or part["fsName"] == "luks2")
            and part["device"] is not None
            and part["fs"] == "linuxswap"
        ):
            nixos_config_content += """  boot.initrd.luks.devices."{}".device = "/dev/disk/by-uuid/{}";
""".format(
                part["luksMapperName"], part["uuid"]
            )

    root_is_encrypted = False
    boot_is_encrypted = False
    boot_is_partition = False

    for part in gs.value("partitions"):
        if part["mountPoint"] == "/":
            root_is_encrypted = part["fsName"] in ["luks", "luks2"]
        elif part["mountPoint"] == "/boot":
            boot_is_partition = True
            boot_is_encrypted = part["fsName"] in ["luks", "luks2"]


    status = _("Configuring NixOS")
    libcalamares.job.setprogress(0.18)


    if gs.value("hostname") is None:
        variables["hostname"] = "nixos"
    else:
        variables["hostname"] = gs.value("hostname")

    desktop_env = gs.value("packagechooser_packagechooser")
    if desktop_env == "gnome":
        module_imports.append("modules/desktop/gnome.nix")
    elif desktop_env == "plasma6":
        module_imports.append("modules/desktop/plasma.nix")
    elif desktop_env == "cinnamon":
        module_imports.append("modules/desktop/cinnamon.nix")
        # add more desktop environments later

    version = ". ".join(subprocess.getoutput(["nixos-version"]).split(".")[:2])[:5]
    variables["nixosversion"] = version

    nixos_config_content = nixos_config_content.replace("@@hostname@@", variables.get("hostname", "nixos"))
    nixos_config_content = nixos_config_content.replace("@@timezone@@", variables.get("timezone", "UTC"))
    nixos_config_content = nixos_config_content.replace("@@LANG@@", variables.get("LANG", "en_US.UTF-8"))
    nixos_config_content = nixos_config_content.replace("@@kblayout@@", variables.get("kblayout", "us"))
    nixos_config_content = nixos_config_content.replace("@@kbvariant@@", variables.get("kbvariant", ""))
    nixos_config_content = nixos_config_content.replace("@@vconsole@@", variables.get("vconsole", "us"))
    nixos_config_content = nixos_config_content.replace("@@username@@", variables.get("username", "user"))
    nixos_config_content = nixos_config_content.replace("@@fullname@@", variables.get("fullname", "User"))
    nixos_config_content = nixos_config_content.replace("@@groups@@", variables.get("groups", "wheel"))
    nixos_config_content = nixos_config_content.replace("@@pkgs@@", variables.get("pkgs", ""))
    nixos_config_content = nixos_config_content.replace("@@nixosversion@@", variables.get("nixosversion", "23.11"))

    status = _("Generating NixOS configuration")
    libcalamares.job.setprogress(0.25)

    libcalamares.utils.host_env_process_output(["cp", "/dev/stdin", config], None, nixos_config_content)

    status = _("Installing NixOS")
    libcalamares.job.setprogress(0.3)

    nixosInstallCmd = [ "pkexec" ]
    nixosInstallCmd.extend(generateProxyStrings())
    nixosInstallCmd.extend(
        [
            "nixos-install",
            "--no-root-passwd",
            "--root",
            root_mount_point
        ]
    )

    try:
        output = ""
        proc = subprocess.Popen(
            nixosInstallCmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        while True:
            line = proc.stdout.readline().decode("utf-8")
            output += line
            libcalamares.utils.debug("nixos-install: {}".format(line.strip()))
            if not line:
                break
        exit = proc.wait()
        if exit != 0:
            return (_("nixos-install failed"), _(output))
    except:
        return (_("nixos-install failed"), _("Installation failed to complete"))

    return None
