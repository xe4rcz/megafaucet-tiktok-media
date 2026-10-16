from playwright.sync_api import sync_playwright
from pathlib import Path
import json
BASE="https://mega-faucet.click/"
OUT=Path("public/screens");OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={"width":1000,"height":1000},device_scale_factor=1,locale="en-US")
 page.route("**/*",lambda route: route.abort() if (route.request.resource_type in ["media"] or any(x in route.request.url.lower() for x in ["doubleclick","googlesyndication","adservice","coinzilla","a-ads.com","propellerads","adsterra"])) else route.continue_())
 selectors=['ins.adsbygoogle','iframe[src*="ad"]','[id*="adsense"]','[class*="advertisement"]','[id*="advertisement"]','.ad-slot','[class*="ad-banner"]']
 response=page.goto(BASE,wait_until="domcontentloaded",timeout=70000)
 if not response or response.status>=400: raise RuntimeError('MegaFaucet homepage unavailable')
 page.wait_for_timeout(1800)
 page.add_style_tag(content=",".join(selectors)+"{visibility:hidden!important} *{scroll-behavior:auto!important;animation:none!important}")
 for i,scroll in enumerate([0,420,950,1450]):
  page.evaluate("(y)=>scrollTo(0,y)",scroll)
  page.wait_for_timeout(200)
  page.screenshot(path=str(OUT/f"site_{i}.png"),animations="disabled")
 browser.close()
print("Captured 4 authentic public page views (ad networks blocked).")
