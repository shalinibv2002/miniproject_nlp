import DrillFlow from "../../components/DrillFlow";

export default function GeneralCategoriesFlow() {
  return (
    <DrillFlow
      scope="general"
      title="General Categories"
      intro="Institution-wide activities only. Drill through academic period, category and stakeholder to see the matching activities — the count above each list always matches the records shown."
      backTo="/categories"
      backLabel="All categories"
    />
  );
}