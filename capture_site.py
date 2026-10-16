#!/usr/bin/env python3
"""Capture real PUBLIC MegaFaucet homepage on a narrow mobile viewport."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://mega-faucet.click/"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="assets/live_site")
    args=p.parse_args()
    dest=Path(args.out)
    dest.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as browser:
        app=browser.chromium.launch(headless=True,args=["--no-sandbox"])
        page=app.new_page(viewport={"width":390,"height":844},device_scale_factor=1,locale="en-US",is_mobile=True,has_touch=True)
        response=page.goto(URL,wait_until="domcontentloaded",timeout=60000)
        page.wait_for_timeout(4500)
        title=page.title()
        body=page.locator("body").inner_text(timeout=12000)
        if not response or response.status>=400 or "faucet" not in (title+" "+body).lower():
            raise RuntimeError("Public MegaFaucet page cannot be verified: refusing synthetic/fake screenshots")
        page.add_style_tag(content="*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important}")
        urls=[]
        for index,scroll in enumerate([0,650,1400,2100]):
            page.evaluate("(top) => window.scrollTo(0,top)",scroll)
            page.wait_for_timeout(550)
            out=dest/f"site_{index}.png"
            page.screenshot(path=str(out),full_page=False,animations="disabled")
            urls.append(str(out))
        meta={"source":URL,"title":title,"status":response.status,"screenshots":urls,"public_capture_only":True}
        (dest/"capture.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
        print(json.dumps(meta))
        app.close()

if __name__=="__main__":
    main()
