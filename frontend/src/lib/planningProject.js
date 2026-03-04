const PLANNING_PROJECT_KEY = 'planning_selected_project_id'

export function getSelectedPlanningProjectId() {
  return window.localStorage.getItem(PLANNING_PROJECT_KEY) || ''
}

export function setSelectedPlanningProjectId(projectId) {
  if (!projectId) {
    window.localStorage.removeItem(PLANNING_PROJECT_KEY)
    return
  }
  window.localStorage.setItem(PLANNING_PROJECT_KEY, projectId)
}
