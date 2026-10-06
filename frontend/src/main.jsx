import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import "./index.css";
import { GlobalFiltersProvider } from "./context/GlobalFilters";
import { AuthProvider, RequireAdmin } from "./context/Auth";
import AdminLayout from "./components/AdminLayout";
import LinkedinPublicLayout from "./components/LinkedinPublicLayout";
import LinkedinPublicDashboard from "./pages/linkedin/LinkedinPublicDashboard";
import LinkedinPublicActivityDetail from "./pages/linkedin/LinkedinPublicActivityDetail";
import LinkedinPublicCategories from "./pages/linkedin/LinkedinPublicCategories";
import LinkedinPublicDepartments from "./pages/linkedin/LinkedinPublicDepartments";
import LinkedinPublicReports from "./pages/linkedin/LinkedinPublicReports";
import LinkedinPublicQuery from "./pages/linkedin/LinkedinPublicQuery";
import GeneralCategoriesFlow from "./pages/linkedin/GeneralCategoriesFlow";
import DepartmentFlow from "./pages/linkedin/DepartmentFlow";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import AdminActivityList from "./pages/AdminActivityList";
import AdminActivityForm from "./pages/AdminActivityForm";
import AdminActivityDetail from "./pages/AdminActivityDetail";
import LinkedinAdminOverview from "./pages/linkedin/LinkedinAdminOverview";
import LinkedinAdminRecords from "./pages/linkedin/LinkedinAdminRecords";
import LinkedinAdminQueue from "./pages/linkedin/LinkedinAdminQueue";
import LinkedinAdminDetail from "./pages/linkedin/LinkedinAdminDetail";
import LinkedinAdminDepartmental from "./pages/linkedin/LinkedinAdminDepartmental";
import LinkedinAdminDepartmentalDetail from "./pages/linkedin/LinkedinAdminDepartmentalDetail";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <GlobalFiltersProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/admin/login" element={<Navigate to="/login" replace />} />

            <Route element={<LinkedinPublicLayout />}>
              <Route index element={<LinkedinPublicDashboard />} />
              <Route path="activities/:activityId" element={<LinkedinPublicActivityDetail />} />
              <Route path="categories" element={<LinkedinPublicCategories />} />
              <Route path="categories/general" element={<GeneralCategoriesFlow />} />
              <Route path="departments" element={<LinkedinPublicDepartments />} />
              <Route path="departments/:dept" element={<DepartmentFlow />} />
              <Route path="reports" element={<LinkedinPublicReports />} />
              <Route path="query" element={<LinkedinPublicQuery />} />
            </Route>

            <Route path="/admin" element={<RequireAdmin><AdminLayout /></RequireAdmin>}>
              <Route index element={<AdminDashboard />} />
              <Route path="activities" element={<AdminActivityList />} />
              <Route path="activities/new" element={<AdminActivityForm />} />
              <Route path="activities/:id" element={<AdminActivityDetail />} />
              <Route path="activities/:id/edit" element={<AdminActivityForm />} />
              <Route path="linkedin" element={<LinkedinAdminOverview />} />
              <Route path="linkedin/records" element={<LinkedinAdminRecords />} />
              <Route path="linkedin/records/:id" element={<LinkedinAdminDetail />} />
              <Route path="linkedin/review" element={<LinkedinAdminQueue />} />
              <Route path="linkedin/departmental" element={<LinkedinAdminDepartmental />} />
              <Route path="linkedin/departmental/:id" element={<LinkedinAdminDepartmentalDetail />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GlobalFiltersProvider>
  </StrictMode>
);