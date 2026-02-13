function asText(value, fallback = '') {
  const text = String(value ?? '').trim()
  return text || fallback
}

export function normalizeUser(raw) {
  const item = raw && typeof raw === 'object' ? raw : {}
  const socialSource = item.social_accounts && typeof item.social_accounts === 'object'
    ? item.social_accounts
    : item.socialAccounts && typeof item.socialAccounts === 'object'
      ? item.socialAccounts
      : {}

  const socialAccounts = Object.fromEntries(
    Object.entries(socialSource)
      .map(([k, v]) => [asText(k), asText(v)])
      .filter(([k, v]) => k && v),
  )

  return {
    id: asText(item.id || item._id),
    username: asText(item.username),
    email: asText(item.email),
    display_name: asText(item.display_name || item.displayName || item.username),
    bio: asText(item.bio),
    avatar_image: asText(item.avatar_image || item.avatarImage),
    social_accounts: socialAccounts,
    follow_requires_approval: Boolean(item.follow_requires_approval ?? item.followRequiresApproval),
    created_at: asText(item.created_at || item.createdAt),
  }
}
