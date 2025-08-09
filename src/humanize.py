from __future__ import annotations
import random
import time
from playwright.sync_api import Page


def random_wait(a=0.6, b=1.6):
    time.sleep(random.uniform(a, b))


def random_scroll(page: Page):
    h = random.randint(200, 1200)
    page.mouse.wheel(0, h)
    random_wait(0.2, 0.6)


def random_mouse_move(page: Page):
    # Move mouse to random points
    for _ in range(random.randint(2, 5)):
        x, y = random.randint(50, 1200), random.randint(50, 800)
        page.mouse.move(x, y, steps=random.randint(8, 20))
        random_wait(0.1, 0.3)

