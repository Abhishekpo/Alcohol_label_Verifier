import { formatStatus } from "../utils/formatter";

function StatusBadge({ status }) {
  return (
    <span className={`status-badge ${status.toLowerCase()}`}>
      {formatStatus(status)}
    </span>
  );
}

export default StatusBadge;