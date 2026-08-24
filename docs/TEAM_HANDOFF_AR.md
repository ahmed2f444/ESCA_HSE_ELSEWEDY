# دليل تسليم المشروع وتشغيل قاعدة البيانات وربط الـAgent

## 1. ما الموجود في الحزمة؟

| الجزء | المكان | الاستخدام |
|---|---|---|
| Spring Boot API | `backend/` | المصدر الوحيد لقواعد العمل والكتابة والتدقيق |
| Admin Web | `apps/admin-web/` | لوحة الإدارة العربية |
| Field PWA | `apps/field-web/` | واجهة العمليات الميدانية والمزامنة |
| AI Automation | `services/automation/` | اكتشاف وجدولة وتنبيهات آمنة، و`dry_run` افتراضيًا |
| MySQL | `database/` و`backend/src/main/resources/schema.sql` | إنشاء القاعدة والمستخدمين والجداول |
| العقود | `docs/API_CONTRACT.md` و`services/automation/docs/SPRING_INTEGRATION_CONTRACT.md` | مرجع الربط مع الـAgent والـAutomation |
| أدوات Windows | `tools/` | Java وMaven وNode وpnpm في نسخة التسليم |
| سكربتات التشغيل | `scripts/` | تشغيل موحد يقلل أخطاء المسارات |

الحزمة لا تحتوي على `.git` أو `.env` أو كلمات سر أو cache أو build output.
`node_modules` وPython virtual environment لا يُنقلان لأنهما مرتبطان بالجهاز؛
سكربتات التشغيل تعيد تثبيتهما من ملفات القفل و`requirements.txt`.

## 2. متطلبات جهاز زميلك

- Windows 10/11 x64.
- MySQL Community Server 8.4 يعمل على المنفذ `3306`.
- اتصال إنترنت في أول تشغيل لتنزيل حزم الواجهات وPython عند الحاجة.
- Python 3.14 لتشغيل خدمة Automation فقط.

Java وMaven وNode وpnpm موجودة داخل الحزمة ولا تحتاج تثبيتًا منفصلًا.

## 3. إنشاء قاعدة MySQL المحلية

من جذر المشروع:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
.\scripts\Setup-LocalDatabase.ps1
```

السكربت يطلب ثلاثة أشياء دون تخزينها في Git:

1. باسورد `root` الخاص بـMySQL لتنفيذ الإنشاء.
2. باسورد جديد للمستخدم `hse_app` الذي يشغّل Spring.
3. باسورد جديد للمستخدم `esca_automation_ro` للقراءة فقط.

ينشئ السكربت قاعدة `esca_hse` ويمنح:

- `hse_app`: صلاحيات التطبيق اللازمة داخل `esca_hse` فقط.
- `esca_automation_ro`: `SELECT` و`SHOW VIEW` فقط.

عند تشغيل Spring أول مرة، يطبّق الملف
`backend/src/main/resources/schema.sql` ويحمّل demo data صناعية تلقائيًا.

## 4. تشغيل النظام بالترتيب

### الباك إند

```powershell
.\scripts\Start-Backend.ps1
```

اكتب باسورد `hse_app` عند الطلب. لا تضعه في الأمر نفسه. انتظر حتى ترى أن
Spring بدأ، ثم افتح <http://localhost:8080/api/v1/health>.

### لوحة الإدارة

في Terminal جديد:

```powershell
.\scripts\Start-Admin.ps1
```

أول تشغيل ينفذ `pnpm install --frozen-lockfile` ثم يفتح الخدمة على
<http://localhost:3100>.

### Field PWA

في Terminal جديد:

```powershell
.\scripts\Start-Field.ps1
```

تعمل على <http://localhost:3200>.

### Automation (اختياري للربط)

```powershell
.\scripts\Start-Automation.ps1 -Mode Setup
```

افتح `services/automation/.env` وضع باسورد `esca_automation_ro` فقط. اترك:

```dotenv
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
```

ثم:

```powershell
.\scripts\Start-Automation.ps1 -Mode Test
.\scripts\Start-Automation.ps1 -Mode Api
```

روابطها:

- <http://127.0.0.1:8000/health/ready>
- <http://127.0.0.1:8000/docs>

## 5. ما الذي يُرسل لزميل الـAgent؟

أرسل له:

1. ملف ZIP الناتج كاملًا.
2. هذا الملف `docs/TEAM_HANDOFF_AR.md` داخل الـZIP.
3. `docs/API_CONTRACT.md` لمعرفة الـendpoints العامة.
4. `services/automation/docs/SPRING_INTEGRATION_CONTRACT.md` إذا كان Agent
   سيتكامل مع أحداث Automation.
5. بشكل منفصل وآمن: القيم السرية الخاصة ببيئته فقط، بعد أن يختارها أو يتم
   إنشاؤها له. لا ترسلها في Git أو واتساب جروب أو داخل ZIP.

لا يحتاج أن ترسل له MySQL data files من جهازك؛ `schema.sql` والـdemo seeder
داخل المشروع يعيدان إنشاء قاعدة تجريبية مطابقة.

## 6. الطريقة الصحيحة لربط الـAgent

### الموصى به

```text
Agent -> Spring REST API -> MySQL
                         -> Audit / validation / RBAC
