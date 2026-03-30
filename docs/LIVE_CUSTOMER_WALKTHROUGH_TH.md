# สคริปต์เดโมลูกค้าแบบสด (Ollama Lane)

ใช้เอกสารนี้เมื่อคุณต้องการเดโม SA-NOM ให้ลูกค้าเห็นภาพว่าเป็น `Private AI Operations Platform` ที่ใช้งานจริงได้ ไม่ใช่แค่เครื่องมือ governance หรือเอกสารเชิงเทคนิค

## เป้าหมายของการเดโม

หลังจบคอล ลูกค้าควรเห็นว่า SA-NOM สามารถ:
- ให้ AI ทำงานใน flow จริงขององค์กร ไม่ใช่แค่ตอบคำถาม
- เก็บ model traffic ไว้ในสภาพแวดล้อมขององค์กรผ่าน Ollama
- พิสูจน์ readiness, provider health, runtime health, และ evidence path ก่อนใช้งานจริง
- ต่อไปสู่ pilot, rollout, compliance tailoring, และ enterprise packaging ได้เมื่อพร้อม

## ประโยคเปิดที่แนะนำ

ใช้ช่วงต้นคอลประมาณนี้:

> วันนี้ตะวันไม่ได้โชว์ AI แบบ hosted ทั่วไป แต่กำลังโชว์ private AI operations lane ที่รันใน environment ขององค์กรเอง พิสูจน์ readiness ได้ และยังคง governance ติดอยู่กับ runtime จริงทุกขั้น

ตามต่อด้วย:

> สำหรับเดโมรอบนี้ เราใช้ Ollama เป็น default private lane ดังนั้น model traffic จะไม่วิ่งออกไปหา hosted provider ถ้าองค์กรยังไม่ต้องการแบบนั้น

## ค่าที่ใช้เดโมแนะนำ

สำหรับ private default lane ตอนนี้ ใช้ค่าแบบนี้:
- `SANOM_MODEL_PROVIDER_DEFAULT=ollama`
- `SANOM_OLLAMA_MODEL=gemma3:1b`
- Ollama daemon ที่ `http://localhost:11434`

คำสั่งเตรียมก่อนเดโม:
- `ollama pull gemma3:1b`
- `python scripts/ollama_demo_environment.py --probe --output _review/ollama_demo_environment.json`
- `python scripts/provider_demo_flow.py --provider ollama --probe --output _review/provider_demo_flow.ollama.json`
- `python scripts/private_server_smoke_test.py`

## เตรียมก่อนเข้าคอล

ควรมีสิ่งเหล่านี้พร้อม:
- `_review/ollama_demo_environment.json`
- `_review/provider_demo_flow.ollama.json`
- ผล smoke test ล่าสุดที่ผ่าน
- one-pager ที่จะใช้ปิดการคุยจาก [ONE_PAGER_TH.md](ONE_PAGER_TH.md) หรือ [ONE_PAGER.md](ONE_PAGER.md)
- เอกสาร commercial จาก [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) และ [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)

หน้าจอที่ควรเปิดไว้:
- terminal ที่อยู่ใน repo root
- browser ที่พร้อมเปิด dashboard
- one-pager หรือ README สำหรับใช้ปิด narrative ตอนท้าย

## โฟลว์เดโม 12 นาทีที่แนะนำ

### 1. ปูโจทย์ให้ตรง (1 นาที)

พูดประมาณนี้:

> วันนี้ปัญหาจริงไม่ใช่แค่ว่า AI ตอบได้ไหม แต่คือ AI จะเข้าไปอยู่ในงานจริงขององค์กรโดยไม่หลุดขอบเขตอำนาจ, traceability, และ operational control ได้อย่างไร SA-NOM ถูกสร้างมาเพื่อแก้ปัญหานั้นโดยตรง

แล้วตามด้วย:

> เดโมนี้ใช้ private default lane ดังนั้น model จะรันผ่าน Ollama ในเครื่องหรือใน infra ขององค์กรเอง ไม่ได้พึ่ง hosted model เป็นเงื่อนไขตั้งต้น

### 2. พิสูจน์ว่า private lane พร้อมจริง (2 นาที)

รัน:
- `python scripts/ollama_demo_environment.py`

สิ่งที่ควรพูด:
- helper ตัวนี้เอาไว้บอกว่า lane local model พร้อมจริง ไม่ใช่เดาว่าพร้อม
- มันเช็ก daemon, model ที่ต้องใช้, และ next actions ให้ operator ในรายงานเดียว
- นี่คือ proof point แรกว่าระบบ private lane ใช้งานได้จริง

สิ่งที่ควรชี้บนหน้าจอ:
- `status: ready`
- `default_private_demo_lane: ollama`
- `daemon.reachable: true`
- `daemon.model_present: true`
- next actions สำหรับ probe และ runtime validation

### 3. พิสูจน์ว่า model lane ตอบสนองจริง (2 นาที)

รัน:
- `python scripts/provider_demo_flow.py --provider ollama --probe`

สิ่งที่ควรพูด:
- นี่คือ live provider check ไปยัง Ollama endpoint จริง
- SA-NOM แยก provider readiness ออกจาก runtime readiness เพื่อให้ operator จับปัญหาได้เร็ว
- ถ้าภายหลังลูกค้าต้องการ OpenAI หรือ Claude ก็รองรับ แต่รอบนี้เราโชว์ private default lane ก่อน

