import { page } from "$app/state"

// Option A: As a utility object (Cleaner syntax in templates)
export const auth = {
  get canEdit() {
    // Automatically reactive because 'page' is a rune
    return page.data.user?.role === "editor"
  },
  get user() {
    return page.data.user
  },
}

// Option B: As a function (If you prefer functional style)
export function getCanEdit() {
  return page.data.user?.role === "editor"
}
