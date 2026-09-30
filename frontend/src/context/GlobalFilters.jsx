import { createContext, useContext, useMemo, useState } from "react";

const GlobalFiltersContext = createContext(null);

const DEFAULT_FILTERS = {
  period: "",
  department: "",
  category: "",
  generalCategory: "",
  departmentalCategory: "",
  stakeholder: "",
  order: "desc",
};

export function GlobalFiltersProvider({ children, initialFilters = DEFAULT_FILTERS }) {
  const [filters, setFilters] = useState(initialFilters);

  const value = useMemo(
    () => ({
      filters,
      setFilters,
      resetFilters: () => setFilters(DEFAULT_FILTERS),
    }),
    [filters]
  );

  return (
    <GlobalFiltersContext.Provider value={value}>
      {children}
    </GlobalFiltersContext.Provider>
  );
}

export function useGlobalFilters() {
  const ctx = useContext(GlobalFiltersContext);
  if (!ctx) throw new Error("useGlobalFilters must be used within provider");
  return ctx;
}
