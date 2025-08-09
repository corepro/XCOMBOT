from __future__ import annotations
import re

# 集中管理选择器，便于后续通过 Playwright MCP 调整
HOME_LINK = '[data-testid="AppTabBar_Home_Link"]'
ACCOUNT_SWITCHER = '[data-testid="SideNav_AccountSwitcher_Button"]'

# Profile 页面
FOLLOW_BUTTON_ROLE = ("button", re.compile(r"^(Follow|关注|フォロー|Seguir|Abonn|Suivre)$", re.I))
FOLLOWING_BUTTON_ROLE = ("button", re.compile(r"^(Following|已关注|フォロー中|Siguiendo|Abonné)$", re.I))

# 推文元素
TWEET_ARTICLE = 'article'
TWEET_DATATESTID_ANY = '[data-testid="tweet"]'
TWEET_REPLY = '[data-testid="reply"]'
TWEET_RETWEET = '[data-testid="retweet"]'
TWEET_REPOST = '[data-testid="repost"]'
TWEET_LIKE = '[data-testid="like"]'
TWEET_UNLIKE = '[data-testid="unlike"]'

# 弹窗/编辑
RETWEET_MENU_RETWEET_ROLE = ("menuitem", re.compile(r"^(Retweet|Repost|转发)$", re.I))
RETWEET_MENU_QUOTE_ROLE = ("menuitem", re.compile(r"^(Quote|引用|Quote Post|引用帖子)$", re.I))
TWEET_TEXTAREA = '[data-testid="tweetTextarea_0"]'
TWEET_BUTTON = '[data-testid="tweetButtonInline"]'
TWEET_BUTTON_MAIN = '[data-testid="tweetButton"]'

