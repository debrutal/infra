#!/usr/bin/env python3
"""
Verification script for all mini.debrutal.dev subdomains.
Checks DNS resolution, HTTP reachability, and valid CA certificate (e.g. Let's Encrypt).
Runs with a maximum timeout of 180s (3 minutes).
"""

import sys
import time
import socket
import subprocess

TARGET_IP = "192.168.1.8"
MAX_TIMEOUT_SECONDS = 180  # Max 3 minutes
POLL_INTERVAL_SECONDS = 10

SUBDOMAINS = [
    "mini.debrutal.dev",
    "traefik.mini.debrutal.dev",
    "dashboard.mini.debrutal.dev",
    "dash.mini.debrutal.dev",
    "lago.mini.debrutal.dev",
    "lago-api.mini.debrutal.dev",
    "invoiceninja.mini.debrutal.dev",
    "espocrm.mini.debrutal.dev",
    "status.mini.debrutal.dev",
    "sentry.mini.debrutal.dev",
    "gitea.mini.debrutal.dev",
    "authentik.mini.debrutal.dev",
    "fusion.mini.debrutal.dev",
]



def check_domain(domain):
    """
    Checks DNS resolution, HTTP status, and TLS certificate details.
    """
    dns_ok = False
    resolved_ip = ""
    try:
        resolved_ip = socket.gethostbyname(domain)
        dns_ok = True
    except Exception as e:
        resolved_ip = f"DNS Error: {e}"

    # Inspect SSL Cert with -k
    cmd_inspect = [
        "curl", "-Iv", "-k", "--connect-timeout", "5",
        "--resolve", f"{domain}:443:{TARGET_IP}",
        f"https://{domain}/"
    ]
    res_inspect = subprocess.run(cmd_inspect, capture_output=True, text=True)

    cert_subject = ""
    cert_issuer = ""
    http_code = ""

    for line in res_inspect.stderr.splitlines():
        if "subject:" in line:
            cert_subject = line.strip()
        if "issuer:" in line:
            cert_issuer = line.strip()
        if "< HTTP/" in line:
            http_code = line.strip()

    is_default_cert = "TRAEFIK DEFAULT CERT" in cert_subject or "TRAEFIK DEFAULT CERT" in cert_issuer

    # Strict SSL verification check (without -k)
    cmd_strict = [
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "--connect-timeout", "5",
        "--resolve", f"{domain}:443:{TARGET_IP}",
        f"https://{domain}/"
    ]
    res_strict = subprocess.run(cmd_strict, capture_output=True, text=True)
    strict_ok = (res_strict.returncode == 0)

    # Valid cert if strict verification succeeds or issuer is a known CA and not Traefik Default
    valid_cert = not is_default_cert and (strict_ok or "Let's Encrypt" in cert_issuer or "Cloudflare" in cert_issuer)

    cert_desc = "TRAEFIK DEFAULT CERT (Self-Signed)" if is_default_cert else (cert_issuer if cert_issuer else "Unknown")
    details = (
        f"DNS: {'OK' if dns_ok else 'FAIL'} ({resolved_ip}) | "
        f"HTTP: {http_code if http_code else 'Response Received'} | "
        f"Cert: {'VALID CA' if valid_cert else cert_desc}"
    )

    return dns_ok, (res_inspect.returncode == 0), valid_cert, details


def run_verification():
    start_time = time.time()
    attempt = 1

    print("=================================================================")
    print(f" Starting Subdomain HTTPS & Certificate Verification (Max 3 Min)")
    print("=================================================================")

    while True:
        elapsed = time.time() - start_time
        remaining = max(0, MAX_TIMEOUT_SECONDS - int(elapsed))
        print(f"\n[Attempt {attempt}] Elapsed: {int(elapsed)}s / Remaining: {remaining}s")
        print("-" * 65)

        results = {}
        all_passed = True

        for domain in SUBDOMAINS:
            dns_ok, http_ok, valid_cert, details = check_domain(domain)
            passed = dns_ok and http_ok and valid_cert
            results[domain] = (passed, details)
            if not passed:
                all_passed = False

            status_icon = "✅" if passed else "⏳"
            print(f"  {status_icon} {domain:<32} -> {details}")

        if all_passed:
            print("\n=================================================================")
            print(" SUCCESS: All subdomains passed DNS, HTTPS, & TLS Certificate checks!")
            print("=================================================================")
            sys.exit(0)

        if elapsed >= MAX_TIMEOUT_SECONDS:
            print("\n=================================================================")
            print(" TIMEOUT: Reached 3-minute limit. Summary of failed domains:")
            print("=================================================================")
            for domain, (passed, details) in results.items():
                if not passed:
                    print(f"  ❌ {domain:<32} -> {details}")
            sys.exit(1)

        time.sleep(POLL_INTERVAL_SECONDS)
        attempt += 1


if __name__ == "__main__":
    run_verification()
