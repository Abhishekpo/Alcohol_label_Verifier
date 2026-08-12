export function formatStatus(status) {
  return status.replaceAll("_", " ");
}

export function formatFieldName(field) {
  return field
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not detected";
  }

  return String(value);
}