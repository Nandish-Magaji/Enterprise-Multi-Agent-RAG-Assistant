import axios from "axios";
const API_URL = "/api/backend";

export async function downloadPdf(workflowId: string): Promise<void> {
  const response = await axios.get(`${API_URL}/workflows/${workflowId}/export/pdf`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `workflow-${workflowId}.pdf`;
  anchor.click();
  window.URL.revokeObjectURL(url);
}
