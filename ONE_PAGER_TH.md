# SA-NOM AI Governance Suite

Private AI operations for organizations that want AI in real roles, with governance built in.


AI ที่มีตำแหน่ง มีขอบเขต และรายงานได้จริง

On-Premise · Air-Gapped Ready · Audit-First · PTAG Runtime · PT-OSS Structural Intelligence

## ปัญหาที่องค์กรส่วนใหญ่กำลังเผชิญ

องค์กรที่นำ AI มาใช้งานในปี 2025–2026 พบว่า AI วิ่งเร็วกว่าโครงสร้างองค์กรรับได้ ทีมใช้ AI ทำงานจริง แต่ไม่มีระบบกำหนดว่าใครรับผิดชอบเรื่องอะไร ไม่มีหลักฐานให้ตรวจสอบ และเมื่อเกิดปัญหาก็ไม่รู้ว่าใครต้องตอบ

- ข้อมูลลูกค้าและข้อมูลภายในรั่วไหลออกนอกองค์กรโดยไม่ตั้งใจ ผ่าน Cloud ของผู้ให้บริการภายนอกที่องค์กรไม่ได้ควบคุม
- การใช้ AI ผิด Compliance ของ PDPA, BOT, SEC หรือมาตรฐานสากล โดยที่ไม่มีใครรู้ว่าเกิดขึ้นแล้ว
- เมื่อถูก Audit หรือถูกร้องเรียน ไม่มีหลักฐานให้ตรวจสอบ ต้องรวบรวมเองแบบ panic
- AI ตัดสินใจหรือสื่อสารแทนองค์กรโดยไม่มีมนุษย์กำกับ ไม่มีใครรู้ว่าใครรับผิดชอบ
- พนักงานใช้ AI แบบ free-for-all ไม่มีมาตรฐาน ไม่มีขอบเขต แต่ละคนใช้ต่างกันโดยสิ้นเชิง
- สิ่งที่องค์กรเสียไปทุกวันที่ยังไม่มีระบบกำกับ AI คือความเชื่อมั่นของลูกค้า หลักฐานที่ควรมีแต่ไม่มี และเวลาของผู้บริหารที่ต้องมานั่งแก้ปัญหาที่ป้องกันได้

## SA-NOM AI Governance Suite คืออะไร

SA-NOM AI Governance Suite คือ Private AI Governance ที่ติดตั้งภายในองค์กรของท่านทั้งหมด ข้อมูลไม่ออกนอกองค์กรเลย ระบบทำให้ AI แต่ละตัวมีตำแหน่ง มีขอบเขตอำนาจ และรายงานต่อมนุษย์ได้จริง ไม่ใช่แค่ chatbot ที่รับคำสั่งแบบ free-form

Community baseline is published under AGPL-3.0-only. Commercial path remains available for enterprise features, direct support, rollout hardening, and regulated deployment programs.

## สามชั้นหลักของระบบ

- **PTAG Runtime Engine**: ภาษากำกับ AI ที่ SA-NOM ออกแบบขึ้นเอง ทุก Role ถูกเขียน parse validate และ sign ด้วยภาษา PTAG ก่อน deploy เสมอ
- **PT-OSS Structural Intelligence**: เรดาร์วัดความพร้อมโครงสร้างองค์กรก่อนปล่อย AI ทำงาน ด้วย 7 ตัวชี้วัดเชิงโครงสร้าง
- **Governance Runtime**: ชุด engine บังคับขอบเขตอำนาจ บันทึกหลักฐาน ส่งต่อมนุษย์ทุกครั้งที่จำเป็น และจัดการ lifecycle ข้อมูลครบวงจร

## ฟีเจอร์หลักแปดประการ

