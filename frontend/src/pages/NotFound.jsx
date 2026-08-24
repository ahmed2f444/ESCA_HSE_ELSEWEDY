import { Link } from 'react-router-dom'
import Icon from '../components/Icon.jsx'

export default function NotFound() {
  return (
    <div className="py-24 text-center">
      <Icon name="search" size={38} className="mx-auto text-txt-3 opacity-50 mb-4" />
      <h2 className="text-lg font-semibold">الصفحة غير موجودة</h2>
      <p className="text-sm text-txt-3 font-mono num mt-1.5">404 · ROUTE NOT FOUND</p>
      <Link to="/" className="btn btn-pri inline-flex mt-6">
        العودة للوحة القيادة
      </Link>
    </div>
  )
}
