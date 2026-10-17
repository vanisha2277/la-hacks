#!/usr/bin/env python3
"""Build a backdated git repo ("drawing vault") with one commit per revision.

Each commit adds that revision's DXFs, with the historical author, date, and MOC in the message.
`git log` then behaves like a document-management version history. Output: ./vault
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.join(HERE, "drawing_history")
EMAIL = {"Dana Okafor": "dokafor@meridian-gas.example", "Priya Raman": "praman@meridian-gas.example"}


def git(*args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    subprocess.run(["git", "-C", VAULT] + list(args), check=True, env=e,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if os.path.exists(VAULT):
        shutil.rmtree(VAULT)
    os.makedirs(os.path.join(VAULT, "drawings"))
    subprocess.run(["git", "init", "-q", VAULT], check=True)
    git("config", "user.name", "vault")
    git("config", "user.email", "vault@meridian-gas.example")
    versions = json.load(open(os.path.join(HERE, "versions", "versions_api.json")))["data"]
    for v in versions:
        for diagram in v["diagramsAffected"]:
            name = "%s_Rev%s.dxf" % (diagram, v["revision"])
            # the "current" file is overwritten in place, like a real drawing vault
            shutil.copy(os.path.join(HERE, "dxf", name), os.path.join(VAULT, "drawings", diagram + ".dxf"))
        git("add", "-A")
        msg = "Rev %s: %s" % (v["revision"], v["comment"])
        if v["moc"]:
            msg += "\n\nMOC: %s" % v["moc"]
        msg += "\nDiagrams: %s" % ", ".join(v["diagramsAffected"])
        stamp = v["createTime"].replace("Z", "+0000")
        a = v["createUserName"]
        env = {"GIT_AUTHOR_NAME": a, "GIT_AUTHOR_EMAIL": EMAIL.get(a, "x@meridian-gas.example"),
               "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_NAME": a,
               "GIT_COMMITTER_EMAIL": EMAIL.get(a, "x@meridian-gas.example"), "GIT_COMMITTER_DATE": stamp}
        git("commit", "-q", "-m", msg, env=env)
    print("vault built with %d commits at %s" % (len(versions), VAULT))


if __name__ == "__main__":
    sys.exit(main())