- **01  Role Private Studio — สร้าง AI ที่มีตำแหน่งจาก JD ขององค์กร**: อัปโหลด Job Description → ระบบสร้าง PTAG Role Pack อัตโนมัติ ไม่ต้องเขียน Prompt เอง AI รับบทบาทจริงได้ทันที เช่น CFO, Legal Director, Compliance Officer, HR Manager ทุก Role ผ่านการประเมิน PT-OSS และ Trusted Registry signature ก่อน publish รองรับ revision history, diff ระหว่างเวอร์ชัน และกู้คืนเวอร์ชันเก่าได้ตลอดเวลา
- **02  Human Ask — เรียก AI รายงานได้ทุกเมื่อ แบบ real-time**: พิมพ์คำถามได้เลย เช่น "สรุปสถานะงานทั้งหมดของทีมกฎหมายในเดือนนี้" รองรับการเรียก AI หลายตำแหน่งพร้อมกันในโหมด Meeting มี confidence threshold ที่ตั้งค่าได้ หากมั่นใจต่ำกว่าเกณฑ์จะหยุดและรอมนุษย์ทันที ทุกการรายงานถูกบันทึกเป็นหลักฐานอัตโนมัติพร้อม scope assessment ก่อนตอบทุกครั้ง
- **03  PT-OSS Structural Intelligence — เรดาร์ตรวจโครงสร้างองค์กรก่อนปล่อย AI**: ประเมินความพร้อมเชิงโครงสร้างด้วย 7 ตัวชี้วัดหลัก (HDI-S, HDI-D, SFS, KPIR, ASP, HOIS, SPAI) หากโครงสร้างองค์กรยังไม่พร้อม ระบบจะ block การ publish Role โดยอัตโนมัติ รองรับโหมด PT_OSS_FULL_CAL_TH สำหรับหน่วยงานรัฐไทย ที่วัดปัจจัยทางวัฒนธรรม เช่น บุญคุณผูกพันและ hierarchy pressure ให้รายงาน posture (healthy / watch / elevated / critical) พร้อมคำแนะนำที่นำไปปฏิบัติได้จริง
- **04  Authority Guard + Resource Lock — ป้องกันทุก action ทุก request**: ตรวจสอบ 3 ระดับก่อนทุกการกระทำ: allow / deny / require human override Resource Lock ป้องกัน race condition เมื่อหลาย request เข้าถึงทรัพยากรเดียวกัน Ethics Guard และ Risk Scorer ทำงานแยกชั้น หากไม่ผ่านการตรวจสอบ ระบบจะปฏิเสธทันทีและบันทึกเหตุผลเป็นหลักฐาน
- **05  Audit Chain + Evidence Pack — หลักฐานที่แก้ไขย้อนหลังไม่ได้**: ทุก event เชื่อมต่อด้วย SHA-256 hash chain ทำให้ตรวจพบการแก้ไขได้ทันที Evidence Pack รวบรวมหลักฐานครบชุด (audit log, role snapshot, compliance mapping, session record) พร้อมส่งให้ Auditor ด้วยคำสั่งเดียว Retention Manager จัดการ lifecycle ข้อมูลแบบครบวงจร ได้แก่ archival, legal hold และ purge policy
- **06  Trusted Registry — ควบคุมการ publish Role อย่างเป็นทางการ**: ทุก Role ต้องผ่านการ sign ด้วย Trusted Registry key ขององค์กรก่อน deploy องค์กรเป็นผู้ถือกุญแจเอง ไม่มีบุคคลที่สามสามารถ publish Role ได้โดยไม่ได้รับอนุมัติ manifest.json บันทึก SHA-256 และลายเซ็นของทุก Role Pack หาก signature ไม่ถูกต้อง ระบบจะปฏิเสธการโหลด Role ทันที
- **07  Integration Outbound — เชื่อมต่อกับระบบเดิมขององค์กร**: รองรับ SIEM Bridge, Service Desk Bridge (Jira / ServiceNow) และ Custom Webhook ทุก integration event ถูกบันทึกใน audit log อย่างครบถ้วน ใช้ Outbox Queue + Dead Letter Queue พร้อม retry policy และ HMAC-SHA256 signing
- **08  Human Alert & Escalation Notification — แจ้งเตือนทันทีเมื่อ AI ต้องการมนุษย์**: ระบบแจ้งเตือนแบบ real-time เมื่อ AI ไม่สามารถตัดสินใจหรือดำเนินการได้ด้วยตนเอง ครอบคลุมกรณี: ถูก block เพราะอยู่นอกขอบเขตอำนาจ, ต้องใช้ Human Override, Policy สั่ง escalate, Confidence Score ต่ำกว่าเกณฑ์ หรือ PT-OSS Posture อยู่ในระดับ elevated ขึ้นไป แสดงผลผ่าน Dashboard และส่งแจ้งเตือนผ่าน Webhook ไปยัง SIEM, Teams, Slack หรือ Ticketing System

## ก่อน และ หลัง

- **Before**: พนักงานใช้ AI แบบ free-for-all ไม่มีขอบเขต ไม่มีมาตรฐาน
  **After**: AI แต่ละตัวมีตำแหน่ง มีขอบเขต PTAG กำหนดไว้ชัดเจน
- **Before**: ไม่มีหลักฐานว่า AI ทำอะไรบ้าง เมื่อถูก Audit ต้องรวบรวมเองแบบ panic
  **After**: Evidence Pack พร้อมส่ง Auditor ทันที Audit Chain SHA-256 ตรวจสอบได้
- **Before**: เมื่อ AI ตัดสินใจเกินขอบเขต ไม่รู้ว่าใครรับผิดชอบ
  **After**: ทุก Role มีเจ้าของ มีขอบเขตอำนาจชัดเจน รู้ทันทีว่าใครต้องตอบ
- **Before**: ผู้บริหารไม่รู้ว่า AI ในองค์กรกำลังทำอะไรอยู่จริงๆ
  **After**: Human Ask — เรียกรายงานได้ทุกเมื่อ real-time ทั้งรายคนและภาพรวม
