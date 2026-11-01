"""아침 뉴스 페이지 만들기.

구글 뉴스에서 분야별 최신 뉴스를 가져와서
휴대폰으로 보기 좋은 웹페이지(public/index.html) 한 장으로 만든다.
"""
import html
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# 보고 싶은 분야와 주소. 줄을 지우거나 더하면 분야가 바뀐다.
BASE = "https://news.google.com/rss"
KO = "hl=ko&gl=KR&ceid=KR:ko"
SECTIONS = [
    ("📰 주요 뉴스", f"{BASE}?{KO}"),
    ("💰 경제", f"{BASE}/headlines/section/topic/BUSINESS?{KO}"),
    ("💻 IT·과학", f"{BASE}/headlines/section/topic/TECHNOLOGY?{KO}"),
    ("🌍 세계", f"{BASE}/headlines/section/topic/WORLD?{KO}"),
    ("⚽ 스포츠", f"{BASE}/headlines/section/topic/SPORTS?{KO}"),
]
PER_SECTION = 8  # 분야마다 보여줄 기사 수
KST = timezone(timedelta(hours=9))
OUT = Path(__file__).parent / "public" / "index.html"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def parse(xml_bytes):
    items = []
    for it in ET.fromstring(xml_bytes).iter("item"):
        title = (it.findtext("title") or "").strip()
        source = (it.findtext("source") or "").strip()
        # 구글 뉴스 제목 끝의 " - 언론사" 떼기
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        when = ""
        try:
            when = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST).strftime("%H:%M")
        except Exception:
            pass
        items.append({"title": title, "link": it.findtext("link") or "#", "source": source, "when": when})
        if len(items) >= PER_SECTION:
            break
    return items


def render(sections, now):
    parts = []
    for name, items in sections:
        if not items:
            body = '<p class="empty">뉴스를 못 가져왔어요.</p>'
        else:
            body = "".join(
                f'<a class="item" href="{html.escape(i["link"])}" target="_blank" rel="noopener">'
                f'<div class="t">{html.escape(i["title"])}</div>'
                f'<div class="m">{html.escape(i["source"])} · {i["when"]}</div></a>'
                for i in items
            )
        parts.append(f"<section><h2>{name}</h2>{body}</section>")
    days = "월화수목금토일"
    date = f"{now.month}월 {now.day}일 ({days[now.weekday()]})"
    greet = "좋은 아침이에요 ☀️" if now.hour < 12 else "안녕하세요 👋"
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>아침 뉴스</title>
<style>
:root {{ color-scheme: light dark; --bg:#f6f6f4; --card:#fff; --fg:#1d1d1f; --sub:#777; --line:#e6e6e2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#111; --card:#1c1c1e; --fg:#eee; --sub:#999; --line:#2c2c2e; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif; }}
header {{ padding:28px 18px 8px; }}
header h1 {{ margin:0; font-size:26px; }}
header p {{ margin:6px 0 0; color:var(--sub); font-size:14px; }}
section {{ background:var(--card); margin:14px 12px; border-radius:16px; padding:6px 0; }}
h2 {{ font-size:17px; margin:10px 16px 4px; }}
.item {{ display:block; padding:12px 16px; color:inherit; text-decoration:none; border-top:1px solid var(--line); }}
.item:first-of-type {{ border-top:none; }}
.t {{ font-size:16px; line-height:1.4; }}
.m {{ font-size:12px; color:var(--sub); margin-top:4px; }}
.empty {{ color:var(--sub); padding:0 16px; }}
footer {{ text-align:center; color:var(--sub); font-size:12px; padding:20px; }}
</style></head><body>
<header><h1>{greet}</h1><p>{date} · {now.strftime('%H:%M')} 업데이트</p></header>
{''.join(parts)}
<footer>출처: Google 뉴스 · 매일 아침 자동으로 새로 만들어져요</footer>
</body></html>
"""


def main():
    sections = []
    for name, url in SECTIONS:
        try:
            sections.append((name, parse(fetch(url))))
        except Exception as e:
            print(f"[경고] {name} 가져오기 실패: {e}", file=sys.stderr)
            sections.append((name, []))
    if not any(items for _, items in sections):
        sys.exit("뉴스를 하나도 못 가져왔어요.")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(sections, datetime.now(KST)), encoding="utf-8")
    print(f"완성: {OUT}")


if __name__ == "__main__":
    main()
