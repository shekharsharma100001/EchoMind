let selectedFiles = [];
let currentFileId = null;
let currentUploadResponse = null;

function preventDefaults(event) {
    event.preventDefault();
    event.stopPropagation();
}

function highlightDropZone() {
    const dropZone = document.getElementById("drop-zone");
    if (dropZone) {
        dropZone.classList.add("drag-active");
    }
}

function unhighlightDropZone() {
    const dropZone = document.getElementById("drop-zone");
    if (dropZone) {
        dropZone.classList.remove("drag-active");
    }
}

function getFileTypeLabel(file) {
    if (!file) return "Unknown";

    const type = (file.type || "").toLowerCase();
    const name = file.name.toLowerCase();

    if (
        type.startsWith("audio/") ||
        [".mp3", ".wav", ".m4a", ".flac", ".aac"].some(ext => name.endsWith(ext))
    ) {
        return "Audio";
    }

    if (
        type.startsWith("video/") ||
        [".mp4", ".mov", ".mkv", ".avi"].some(ext => name.endsWith(ext))
    ) {
        return "Video";
    }

    if (
        type === "application/pdf" ||
        type.includes("word") ||
        type.includes("document") ||
        [".txt", ".pdf", ".doc", ".docx"].some(ext => name.endsWith(ext))
    ) {
        return "Document";
    }

    return "File";
}

function updateDropZoneUI() {
    const content = document.getElementById("drop-zone-content");
    if (!content) return;

    if (!selectedFiles.length) {
        content.innerHTML = `
            <div class="w-20 h-20 rounded-full bg-[#1A1625] flex items-center justify-center group-hover:bg-[#251B35] transition-colors duration-300">
                <i class="fa-solid fa-cloud-arrow-up text-3xl text-purple-500"></i>
            </div>

            <div class="space-y-2">
                <h3 class="text-xl font-medium text-white">Drop your files here</h3>
                <p class="text-gray-500 text-sm">or click to browse from your device</p>
            </div>

            <button type="button" class="bg-[#1F2937] hover:bg-[#374151] border border-gray-700 text-white px-6 py-2.5 rounded-lg flex items-center gap-2 transition-all mt-4 text-sm font-medium">
                <i class="fa-regular fa-file"></i>
                Browse Files
            </button>

            <div class="pt-6 mt-4 border-t border-gray-800 w-full max-w-sm mx-auto">
                <p class="text-xs text-gray-500">
                    Supported: MP3, WAV, M4A, FLAC, AAC, MP4, MOV, MKV, AVI, TXT, PDF, DOC, DOCX
                </p>
            </div>
        `;
        return;
    }

    const fileListHtml = selectedFiles
        .slice(0, 3)
        .map((file) => {
            const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
            return `
                <div class="flex items-center justify-between w-full bg-white/5 rounded-lg px-4 py-3 border border-white/5">
                    <div class="flex items-center gap-3 min-w-0">
                        <i class="fa-solid fa-file text-purple-400"></i>
                        <div class="min-w-0">
                            <p class="text-sm text-white truncate">${file.name}</p>
                            <p class="text-xs text-gray-500">${getFileTypeLabel(file)} • ${sizeMb} MB</p>
                        </div>
                    </div>
                </div>
            `;
        })
        .join("");

    const moreFilesNote =
        selectedFiles.length > 3
            ? `<p class="text-xs text-gray-500 mt-2">+${selectedFiles.length - 3} more file(s)</p>`
            : "";

    content.innerHTML = `
        <div class="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center">
            <i class="fa-solid fa-circle-check text-3xl text-green-400"></i>
        </div>

        <div class="space-y-2">
            <h3 class="text-xl font-medium text-white">Files Selected</h3>
            <p class="text-gray-400 text-sm">${selectedFiles.length} file(s) ready for processing</p>
        </div>

        <div class="w-full max-w-2xl space-y-3">
            ${fileListHtml}
            ${moreFilesNote}
        </div>

        <button type="button" id="change-files-btn" class="bg-[#1F2937] hover:bg-[#374151] border border-gray-700 text-white px-6 py-2.5 rounded-lg flex items-center gap-2 transition-all mt-4 text-sm font-medium">
            <i class="fa-solid fa-rotate"></i>
            Change Files
        </button>
    `;

    const changeFilesBtn = document.getElementById("change-files-btn");
    const fileInput = document.getElementById("file-input");
    if (changeFilesBtn && fileInput) {
        changeFilesBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            fileInput.click();
        });
    }
}

function handleFiles(fileList) {
    selectedFiles = Array.from(fileList || []);
    updateDropZoneUI();
}

function getProcessingOptions() {
    const checkboxes = document.querySelectorAll('#upload-view input[type="checkbox"]');

    return {
        generate_transcript: checkboxes[0]?.checked ?? true,
        refine_transcript: checkboxes[1]?.checked ?? true,
        speaker_diarization: checkboxes[2]?.checked ?? true,
        generate_summary: checkboxes[3]?.checked ?? true,
        sentiment_analysis: checkboxes[4]?.checked ?? true,
        enable_rag: checkboxes[5]?.checked ?? true,
    };
}

function bindUploadEvents() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    if (!dropZone || !fileInput) return;

    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, highlightDropZone, false);
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, unhighlightDropZone, false);
    });

    dropZone.addEventListener("drop", (event) => {
        const dt = event.dataTransfer;
        const files = dt?.files;
        handleFiles(files);
    });

    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", (event) => {
        handleFiles(event.target.files);
    });
}

async function uploadFilesAndProcess() {
    if (!selectedFiles.length) {
        throw new Error("Please select at least one file.");
    }

    const formData = new FormData();

    selectedFiles.forEach((file) => {
        formData.append("file", selectedFiles[0]);
    });

    const context = document.getElementById("audio-context")?.value?.trim() || "";
    formData.append("context", context);

    const options = getProcessingOptions();
    Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value));
    });

    const response = await fetch("http://127.0.0.1:8000/api/upload", {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        let message = "File processing failed.";
        try {
            const errorData = await response.json();
            message = errorData.detail || errorData.message || message;
        } catch (_) {
            // ignore parse failure
        }
        throw new Error(message);
    }

    const data = await response.json();
    currentUploadResponse = data;
    currentFileId = data.file_id || null;

    return data;
}