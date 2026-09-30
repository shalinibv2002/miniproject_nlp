import { useParams } from "react-router-dom";
import DrillFlow from "../../components/DrillFlow";
import { publicDepartmentLabel } from "../../lib/linkedin";

export default function DepartmentFlow() {
  const { dept = "" } = useParams();
  const label = publicDepartmentLabel(dept);
  return (
    <DrillFlow
      department={dept}
      title={label}
      intro={`Activities credited to ${label}. Drill through academic period, category and stakeholder to see the matching activities — the count above each list always matches the records shown.`}
      backTo="/departments"
      backLabel="All departments"
    />
  );
}