สิ่งที่ควรชี้บนหน้าจอ:
- `selected_provider: ollama`
- `recommended_provider: ollama`
- `probe.status: ok`
- `response_excerpt: PONG`

### 4. พิสูจน์ว่า governed runtime path ผ่านทั้งเส้น (3 นาที)

รัน:
- `python scripts/private_server_smoke_test.py`

สิ่งที่ควรพูด:
- นี่ไม่ใช่แค่ model ping
- smoke path นี้เช็ก login, dashboard, health, evidence, integrations, และ model-provider surfaces ไปพร้อมกัน
- ตรงนี้คือจุดที่ SA-NOM เปลี่ยนจาก AI demo เป็น operational system demo

สิ่งที่ควรชี้บนหน้าจอ:
- `passed: true`
- `errors: 0`
- `warnings: 0`
- `MODEL_PROVIDER_PROBE: ok`
- `EVIDENCE_EXPORT: ok`
- `GO_LIVE_READINESS: ok`

### 5. เปิด runtime จริงให้เห็นภาพ (2 นาที)

รัน:
- `python scripts/run_private_server.py --host 127.0.0.1 --port 8080`

แล้วพูดประมาณนี้:

> จุดสำคัญไม่ใช่แค่ว่ามี dashboard แต่คือ runtime, provider lane, evidence path, และ operational checks ทั้งหมดอยู่ในระบบเดียวกันและ govern อยู่ตลอดเวลา

ส่วนที่แนะนำให้โชว์:
- dashboard summary หรือ health status
- model providers panel
- compliance หรือ evidence sections
- role หรือ runtime sections ที่สะท้อนการใช้งานจริง

### 6. ปิดการคุยให้ไปทางงานจริง (2 นาที)

พูดประมาณนี้:

> community baseline แสดงให้เห็น governed private runtime และ local-model lane ที่พร้อมใช้งาน ส่วน commercial engagement จะเริ่มเมื่อองค์กรต้องการ rollout support, enterprise packaging, compliance tailoring, หรือ guided implementation

จากนั้นเปิดหนึ่งในเอกสารนี้:
- [COMMERCIAL_DISCOVERY_CHECKLIST.md](COMMERCIAL_DISCOVERY_CHECKLIST.md)
- [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)

คำถามปิดที่แนะนำ:

> ถ้าสิ่งนี้จะถูกประเมินต่ออย่างจริงจัง ขั้นถัดไปของคุณน่าจะเป็น guided pilot, infrastructure review, หรือ compliance และ rollout discussion แบบไหนมากที่สุด

## แผนสำรองถ้าระหว่างเดโมมีสะดุด

ถ้า Ollama daemon ไม่ขึ้น:
- รัน `python scripts/ollama_demo_environment.py`
- อธิบายว่าตัว helper ถูกออกแบบมาเพื่อบอก operator ว่าต้องแก้อะไรต่อทันที

ถ้า model ยังไม่ถูกดึง:
- รัน `ollama pull gemma3:1b`
- อธิบายว่า SA-NOM ทำให้ private lane ชัดเจน ไม่ failover ไป hosted path แบบเงียบ ๆ

ถ้า dashboard ยังไม่ใช่หน้าจอที่ดีที่สุดตอนนั้น:
- อยู่ที่ terminal ต่อและใช้รายงานจาก:
  - `python scripts/ollama_demo_environment.py --probe`
  - `python scripts/provider_demo_flow.py --provider ollama --probe`
  - `python scripts/private_server_smoke_test.py`
- อธิบายว่าผลที่เห็นยังเป็น live operator evidence ไม่ใช่ mock output

## คำถามใช้ qualify ระหว่างหรือหลังเดโม

เลือกใช้ 1-2 ข้อตามจังหวะ:
- production lane แรกขององค์กรจำเป็นต้อง private ทั้งหมดไหม หรือ hosted provider ใช้ได้เฉพาะช่วง evaluation?
- ทีมไหนจะเป็น owner ของ AI operations ก่อน: IT, product, compliance หรือ governance team แบบ cross-functional?
- use case แรกขององค์กรเน้น controlled internal operations, compliance posture หรือ business workflow execution มากกว่ากัน?
- checkpoint ถัดไปควรเป็น technical pilot, security review หรือ commercial rollout discussion?

## หลังจบคอลควรเก็บอะไรไว้

เก็บหรือส่งต่อสิ่งเหล่านี้:
- Ollama environment report
- provider probe report
- runtime smoke result
- ข้อกังวลหรือข้อจำกัด deployment ที่ลูกค้าพูดระหว่างคอล
- next step ที่สรุปได้จาก commercial discovery checklist

สำหรับฉบับภาษาอังกฤษ ดู [LIVE_CUSTOMER_WALKTHROUGH.md](LIVE_CUSTOMER_WALKTHROUGH.md)
สำหรับ runbook เดโมสั้น ดู [DISCOVERY_DEMO.md](DISCOVERY_DEMO.md)
สำหรับเอกสาร setup ฝั่ง operator ดู [OLLAMA_DEMO_ENVIRONMENT.md](OLLAMA_DEMO_ENVIRONMENT.md)



สำหรับเช็กลิสต์ 1 หน้า ดู [DEMO_CHECKLIST_TH.md](DEMO_CHECKLIST_TH.md)

