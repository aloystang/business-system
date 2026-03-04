import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Login from './pages/Login'
import Overview from './pages/Overview'
import PlanningOverview from './pages/PlanningOverview'
import PlanningCollect from './pages/PlanningCollect'
import PlanningScreeningHistory from './pages/PlanningScreeningHistory'
import PlanningScreeningWorkbench from './pages/PlanningScreeningWorkbench'
import PlanningCalc from './pages/PlanningCalc'
import PlanningMerchant from './pages/PlanningMerchant'
import PlanningCompetitor from './pages/PlanningCompetitor'
import ProjectDetail from './pages/ProjectDetail'
import Management from './pages/Management'
import Leasing from './pages/Leasing'
import Operations from './pages/Operations'
import SectionModulePage from './pages/SectionModulePage'
import Settings from './pages/Settings'
import Profile from './pages/Profile'
import IntelNews from './pages/IntelNews'
import IntelTenders from './pages/IntelTenders'
import { leasingModules, managementModules, operationsModules } from './data/modules'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/overview" replace />} />
      <Route path="/projects" element={<Navigate to="/planning" replace />} />
      <Route path="/projects/:projectId" element={<ProjectDetail />} />
      <Route path="/overview" element={<Overview />} />
      <Route path="/planning" element={<PlanningOverview />} />
      <Route path="/planning/new" element={<Navigate to="/planning/new/collect" replace />} />
      <Route path="/planning/new/collect" element={<PlanningCollect />} />
      <Route path="/planning/new/screening" element={<PlanningScreeningWorkbench />} />
      <Route path="/planning/new/calc" element={<PlanningCalc />} />
      <Route path="/planning/history" element={<PlanningScreeningHistory />} />
      <Route path="/planning/merchant" element={<PlanningMerchant />} />
      <Route path="/planning/competitor" element={<PlanningCompetitor />} />
      <Route path="/planning/collect" element={<Navigate to="/planning/new/collect" replace />} />
      <Route path="/planning/screening" element={<Navigate to="/planning/new/screening" replace />} />
      <Route path="/planning/screening/workbench" element={<Navigate to="/planning/new/screening" replace />} />
      <Route path="/planning/screening/history" element={<Navigate to="/planning/history" replace />} />
      <Route path="/planning/calc" element={<Navigate to="/planning/new/calc" replace />} />
      <Route path="/management" element={<Management />} />
      <Route
        path="/management/:moduleId"
        element={
          <SectionModulePage
            sectionTitle="管理咨询"
            overline="MANAGEMENT"
            modules={managementModules}
            basePath="/management"
          />
        }
      />
      <Route path="/leasing" element={<Leasing />} />
      <Route
        path="/leasing/:moduleId"
        element={
          <SectionModulePage
            sectionTitle="招商运营"
            overline="LEASING"
            modules={leasingModules}
            basePath="/leasing"
          />
        }
      />
      <Route path="/operations" element={<Operations />} />
      <Route
        path="/operations/:moduleId"
        element={
          <SectionModulePage
            sectionTitle="委托运营"
            overline="OPERATIONS"
            modules={operationsModules}
            basePath="/operations"
          />
        }
      />
      <Route path="/settings" element={<Settings />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/intel" element={<IntelNews />} />
      <Route path="/intel/news" element={<IntelNews />} />
      <Route path="/intel/tenders" element={<IntelTenders />} />
      <Route path="/intel/items/:itemId" element={<Navigate to="/intel" replace />} />
      <Route path="/intel/rules" element={<Navigate to="/intel" replace />} />
      <Route path="/intel/sync" element={<Navigate to="/intel" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
