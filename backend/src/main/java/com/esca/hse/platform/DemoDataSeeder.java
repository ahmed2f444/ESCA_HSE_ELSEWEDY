package com.esca.hse.platform;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
@Order(20)
public class DemoDataSeeder implements CommandLineRunner {
    private final NamedParameterJdbcTemplate jdbc;
    private final boolean enabled;

    public DemoDataSeeder(@org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc,
            @Value("${app.demo-data.enabled:true}") boolean enabled) {
        this.jdbc = jdbc;
        this.enabled = enabled;
    }

    @Override
    @Transactional
    public void run(String... args) {
        if (!enabled) return;

        insert("departments", "department_id", "DEP-HSE",
                "INSERT INTO departments (department_id, department_code, department_name, location) VALUES (:id,'HSE','إدارة السلامة والصحة المهنية','المقر الرئيسي')", Map.of());
        insert("departments", "department_id", "DEP-OPS",
                "INSERT INTO departments (department_id, department_code, department_name, location) VALUES (:id,'OPS','التشغيل والإنتاج','مصنع الكابلات')", Map.of());
        insert("departments", "department_id", "DEP-WHS",
                "INSERT INTO departments (department_id, department_code, department_name, location) VALUES (:id,'WHS','المخازن واللوجستيات','المخزن الرئيسي')", Map.of());

        insert("zones", "zone_id", "ZON-CABLE",
                "INSERT INTO zones (zone_id, zone_code, zone_name, department_id, risk_level) VALUES (:id,'CBL-01','خط إنتاج الكابلات','DEP-OPS','HIGH')", Map.of());
        insert("zones", "zone_id", "ZON-TRANSFORMER",
                "INSERT INTO zones (zone_id, zone_code, zone_name, department_id, risk_level, restricted_access) VALUES (:id,'TRF-03','منطقة المحولات T3','DEP-OPS','CRITICAL',TRUE)", Map.of());
        insert("zones", "zone_id", "ZON-WAREHOUSE",
                "INSERT INTO zones (zone_id, zone_code, zone_name, department_id, risk_level) VALUES (:id,'WHS-01','مخزن المواد الخام','DEP-WHS','MEDIUM')", Map.of());

        insert("employees", "employee_id", "EMP-001",
                "INSERT INTO employees (employee_id, employee_code, full_name, email, job_title, department_id, status, hire_date) VALUES (:id,'E001','أحمد حسن','ahmed.hassan@example.test','مشرف سلامة','DEP-HSE','ACTIVE',:date)", Map.of("date", LocalDate.of(2022, 2, 1)));
        insert("employees", "employee_id", "EMP-002",
                "INSERT INTO employees (employee_id, employee_code, full_name, email, job_title, department_id, manager_id, status, hire_date) VALUES (:id,'E002','سارة علي','sara.ali@example.test','أخصائي HSE','DEP-HSE','EMP-001','ACTIVE',:date)", Map.of("date", LocalDate.of(2023, 5, 10)));
        insert("employees", "employee_id", "EMP-003",
                "INSERT INTO employees (employee_id, employee_code, full_name, email, job_title, department_id, status, hire_date) VALUES (:id,'E003','محمود عمر','mahmoud.omar@example.test','مشرف إنتاج','DEP-OPS','ACTIVE',:date)", Map.of("date", LocalDate.of(2020, 9, 15)));

        LocalDateTime now = LocalDateTime.now();
        insert("incidents", "incident_id", "INC-2026-0142",
                "INSERT INTO incidents (incident_id, incident_type, title, description, department_id, zone_id, reported_by, occurred_at, severity, status, immediate_action) VALUES (:id,'NEAR_MISS','انزلاق بدون إصابة','أرضية رطبة قرب منطقة التشغيل','DEP-OPS','ZON-CABLE','EMP-002',:occurred,'MEDIUM','INVESTIGATING','تم عزل المنطقة وتجفيفها')", Map.of("occurred", now.minusHours(3)));
        insert("incidents", "incident_id", "INC-2026-0143",
                "INSERT INTO incidents (incident_id, incident_type, title, description, department_id, zone_id, reported_by, occurred_at, severity, status) VALUES (:id,'OBSERVATION','ممر طوارئ غير واضح','تحتاج علامات الأرضية إلى إعادة طلاء','DEP-WHS','ZON-WAREHOUSE','EMP-001',:occurred,'LOW','OPEN')", Map.of("occurred", now.minusDays(1)));
        insert("incidents", "incident_id", "INC-2026-0144",
                "INSERT INTO incidents (incident_id, incident_type, title, description, department_id, zone_id, reported_by, occurred_at, severity, status) VALUES (:id,'NEAR_MISS','سقوط جسم بالقرب من عامل','تم منع الدخول وفحص الرفوف','DEP-WHS','ZON-WAREHOUSE','EMP-003',:occurred,'HIGH','OPEN')", Map.of("occurred", now.minusDays(2)));

        insert("jsa", "jsa_id", "JSA-2026-001",
                "INSERT INTO jsa (jsa_id,title,activity,department_id,zone_id,prepared_by,hazards,controls,required_ppe,risk_level,status,review_date) VALUES (:id,'أعمال صيانة لوحة كهربائية','عزل وفحص لوحة الجهد','DEP-OPS','ZON-TRANSFORMER','EMP-001','صدمة كهربائية، قوس كهربائي','LOTO، اختبار انعدام الجهد، تصريح عمل','خوذة، نظارة، قفازات عازلة','HIGH','APPROVED',:review)", Map.of("review", LocalDate.now().plusMonths(6)));
        insert("jsa", "jsa_id", "JSA-2026-002",
                "INSERT INTO jsa (jsa_id,title,activity,department_id,zone_id,prepared_by,hazards,controls,required_ppe,risk_level,status,review_date) VALUES (:id,'عمل ساخن بخط الإنتاج','لحام وإصلاح قاعدة معدنية','DEP-OPS','ZON-CABLE','EMP-002','شرر، حريق، أبخرة','مراقب حريق، ستارة لحام، تهوية','درع وجه، قفازات لحام','HIGH','DRAFT',:review)", Map.of("review", LocalDate.now().plusMonths(3)));

        insert("permits", "permit_id", "PTW-2026-0418",
                "INSERT INTO permits (permit_id,permit_type,department_id,zone_id,work_description,requester_id,issuer_id,executor_type,executor_name,start_at,expiry_at,risk_level,jsa_id,status) VALUES (:id,'HOT_WORK','DEP-OPS','ZON-CABLE','لحام قاعدة حماية الماكينة','EMP-003','EMP-001','INTERNAL','فريق الصيانة',:start,:expiry,'HIGH','JSA-2026-002','ACTIVE')", Map.of("start", now.minusHours(1), "expiry", now.plusHours(2)));
        insert("permits", "permit_id", "PTW-2026-0419",
                "INSERT INTO permits (permit_id,permit_type,department_id,zone_id,work_description,requester_id,executor_type,executor_name,start_at,expiry_at,risk_level,jsa_id,status) VALUES (:id,'ELECTRICAL','DEP-OPS','ZON-TRANSFORMER','فحص نقطة ربط لوحة الجهد','EMP-003','CONTRACTOR','Delta Maintenance',:start,:expiry,'CRITICAL','JSA-2026-001','REQUESTED')", Map.of("start", now.plusHours(2), "expiry", now.plusHours(8)));

        insert("risk_register", "risk_id", "RSK-2026-001",
                "INSERT INTO risk_register (risk_id,department_id,zone_id,hazard,activity,likelihood,severity,inherent_score,risk_level,controls,residual_likelihood,residual_severity,residual_score,owner_id,status,last_reviewed_at,next_review_date) VALUES (:id,'DEP-OPS','ZON-TRANSFORMER','التعرض لطاقة كهربائية','أعمال الصيانة',4,5,20,'CRITICAL','عزل الطاقة وLOTO وتصريح خاص',1,5,5,'EMP-001','OPEN',:last,:next)", Map.of("last", LocalDate.now().minusDays(45), "next", LocalDate.now().minusDays(15)));
        insert("risk_register", "risk_id", "RSK-2026-002",
                "INSERT INTO risk_register (risk_id,department_id,zone_id,hazard,activity,likelihood,severity,inherent_score,risk_level,controls,residual_likelihood,residual_severity,residual_score,owner_id,status,last_reviewed_at,next_review_date) VALUES (:id,'DEP-WHS','ZON-WAREHOUSE','سقوط مواد من الرفوف','التخزين والمناولة',3,4,12,'HIGH','حدود تحميل وفحص أسبوعي',2,3,6,'EMP-003','OPEN',:last,:next)", Map.of("last", LocalDate.now().minusDays(10), "next", LocalDate.now().plusDays(20)));

        insert("inspections", "inspection_id", "INS-2026-0211",
                "INSERT INTO inspections (inspection_id,inspection_type,title,department_id,zone_id,inspector_id,scheduled_at,status,notes) VALUES (:id,'WEEKLY','جولة سلامة أسبوعية','DEP-WHS','ZON-WAREHOUSE','EMP-002',:scheduled,'IN_PROGRESS','فحص المخارج والرفوف ومعدات المناولة')", Map.of("scheduled", now.plusHours(4)));
        insert("inspections", "inspection_id", "INS-2026-0212",
                "INSERT INTO inspections (inspection_id,inspection_type,title,department_id,zone_id,inspector_id,scheduled_at,status) VALUES (:id,'FIRE','فحص معدات الحريق','DEP-OPS','ZON-CABLE','EMP-001',:scheduled,'SCHEDULED')", Map.of("scheduled", now.plusDays(1)));
        insert("inspection_findings", "finding_id", "FND-2026-001",
                "INSERT INTO inspection_findings (finding_id,inspection_id,category,description,severity,status) VALUES (:id,'INS-2026-0211','HOUSEKEEPING','إعادة تحديد ممر الطوارئ','MEDIUM','OPEN')", Map.of());

        insert("capa", "capa_id", "CAPA-2026-0083",
                "INSERT INTO capa (capa_id,incident_id,finding_id,title,action_type,priority,assigned_to,due_date,status) VALUES (:id,'INC-2026-0143','FND-2026-001','إعادة طلاء وتحديد ممر الطوارئ','CORRECTIVE','HIGH','EMP-003',:due,'OPEN')", Map.of("due", LocalDate.now().minusDays(2)));
        insert("capa", "capa_id", "CAPA-2026-0084",
                "INSERT INTO capa (capa_id,incident_id,title,action_type,priority,assigned_to,due_date,status) VALUES (:id,'INC-2026-0142','مراجعة خطة منع الانزلاق','PREVENTIVE','MEDIUM','EMP-002',:due,'IN_PROGRESS')", Map.of("due", LocalDate.now().plusDays(5)));

        insert("chemicals", "chemical_id", "CHM-001",
                "INSERT INTO chemicals (chemical_id,chemical_name,cas_number,department_id,zone_id,quantity,unit,hazard_class,storage_requirements,sds_url,expiry_date,status) VALUES (:id,'أسيتون','67-64-1','DEP-OPS','ZON-CABLE',120,'L','FLAMMABLE','خزانة مواد قابلة للاشتعال','/documents/sds/acetone.pdf',:expiry,'ACTIVE')", Map.of("expiry", LocalDate.now().plusYears(1)));
        insert("health_exams", "exam_id", "HEX-001",
                "INSERT INTO health_exams (exam_id,employee_id,exam_type,exam_date,next_exam_date,fitness_status,provider,status) VALUES (:id,'EMP-003','PERIODIC',:exam,:next,'FIT','ESCA Medical Center','COMPLETED')", Map.of("exam", LocalDate.now().minusMonths(6), "next", LocalDate.now().plusMonths(6)));

        insert("training_courses", "course_id", "CRS-001",
                "INSERT INTO training_courses (course_id,course_code,course_name,validity_months,provider,mandatory) VALUES (:id,'FIRE-101','مكافحة الحريق والإخلاء',12,'ESCA Academy',TRUE)", Map.of());
        insert("training_courses", "course_id", "CRS-002",
                "INSERT INTO training_courses (course_id,course_code,course_name,validity_months,provider,mandatory) VALUES (:id,'LOTO-201','العزل وتأمين مصادر الطاقة LOTO',24,'ESCA Academy',TRUE)", Map.of());
        insert("certificates", "certificate_id", "CERT-001",
                "INSERT INTO certificates (certificate_id,employee_id,course_id,issue_date,expiry_date,certificate_number,provider,status) VALUES (:id,'EMP-001','CRS-001',:issue,:expiry,'ESCA-FIRE-001','ESCA Academy','VALID')", Map.of("issue", LocalDate.now().minusMonths(11), "expiry", LocalDate.now().plusDays(20)));
        insert("certificates", "certificate_id", "CERT-002",
                "INSERT INTO certificates (certificate_id,employee_id,course_id,issue_date,expiry_date,certificate_number,provider,status) VALUES (:id,'EMP-003','CRS-002',:issue,:expiry,'ESCA-LOTO-002','ESCA Academy','EXPIRED')", Map.of("issue", LocalDate.now().minusYears(2), "expiry", LocalDate.now().minusDays(7)));

        insert("notifications", "notification_id", "NTF-001",
                "INSERT INTO notifications (notification_id,recipient_employee_id,type,title,message,entity_type,entity_id,status) VALUES (:id,'EMP-001','PERMIT_EXPIRY','تصريح عمل ينتهي قريبًا','ينتهي التصريح PTW-2026-0418 خلال ساعتين','PERMIT','PTW-2026-0418','UNREAD')", Map.of());
        insert("notifications", "notification_id", "NTF-002",
                "INSERT INTO notifications (notification_id,recipient_employee_id,type,title,message,entity_type,entity_id,status) VALUES (:id,'EMP-002','INSPECTION_ASSIGNED','تم إسناد جولة تفتيش','جولة المخزن الأسبوعية جاهزة للبدء','INSPECTION','INS-2026-0211','UNREAD')", Map.of());

        insert("automation_rules", "rule_id", "AUT-001",
                "INSERT INTO automation_rules (rule_id,rule_name,entity_type,trigger_type,schedule_cron,conditions_json,action_type,action_endpoint,active) VALUES (:id,'متابعة التصاريح المتأخرة','PERMIT','SCHEDULE','*/5 * * * *','{\"status\":\"ACTIVE\"}','CREATE_NOTIFICATION','/api/v1/internal/automation/actions',TRUE)", Map.of());
        insert("automation_rules", "rule_id", "AUT-002",
                "INSERT INTO automation_rules (rule_id,rule_name,entity_type,trigger_type,schedule_cron,conditions_json,action_type,action_endpoint,active) VALUES (:id,'تنبيه انتهاء الشهادات','CERTIFICATE','SCHEDULE','0 8 * * *','{\"days\":[30,14,7,0]}','CREATE_NOTIFICATION','/api/v1/internal/automation/actions',TRUE)", Map.of());
        insert("automation_rules", "rule_id", "AUT-003",
                "INSERT INTO automation_rules (rule_id,rule_name,entity_type,trigger_type,schedule_cron,conditions_json,action_type,action_endpoint,active) VALUES (:id,'تصعيد CAPA المتأخر','CAPA','SCHEDULE','0 9 * * *','{\"days\":[1,3,7]}','CREATE_NOTIFICATION','/api/v1/internal/automation/actions',TRUE)", Map.of());
        insert("automation_rules", "rule_id", "AUT-004",
                "INSERT INTO automation_rules (rule_id,rule_name,entity_type,trigger_type,schedule_cron,conditions_json,action_type,action_endpoint,active) VALUES (:id,'مراجعة المخاطر المرتفعة','RISK','SCHEDULE','0 7 * * 1','{\"review_age_days\":30}','CREATE_NOTIFICATION','/api/v1/internal/automation/actions',TRUE)", Map.of());

        insert("sensor_events", "sensor_event_id", "SNS-001",
                "INSERT INTO sensor_events (sensor_event_id,sensor_type,zone_id,reading_value,reading_unit,threshold_value,alert_level,source,recorded_at) VALUES (:id,'TEMPERATURE','ZON-CABLE',38.5,'C',45,'NORMAL','SIMULATED',:recorded)", Map.of("recorded", now.minusMinutes(3)));

        insert("ppe_inventory", "ppe_item_id", "PPE-1001",
                "INSERT INTO ppe_inventory (ppe_item_id,item_code,name_ar,category_id,unit,balance_qty,reorder_threshold,monthly_consumption,supplier,storage_zone_id) VALUES (:id,'HLM-001','خوذة أمان','HEAD','قطعة',84,20,18,'SafePro','ZON-WAREHOUSE')", Map.of());
        insert("ppe_inventory", "ppe_item_id", "PPE-1002",
                "INSERT INTO ppe_inventory (ppe_item_id,item_code,name_ar,category_id,unit,balance_qty,reorder_threshold,monthly_consumption,supplier,storage_zone_id) VALUES (:id,'GLV-ELC','قفازات عازلة','HANDS','زوج',12,15,8,'ElectroSafe','ZON-WAREHOUSE')", Map.of());
        insert("ppe_matrix", "matrix_id", "PPM-001",
                "INSERT INTO ppe_matrix (matrix_id,zone_id,ppe_item_id,required_flag,notes) VALUES (:id,'ZON-TRANSFORMER','PPE-1001',1,'إلزامي قبل الدخول')", Map.of());

        insert("fire_equipment", "equipment_id", "FIRE-EXT-001",
                "INSERT INTO fire_equipment (equipment_id,asset_type_id,subtype,department_id,zone_id,location_detail,capacity,installation_date,expiry_date,status,vendor,qr_code,last_inspection_date,next_inspection_date) VALUES (:id,'EXTINGUISHER','CO2','DEP-OPS','ZON-CABLE','بجوار لوحة التحكم','6 kg',:installed,:expiry,'ACTIVE','FireSafe','QR-FIRE-EXT-001',:last,:next)", Map.of("installed", LocalDate.now().minusYears(2), "expiry", LocalDate.now().plusYears(3), "last", LocalDate.now().minusDays(20), "next", LocalDate.now().plusDays(10)));
        insert("fire_equipment", "equipment_id", "FIRE-EXT-002",
                "INSERT INTO fire_equipment (equipment_id,asset_type_id,subtype,department_id,zone_id,location_detail,capacity,installation_date,expiry_date,status,vendor,qr_code,last_inspection_date,next_inspection_date) VALUES (:id,'EXTINGUISHER','DRY_POWDER','DEP-WHS','ZON-WAREHOUSE','مدخل المخزن','9 kg',:installed,:expiry,'ACTIVE','FireSafe','QR-FIRE-EXT-002',:last,:next)", Map.of("installed", LocalDate.now().minusYears(1), "expiry", LocalDate.now().plusYears(4), "last", LocalDate.now().minusDays(28), "next", LocalDate.now().plusDays(2)));
        insert("fire_inspections", "id", "FINSP-001",
                "INSERT INTO fire_inspections (id,equipment_id,inspection_date,inspector_name,status,notes) VALUES (:id,'FIRE-EXT-001',:date,'سارة علي','PASSED','الضغط والختم بحالة جيدة')", Map.of("date", LocalDate.now().minusDays(20)));
        insert("fixed_safety_assets", "id", "FSA-001",
                "INSERT INTO fixed_safety_assets (id,asset_name,asset_type,zone_id,location_detail,status) VALUES (:id,'محطة غسيل عين 1','EYEWASH_STATION','ZON-CABLE','بوابة خط الإنتاج','OPERATIONAL')", Map.of());
    }

    private void insert(String table, String idColumn, String id, String sql, Map<String, ?> values) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM " + table + " WHERE " + idColumn + " = :id", Map.of("id", id), Integer.class);
        if (count != null && count > 0) return;
        Map<String, Object> parameters = new LinkedHashMap<>();
        parameters.put("id", id);
        parameters.putAll(values);
        jdbc.update(sql, parameters);
    }
}
