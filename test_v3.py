"""Screenshot tests for v3 rebrand (OKLCH + dark mode + responsive)."""
import os, sys
from playwright.sync_api import sync_playwright
BASE = 'http://127.0.0.1:5000'
OUT = r'D:\my-first-backend\screenshots'

os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':390,'height':844})

    page.goto(BASE)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)

    # 1. Home page
    page.screenshot(path=os.path.join(OUT,'01-home.png'), full_page=True)
    print('1/7 Home captured')

    # 2. Open search overlay
    page.click('.h-search')
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(OUT,'02-search.png'), full_page=True)
    print('2/7 Search overlay captured')

    # Close search via cancel button
    page.click('.search-cancel')
    page.wait_for_timeout(300)

    # 3. Browse page
    page.locator('.tab').nth(1).click()
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(OUT,'03-browse.png'), full_page=True)
    print('3/7 Browse captured')

    # 4. Expanded category Q&A
    page.locator('.cat-card').first.click()
    page.wait_for_timeout(700)
    page.screenshot(path=os.path.join(OUT,'04-category.png'), full_page=True)
    print('4/7 Category expanded captured')

    # 5. Chat page
    page.locator('.tab').nth(2).click()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(OUT,'05-chat.png'), full_page=True)
    print('5/7 Chat captured')

    # 6. Chat with response
    page.fill('#cInput', '图书馆开馆时间')
    page.click('#cBtn')
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(OUT,'06-chat-response.png'), full_page=True)
    print('6/7 Chat response captured')

    # 7. Profile
    page.locator('.tab').nth(3).click()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(OUT,'07-profile.png'), full_page=True)
    print('7/7 Profile captured')

    browser.close()
    print(f'\nAll screenshots saved to {OUT}')
