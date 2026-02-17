function asText(value) {
  return String(value || '')
}

export function readFileAsDataUrl(file, { errorMessage = 'Could not read image file' } = {}) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(errorMessage))
    reader.onload = () => resolve(asText(reader.result))
    reader.readAsDataURL(file)
  })
}

export async function readFileAsBase64(file, options = {}) {
  const out = await readFileAsDataUrl(file, options)
  const idx = out.indexOf(',')
  return idx >= 0 ? out.slice(idx + 1) : out
}
