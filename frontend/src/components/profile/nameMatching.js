function compact(value) {
  return value.toLocaleLowerCase().replace(/[^\p{L}\p{N}]/gu, '')
}

function transliterateArabic(value) {
  const letters = {
    ا: 'a', أ: 'a', إ: 'a', آ: 'a', ب: 'b', ت: 't', ث: 'th', ج: 'j',
    ح: 'h', خ: 'kh', د: 'd', ذ: 'dh', ر: 'r', ز: 'z', س: 's', ش: 'sh',
    ص: 's', ض: 'd', ط: 't', ظ: 'z', ع: 'a', غ: 'gh', ف: 'f', ق: 'q',
    ك: 'k', ل: 'l', م: 'm', ن: 'n', ه: 'h', ة: 'a', و: 'u', ؤ: 'u',
    ي: 'i', ى: 'i', ئ: 'i',
  }
  return [...value].map((letter) => letters[letter] || '').join('')
}

function consonantsOnly(value) {
  return value.replace(/[aeiou]/g, '')
}

export function containsNamePart(value, fullName) {
  if (!value || !fullName) return false
  const normalizedValue = compact(value)
  const normalizedName = compact(fullName)
  if (normalizedValue.includes(normalizedName)) return true

  return fullName.trim().toLocaleLowerCase().split(/\s+/).some((part) => {
    const normalizedPart = compact(part)
    if (normalizedPart && normalizedValue.includes(normalizedPart)) return true
    const arabicPart = [...part].filter((letter) => /[\u0600-\u06ff]/.test(letter)).join('')
    if (!arabicPart) return false
    const transliterated = transliterateArabic(arabicPart)
    return normalizedValue.includes(transliterated)
      || consonantsOnly(normalizedValue).includes(consonantsOnly(transliterated))
  })
}
