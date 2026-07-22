# backend/app/git.py
# Commits uploaded model files to a remote Git repository using git commands.
#
# GIT_REPO_PATH must be an absolute path to an existing local git clone.
# Set it in backend/.env — example:
#   GIT_REPO_PATH=/home/
#
# SSH key authentication is used — configure your SSH key in GitLab once
# and git push works without any passwords or tokens in this code.
#
# If GIT_REPO_PATH does not exist the Git step is skipped silently.
# The model is still saved to MongoDB — nothing breaks.

import os
import asyncio
import shutil
#from dotenv import load_dotenv

#load_dotenv()

GIT_REPO_PATH  = os.getenv("GIT_REPO_PATH",  "")
GIT_BRANCH     = os.getenv("GIT_BRANCH",     "main")
GIT_USER_NAME  = os.getenv("GIT_USER_NAME",  "SimFlow Bot")
GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "simflow@example.com")


async def _run(cmd: list[str]) -> tuple[int, str]:
    """
    Run a git command inside GIT_REPO_PATH.
    Returns (exit_code, stderr).
    """
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=GIT_REPO_PATH,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stderr.decode().strip()


async def push_model_to_git(
    file_path:  str,
    file_name:  str,
    commit_msg: str,
    author:     str,
) -> dict:
    """
    Copy the uploaded file into the local git repository
    and push to remote.

    Steps:
      1. Check local repo exists — skip silently if not
      2. Copy file into root of repo
      3. git config user.name
      4. git config user.email
      5. git add <file>
      6. git commit -m <message>
      7. git push origin <branch>
      8. Return the commit hash

    Returns:
      { success: bool, commit_id: str | None, error: str | None }
    """

    # Skip if not configured or folder does not exist
    if not GIT_REPO_PATH:
        print("[git] GIT_REPO_PATH not set in .env — skipping")
        return {"success": False, "commit_id": None, "error": "GIT_REPO_PATH not set"}

    if not os.path.isdir(GIT_REPO_PATH):
        print(f"[git] '{GIT_REPO_PATH}' not found — skipping")
        return {"success": False, "commit_id": None, "error": "Repo not found"}

    # Copy uploaded file directly into the root of the repo
    shutil.copy2(file_path, os.path.join(GIT_REPO_PATH, file_name))

    # Git commands — stop on first failure
    commands = [
        ["git", "config", "user.name",  GIT_USER_NAME],
        ["git", "config", "user.email", GIT_USER_EMAIL],
        ["git", "add",    file_name],
        ["git", "commit", "-m", f"{commit_msg} (by {author})"],
        ["git", "push",   "origin", GIT_BRANCH],
    ]

    for cmd in commands:
        rc, err = await _run(cmd)
        if rc != 0:
            label = " ".join(cmd[:2])
            print(f"[git] '{label}' failed: {err}")
            return {"success": False, "commit_id": None,
                    "error": f"'{label}' failed: {err}"}

    # Read the short commit hash
    proc = await asyncio.create_subprocess_exec(
        "git", "rev-parse", "--short", "HEAD",
        cwd=GIT_REPO_PATH,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_id  = stdout.decode().strip()

    print(f"[git] Pushed '{file_name}' — commit {commit_id}")
    return {"success": True, "commit_id": commit_id, "error": None}
