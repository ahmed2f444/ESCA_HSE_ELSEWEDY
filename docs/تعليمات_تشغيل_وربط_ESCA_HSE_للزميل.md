# تعليمات تشغيل مشروع ESCA HSE وربط الـAgent

مرحبًا،

الملف المضغوط المرفق يحتوي على مشروع **ESCA HSE Management System** كاملًا، باستثناء الـConversational Agent. المشروع يحتوي على:

- Spring Boot Backend API.
- قاعدة بيانات MySQL ومخطط الجداول والبيانات التجريبية.
- لوحة الإدارة Admin Web.
- تطبيق العمليات الميدانية Field PWA.
- خدمة AI Automation بنظام قراءة آمن و`dry_run` افتراضيًا.
- Java 17 وMaven وNode.js وpnpm داخل المشروع.
- الاختبارات وعقود التكامل مع الـAgent.

## 1. فك الضغط

فك ملف:

```text
ESCA_HSE_Unified_TEAM_HANDOFF_2026-08-23.zip
```

في مسار قصير وواضح، مثل:

```text
C:\Projects\ESCA_HSE_Unified
```

بعد فك الضغط، افتح PowerShell داخل مجلد `ESCA_HSE_Unified`.

## 2. المتطلبات

المطلوب تثبيته على الجهاز:

- Windows 10 أو Windows 11 بنظام 64-bit.
- MySQL Community Server 8.4 يعمل على المنفذ `3306`.
- Python 3.14 في حالة تشغيل خدمة AI Automation.
- اتصال إنترنت في أول تشغيل لتنزيل حزم الواجهات وPython عند الحاجة.

لا تحتاج لتثبيت Java أو Maven أو Node أو pnpm؛ النسخ المطلوبة موجودة داخل مجلد `tools`.

## 3. إنشاء قاعدة البيانات المحلية

أثناء تثبيت MySQL اختر كلمة سر لحساب `root` واحتفظ بها على جهازك.

من جذر المشروع شغّل:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
.\scripts\Setup-LocalDatabase.ps1
```

سيطلب السكربت:

1. كلمة سر جديدة لمستخدم التطبيق `hse_app`.
2. كلمة سر جديدة لمستخدم Automation للقراءة فقط `esca_automation_ro`.
3. كلمة سر MySQL المحلية لحساب `root` لتنفيذ الإنشاء.

السكربت ينشئ تلقائيًا:

- قاعدة البيانات `esca_hse`.
- مستخدم `hse_app` بصلاحيات التطبيق داخل قاعدة المشروع فقط.
- مستخدم `esca_automation_ro` بصلاحيات `SELECT` و`SHOW VIEW` فقط.

لا تستخدم حساب `root` لتشغيل المشروع أو ربط الـAgent.

## 4. تشغيل Spring Boot Backend

من جذر المشروع:

```powershell
.\scripts\Start-Backend.ps1
```

عند الطلب، اكتب كلمة سر `hse_app` التي اخترتها في الخطوة السابقة.

انتظر حتى يبدأ Spring، ثم افتح:

```text
http://localhost:8080/api/v1/health
```

النتيجة الصحيحة تحتوي على:

```json
{
  "status": "ready",
  "database": "connected"
}
```

يجب إبقاء Terminal الباك إند مفتوحًا أثناء استخدام المشروع.

## 5. تشغيل لوحة الإدارة

افتح Terminal جديد من جذر المشروع وشغّل:

```powershell
.\scripts\Start-Admin.ps1
```

ثم افتح:

```text
http://localhost:3100
```

## 6. تشغيل Field PWA

افتح Terminal جديد من جذر المشروع وشغّل:

```powershell
.\scripts\Start-Field.ps1
```

ثم افتح:

```text
http://localhost:3200
```

## 7. تشغيل AI Automation اختياريًا

ابدأ بإعداد بيئة الخدمة:

```powershell
.\scripts\Start-Automation.ps1 -Mode Setup
```

افتح الملف:

```text
services\automation\.env
```

ضع فيه كلمة سر مستخدم `esca_automation_ro` فقط، واترك الإرسال الحقيقي مغلقًا:

```dotenv
AUTOMATION_DELIVERY_MODE=dry_run
AUTOMATION_LIVE_ENABLED=false
```

ثم شغّل الاختبارات والخدمة:

```powershell
.\scripts\Start-Automation.ps1 -Mode Test
.\scripts\Start-Automation.ps1 -Mode Api
```

روابط الخدمة:

```text
http://127.0.0.1:8000/health/ready
http://127.0.0.1:8000/docs
```

## 8. ربط الـAgent

الربط الموصى به:

```text
Agent -> Spring REST API -> MySQL
```

استخدم داخل إعدادات الـAgent:

```text
API_BASE_URL=http://localhost:8080
```

لا تجعل الـAgent يكتب مباشرة في MySQL؛ Spring مسؤول عن التحقق من البيانات، الصلاحيات، قواعد العمل وسجل العمليات.

راجع الملفات التالية قبل الربط:

```text
docs\API_CONTRACT.md
services\automation\docs\SPRING_INTEGRATION_CONTRACT.md
docs\TEAM_HANDOFF_AR.md
```

في التشغيل المحلي الأول يمكن إبقاء:

```text
APP_SECURITY_ENABLED=false
```

وعند اختبار المصادقة يتم تفعيل الحماية واستخدام JWT من خلال Spring API.

إذا احتاج الـAgent قراءة SQL بشكل مباشر لأغراض تحليلية، أنشئ له مستخدمًا منفصلًا بصلاحية `SELECT` فقط. لا تستخدم `root` أو `hse_app` لهذا الغرض.

## 9. استخدام قاعدة Cloud لاحقًا

اختبر النظام كاملًا على قاعدة محلية أولًا. عند الانتقال إلى Cloud:

1. خذ نسخة احتياطية من القاعدة.
2. غيّر أي كلمة سر تم تداولها سابقًا.
3. أنشئ مستخدم تطبيق محدود بدل `root`.
4. أنشئ مستخدم Automation للقراءة فقط.
5. أرسل بيانات الاتصال عبر قناة خاصة وآمنة، وليس داخل ZIP أو Git.

القيم المطلوبة للاتصال بالـCloud هي:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USERNAME
DB_PASSWORD
TLS/SSL requirement
```

## 10. فحص النظام

بعد تشغيل الباك إند والواجهتين، شغّل من جذر المشروع:

```powershell
.\scripts\Verify-LocalSystem.ps1
```

## 11. حل الأخطاء الشائعة

- `pnpm is not recognized`: استخدم `Start-Admin.ps1` أو `Start-Field.ps1` بدل تشغيل `pnpm` يدويًا.
- `mvn.cmd is not recognized`: استخدم `Start-Backend.ps1` من جذر المشروع.
- `Access denied`: تأكد أنك تستخدم كلمة سر `hse_app` مع Spring، وكلمة سر `esca_automation_ro` مع Automation.
- `Unknown database esca_hse`: شغّل `Setup-LocalDatabase.ps1` أولًا.
- الواجهة تعرض `Disconnected`: تأكد أن الباك إند يعمل على port `8080`.
- المنفذ مستخدم: أغلق النسخة القديمة قبل تشغيل نسخة جديدة.

## ملاحظات أمان مهمة

- لا ترسل ملفات `.env` لأي شخص.
- لا ترفع كلمات السر إلى GitHub.
- لا تستخدم حساب MySQL `root` داخل التطبيق أو الـAgent.
- لا تشغّل الإرسال الحقيقي لخدمة Automation قبل مراجعة الفريق؛ اتركها في وضع `dry_run`.
