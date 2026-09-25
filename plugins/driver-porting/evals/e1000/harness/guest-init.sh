#!/bin/busybox sh
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
#
# /init for both harness guests. The kernel console is ttyS0; ttyS1 is a command channel
# to the host driver (l02harness.py). The guest reads one command per line, "<seq> <shell
# command>", runs it, and answers with
#
#   L02 BEGIN <seq>
#   <combined stdout and stderr>
#   L02 END <seq> <exit status>
#
# The peer configures its virtio-net link at boot; the DUT loads nothing until told to, so
# the host decides which e1000 driver binds.

/bin/busybox mkdir -p /proc /sys /dev /tmp /bin /sbin /usr/bin /usr/sbin
/bin/busybox --install -s /bin
export PATH=/bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t debugfs debugfs /sys/kernel/debug 2>/dev/null
mount -t tmpfs tmpfs /tmp

role=unknown
for arg in $(cat /proc/cmdline); do
  case "$arg" in
    l02.role=*) role="${arg#l02.role=}" ;;
  esac
done

ip link set lo up
if [ "$role" = peer ]; then
  ip link set eth0 up
  ip addr add 192.0.2.2/24 dev eth0
fi

stty -F /dev/ttyS1 raw -echo 115200
exec 3<>/dev/ttyS1
# QEMU drops serial output while no host is connected to the socket, so a background loop
# repeats READY every second until the first command shows the host is listening. The
# foreground read never times out: busybox `read -t` discards a partly read line when the
# timeout fires, which loses commands.
( while :; do echo "L02 READY $role" >&3; sleep 1; done ) &
announcer=$!
while read -r line <&3; do
  if [ -n "$announcer" ]; then
    kill "$announcer"
    wait "$announcer" 2>/dev/null
    announcer=
  fi
  seq="${line%% *}"
  cmd="${line#* }"
  sh -c "$cmd" </dev/null >/tmp/l02-out 2>&1
  rc=$?
  echo "L02 BEGIN $seq" >&3
  cat /tmp/l02-out >&3
  echo "L02 END $seq $rc" >&3
done
echo "L02 CHANNEL CLOSED" >/dev/console
poweroff -f
