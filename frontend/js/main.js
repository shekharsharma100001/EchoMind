function setProcessingState(isLoading) {
    const processButton = document.getElementById("start-processing-btn");

    if (!processButton) return;

    processButton.disabled = isLoading;

    if (isLoading) {
        processButton.dataset.originalText = processButton.textContent;
        processButton.innerHTML = `
            <span class="inline-flex items-center gap-2">
                <i class="fa-solid fa-spinner fa-spin"></i>
                Processing...
            </span>
        `;
        processButton.classList.add("opacity-80", "cursor-not-allowed");
    } else {
        processButton.textContent = processButton.dataset.originalText || "Start Processing";
        processButton.classList.remove("opacity-80", "cursor-not-allowed");
    }
}

function populateFromResponse(data) {
    console.log("CONVERSATION DATA:", data.conversation);

    renderTranscript(data.cleaned_transcript || data.transcript || data.full_transcript || "");
    renderConversation(data.conversation || "");
    renderSummary(data.summary || data.structured_summary || "");
    renderSentiment(data.sentiment || data.sentiment_report || "");
}

function bindProcessingEvent() {
    const processButton = document.getElementById("start-processing-btn");
    if (!processButton) return;

    processButton.addEventListener("click", async () => {
        try {
            setProcessingState(true);

            const data = await uploadFilesAndProcess();
            populateFromResponse(data);

            const resultsSection = document.getElementById("results-section");
            if (resultsSection) {
                resultsSection.classList.remove("hidden");
                resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        } catch (error) {
            alert(error.message || "Something went wrong while processing the file.");
        } finally {
            setProcessingState(false);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindNavigation();
    bindUploadEvents();
    bindQaEvents();
    bindProcessingEvent();
    switchPage("home");
});