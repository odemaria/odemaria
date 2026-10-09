#!/usr/bin/env python3
"""Actualiza data.json con estadisticas de GitHub. Solo stdlib.

Env vars:
    PROFILE_TOKEN  PAT del usuario (fine-grained, solo lectura). Con el se cuentan
                   tambien los repos privados; solo se publican los totales.
    GITHUB_TOKEN   fallback: solo ve datos publicos.
"""
import json
import os
import time
import urllib.error
import urllib.request

USER = "odemaria"
TOKEN = os.environ.get("PROFILE_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")


def gh(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, {}


def is_own_token():
    code, me = gh("https://api.github.com/user")
    return code == 200 and me.get("login", "").lower() == USER.lower()


def list_repos(own):
    url = ("https://api.github.com/user/repos?affiliation=owner&visibility=all&per_page=100"
           if own else f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100")
    repos, page = [], 1
    while True:
        _, batch = gh(f"{url}&page={page}")
        if not batch:
            return [r for r in repos if not r["fork"]]
        repos += batch
        page += 1


def code_stats(repos):
    commits = pending = 0
    for r in repos:
        # /stats/contributors responde 202 mientras GitHub calcula: reintentar
        for _ in range(8):
            code, stats = gh(f"https://api.github.com/repos/{r['full_name']}/stats/contributors")
            if code == 200 and isinstance(stats, list):
                break
            if code == 204:                      # repo vacio
                stats = []
                break
            time.sleep(4)
        else:
            print(f"stats pendientes: {r['full_name']} ({code})")
            pending += 1
            continue
        for c in stats:
            if c.get("author") and c["author"]["login"].lower() == USER.lower():
                commits += c["total"]
    return commits, pending


if __name__ == "__main__":
    own = is_own_token()
    print("token del usuario:", own, "(incluye privados)" if own else "(solo publicos)")
    repos = list_repos(own)
    _, u = gh(f"https://api.github.com/users/{USER}")
    commits, pending = code_stats(repos)
    data = {
        "repos": str(len(repos)),
        "stars": str(sum(r["stargazers_count"] for r in repos)),
        "followers": str(u.get("followers", "?")),
        "commits": f"{commits:,}",
        "pending": pending,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("data.json:", json.dumps(data, ensure_ascii=False))
