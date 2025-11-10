## SSH Operations Playbook

This guide covers the canonical workflow for enabling non-interactive SSH access to `andy-wsl` so automation (for example `make restart`) runs without prompts.

### Prerequisites

- DNS or `/etc/hosts` entry for `andy-wsl` → current WSL IP (`100.67.88.114` as of 2025-11-10).
- Remote user `andy` on Ubuntu/WSL with `systemd` enabled via `/etc/wsl.conf`.
- Local SSH key at `~/.ssh/id_ed25519` (generated automatically by the client setup script if missing).

### Setup Steps

1. **Configure the client**

   ```bash
   bash scripts/setup_ssh_client.sh
   ```

   - Ensures `~/.ssh` permissions are correct.
   - Generates an `ed25519` key when absent.
   - Pins the remote host fingerprint with `ssh-keyscan`.
   - Adds a `Host andy-wsl` stanza to `~/.ssh/config` that enforces public-key auth (`BatchMode yes`).

2. **Prepare the remote server**

   ```bash
   # optional: export WSL_PASS=... to avoid interactive password prompts
   bash scripts/setup_ssh_server.sh
   ```

   Remote actions:

   - Installs and enables `openssh-server`.
   - Starts `sshd` at boot (`systemctl enable --now ssh`).
   - Allows port 22 through `ufw` if available.
   - Forces `PubkeyAuthentication yes` and keeps password auth enabled for bootstrapping.
   - Copies the local public key with `ssh-copy-id`; supports `WSL_PASS` + `sshpass`.

3. **(Optional) Enable Tailscale SSH**

   ```bash
   ssh andy@andy-wsl 'bash -s' < scripts/setup_tailscale_ssh.sh
   ```

   Useful for zero-trust fallback. Requires tailnet ACLs permitting SSH.

4. **Verify the path**

   ```bash
   bash scripts/verify_ssh.sh
   ```

   Produces resolution, ping, port, and `ssh -o BatchMode=yes` checks. Should print `ok`, hostname, and username without prompting.

5. **Run automation**

   ```bash
   make restart
   ```

   Uses the configured host alias. No passwords should be required.

### Troubleshooting

- **`Connection refused`**  
  Run `ssh andy@andy-wsl 'sudo systemctl status ssh'`. If inactive, rerun `scripts/setup_ssh_server.sh`.

- **`Permission denied (publickey)`**  
  Ensure `~/.ssh/id_ed25519.pub` exists on the remote under `~/.ssh/authorized_keys` and permissions are `600` (file) / `700` (directory).

- **Host key mismatch**  
  The scripts rely on fingerprints in `~/.ssh/known_hosts`. If the remote host was reprovisioned, remove the old entry:  
  `ssh-keygen -R andy-wsl`.

- **WSL restarts lose services**  
  Confirm `/etc/wsl.conf` contains:

  ```
  [boot]
  systemd=true
  ```

  Then run `wsl.exe --shutdown` from Windows before re-entering WSL.

- **Firewall blocks**  
  Verify Windows Firewall allows inbound port 22 from the Tailscale subnet if connecting from outside the host.

### Reference Commands

- `scripts/setup_ssh_client.sh` – client bootstrap.
- `scripts/setup_ssh_server.sh` – remote bootstrap.
- `scripts/setup_tailscale_ssh.sh` – enable Tailscale SSH.
- `scripts/verify_ssh.sh` – diagnostic checks.

Keep these scripts idempotent by re-running them whenever credentials rotate or the WSL IP changes.

### WSL + SSH Hardening Quicksteps

1. **Remote hardening (WSL Ubuntu)**
   - Write `/etc/ssh/sshd_config.d/99_hardening.conf` with:

     ```
     PubkeyAuthentication yes
     PasswordAuthentication no
     PermitRootLogin no
     MaxAuthTries 3
     KexAlgorithms curve25519-sha256@libssh.org
     Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
     ```

   - Enable SSH on boot: `sudo systemctl enable --now ssh`.
   - Firewall: `sudo ufw allow OpenSSH`, then `sudo ufw --force enable`.
   - Tailscale fallback: `sudo tailscale up --ssh --hostname=andy-wsl`; fetch the IP with `tailscale ip -4 | head -n1`.

2. **Local workstation**
   - Ensure `~/.ssh/config` contains:

     ```
     Host andy-wsl
       HostName 100.x.x.x
       User andy
       IdentitiesOnly yes
       ServerAliveInterval 30
       ServerAliveCountMax 3
       StrictHostKeyChecking accept-new
     ```

   - Update the `HostName` field whenever the Tailscale IP changes.

