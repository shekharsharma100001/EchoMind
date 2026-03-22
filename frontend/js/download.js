function downloadReport(format, fileId = currentFileId) {
    if (!fileId) {
        alert("No processed file available for download.");
        return;
    }

    const url = `/api/download/${fileId}/${format}`;
    window.open(url, "_blank");
}