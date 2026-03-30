# เดโมเช็กลิสต์ 1 หน้า

ใช้เอกสารนี้ระหว่างเดโม SA-NOM เพื่อให้เล่าเรื่องได้ครบโดยไม่ต้องจำทุกจุดเอง

## เป้าหมายของเดโม

เดโมนี้ควรทำให้คนฟังเห็นว่า SA-NOM สามารถ:
- ให้ AI ทำงานใน role ที่มีขอบเขตจริง
- ใช้ Ollama เป็น private default lane
- พิสูจน์ readiness ก่อนใช้งานจริง
- เชื่อม runtime, evidence, escalation, และ deployment posture เข้าด้วยกัน

## Default Demo Lane

ใช้ค่าชุดนี้เป็นหลัก เว้นแต่ลูกค้าจะต้องการ hosted evaluation lane โดยเฉพาะ:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- `SANOM_OLLAMA_MODEL=gemma3:1b`
- Ollama daemon ที่ `http://localhost:11434`

## ก่อนเข้าคอล

เช็กให้พร้อม:
- `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
- `python scripts/provider_demo_flow.py --provider ollama --probe --output _review/provider_demo_flow.ollama.json`
- `python scripts/private_server_smoke_test.py`
- browser tab สำหรับ dashboard
- [LIVE_CUSTOMER_WALKTHROUGH_TH.md](LIVE_CUSTOMER_WALKTHROUGH_TH.md)
- [ROI_ONE_PAGER.md](ROI_ONE_PAGER.md)

## ประโยคเปิด 60 วินาที

พูดประมาณนี้:

> วันนี้ตะวันไม่ได้โชว์ AI แบบ hosted ทั่วไป แต่กำลังโชว์ private AI operations lane ที่รันใน environment ขององค์กรเอง พิสูจน์ readiness ได้ และยังคง governance ติดอยู่กับ runtime จริงทุกขั้น

แล้วตามด้วย:

> รอบนี้เราใช้ Ollama เป็น default private lane ดังนั้น model traffic จะอยู่ใน environment ขององค์กร ไม่วิ่งออกไปหา hosted provider โดยอัตโนมัติ

## ลำดับเดโมสด

1. รัน `python scripts/ollama_demo_environment.py`
   ชี้ให้เห็น:
   `status: ready`, `default_private_demo_lane: ollama`, `daemon.reachable: true`, `daemon.model_present: true`

2. รัน `python scripts/provider_demo_flow.py --provider ollama --probe`
   ชี้ให้เห็น:
   `selected_provider: ollama`, `probe.status: ok`, `response_excerpt: PONG`

3. รัน `python scripts/private_server_smoke_test.py`
   ชี้ให้เห็น:
   `passed: true`, `errors: 0`, `warnings: 0`, `MODEL_PROVIDER_PROBE: ok`, `GO_LIVE_READINESS: ok`

4. รัน `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`
   โชว์:
   dashboard summary, model providers, compliance/evidence views, หรือ operator-facing runtime state

## ประเด็นที่ควรย้ำซ้ำ

ย้ำประเด็นเหล่านี้ระหว่างคอล:
- SA-NOM คือ governed AI operations ไม่ใช่แค่ chatbot usage
- Ollama คือ default private lane
- OpenAI และ Claude ยังเป็น optional hosted evaluation lanes
- readiness, provider health, runtime health, และ evidence ถูกตรวจอย่างชัดเจน
- commercial scope จะเริ่มเมื่อองค์กรต้องการ rollout, support, compliance tailoring, หรือ enterprise packaging

## แผนสำรองถ้าเดโมสะดุด

ถ้า Ollama ไม่ขึ้น:
- รัน `python scripts/ollama_demo_environment.py`
- อธิบายว่าตัว helper นี้บอกได้ทันทีว่าต้องแก้อะไรต่อ

ถ้า model ยังไม่มี:
- รัน `ollama pull gemma3:1b`
- อธิบายว่า SA-NOM ทำให้ private lane ชัดเจน ไม่ failover ไป hosted path แบบเงียบ ๆ

ถ้า dashboard ยังไม่ใช่หน้าจอที่ดีที่สุด:
- อยู่ที่ terminal ต่อและใช้ JSON หรือ smoke outputs เป็นหลักฐานสด

## ปิดการคอล

เลือกถาม 1 ข้อ:
- ขั้นถัดไปขององค์กรคือ guided evaluation, paid pilot หรือ production rollout discussion?
- production lane แรกต้อง private ตั้งแต่วันแรกหรือไม่?
- workflow แรกที่ควรทำ pilot คืออะไร?

แล้วต่อไปที่:
- [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [ROI_ONE_PAGER.md](ROI_ONE_PAGER.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
