"""End-to-end integration test for BotForge."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = ""
TENANT_HEADERS = {}


def step(title):
    print(f"\n{'='*50}\n[STEP] {title}\n{'='*50}")


def main():
    global TOKEN, TENANT_HEADERS

    step("1. Login")
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "tester2", "password": "123456"})
    assert r.status_code == 200, r.text
    TOKEN = r.json()["access_token"]
    TENANT_HEADERS = {"Authorization": f"Bearer {TOKEN}"}
    print("login ok, company:", r.json()["company"])

    step("2. Create knowledge base")
    r = httpx.post(
        f"{BASE}/api/kb",
        json={"name": "枫叶产品手册", "description": "枫叶软件公司产品使用说明"},
        headers=TENANT_HEADERS,
    )
    assert r.status_code == 200, r.text
    kb_id = r.json()["id"]
    print("kb created, id:", kb_id)

    step("3. Upload document (markdown)")
    doc_content = """# 枫叶智能客服系统产品手册

## 1. 产品简介

枫叶智能客服系统（MapleChat）是枫叶软件科技有限公司旗下的企业级智能客服产品，
旨在帮助企业快速搭建 7x24 小时不间断的智能客服体系。产品基于 RAG 检索增强生成技术，
支持多格式知识库文档导入，包括 PDF、Word、Markdown 等格式。

## 2. 价格与套餐

MapleChat 提供三个版本：
- **基础版**：980 元/年，支持 1 个机器人、500MB 知识库空间、单轮问答。
- **专业版**：2980 元/年，支持 5 个机器人、5GB 知识库空间、多轮对话、引用溯源。
- **旗舰版**：8800 元/年，不限机器人数量、50GB 知识库空间、私有化部署支持。

教育机构与非营利组织可申请 5 折优惠。

## 3. 退款政策

购买后 7 天内未产生超过 100 次对话的，可申请全额退款。
超过 7 天的，按剩余服务时长折算退款，需扣除 15% 手续费。
退款申请请发送邮件至 refund@maplesoft.cn，处理周期为 3-5 个工作日。

## 4. 技术支持

工作时间：周一至周五 9:00-18:00（法定节假日除外）。
支持邮箱：support@maplesoft.cn
售后热线：400-800-1234
企业微信技术支持群仅对专业版及以上用户开放。

## 5. 常见问题

Q: 支持哪些部署方式？
A: 支持公有云 SaaS 部署与私有化本地部署（旗舰版）。

