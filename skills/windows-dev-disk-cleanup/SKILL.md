---
name: windows-dev-disk-cleanup
description: Safely inspect and clean disk space on a Windows development machine with Go caches, Docker Desktop, WSL VHDX files, Temp directories, and project build artifacts, while avoiding accidental removal of project-owned middleware containers or data.
---

<Purpose>
Use this skill when the user wants to free disk space on a Windows dev machine, especially one that uses Go, Docker Desktop, WSL, and large local project folders such as `Documents\src`.
</Purpose>

<Use_When>
- The user says disk space is shrinking or asks to "clean up", "free space", or "release disk space"
- Go build cache, module cache, Temp, Docker, WSL, or project build artifacts are plausible contributors
- The user wants practical cleanup, not just diagnosis
</Use_When>

<Do_Not_Use_When>
- The user only wants a storage report with no cleanup
- The machine is production-like and Docker/container state must not be touched without explicit approval
- The task is about cleaning source code rather than disk usage
</Do_Not_Use_When>

<Workflow>
1. Record a baseline:
   - `Get-PSDrive -Name C`
   - `docker system df` if Docker exists
   - `docker buildx du` if Docker Desktop / BuildKit is in use
   - large `*.vhdx` files under `C:\Users\<user>\AppData\Local`
   - capture `CreationTime` / `LastWriteTime` for `docker_data.vhdx` and any large WSL distro `ext4.vhdx`
   - if the user has repeated "C drive suddenly dropped by tens or hundreds of GB" incidents, generate a one-click PowerShell probe that records the commands above plus the top recently changed large files
2. Identify the big buckets before deleting anything:
   - project roots such as `C:\Users\<user>\Documents\src`
   - `C:\Users\<user>\AppData\Local\go-build`
   - `C:\Users\<user>\go\pkg\mod`
   - `C:\Users\<user>\AppData\Local\Temp`
   - `C:\Users\<user>\AppData\Local\Docker`
   - `C:\Users\<user>\AppData\Local\Packages`
   - BuildKit cache and recently created image layers inside Docker Desktop
3. Separate safe targets from stateful runtime data:
   - usually safe: Go cache, Temp, build outputs, `.tmp`, `target`, `build`, generated `.exe`, logs
   - caution: stopped Docker containers, Docker networks, Docker volumes, WSL distro disks, project-specific middleware stacks
4. Before any Docker cleanup, inspect the active project folders for Docker ownership:
   - search for `docker-compose*.yml`, `compose*.yml`, deploy scripts, and `scripts/*.md`
   - compare those files against `docker ps -a`, `docker network ls`, and `docker volume ls`
   - treat stopped project containers as required until proven disposable
5. If disk space dropped suddenly and `docker_data.vhdx` is large, check BuildKit before assuming ordinary image growth:
   - compare `docker system df` with `docker buildx du`
   - if `docker buildx du` shows tens or hundreds of GB reclaimable, treat that as the primary suspect
   - remember that `docker system df` may look moderate while BuildKit cache inside Docker Desktop is still huge
6. Preferred cleanup order:
   - clear Go caches
   - clear Temp, skipping locked files
   - delete project build outputs and generated binaries, not source or dependency trees unless the user asked for that
   - run `docker buildx prune -a -f` when BuildKit cache is the main culprit
   - run `docker builder prune -f`
   - run `docker image prune -f`
   - only run `docker container prune -f` or `docker network prune -f` after confirming no project relies on stopped containers or custom networks
7. If Docker/WSL VHDX files dominate and the user accepts a brief interruption:
   - run `wsl -d docker-desktop -u root -- sh -lc 'fstrim -av'` first when Docker Desktop is the main growth source
   - stop Docker Desktop workloads cleanly
   - `wsl --shutdown`
   - compact the relevant VHDX files with `diskpart`
   - expect host free space to recover only after trim plus compaction; deleting cache alone may not immediately grow `C:` free space
8. Re-check free space, Docker usage, BuildKit usage, and VHDX sizes after cleanup.
</Workflow>

<Safety_Rules>
- Do not assume "stopped" means "disposable". Many local projects keep middleware stopped until needed.
- Prefer deleting caches and build artifacts before touching runtime state.
- Do not delete Docker volumes unless the user explicitly approves losing persisted data.
- Do not trust `docker system df` alone when Docker Desktop VHDX growth is disproportionate; always compare it with `docker buildx du`.
- If a project documents manual Docker setup under `scripts/` or similar, follow that documentation first for restore actions.
- Read [references/project-caveats.md](references/project-caveats.md) when the workspace contains known local middleware stacks or after any cleanup that touched Docker.
</Safety_Rules>

<Verification>
- Compare `Get-PSDrive -Name C` before and after
- Compare `docker system df` before and after if Docker is involved
- Compare `docker buildx du` before and after when BuildKit was involved
- Re-check the large `*.vhdx` files after compaction
- If Docker Desktop was trimmed / compacted, confirm that `C:` free space increased even if the VHDX logical file size still appears large
- If cleanup touched a project's middleware, verify the documented services are reachable again
- If Go cache was removed, rebuild at least one representative Go project
</Verification>

<Reporting>
- Summarize reclaimed space in GB
- List what was cleaned
- Call out whether the root cause was ordinary images, BuildKit cache, Temp / Go cache, or VHDX growth
- Call out anything intentionally skipped for safety
- If Docker cleanup removed something important, say that plainly and restore it using the project's own documentation
</Reporting>
