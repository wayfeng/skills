#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  printf 'Usage: %s user@host\n' "$0" >&2
  exit 2
fi

remote_host="$1"
key="$HOME/.ssh/id_ed25519"
ssh_config="$HOME/.ssh/config"

remote_user=""
host_name="$remote_host"
if [[ "$remote_host" == *@* ]]; then
  remote_user="${remote_host%@*}"
  host_name="${remote_host#*@}"
fi

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$key" ]; then
  ssh-keygen -t ed25519 -f "$key" -N "" -C "$(whoami)@$(hostname)"
fi

if [ ! -f "$key.pub" ]; then
  ssh-keygen -y -f "$key" > "$key.pub"
fi

touch "$ssh_config"
chmod 600 "$ssh_config"

host_exists=0
while IFS= read -r keyword value _; do
  if [ "$keyword" = "Host" ] && [ "$value" = "$host_name" ]; then
    host_exists=1
    break
  fi
done < "$ssh_config"

if [ "$host_exists" -eq 0 ]; then
  {
    printf '\nHost %s\n' "$host_name"
    printf '  HostName %s\n' "$host_name"
    if [ -n "$remote_user" ]; then
      printf '  User %s\n' "$remote_user"
    fi
    printf '  IdentityFile %s\n' "$key"
  } >> "$ssh_config"
fi

ssh-copy-id -i "$key.pub" "$remote_host"
ssh -o BatchMode=yes "$remote_host" true
