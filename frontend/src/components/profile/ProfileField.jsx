/**
 * One profile field row: label above, value + edit icon inline below.
 *
 * `editable = false` renders a permanently read-only row with no edit icon
 * (used for job_title, zone_name, department_name per the spec — those are
 * the manager's responsibility, not user-editable here).
 *
 * For editable fields: the edit icon just UNLOCKS the row into an input
 * (matches the hand-drawn sketch, which has both per-field edit icons AND
 * one shared Save button at the bottom of the whole form). Nothing is sent
 * to the server from this component — the parent owns the draft value and
 * decides when to save, via the bottom Save button.
 */
export default function ProfileField({
  label,
  value,
  editable = true,
  masked = false,
  unlocked,
  onUnlock,
  onChange,
  fullWidth = false,
  numeric = false,
  maxLength,
}) {
  return (
    <div className={fullWidth ? 'field field-row-full' : 'field'}>
      <span className="field-label">{label}</span>
      <div className={`field-value-row${editable ? '' : ' readonly'}`}>
        {unlocked ? (
          <input
            className="field-input"
            value={value}
            type={masked ? 'password' : numeric ? 'tel' : 'text'}
            inputMode={numeric ? 'numeric' : undefined}
            pattern={numeric ? '[0-9]*' : undefined}
            maxLength={maxLength}
            autoFocus
            onChange={(e) => onChange(numeric ? e.target.value.replace(/\D/g, '') : e.target.value)}
          />
        ) : (
          <span className="field-value-text">{masked ? (value ? '*********' : '') : value}</span>
        )}

        {editable && !unlocked && (
          <button type="button" className="field-icon-btn" onClick={onUnlock} title="تعديل">
            ✎
          </button>
        )}
      </div>
    </div>
  )
}
