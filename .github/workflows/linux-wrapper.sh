#!/bin/bash
# Verilog Quiz System - VM-compatible launcher
# Auto-detects VM environment and forces software rendering when needed

IS_VM=false

# Detect VM via CPU flags
if [ -f /proc/cpuinfo ] && grep -qiE "hypervisor|qemu|kvm|vmware" /proc/cpuinfo 2>/dev/null; then
  IS_VM=true
fi

# Detect VM via DMI
if [ -f /sys/class/dmi/id/product_name ] && grep -qiE "virtualbox|vmware|kvm|qemu|bochs" /sys/class/dmi/id/product_name 2>/dev/null; then
  IS_VM=true
fi

# Detect VM via systemd-detect-virt
if command -v systemd-detect-virt >/dev/null 2>&1; then
  VIRT=$(systemd-detect-virt 2>/dev/null)
  if [ -n "$VIRT" ] && [ "$VIRT" != "none" ]; then
    IS_VM=true
  fi
fi

# Force software rendering in VM or when no GPU available
if [ "$IS_VM" = "true" ] || [ ! -d /dev/dri ]; then
  export LIBGL_ALWAYS_SOFTWARE=1
  export GALLIUM_DRIVER=llvmpipe
  export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe
  export MESA_GLTHREAD=false
  export GDK_BACKEND=x11
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/$(basename "$0").bin" "$@"
