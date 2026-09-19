#!/bin/bash
# 전체 흐름 테스트용 샘플 저장소를 만든다.  사용: bash tests/e2e/setup_sample.sh <대상 디렉터리>
# CCForge를 README의 설치 방법대로 <대상>/.claude/에 복사한다. 실행:  (cd <대상> && claude -p "/orchestrate ...")
set -eu
FW=$(cd "$(dirname "$0")/../.." && pwd); T=${1:?대상 디렉터리}
rm -rf "$T"; mkdir -p "$T/shop" "$T/tests" "$T/.claude"; cd "$T"
cat > shop/__init__.py <<'P'
P
cat > shop/cart.py <<'P'
"""장바구니."""


class Cart:
    def __init__(self):
        self.items = []  # (name, unit_price, quantity)

    def add(self, name, unit_price, quantity=1):
        self.items.append((name, unit_price, quantity))

    def total(self):
        # BUG: 수량을 곱하지 않는다
        return sum(price for _, price, _ in self.items)
P
cat > tests/__init__.py <<'P'
P
cat > tests/test_cart.py <<'P'
import unittest

from shop.cart import Cart


class CartTest(unittest.TestCase):
    def test_single_item(self):
        c = Cart()
        c.add("pen", 1000)
        self.assertEqual(c.total(), 1000)


if __name__ == "__main__":
    unittest.main()
P
printf '# sample shop\n\n테스트: `python3 -m unittest discover -s tests -t .`\n' > README.md
printf '# sample shop\n\n- 언어: Python 3 (표준 라이브러리만)\n- 테스트: `python3 -m unittest discover -s tests -t .`\n' > CLAUDE.md
cp -R "$FW/agents" "$FW/commands" "$FW/protocols" "$FW/skills" .claude/
echo '.claude/workspace/' >> .gitignore
cp "$FW/orchestrate.config.json" .claude/
git init -q -b main .; git config user.email e2e@test; git config user.name e2e
git add -A; git commit -qm "init sample"
echo "sample repo: $T"
