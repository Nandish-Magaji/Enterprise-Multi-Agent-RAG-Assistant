import axios from "axios";
const API_URL = "/api/backend";

export async function downloadMarkdown(workflowId: string): Promise<void> {
  const response = await axios.get(`${API_URL}/workflows/${workflowId}/export/markdown`, {
    responseType: "blob",
  });
  downloadBlob(response.data, `workflow-${workflowId}.md`);
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}