Q: 数据安全如何保障？
A: 所有数据传输采用 TLS 1.3 加密，知识库数据支持 AES-256 静态加密，
私有化部署时数据完全存储在客户本地服务器。
"""
    files = {"file": ("product_manual.md", doc_content.encode("utf-8"), "text/markdown")}
    r = httpx.post(f"{BASE}/api/kb/{kb_id}/docs", files=files, headers=TENANT_HEADERS)
    assert r.status_code == 200, r.text
    doc = r.json()
    print("doc uploaded, id:", doc["id"], "status:", doc["status"])

    step("4. Wait for ingestion (parse -> chunk -> embed)")
    for i in range(30):
        r = httpx.get(f"{BASE}/api/kb/{kb_id}/docs", headers=TENANT_HEADERS)
        docs = r.json()
        target = next(d for d in docs if d["id"] == doc["id"])
        print(f"  poll {i+1}: status={target['status']} chunks={target['chunk_count']}")
        if target["status"] in ("done", "failed"):
            break
        time.sleep(2)
    assert target["status"] == "done", f"ingestion failed: {target.get('error')}"
    print("ingestion done, chunks:", target["chunk_count"])

    step("5. Create bot")
    r = httpx.post(
        f"{BASE}/api/bots",
        json={
            "name": "枫叶小助手",
            "system_prompt": "你是枫叶软件科技有限公司的官方客服助手「小枫」，语气亲切专业，回答简洁准确。",
            "welcome_message": "你好，我是小枫，枫叶智能客服的官方助手，有什么可以帮您？",
            "suggested_questions": ["专业版多少钱一年？", "退款政策是怎样的？", "支持私有化部署吗？"],
            "temperature": 0.3,
            "kb_ids": [kb_id],
        },
        headers=TENANT_HEADERS,
    )
    assert r.status_code == 200, r.text
    bot_id = r.json()["id"]
    print("bot created, id:", bot_id)

    step("6. Chat test A - question inside knowledge base (expect citations)")
    answer = stream_chat(bot_id, "专业版套餐的价格和包含的功能是什么？")
    print("\nANSWER:\n", answer["text"][:500])
    print("\nCITATIONS:", len(answer["citations"]))
    for c in answer["citations"]:
        print(f"  [{c['index']}] {c['filename']} score={c['score']}")

    step("7. Chat test B - question outside knowledge base (expect honest refusal)")
    answer2 = stream_chat(bot_id, "你们公司的CEO是谁？公司成立于哪一年？")
    print("\nANSWER:\n", answer2["text"][:500])
    print("\nCITATIONS:", len(answer2["citations"]))

    step("8. Stats check")
    r = httpx.get(f"{BASE}/api/stats", headers=TENANT_HEADERS)
    stats = r.json()
    print(
        "conversations:", stats["total_conversations"],
        "| user msgs:", stats["total_user_messages"],
        "| hit_rate:", stats["hit_rate"],
        "| chunks:", stats["chunk_count"],
        "| hot:", len(stats["hot_questions"]),
    )

    step("9. Audit check")
    r = httpx.get(f"{BASE}/api/conversations", headers=TENANT_HEADERS)
    print("conversations in audit:", len(r.json()))

    step("10. Publish bot")
    r = httpx.post(f"{BASE}/api/bots/{bot_id}/publish", headers=TENANT_HEADERS)
    assert r.status_code == 200, r.text
    token = r.json()["publish_token"]
    print("published, token:", token)

    step("11. Public chat (no auth)")
    r = httpx.get(f"{BASE}/api/public/{token}/info")
    print("public info:", r.json())
    pub_answer = stream_chat_public(token, "退款需要扣手续费吗？")
    print("\nPUBLIC ANSWER:\n", pub_answer["text"][:400])
    print("\nCITATIONS:", len(pub_answer["citations"]))

    print("\n\n" + "=" * 50)
    print("ALL END-TO-END TESTS PASSED")
    print("=" * 50)


def parse_sse(resp):
    events = []
    buffer = ""
    for chunk in resp.iter_text():
        buffer += chunk
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            ev, data = "", ""
            for line in block.split("\n"):
                if line.startswith("event: "):
                    ev = line[7:].strip()
                elif line.startswith("data: "):
                    data += line[6:]
            if ev and data:
                import json as j

                events.append((ev, j.loads(data)))
    return events


def stream_chat(bot_id, message):
    with httpx.stream(
        "POST",
        f"{BASE}/api/chat/{bot_id}/stream",
        json={"message": message, "session_key": "e2e_test"},
        headers=TENANT_HEADERS,
        timeout=180,
    ) as resp:
        assert resp.status_code == 200, resp.read()
        text = ""
        citations = []
        for ev, data in parse_sse(resp):
            if ev == "chunk":
                text += data["content"]
            elif ev == "done":
                citations = data["citations"]
        return {"text": text, "citations": citations}


def stream_chat_public(token, message):
    with httpx.stream(
        "POST",
        f"{BASE}/api/public/{token}/stream",
        json={"message": message, "session_key": "e2e_public"},
        timeout=180,
    ) as resp:
        assert resp.status_code == 200, resp.read()
        text = ""
        citations = []
        for ev, data in parse_sse(resp):
            if ev == "chunk":
                text += data["content"]
            elif ev == "done":
                citations = data["citations"]
        return {"text": text, "citations": citations}


if __name__ == "__main__":
    main()
