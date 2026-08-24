import { Component } from 'react'
import { Link } from 'react-router-dom'
import Icon from './Icon.jsx'
import { Btn } from './ui.jsx'

/**
 * Keeps one broken screen from taking the whole console down.
 *
 * Without this, a single unexpected value in one row throws during render,
 * React unmounts the entire tree, and the operator is left staring at a blank
 * page with no nav and no way back — on every route, not just the broken one.
 * A plant console has to degrade one screen at a time.
 *
 * Resets when the route changes, so navigating away actually recovers.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidUpdate(prevProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null })
    }
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="py-16 text-center">
        <Icon name="incident" size={36} className="mx-auto text-crit opacity-70 mb-4" />
        <h2 className="text-lg font-semibold">تعذّر عرض هذه الشاشة</h2>
        <p className="text-sm text-txt-2 mt-2 leading-7 max-w-lg mx-auto">
          حصل خطأ أثناء رسم الشاشة دي. باقي شاشات النظام شغّالة عادي — تقدر ترجع للوحة القيادة
          أو تجرّب تاني.
        </p>

        <pre
          className="mt-5 mx-auto max-w-xl overflow-x-auto text-start text-2xs font-mono num p-3 rounded border"
          style={{ background: 'rgba(224,72,60,.08)', borderColor: 'rgba(224,72,60,.35)', color: '#f08b82' }}
        >
          {String(error?.message || error)}
        </pre>

        <div className="flex gap-2.5 justify-center mt-5">
          <Btn icon="refresh" onClick={() => this.setState({ error: null })}>
            إعادة المحاولة
          </Btn>
          <Link to="/" className="btn btn-pri">
            لوحة القيادة
          </Link>
        </div>
      </div>
    )
  }
}
