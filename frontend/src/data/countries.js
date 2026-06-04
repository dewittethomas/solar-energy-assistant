export const countryOptions = [
  { code: 'BE', apiValue: 'Belgium', labelKey: 'countries.BE' },
  { code: 'NL', apiValue: 'Netherlands', labelKey: 'countries.NL' },
  { code: 'LU', apiValue: 'Luxembourg', labelKey: 'countries.LU' },
  { code: 'DE', apiValue: 'Germany', labelKey: 'countries.DE' },
]

export function countryCodeToApiValue(code) {
  return countryOptions.find((option) => option.code === code)?.apiValue || 'Belgium'
}

export function countryValueToCode(country) {
  return countryOptions.find((option) => option.apiValue === country)?.code || 'BE'
}