- **Before**: ข้อมูลองค์กรส่งออกไปยัง Cloud ของผู้ให้บริการภายนอก
  **After**: ติดตั้งในองค์กร 100% ข้อมูลไม่ออกนอกองค์กรเลย
- **Before**: AI publish ใช้งานได้ทันทีโดยไม่มีการตรวจสอบ
  **After**: ทุก Role ผ่าน PT-OSS + Trusted Registry signature ก่อน publish

## เหมาะกับองค์กรแบบใด

SA-NOM AI Governance Suite ออกแบบมาสำหรับองค์กรที่มีข้อมูลละเอียดอ่อน ต้องการ Compliance ที่ชัดเจน และรับผิดชอบต่อผลของการตัดสินใจที่ใช้ AI สนับสนุน

- **ธนาคารและสถาบันการเงิน**: PDPA, BOT, SEC, Basel compliance
- **หน่วยงานรัฐและราชการ**: ต้องการความโปร่งใสตามกฎหมาย รองรับ PT_OSS_FULL_CAL_TH สำหรับโครงสร้างอำนาจแบบไทย
- **โรงพยาบาลและ Healthcare**: ข้อมูลผู้ป่วยต้องได้รับการปกป้องขั้นสูงสุด
- **พลังงาน โรงงาน โครงสร้างพื้นฐาน**: ต้นทุนของการตัดสินใจผิดพลาดสูงมาก ต้องการ human override ที่เชื่อถือได้
- **กฎหมาย การศึกษา โทรคมนาคม**: ต้องการ AI ที่มีตำแหน่งชัดเจนและตรวจสอบได้ในแต่ละ department

## The Governance Engine — สำหรับทีม IT และ Compliance

- **PTAG Runtime Pipeline**: ทุก Role Pack ผ่าน 3 ขั้นตอนก่อน deploy: PTAGParser แปลง .ptn ให้เป็น AST ตรวจ syntax ทุก block — SemanticAnalyzer ตรวจว่าทุก action ที่ allow มี policy หรือ constraint รองรับ ถ้าไม่มีจะ flag เป็น POLICY_COVERAGE_GAP — PTAGValidator ตรวจ required headers, block types, authority-role consistency และ semantic issues
- **Audit Chain — SHA-256 Hash Chain**: ทุก event มี entry_id, sequence number, prev_hash (hash ของ entry ก่อนหน้า) และ entry_hash (hash ของตัวเอง) การแก้ไขใดๆ ทำให้ chain ขาดและตรวจพบทันที รองรับ reseal legacy entries เพื่อ migrate log เก่าเข้า chain ใหม่ได้
- **Request Consistency — Idempotency & Event Ordering**: ระบบรองรับ idempotency key เพื่อป้องกัน duplicate execution และ event stream ordering เพื่อป้องกัน out-of-order processing ทุก request ที่ซ้ำจะถูก replay จาก store โดยไม่ execute ซ้ำ
- **Access Control — 4 ระดับ Token Hashing**: Token ทุกตัวถูก SHA-256 hash ก่อนจัดเก็บ ไม่มี plain text token ในระบบ รองรับ token rotation policy และ SSO/SCIM สำหรับ Enterprise
- **Compliance Framework ในตัว — ไม่ต้อง map เอง**: ระบบ map ความสอดคล้องกับมาตรฐานสากลไว้ในตัวแล้ว: ISO/IEC 27001, NIST Cybersecurity Framework, SOC 2 และ PDPA Governance Baseline แต่ละ control ถูก map กับ capability และรายงานสถานะ covered / partial / gap ให้เห็นทันที
- **Persistence & Scale**: File-based (default) ทำงานได้ทันทีไม่ต้องตั้งค่าเพิ่ม — PostgreSQL-ready ตั้ง SANOM_PERSISTENCE_BACKEND=postgresql พร้อม DSN ได้เลย — Redis-ready สำหรับ outbox queue delivery — Docker Compose พร้อม optional PostgreSQL และ Redis สำหรับ enterprise scale-up
- **Go-Live Readiness Gate**: ก่อน go-live ระบบตรวจ 8 gate อัตโนมัติ: deployment validation, trusted registry signature, audit integrity, plain-token posture, startup smoke test, review pack, privileged operations delegation และ studio structural posture

## ราคาและแพ็กเกจ (ปี 2026)

Use [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) as the source of truth for current commercial terms and pricing.

- **Community**: Free
- **Starter**: 180,000 - 350,000 THB / year
- **Professional**: 950,000 - 2,800,000 THB / year
- **Enterprise**: 4,500,000 - 9,500,000+ THB / year
- **Sovereign / Gov**: Custom pricing

## Start Here

- Project overview: [README.md](README.md)
- Deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Commercial terms: [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)
- Sales intake template: [SALES_INTAKE_TEMPLATE.md](SALES_INTAKE_TEMPLATE.md)
- English one-pager: [ONE_PAGER.md](ONE_PAGER.md)

## Contact

Commercial, rollout, security, and evaluation contact: `sanomaiarch@gmail.com`