```

لا تجعل الـAgent يكتب في MySQL مباشرة. Spring هو المسؤول عن validation،
authorization، business workflows، audit، وidempotency.

- للعمليات التي ينفذها مستخدم: استخدم `POST /api/v1/auth/login` ثم Bearer JWT
  واستدعِ endpoints الموجودة في `docs/API_CONTRACT.md`.
- لأحداث Automation الداخلية فقط: استخدم
  `POST /api/v1/internal/auth/service-token` ثم
  `POST /api/v1/internal/automation/actions`.
- الـAgent لا يستخدم حساب `root` إطلاقًا.
- لو احتاج قراءة SQL لأغراض تحليلية استثنائية، أنشئ له مستخدمًا منفصلًا
  بصلاحية `SELECT` فقط؛ لا تعطه `hse_app` ولا `root`.

### إعداد محلي سريع للـAgent

```text
API_BASE_URL=http://localhost:8080
```

يمكن إبقاء `APP_SECURITY_ENABLED=false` في العرض المحلي الأول. عند اختبار
المصادقة فعّلها في الباك إند واجعل الـAgent يستخدم JWT بدل تجاوز الـAPI.

## 7. لو أراد استخدام قاعدة Cloud لاحقًا

لا تستخدم حساب `root` المنشور سابقًا. بما أن بيانات اتصال Cloud تم تداولها
في المحادثة، يجب **تغيير/تدوير كلمة السر أولًا** وإنشاء مستخدم تطبيق محدود.

أرسل القيم التالية فقط عبر قناة أسرار منفصلة، وليس داخل المشروع:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USERNAME
DB_PASSWORD
TLS/SSL requirement
```

قبل ربط Cloud:

1. خذ backup.
2. اختبر كل شيء محليًا.
3. أنشئ مستخدم تطبيق محدود ومستخدم Automation للقراءة فقط.
4. نفّذ migration/schema review.
5. شغّل الاختبارات.
6. غيّر الإعدادات من local إلى cloud بعد الموافقة فقط.

## 8. فحص التسليم

من جذر المشروع والباك إند يعمل:

```powershell
.\scripts\Verify-LocalSystem.ps1
```

النتيجة المطلوبة: API وAdmin وField متاحة. فحص Automation يظهر فقط إذا كانت
خدمتها تعمل.

## 9. أشهر الأخطاء

- `pnpm is not recognized`: استخدم سكربتات الحزمة من الجذر بدل كتابة `pnpm`
  يدويًا.
- `mvn.cmd is not recognized`: استخدم `scripts/Start-Backend.ps1` من الجذر.
- `Access denied`: راجع اسم المستخدم والباسورد، ولا تستخدم باسورد PostgreSQL
  مع MySQL.
- `Unknown database esca_hse`: شغّل `Setup-LocalDatabase.ps1` أولًا.
- الواجهة تقول Disconnected: شغّل الباك إند وافحص port `8080`.
- port مستخدم: أغلق النسخة القديمة قبل تشغيل نسخة ثانية.
