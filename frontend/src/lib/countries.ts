/** Country phone dial codes for the OTP login screen. World-wide coverage. */
export interface CountryOption {
  name: string
  code: string
  dial: string
  flag: string
}

function flagEmoji(cc: string): string {
  return cc.toUpperCase().replace(/./g, (ch) => String.fromCodePoint(127397 + ch.charCodeAt(0)))
}

const RAW: [string, string, string][] = [
  ['United States', 'US', '+1'],
  ['Canada', 'CA', '+1'],
  ['United Kingdom', 'GB', '+44'],
  ['Pakistan', 'PK', '+92'],
  ['India', 'IN', '+91'],
  ['Afghanistan', 'AF', '+93'],
  ['Australia', 'AU', '+61'],
  ['Germany', 'DE', '+49'],
  ['France', 'FR', '+33'],
  ['Italy', 'IT', '+39'],
  ['Spain', 'ES', '+34'],
  ['Netherlands', 'NL', '+31'],
  ['Belgium', 'BE', '+32'],
  ['Switzerland', 'CH', '+41'],
  ['Sweden', 'SE', '+46'],
  ['Norway', 'NO', '+47'],
  ['Denmark', 'DK', '+45'],
  ['Finland', 'FI', '+358'],
  ['Poland', 'PL', '+48'],
  ['Russia', 'RU', '+7'],
  ['Ukraine', 'UA', '+380'],
  ['Turkey', 'TR', '+90'],
  ['Greece', 'GR', '+30'],
  ['Portugal', 'PT', '+351'],
  ['Ireland', 'IE', '+353'],
  ['Austria', 'AT', '+43'],
  ['Romania', 'RO', '+40'],
  ['Bulgaria', 'BG', '+359'],
  ['Croatia', 'HR', '+385'],
  ['Czech Republic', 'CZ', '+420'],
  ['Hungary', 'HU', '+36'],
  ['China', 'CN', '+86'],
  ['Japan', 'JP', '+81'],
  ['South Korea', 'KR', '+82'],
  ['Singapore', 'SG', '+65'],
  ['Malaysia', 'MY', '+60'],
  ['Thailand', 'TH', '+66'],
  ['Vietnam', 'VN', '+84'],
  ['Philippines', 'PH', '+63'],
  ['Indonesia', 'ID', '+62'],
  ['Bangladesh', 'BD', '+880'],
  ['Sri Lanka', 'LK', '+94'],
  ['Nepal', 'NP', '+977'],
  ['UAE', 'AE', '+971'],
  ['Saudi Arabia', 'SA', '+966'],
  ['Qatar', 'QA', '+974'],
  ['Kuwait', 'KW', '+965'],
  ['Bahrain', 'BH', '+973'],
  ['Oman', 'OM', '+968'],
  ['Jordan', 'JO', '+962'],
  ['Egypt', 'EG', '+20'],
  ['Morocco', 'MA', '+212'],
  ['Nigeria', 'NG', '+234'],
  ['Kenya', 'KE', '+254'],
  ['South Africa', 'ZA', '+27'],
  ['Brazil', 'BR', '+55'],
  ['Mexico', 'MX', '+52'],
  ['Argentina', 'AR', '+54'],
  ['Chile', 'CL', '+56'],
  ['Colombia', 'CO', '+57'],
  ['Peru', 'PE', '+51'],
  ['New Zealand', 'NZ', '+64'],
  ['Israel', 'IL', '+972'],
  ['Iran', 'IR', '+98'],
  ['Iraq', 'IQ', '+964'],
  ['Syria', 'SY', '+963'],
]

export const COUNTRIES: CountryOption[] = RAW.map(([name, code, dial]) => ({
  name,
  code,
  dial,
  flag: flagEmoji(code),
}))

export function getCountryByDial(dial: string): CountryOption | undefined {
  return COUNTRIES.find((c) => c.dial === dial)
}